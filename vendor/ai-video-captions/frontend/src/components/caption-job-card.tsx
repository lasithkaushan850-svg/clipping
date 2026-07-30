"use client";

import Link from "next/link";
import { Film } from "lucide-react";
import { CAPTION_STYLE_CONFIGS } from "~/lib/caption-styles";
import { formatDuration } from "~/lib/utils";
import type { CaptionJob } from "~/types/caption";

interface CaptionJobCardProps {
  job: CaptionJob;
}

function getStatusIndicator(status: CaptionJob["status"]) {
  switch (status) {
    case "completed":
      return { color: "bg-green-500", label: "Completed" };
    case "processing":
    case "uploading":
      return { color: "bg-yellow-500", label: "Processing" };
    case "failed":
      return { color: "bg-red-500", label: "Failed" };
    default:
      return { color: "bg-gray-400", label: "Pending" };
  }
}

function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) return "just now";
  if (diffMinutes < 60)
    return `${diffMinutes} minute${diffMinutes === 1 ? "" : "s"} ago`;
  if (diffHours < 24)
    return `${diffHours} hour${diffHours === 1 ? "" : "s"} ago`;
  if (diffDays < 7)
    return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;

  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function CaptionJobCard({ job }: CaptionJobCardProps) {
  const styleConfig = CAPTION_STYLE_CONFIGS[job.captionStyle];
  const statusIndicator = getStatusIndicator(job.status);

  return (
    <Link
      href={`/captions/${job.id}`}
      className="group rounded-2xl bg-white p-4 shadow-sm transition-all hover:shadow-lg dark:bg-gray-800"
    >
      {/* Thumbnail */}
      <div className="mb-4 overflow-hidden rounded-xl bg-gradient-to-br from-gray-800 to-gray-950">
        <div
          className="flex items-center justify-center"
          style={{ aspectRatio: "16/9" }}
        >
          <Film className="h-10 w-10 text-gray-600" />
        </div>
      </div>

      {/* File name */}
      <p
        className="mb-2 truncate text-sm font-semibold text-gray-900 dark:text-white"
        title={job.originalFileName}
      >
        {job.originalFileName}
      </p>

      {/* Meta row */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {/* Caption style badge */}
        <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/50 px-2 py-0.5 text-xs font-medium text-foreground">
          <span
            className="h-3 w-3 flex-shrink-0 rounded-full ring-1 ring-black/20"
            style={{
              background: `linear-gradient(135deg, ${styleConfig.primaryColor} 50%, ${styleConfig.highlightColor} 50%)`,
            }}
          />
          {styleConfig.name}
        </span>

        {/* Duration */}
        {job.durationSeconds !== null && (
          <span className="text-xs text-muted-foreground">
            {formatDuration(job.durationSeconds)}
          </span>
        )}
      </div>

      {/* Status + date row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span
            className={`h-2 w-2 flex-shrink-0 rounded-full ${statusIndicator.color}`}
          />
          <span className="text-xs text-muted-foreground">
            {statusIndicator.label}
          </span>
        </div>
        <span className="text-xs text-muted-foreground">
          {formatRelativeDate(job.createdAt)}
        </span>
      </div>
    </Link>
  );
}
