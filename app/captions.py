"""Caption generation + burn-in.

The vendored ``ai-video-captions`` project does this beautifully with
``pysubs2`` — we re-implement the same approach here (slightly simplified)
so the three vendored repos stay untouched. Style definitions live in
``caption_styles.py`` and are shared with the frontend so the preview
matches the final render exactly.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Style definitions (mirrors vendor/ai-video-captions/backend/caption-styles.config.json)
# --------------------------------------------------------------------------- #
STYLES_FILE = Path(__file__).parent / "caption_styles.json"


def _load_styles() -> Dict[str, dict]:
    if not STYLES_FILE.exists():
        return {}
    with STYLES_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh).get("styles", {})


STYLES: Dict[str, dict] = _load_styles()


def list_styles() -> List[dict]:
    out = []
    for sid, s in STYLES.items():
        out.append({
            "id": sid,
            "name": s.get("name", sid),
            "description": s.get("description", ""),
            "bestFor": s.get("bestFor", ""),
            "previewText": s.get("previewText", "MOVE ME UP OR DOWN"),
            "primaryColor": s.get("primaryColor", "#FFFFFF"),
            "highlightColor": s.get("highlightColor", "#FFFF00"),
            "outlineColor": s.get("outlineColor", "#000000"),
        })
    return out


def get_style(style_id: str) -> dict:
    if style_id not in STYLES:
        # fall back to first available
        return next(iter(STYLES.values()))
    return STYLES[style_id]


# --------------------------------------------------------------------------- #
# ASS helpers
# --------------------------------------------------------------------------- #
def _hex_to_ass(hex_color: str, alpha: int = 0) -> str:
    """#RRGGBB → &HAA BB GG RR (ASS uses BGR + alpha)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return f"&H{alpha:02X}00FFFF"
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def _escape_ass(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


# --------------------------------------------------------------------------- #
# Generate the .ass subtitle file from a transcript + a clip range.
# --------------------------------------------------------------------------- #
def generate_ass(
    transcript: Dict,
    clip_start: float,
    clip_end: float,
    output_path: Path,
    style_id: str = "hormozi",
    caption_position: int = 10,
    video_width: int = 1080,
    video_height: int = 1920,
) -> bool:
    """Write a styled .ass file to ``output_path``.

    Returns True on success, False if there are no words in the clip.
    """
    style = get_style(style_id)
    language = transcript.get("language", "en")

    # Gather words that fall inside the clip range
    words_in_range: List[Dict] = []
    for seg in transcript.get("segments", []):
        for w in seg.get("words", []):
            ws = w.get("start")
            we = w.get("end")
            if ws is None or we is None:
                continue
            if we > clip_start and ws < clip_end:
                # Convert to clip-relative timestamps
                rel_s = max(0.0, ws - clip_start)
                rel_e = max(0.0, we - clip_start)
                if rel_e > rel_s:
                    text = w["word"].strip()
                    if text:
                        words_in_range.append({
                            "word": text,
                            "start": rel_s,
                            "end": rel_e,
                        })
    if not words_in_range:
        return False

    # Group into subtitle lines (max ~6 words, line break every 0.8s of silence)
    max_words_per_line = 6
    max_lines = 2
    lines: List[List[Dict]] = []
    current_line: List[Dict] = []
    current_pause = 0.0
    for w in words_in_range:
        if current_line:
            pause = w["start"] - current_line[-1]["end"]
        else:
            pause = 0.0
        if (current_pause > 0.6 and lines and len(lines[-1]) >= 2) or len(current_line) >= max_words_per_line:
            lines.append(current_line)
            current_line = [w]
            current_pause = pause
        else:
            current_line.append(w)
            current_pause = pause
    if current_line:
        lines.append(current_line)

    # For 2-line layout: combine pairs of consecutive short lines.
    if max_lines == 2:
        paired: List[List[Dict]] = []
        for i in range(0, len(lines), 2):
            chunk = lines[i]
            if i + 1 < len(lines) and len(chunk) + len(lines[i + 1]) <= max_words_per_line * 1.5:
                chunk = chunk + lines[i + 1]
            paired.append(chunk)
        lines = paired

    # Build the ASS file
    play_res_x = video_width
    play_res_y = video_height
    dim_scale = max(video_height / 1920, 0.35)
    font_size = int(style["fontSize"] * dim_scale)
    margin_v = int(play_res_y * caption_position / 100)
    outline = round(style["outlineSize"] * dim_scale, 1)
    shadow = round(style["shadowDepth"] * dim_scale, 1)
    primary = _hex_to_ass(style["primaryColor"])
    highlight = _hex_to_ass(style["highlightColor"])
    outline_c = _hex_to_ass(style["outlineColor"])
    shadow_c = _hex_to_ass(style.get("shadowColor", "#000000"), alpha=int(style.get("shadowAlpha", 128)))
    bold_flag = -1 if style.get("bold") else 0
    italic_flag = -1 if style.get("italic") else 0
    font_name = style["fontName"]
    anim = style.get("animationType", "highlight")
    letter_spacing = style.get("letterSpacing", 0)

    header = f"""[Script Info]
ScriptType: V4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
ScaledBorderAndShadow: yes
WrapStyle: 3

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary},{highlight},{outline_c},{shadow_c},{bold_flag},{italic_flag},0,0,100,100,{letter_spacing},0,1,{outline},{shadow},2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: List[str] = []
    for line in lines:
        if not line:
            continue
        line_start = line[0]["start"]
        line_end = line[-1]["end"]
        for idx, w in enumerate(line):
            # Event for this word: starts at w.start, ends at next word start
            event_end = line[idx + 1]["start"] if idx + 1 < len(line) else line_end
            text = w["word"].upper()
            text = _escape_ass(text)
            # Build text with the current word highlighted
            parts: List[str] = []
            for j, wj in enumerate(line):
                wt = _escape_ass(wj["word"].upper())
                if j == idx:
                    if anim == "scale":
                        parts.append(
                            f"{{\\fscx115\\fscy115\\c{highlight}}}{wt}{{\\r}}"
                        )
                    elif anim == "bounce":
                        bp = 120 if dim_scale >= 1.0 else 112
                        parts.append(
                            f"{{\\t(0,60,\\fscx{bp}\\fscy{bp})"
                            f"\\t(60,140,\\fscx100\\fscy100)"
                            f"\\c{highlight}}}{wt}{{\\r}}"
                        )
                    elif anim == "karaoke":
                        dur_cs = max(20, int((wj["end"] - wj["start"]) * 100))
                        parts.append(
                            f"{{\\kf{dur_cs}\\c{highlight}}}{wt}{{\\r}}"
                        )
                    else:
                        # default: simple colour swap
                        parts.append(f"{{\\c{highlight}}}{wt}{{\\r}}")
                else:
                    parts.append(wt)
            text_line = " ".join(parts)
            events.append(
                f"Dialogue: 0,{_fmt_ts(w['start'])},{_fmt_ts(event_end)},Default,,0,0,0,,{text_line}"
            )
    ass_text = header + "\n".join(events) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ass_text, encoding="utf-8")
    return True


def _fmt_ts(seconds: float) -> str:
    """Format seconds as H:MM:SS.cs (ASS timestamp)."""
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - h * 3600 - m * 60
    cs = int(round((s - int(s)) * 100))
    if cs == 100:
        cs = 0
        s += 1
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"


def burn_subtitles(
    video_path: Path,
    ass_path: Path,
    output_path: Path,
) -> Path:
    """Run ffmpeg to burn the .ass into the video."""
    import subprocess
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(video_path),
        "-vf", f"ass={ass_path}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800)
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg not installed") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg burn-in failed: {exc.stderr[-500:]}") from exc
    return output_path


def render_captioned_clip(
    source_mp4: Path,
    transcript: Dict,
    clip_start: float,
    clip_end: float,
    output_mp4: Path,
    style_id: str = "hormozi",
    caption_position: int = 10,
) -> bool:
    """Generate an .ass for the clip and burn it in. Returns True on success."""
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    ass_path = output_mp4.with_suffix(".ass")
    width, height = _probe_size(source_mp4)
    ok = generate_ass(
        transcript,
        clip_start=clip_start,
        clip_end=clip_end,
        output_path=ass_path,
        style_id=style_id,
        caption_position=caption_position,
        video_width=width,
        video_height=height,
    )
    if not ok:
        log.info("No transcript words in [%s, %s] — skipping captions", clip_start, clip_end)
        import shutil
        shutil.copy2(source_mp4, output_mp4)
        return True
    burn_subtitles(source_mp4, ass_path, output_mp4)
    ass_path.unlink(missing_ok=True)
    return True


def _probe_size(path: Path) -> tuple[int, int]:
    import json as _json
    import subprocess
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json", str(path),
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        s = _json.loads(out.stdout)["streams"][0]
        return int(s["width"]), int(s["height"])
    except Exception:  # noqa: BLE001
        return 1080, 1920
