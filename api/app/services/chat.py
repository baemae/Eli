"""Streams a chat reply, falling back to the next provider when one fails.

Fallback only happens before the first token is sent; once text has reached
the client, switching models mid-answer would produce a garbled reply, so a
later failure is reported as an error instead.
"""

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from app.providers.base import ProviderError
from app.providers.registry import ProviderRegistry
from app.schemas import ChatMessage, ChatRequest
from app.services.file_extractor import (
    FileExtractionError,
    extract_file_text,
)

logger = logging.getLogger(__name__)


@dataclass
class ChatEvent:
    type: str  # "meta" | "delta" | "error" | "done"
    data: dict[str, Any] = field(default_factory=dict)

    def to_sse(self) -> str:
        payload = json.dumps(self.data, ensure_ascii=False)

        if self.type == "delta":
            return f"data: {payload}\n\n"

        return f"event: {self.type}\ndata: {payload}\n\n"


NO_MODELS_MESSAGE = (
    "No AI model is available. Install a local model with `ollama pull llama3.2`, "
    "or add a cloud API key (Anthropic, OpenAI, Gemini, Grok or Meta) to the API's .env file."
)


def _prepare_file_messages(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Extract attached files and turn them into normal text messages."""

    prepared: list[ChatMessage] = []

    for message in messages:
        if not isinstance(message.content, list):
            prepared.append(message)
            continue

        new_parts: list[dict[str, Any]] = []

        for part in message.content:
            if part.get("type") != "file":
                new_parts.append(part)
                continue

            file_info = part.get("file")

            if not isinstance(file_info, dict):
                raise FileExtractionError("Invalid file attachment.")

            data_url = file_info.get("data")
            filename = file_info.get("name", "attachment")
            mime_type = file_info.get("type", "")

            if not isinstance(data_url, str):
                raise FileExtractionError("Invalid file attachment.")

            if not isinstance(filename, str):
                filename = "attachment"

            if not isinstance(mime_type, str):
                mime_type = ""

            extracted_text = extract_file_text(
                data_url=data_url,
                filename=filename,
                mime_type=mime_type,
            )

            if not extracted_text.strip():
                extracted_text = "(The attached file contains no extractable text.)"

            new_parts.append(
                {
                    "type": "text",
                    "text": (
                        f"\n\n[Attached file: {filename}]\n"
                        f"{extracted_text}\n"
                        f"[End of attached file: {filename}]\n"
                    ),
                }
            )

        prepared.append(
            ChatMessage(
                role=message.role,
                content=new_parts,
            )
        )

    return prepared


class ChatService:
    def __init__(
        self,
        registry: ProviderRegistry,
        system_prompt: str,
        allow_fallback: bool,
    ):
        self._registry = registry
        self._system_prompt = system_prompt
        self._allow_fallback = allow_fallback

    def _with_system(
        self,
        messages: list[ChatMessage],
    ) -> list[ChatMessage]:
        if not self._system_prompt or any(
            m.role == "system" for m in messages
        ):
            return messages

        return [
            ChatMessage(
                role="system",
                content=self._system_prompt,
            ),
            *messages,
        ]

    async def stream(
        self,
        request: ChatRequest,
    ) -> AsyncIterator[ChatEvent]:
        try:
            candidates = await self._registry.candidates(
                request.provider,
                request.model,
                self._allow_fallback,
            )
        except ProviderError as exc:
            yield ChatEvent(
                "error",
                {"message": str(exc)},
            )
            return

        if not candidates:
            yield ChatEvent(
                "error",
                {"message": NO_MODELS_MESSAGE},
            )
            return

        try:
            messages = _prepare_file_messages(
                request.messages
            )
        except FileExtractionError as exc:
            yield ChatEvent(
                "error",
                {"message": str(exc)},
            )
            return

        messages = self._with_system(messages)
        failures: list[str] = []

        for candidate in candidates:
            provider, model = (
                candidate.provider,
                candidate.model,
            )

            started = False

            try:
                async for delta in provider.stream_chat(
                    model,
                    messages,
                    request.temperature,
                ):
                    if not started:
                        started = True

                        yield ChatEvent(
                            "meta",
                            {
                                "provider": provider.id,
                                "provider_label": provider.label,
                                "model": model,
                                "local": provider.local,
                                "fallback": bool(failures),
                                "notice": "; ".join(failures) or None,
                            },
                        )

                    yield ChatEvent(
                        "delta",
                        {"delta": delta},
                    )

            except ProviderError as exc:
                logger.warning(
                    "Provider %s/%s failed: %s",
                    provider.id,
                    model,
                    exc,
                )

                if started:
                    yield ChatEvent(
                        "error",
                        {"message": str(exc)},
                    )
                    return

                failures.append(str(exc))
                self._registry.invalidate()
                continue

            if not started:
                yield ChatEvent(
                    "meta",
                    {
                        "provider": provider.id,
                        "provider_label": provider.label,
                        "model": model,
                        "local": provider.local,
                        "fallback": bool(failures),
                        "notice": "; ".join(failures) or None,
                    },
                )

            yield ChatEvent("done", {})
            return

        yield ChatEvent(
            "error",
            {
                "message": " · ".join(failures)
                or NO_MODELS_MESSAGE
            },
        )