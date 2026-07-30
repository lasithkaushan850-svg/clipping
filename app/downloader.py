"""YouTube download + metadata extraction.

We use ``yt-dlp`` because it handles the messy bits (cookie refresh, age
gates, format selection) better than anything else. For the 2-hour-long
videos the user mentioned, we always grab a single progressive MP4 when
possible so the file is one piece and we don't have to merge DASH streams.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import config


@dataclass
class SourceMeta:
    title: str
    channel: str
    duration: float
    thumbnail: str
    video_id: str
    url: str


def _resolution_to_format(res: str) -> str:
    """Map our friendly resolution string to a yt-dlp format selector."""
    try:
        height = int(res)
    except ValueError:
        height = 720
    # Prefer a single progressive MP4 at the requested height, but fall back
    # to anything ≤ that height. Progressive files don't need merging.
    return (
        f"bv*[height<={height}][ext=mp4][vcodec!=none][acodec!=none]"
        f"+ba[ext=m4a]/b[height<={height}][ext=mp4] / bv*+ba/b"
    )


def probe_metadata(url: str) -> SourceMeta:
    """Fetch title / channel / duration without downloading the video.

    Uses ``yt-dlp --dump-json`` which is much faster than a full download.
    """
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        "--no-warnings",
        "--no-playlist",
        url,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "yt-dlp is not installed. Run `pip install yt-dlp` and try again."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"yt-dlp metadata failed: {exc.stderr.strip()}") from exc

    try:
        data = json.loads(out.stdout.splitlines()[0])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("yt-dlp returned no metadata") from exc

    return SourceMeta(
        title=data.get("title") or "Untitled",
        channel=data.get("uploader") or data.get("channel") or "Unknown",
        duration=float(data.get("duration") or 0),
        thumbnail=data.get("thumbnail") or "",
        video_id=data.get("id") or "",
        url=url,
    )


def download_youtube(url: str, resolution: str, out_dir: Path) -> Path:
    """Download the full video to ``out_dir/source.<ext>``.

    Returns the path to the downloaded file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(out_dir / "source.%(ext)s")
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--no-warnings",
        "--no-part",
        "--restrict-filenames",
        "-f", _resolution_to_format(resolution),
        "--merge-output-format", "mp4",
        "-o", out_template,
        url,
    ]
    try:
        subprocess.run(cmd, check=True, timeout=60 * 60)  # 1h cap
    except FileNotFoundError as exc:
        raise RuntimeError(
            "yt-dlp is not installed. Run `pip install yt-dlp` and try again."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"yt-dlp download failed: {exc}") from exc

    # yt-dlp writes the extension based on what was actually chosen. Find it.
    candidates = sorted(out_dir.glob("source.*"))
    candidates = [c for c in candidates if c.suffix.lower() in (".mp4", ".mkv", ".webm")]
    if not candidates:
        raise RuntimeError(f"yt-dlp did not produce a video file in {out_dir}")
    # Pick the largest file in case multiple streams landed.
    return max(candidates, key=lambda p: p.stat().st_size)


YOUTUBE_URL_RE = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w\-]+"
)


def is_youtube_url(text: str) -> bool:
    return bool(YOUTUBE_URL_RE.match(text.strip()))


def copy_uploaded_file(src_path: Path, dest_dir: Path) -> Path:
    """Copy a user-uploaded video into the source directory."""
    import shutil
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = src_path.suffix.lower() or ".mp4"
    dest = dest_dir / f"source{ext}"
    shutil.copy2(src_path, dest)
    return dest


def probe_local_duration(path: Path) -> float:
    """Return duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return 0.0
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0
