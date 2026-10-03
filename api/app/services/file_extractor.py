import base64
import io
from typing import Any

from docx import Document
from pypdf import PdfReader


class FileExtractionError(Exception):
    """Raised when an attached file cannot be extracted."""


def _decode_data_url(data_url: str) -> bytes:
    """Convert a base64 data URL into raw file bytes."""

    if not data_url.startswith("data:"):
        raise FileExtractionError("Invalid file data.")

    try:
        encoded = data_url.split(",", 1)[1]
        return base64.b64decode(encoded)
    except (ValueError, IndexError) as exc:
        raise FileExtractionError("Invalid file data.") from exc


def extract_file_text(
    *,
    data_url: str,
    filename: str,
    mime_type: str,
) -> str:
    """Extract readable text from a supported attachment."""

    data = _decode_data_url(data_url)

    lower_name = filename.lower()

    # TXT
    if mime_type == "text/plain" or lower_name.endswith(".txt"):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise FileExtractionError(
                f"Could not read {filename} as UTF-8 text."
            ) from exc

    # PDF
    if mime_type == "application/pdf" or lower_name.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(data))
            pages: list[str] = []

            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(text)

            return "\n\n".join(pages)
        except Exception as exc:
            raise FileExtractionError(
                f"Could not extract text from {filename}."
            ) from exc

    # DOCX
    if (
        mime_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or lower_name.endswith(".docx")
    ):
        try:
            document = Document(io.BytesIO(data))

            paragraphs = [
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            return "\n\n".join(paragraphs)
        except Exception as exc:
            raise FileExtractionError(
                f"Could not extract text from {filename}."
            ) from exc

    raise FileExtractionError(
        f"Unsupported file type: {filename}"
    )