"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, X, FileVideo } from "lucide-react";
import { cn, formatBytes, formatDuration } from "~/lib/utils";

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500 MB
const ACCEPTED_TYPES = ["video/mp4", "video/quicktime", "video/webm"];
const ACCEPT_ATTR = ".mp4,.mov,.webm";

interface VideoDropzoneProps {
  file: File | null;
  onFileSelect: (file: File, duration: number) => void;
  onFileClear: () => void;
  uploadProgress: number | null;
  disabled?: boolean;
}

function getVideoDuration(file: File): Promise<number> {
  return new Promise((resolve, reject) => {
    const video = document.createElement("video");
    video.preload = "metadata";

    const url = URL.createObjectURL(file);
    video.src = url;

    video.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      resolve(video.duration);
    };

    video.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Failed to load video metadata"));
    };
  });
}

export function VideoDropzone({
  file,
  onFileSelect,
  onFileClear,
  uploadProgress,
  disabled,
}: VideoDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);

  const validateAndSelect = useCallback(
    async (selected: File) => {
      setError(null);

      if (!ACCEPTED_TYPES.includes(selected.type)) {
        setError("Unsupported format. Please use MP4, MOV, or WebM.");
        return;
      }

      if (selected.size > MAX_FILE_SIZE) {
        setError("File too large. Maximum size is 500 MB.");
        return;
      }

      try {
        const dur = await getVideoDuration(selected);
        setDuration(dur);
        onFileSelect(selected, dur);
      } catch {
        setError("Could not read video duration. Please try another file.");
      }
    },
    [onFileSelect],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragOver(false);

      const dropped = e.dataTransfer.files[0];
      if (dropped) {
        void validateAndSelect(dropped);
      }
    },
    [validateAndSelect],
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (selected) {
        void validateAndSelect(selected);
      }
      // Reset input so re-selecting the same file works
      e.target.value = "";
    },
    [validateAndSelect],
  );

  const isUploading = uploadProgress !== null;

  return (
    <div style={{ fontFamily: "var(--font-outfit)" }}>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT_ATTR}
        onChange={handleInputChange}
        className="hidden"
        disabled={disabled}
      />

      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        onClick={!file && !disabled ? handleClick : undefined}
        onKeyDown={(e) => {
          if (!file && !disabled && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            handleClick();
          }
        }}
        onDrop={!file && !disabled ? handleDrop : undefined}
        onDragOver={!file && !disabled ? handleDragOver : undefined}
        onDragLeave={!file && !disabled ? handleDragLeave : undefined}
        className={cn(
          "rounded-xl border-2 border-dashed p-8 transition-colors duration-200",
          disabled && "pointer-events-none opacity-50",
          !file && !disabled && "cursor-pointer",
          isDragOver
            ? "border-[#459F94] bg-[#459F94]/10"
            : "border-border hover:border-[#459F94]/50",
          file && "border-solid",
        )}
      >
        {/* Empty state */}
        {!file && (
          <div className="flex flex-col items-center gap-3 text-center">
            <div className="rounded-full bg-muted p-3">
              <Upload className="h-6 w-6 text-muted-foreground" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                Drop your video here or click to browse
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                MP4, MOV, or WebM up to 500MB
              </p>
            </div>
          </div>
        )}

        {/* File selected state */}
        {file && !isUploading && (
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-muted p-2">
              <FileVideo className="h-5 w-5 text-[#459F94]" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-foreground">
                {file.name}
              </p>
              <p className="text-xs text-muted-foreground">
                {formatBytes(file.size)}
                {duration !== null && ` \u00B7 ${formatDuration(duration)}`}
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onFileClear();
                setDuration(null);
                setError(null);
              }}
              className="rounded-full p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              disabled={disabled}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Uploading state */}
        {file && isUploading && (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-muted p-2">
                <FileVideo className="h-5 w-5 text-[#459F94]" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {file.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatBytes(file.size)}
                </p>
              </div>
              <span className="text-sm font-medium text-[#459F94]">
                {Math.round(uploadProgress)}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-[#459F94] transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <p className="mt-2 text-sm text-destructive">{error}</p>
      )}
    </div>
  );
}
