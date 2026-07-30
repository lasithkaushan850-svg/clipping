"use client";

import { cn } from "~/lib/utils";
import { CAPTION_STYLES, CAPTION_STYLE_CONFIGS } from "~/lib/caption-styles";
import type { CaptionStyle } from "~/types/caption";

interface CaptionStylePickerProps {
  selectedStyle: CaptionStyle;
  onStyleChange: (style: CaptionStyle) => void;
}

export function CaptionStylePicker({
  selectedStyle,
  onStyleChange,
}: CaptionStylePickerProps) {
  const selectedConfig = CAPTION_STYLE_CONFIGS[selectedStyle];

  return (
    <div
      className="space-y-3"
      style={{ fontFamily: "var(--font-outfit)" }}
    >
      <div className="flex flex-wrap gap-2">
        {CAPTION_STYLES.map((style) => {
          const config = CAPTION_STYLE_CONFIGS[style];
          return (
            <button
              key={style}
              type="button"
              onClick={() => onStyleChange(style)}
              className={cn(
                "flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium",
                "border-2 transition-all duration-150",
                "cursor-pointer",
                selectedStyle === style
                  ? "border-[#459F94] bg-[#459F94]/10"
                  : "border-border hover:border-[#459F94]/50 hover:bg-accent/50",
              )}
            >
              <span
                className="h-4 w-4 rounded-full ring-1 ring-black/20"
                style={{
                  background: `linear-gradient(135deg, ${config.primaryColor} 50%, ${config.highlightColor} 50%)`,
                }}
              />
              {config.name}
            </button>
          );
        })}
      </div>

      <div className="rounded-lg border border-border bg-muted/50 p-3">
        <p className="text-xs text-muted-foreground">
          <span className="font-medium text-foreground">
            {selectedConfig.name}
          </span>{" "}
          — {selectedConfig.description}
        </p>
        <p className="mt-1 text-[10px] text-muted-foreground">
          Best for: {selectedConfig.bestFor}
        </p>
      </div>
    </div>
  );
}
