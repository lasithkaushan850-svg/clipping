"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "~/lib/utils";
import { CAPTION_POSITION_MIN, CAPTION_POSITION_MAX } from "~/lib/caption-styles";
import type { CaptionStyleConfig } from "~/types/caption";

interface CaptionPreviewProps {
  style: CaptionStyleConfig;
  position: number;
  onPositionChange: (position: number) => void;
}

const POSITION_PRESETS = [
  { label: "Top", value: 45 },
  { label: "Middle", value: 30 },
  { label: "Bottom", value: 10 },
] as const;

const SAMPLE_WORDS = ["SAMPLE", "TEXT"];

function getAnimationClass(animationType: string): string {
  switch (animationType) {
    case "karaoke":
      return "animate-caption-karaoke";
    case "scale":
      return "animate-caption-scale";
    case "bounce":
      return "animate-caption-bounce";
    case "highlight":
    default:
      return "animate-caption-highlight";
  }
}

function buildTextShadow(
  outlineColor: string,
  outlineSize: number,
  shadowDepth: number,
): string {
  return [
    `${outlineSize}px ${outlineSize}px 0 ${outlineColor}`,
    `-${outlineSize}px -${outlineSize}px 0 ${outlineColor}`,
    `${outlineSize}px -${outlineSize}px 0 ${outlineColor}`,
    `-${outlineSize}px ${outlineSize}px 0 ${outlineColor}`,
    `0 ${shadowDepth}px ${shadowDepth * 2}px rgba(0,0,0,0.5)`,
  ].join(", ");
}

export function CaptionPreview({
  style,
  position,
  onPositionChange,
}: CaptionPreviewProps) {
  const screenRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const isDraggingRef = useRef(false);

  const animationClass = getAnimationClass(style.animationType);

  const cssVars = {
    "--caption-primary": style.primaryColor,
    "--caption-highlight": style.highlightColor,
  } as React.CSSProperties;

  const textShadow = buildTextShadow(
    style.outlineColor,
    style.previewOutlineSize,
    style.previewShadowDepth,
  );

  // Convert clientY to position percentage
  const clientYToPosition = useCallback(
    (clientY: number) => {
      if (!screenRef.current) return position;

      const rect = screenRef.current.getBoundingClientRect();
      const relativeY = rect.bottom - clientY;
      const percentage = (relativeY / rect.height) * 100;

      return Math.round(
        Math.max(CAPTION_POSITION_MIN, Math.min(CAPTION_POSITION_MAX, percentage)),
      );
    },
    [position],
  );

  const handleDragStart = useCallback(() => {
    setIsDragging(true);
    isDraggingRef.current = true;
  }, []);

  useEffect(() => {
    const handleDragMove = (e: MouseEvent | TouchEvent) => {
      if (!isDraggingRef.current) return;

      const clientY =
        "touches" in e
          ? (e.touches[0]?.clientY ?? 0)
          : e.clientY;

      onPositionChange(clientYToPosition(clientY));
    };

    const handleDragEnd = () => {
      if (!isDraggingRef.current) return;
      isDraggingRef.current = false;
      setIsDragging(false);
    };

    window.addEventListener("mousemove", handleDragMove);
    window.addEventListener("mouseup", handleDragEnd);
    window.addEventListener("touchmove", handleDragMove);
    window.addEventListener("touchend", handleDragEnd);

    return () => {
      window.removeEventListener("mousemove", handleDragMove);
      window.removeEventListener("mouseup", handleDragEnd);
      window.removeEventListener("touchmove", handleDragMove);
      window.removeEventListener("touchend", handleDragEnd);
    };
  }, [clientYToPosition, onPositionChange]);

  return (
    <div
      className="flex flex-col items-center gap-3"
      style={{ fontFamily: "var(--font-outfit)" }}
    >
      {/* Phone frame */}
      <div
        className="relative mx-auto rounded-[2rem] bg-gray-900 p-1.5 shadow-2xl ring-1 ring-gray-700"
        style={{ width: 220 }}
      >
        {/* Dynamic Island */}
        <div className="absolute top-3 left-1/2 z-10 h-6 w-24 -translate-x-1/2 rounded-full bg-black ring-1 ring-gray-800" />

        {/* Inner screen */}
        <div className="relative overflow-hidden rounded-[1.7rem] bg-black" style={{ aspectRatio: "9 / 19.5" }}>
          <div
            ref={screenRef}
            className="relative h-full w-full"
          >
            {/* Dark gradient background */}
            <div className="absolute inset-0 bg-gradient-to-b from-gray-900 via-gray-950 to-black" />

            {/* Draggable caption overlay */}
            <div
              className={cn(
                "absolute right-0 left-0 flex justify-center px-3 transition-[bottom] duration-100",
                "touch-none select-none",
                isDragging ? "cursor-grabbing" : "cursor-grab",
              )}
              style={{ bottom: `${position}%` }}
              onMouseDown={handleDragStart}
              onTouchStart={handleDragStart}
            >
              <span
                className="pointer-events-none text-center leading-tight"
                style={{
                  color: style.primaryColor,
                  fontFamily: `${style.fontName}, ${style.fontNameFallback}, sans-serif`,
                  fontWeight: style.bold ? 700 : 400,
                  fontStyle: style.italic ? "italic" : "normal",
                  fontSize: `${style.previewFontSize}px`,
                  letterSpacing: `${style.previewLetterSpacing}px`,
                  textShadow,
                  ...cssVars,
                }}
              >
                {SAMPLE_WORDS.map((word, i) => (
                  <span key={word}>
                    {i > 0 && " "}
                    <span
                      className={animationClass}
                      style={{
                        ...cssVars,
                        "--delay": `${i * 0.5}s`,
                      } as React.CSSProperties}
                    >
                      {word}
                    </span>
                  </span>
                ))}
              </span>
            </div>

            {/* Drag hint */}
            {!isDragging && (
              <div
                className="absolute right-0 left-0 text-center text-[9px] text-gray-500"
                style={{ bottom: `calc(${position}% - 18px)` }}
              >
                Drag to reposition
              </div>
            )}

            {/* Home indicator */}
            <div className="absolute bottom-1.5 left-1/2 h-1 w-28 -translate-x-1/2 rounded-full bg-gray-600" />
          </div>
        </div>
      </div>

      {/* Position presets */}
      <div className="flex gap-2">
        {POSITION_PRESETS.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => onPositionChange(preset.value)}
            className={cn(
              "rounded-full px-3 py-1 text-xs font-medium transition-all duration-150",
              "border cursor-pointer",
              position === preset.value
                ? "border-[#459F94] bg-[#459F94]/10 text-[#459F94]"
                : "border-border text-muted-foreground hover:border-[#459F94]/50",
            )}
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}
