"use client";

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import {
  ArrowUpIcon,
  AudioLinesIcon,
  ImagePlusIcon,
  SquareIcon,
  XIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { APP_CONFIG } from "@/lib/config";
import { cn } from "@/lib/utils";

export type ComposerImage = {
  dataUrl: string;
  name: string;
  type: string;
};

export function Composer({
  onSend,
  onStop,
  onVoice,
  streaming,
  disabled,
  placeholder = `Message ${APP_CONFIG.appName}…`,
  autoFocus,
}: {
  onSend: (text: string, image?: ComposerImage) => void;
  onStop: () => void;
  onVoice?: () => void;
  streaming: boolean;
  disabled?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
}) {
  const [value, setValue] = useState("");
  const [image, setImage] = useState<ComposerImage | null>(null);

  const ref = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (autoFocus && window.matchMedia("(min-width: 768px)").matches) {
      ref.current?.focus();
    }
  }, [autoFocus]);

  const chooseImage = (file?: File) => {
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      window.alert("Please select an image file.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      window.alert("Image must be smaller than 10 MB.");
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      if (typeof reader.result !== "string") return;

      setImage({
        dataUrl: reader.result,
        name: file.name,
        type: file.type,
      });
    };

    reader.readAsDataURL(file);
  };

  const submit = (e?: FormEvent) => {
    e?.preventDefault();

    if (streaming) return onStop();
    if ((!value.trim() && !image) || disabled) return;

    onSend(value.trim(), image ?? undefined);

    setValue("");
    setImage(null);

    if (fileRef.current) {
      fileRef.current.value = "";
    }
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    const touch = window.matchMedia("(hover: none)").matches;

    if (
      e.key === "Enter" &&
      !e.shiftKey &&
      !e.nativeEvent.isComposing &&
      !touch
    ) {
      e.preventDefault();
      submit();
    }
  };

  const canSend =
    streaming || (!!value.trim() && !disabled) || (!!image && !disabled);

  const showVoice = !!onVoice && !streaming && !value.trim() && !image;

  return (
    <form
      onSubmit={submit}
      className="mx-auto w-full max-w-3xl rounded-3xl border bg-card p-2.5 pl-4 shadow-sm transition-colors focus-within:border-ring"
    >
      {image && (
        <div className="mb-2 flex items-center gap-2">
          <div className="relative">
            <img
              src={image.dataUrl}
              alt={image.name}
              className="size-16 rounded-xl border object-cover"
            />

            <button
              type="button"
              onClick={() => setImage(null)}
              className="absolute -right-2 -top-2 grid size-5 place-items-center rounded-full border bg-background"
              aria-label="Remove image"
            >
              <XIcon className="size-3" />
            </button>
          </div>

          <span className="max-w-48 truncate text-xs text-muted-foreground">
            {image.name}
          </span>
        </div>
      )}

      <label htmlFor="composer" className="sr-only">
        Message
      </label>

      <textarea
        id="composer"
        ref={ref}
        rows={1}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        enterKeyHint="send"
        className="field-sizing-content max-h-52 min-h-7 w-full resize-none bg-transparent py-1.5 text-[15px] leading-6 outline-none placeholder:text-muted-foreground"
      />

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => chooseImage(e.target.files?.[0])}
      />

      <div className="mt-1 flex items-center justify-between">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              size="icon"
              variant="ghost"
              disabled={streaming || disabled}
              onClick={() => fileRef.current?.click()}
              aria-label="Attach image"
              className="rounded-full"
            >
              <ImagePlusIcon />
            </Button>
          </TooltipTrigger>

          <TooltipContent>Attach image</TooltipContent>
        </Tooltip>

        <div className="flex items-center">
          {showVoice ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="icon"
                  onClick={onVoice}
                  aria-label="Start voice mode"
                  className="rounded-full"
                >
                  <AudioLinesIcon />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Start voice mode</TooltipContent>
            </Tooltip>
          ) : (
            <Button
              type="submit"
              size="icon"
              disabled={!canSend}
              aria-label={streaming ? "Stop generating" : "Send message"}
              className={cn("rounded-full", !canSend && "opacity-30")}
            >
              {streaming ? (
                <SquareIcon className="size-3.5 fill-current" />
              ) : (
                <ArrowUpIcon />
              )}
            </Button>
          )}
        </div>
      </div>
    </form>
  );
}