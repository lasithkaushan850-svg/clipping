"""Video clipping + 9:16 face-tracking reframe.

The pipeline per candidate:

  1. ``ffmpeg -ss START -to END -i source … cut.mp4``  — hard cut subclip.
  2. OpenCV face tracking on the cut clip → produce a silent reframed
     9:16 (or chosen aspect) mp4 where the speaker is kept centred.
  3. ``ffmpeg`` mux → re-attach the original audio track.

This mirrors ``vendor/AI-Youtube-Shorts-Generator/shorts_generator/local/clipper.py``
but is inlined here so the three vendored projects stay untouched and
we can extend it (hook text overlay, B-roll, etc.) without forking.
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

log = logging.getLogger(__name__)


def _ratio(aspect: str) -> float:
    try:
        w, h = aspect.split(":")
        return float(w) / float(h)
    except (ValueError, ZeroDivisionError):
        return 9.0 / 16.0


def _run(cmd, timeout: int = 1800) -> None:
    """Run a subprocess command, raising on failure."""
    log.debug("$ %s", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Required tool not on PATH: {cmd[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "")[-500:]
        raise RuntimeError(f"Command failed: {' '.join(cmd[:6])}…\n{stderr}") from exc


def cut_subclip(source: Path, start: float, end: float, out_path: Path) -> Path:
    """Hard cut a subclip, re-encoding both video and audio."""
    duration = end - start
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{max(0.0, start):.3f}",
        "-i", str(source),
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart",
        str(out_path),
    ]
    _run(cmd)
    return out_path


def reframe_aspect(
    in_path: Path,
    out_path: Path,
    aspect_ratio: str = "9:16",
) -> Path:
    """Crop the cut to the target aspect ratio with optional face tracking.

    We try OpenCV's Haar cascade for face tracking. If OpenCV isn't
    available, we fall back to a centred static crop.
    """
    try:
        import cv2  # type: ignore
        return _reframe_with_faces(in_path, out_path, aspect_ratio)
    except ImportError:
        return _reframe_static(in_path, out_path, aspect_ratio)


def _reframe_static(in_path: Path, out_path: Path, aspect_ratio: str) -> Path:
    target_ratio = _ratio(aspect_ratio)
    # Probe the source
    info = _probe(in_path)
    src_w, src_h = info["width"], info["height"]
    if target_ratio < src_w / src_h:
        crop_h = src_h
        crop_w = int(crop_h * target_ratio)
    else:
        crop_w = src_w
        crop_h = int(crop_w / target_ratio)
    crop_w -= crop_w % 2
    crop_h -= crop_h % 2
    x = (src_w - crop_w) // 2
    y = (src_h - crop_h) // 2
    vf = f"crop={crop_w}:{crop_h}:{x}:{y}"
    silent = out_path.with_suffix(".silent.mp4")
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_path),
        "-vf", vf, "-an",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        str(silent),
    ]
    _run(cmd)
    _mux_audio(silent, in_path, out_path)
    silent.unlink(missing_ok=True)
    return out_path


def _reframe_with_faces(in_path: Path, out_path: Path, aspect_ratio: str) -> Path:
    import cv2  # type: ignore
    target_ratio = _ratio(aspect_ratio)
    cap = cv2.VideoCapture(str(in_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open {in_path}")
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FRAME_FPS) or 30.0

    if target_ratio < src_w / src_h:
        crop_h = src_h
        crop_w = int(crop_h * target_ratio)
    else:
        crop_w = src_w
        crop_h = int(crop_w / target_ratio)
    crop_w -= crop_w % 2
    crop_h -= crop_h % 2

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    silent = out_path.with_suffix(".silent.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(silent), fourcc, fps, (crop_w, crop_h))

    last_cx: Optional[int] = None
    last_cy: Optional[int] = None
    smoothing = 0.18
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )
        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            cx = x + w // 2
            cy = y + h // 2
            if last_cx is None:
                last_cx, last_cy = cx, cy
            else:
                last_cx = int(last_cx + (cx - last_cx) * smoothing)
                last_cy = int(last_cy + (cy - last_cy) * smoothing)
        if last_cx is None:
            last_cx, last_cy = src_w // 2, src_h // 2
        x0 = max(0, min(src_w - crop_w, last_cx - crop_w // 2))
        y0 = max(0, min(src_h - crop_h, last_cy - crop_h // 2))
        cropped = frame[y0: y0 + crop_h, x0: x0 + crop_w]
        writer.write(cropped)

    cap.release()
    writer.release()
    _mux_audio(silent, in_path, out_path)
    silent.unlink(missing_ok=True)
    return out_path


def _mux_audio(silent_video: Path, audio_source: Path, out_path: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(silent_video),
        "-i", str(audio_source),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
        "-map", "0:v:0", "-map", "1:a:0?", "-shortest",
        "-movflags", "+faststart",
        str(out_path),
    ]
    _run(cmd)


def _probe(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json", str(path),
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        import json as _json
        data = _json.loads(out.stdout)
        s = data["streams"][0]
        return {"width": int(s["width"]), "height": int(s["height"])}
    except Exception:  # noqa: BLE001
        return {"width": 1920, "height": 1080}


def overlay_hook_text(
    in_path: Path,
    out_path: Path,
    text: str,
    duration: float = 2.5,
) -> Path:
    """Burn a short hook banner at the top of the clip.

    Uses ffmpeg's drawtext with a system font. Skips silently if no
    drawtext support (very old ffmpeg builds).
    """
    if not text or not text.strip():
        # No hook — just copy the stream.
        import shutil
        shutil.copy2(in_path, out_path)
        return out_path
    safe = text.replace("'", "").replace(":", "\\:").replace("\\", "\\\\")[:80]
    drawtext = (
        f"drawtext=fontcolor=white:fontsize=58:box=1:boxcolor=black@0.55:boxborderw=18:"
        f"x=(w-text_w)/2:y=80:text='{safe}':enable='lt(t,{duration})'"
    )
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_path),
        "-vf", drawtext,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(out_path),
    ]
    try:
        _run(cmd)
    except RuntimeError:
        # drawtext not available — fall back to a plain copy
        import shutil
        shutil.copy2(in_path, out_path)
    return out_path
