"""Viral-moment detection.

This module scores segments of a transcript for *virality* and returns
ranked highlight candidates. Two scoring engines are supported and
combined into a single ``success_rate`` percentage that the UI shows:

  1. **LLM scoring** — uses Gemini (free tier) or OpenAI to read the
     transcript and pick out hook / emotional-peak / reveal moments.
     Implements the same prompt philosophy as
     ``vendor/AI-Youtube-Shorts-Generator/shorts_generator/highlights.py``
     but with a simpler, more robust JSON contract and a custom scoring
     rubric tailored to short-form success.

  2. **Audio/keyword scoring** (free fallback) — runs entirely offline
     using:
       • audio energy peaks from the source file
       • laughter / applause keyword spotting
       • strong-emotion keyword spotting
       • sentence-length variance and question density
     Always runs alongside the LLM score so we can blend the two.

The LLM call is opt-out via ``LLM_OFFLINE_ONLY=true`` in ``.env``.
"""
from __future__ import annotations

import json
import logging
import math
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from . import config
from .jobs import Candidate

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
TARGET_CLIP_MIN = 25.0
TARGET_CLIP_MAX = 90.0
TARGET_CLIP_IDEAL = 55.0

VIRAL_KEYWORDS = {
    # strength 2 — top-tier hooks
    "secret": 2.0, "nobody": 2.0, "everyone": 1.6, "actually": 1.4,
    "realize": 1.6, "realised": 1.6, "realized": 1.6, "crazy": 1.8,
    "insane": 1.8, "shocking": 2.0, "truth": 1.6, "lie": 1.4,
    "lies": 1.4, "myth": 1.6, "wrong": 1.4, "never": 1.2, "always": 1.0,
    "lesson": 1.4, "hack": 1.8, "trick": 1.4, "free": 1.0, "easy": 1.0,
    "immediately": 1.2, "guaranteed": 1.4, "promise": 1.0, "love": 0.8,
    "hate": 1.0, "best": 1.0, "worst": 1.2, "first": 0.6, "last": 0.6,
    # emotional / viral reactions
    "literally": 1.4, "honestly": 1.2, "obviously": 1.0, "savage": 1.6,
    "brutal": 1.6, "wild": 1.6, "plot twist": 2.0, "unbelievable": 1.8,
    "mind-blowing": 1.8, "epic": 1.4, "legend": 1.2, "genius": 1.4,
    "stupid": 1.0, "idiot": 1.0, "fool": 1.0,
}

LAUGHTER_RE = re.compile(
    r"\b(ha(ha)+|he(he)+|lol|lmao|haha|rofl)\b", re.IGNORECASE
)
APPLAUSE_RE = re.compile(r"\b(applause|cheer|clap|cheering)\b", re.IGNORECASE)
QUESTION_RE = re.compile(r"\?")
EXCLAMATION_RE = re.compile(r"!")


# --------------------------------------------------------------------------- #
# LLM call — pluggable
# --------------------------------------------------------------------------- #
LLMFn = Callable[[str], str]


def _call_gemini(prompt: str) -> str:
    from google import genai  # type: ignore
    client = genai.Client(api_key=config.require_gemini_key())
    resp = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "max_output_tokens": 8192,
        },
    )
    return resp.text or ""


def _call_openai(prompt: str) -> str:
    from openai import OpenAI  # type: ignore
    client = OpenAI(api_key=config.require_openai_key())
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or ""


def get_llm() -> Optional[LLMFn]:
    if config.LLM_OFFLINE_ONLY:
        return None
    try:
        if config.LLM_PROVIDER == "openai":
            return _call_openai
        # default = gemini
        if not config.GEMINI_API_KEY:
            return None
        return _call_gemini
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM unavailable, falling back to audio-only scoring: %s", exc)
        return None


# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """You are an elite short-form video editor who has studied
thousands of viral clips on TikTok, Instagram Reels, and YouTube Shorts. You
know exactly what makes viewers stop scrolling, watch to the end, and share.

Score each candidate window from 0-100 on *viral potential* (not general
quality). Prioritise these signals in order:

  1. HOOK MOMENTS — a line that creates immediate curiosity ("The secret
     is...", "Nobody talks about...", "I was completely wrong about...")
  2. EMOTIONAL PEAKS — genuine surprise, laughter, anger, vulnerability
  3. OPINION BOMBS — strong, polarizing, counter-intuitive statements
  4. REVELATION MOMENTS — surprising facts, stats, confessions
  5. CONFLICT / TENSION — disagreement or pushback
  6. QUOTABLE ONE-LINERS — a sentence that works as a standalone quote
  7. STORY PEAKS — the climax or twist of an anecdote
  8. PRACTICAL VALUE — a concrete tip, hack, or insight

Rules for the windows you propose:
  • Each highlight must open with a strong HOOK.
  • Duration sweet spot: 30-90 seconds. Allow 20-120s when justified.
  • Never cut mid-sentence. Each clip must feel self-contained.
  • Clips must not overlap significantly with each other.
  • Return JSON only. No markdown, no commentary.

JSON schema (return ONLY this object):
{{
  "highlights": [
    {{
      "title": "short catchy title, 3-7 words",
      "start_time": 12.5,
      "end_time": 67.0,
      "score": 87,
      "hook_sentence": "the exact opening line that would make someone stop scrolling",
      "virality_reason": "one sentence explaining why this clip works"
    }}
  ]
}}
"""


def _build_user_prompt(transcript_text: str, max_candidates: int) -> str:
    return (
        f"Identify the {max_candidates} most viral-worthy highlights from "
        f"the following timestamped transcript. Each highlight must be a "
        f"self-contained 20-120 second clip with a strong opening hook.\n\n"
        f"=== TRANSCRIPT ===\n{transcript_text}\n=== END ==="
    )


def _parse_llm_json(raw: str) -> List[Dict]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("LLM returned no JSON")
        data = json.loads(text[start:end + 1])
    hl = data.get("highlights", [])
    if not isinstance(hl, list):
        raise ValueError("LLM JSON has no 'highlights' array")
    return hl


def _coerce_float(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _coerce_int(v, default=0) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------- #
# Audio energy / keyword scorer (offline)
# --------------------------------------------------------------------------- #
def _audio_energy_peaks(video_path: Path, duration: float) -> List[float]:
    """Return a list of (timestamp, normalised energy) tuples via ffmpeg.

    We use the ebur128 filter to get a loudness estimate per ~1 second
    window. If ffmpeg isn't available, return an empty list (the keyword
    scorer still works).
    """
    if duration <= 0:
        return []
    try:
        # -af ebur128=peak=true → loudness per second
        cmd = [
            "ffmpeg", "-hide_banner", "-nostats",
            "-i", str(video_path),
            "-af", "ebur128=peak=true",
            "-f", "null", "-",
        ]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    # Parse ebur128 summary lines: "  t: 12.345  M:-23.4 S:-22.1  ...  Peak:-1.2"
    energies: List[Tuple[float, float]] = []
    for line in proc.stderr.splitlines():
        m = re.search(r"t:\s*([\d.]+).*Peak:\s*(-?[\d.]+)", line)
        if m:
            ts = float(m.group(1))
            peak_db = float(m.group(2))
            # Convert dB peak → 0..1
            peak_norm = max(0.0, min(1.0, (peak_db + 40) / 40))
            energies.append((ts, peak_norm))
    return energies


def _build_transcript_text(transcript: Dict, window: int = 60) -> List[Dict]:
    """Group transcript segments into rolling ``window``-second buckets.

    Returns a list of dicts with ``start``, ``end`` and ``text``.
    """
    segments = transcript.get("segments", [])
    duration = transcript.get("duration", 0)
    if not segments:
        return []
    buckets: List[Dict] = []
    pos = 0.0
    while pos < duration:
        chunk_segs = [s for s in segments if s["end"] > pos and s["start"] < pos + window]
        text = " ".join(s["text"] for s in chunk_segs).strip()
        if text:
            buckets.append({
                "start": pos,
                "end": pos + window,
                "text": text,
            })
        pos += window / 2  # 50% overlap so good moments don't slip through
    return buckets


def _keyword_score(text: str) -> float:
    """0..100 score for one text block based on viral keywords + signals."""
    if not text:
        return 0.0
    words = re.findall(r"\b[\w'-]+\b", text.lower())
    if not words:
        return 0.0
    word_set = set(words)
    kw_score = 0.0
    for w in word_set:
        if w in VIRAL_KEYWORDS:
            kw_score += VIRAL_KEYWORDS[w]
    # Boost for laughter / applause
    if LAUGHTER_RE.search(text):
        kw_score += 4
    if APPLAUSE_RE.search(text):
        kw_score += 5
    # Question / exclamation density
    q = len(QUESTION_RE.findall(text))
    e = len(EXCLAMATION_RE.findall(text))
    kw_score += min(q * 0.5, 3) + min(e * 0.3, 2)
    # Length variance proxy: short punchy sentences score slightly higher
    sentences = re.split(r"[.!?]+", text)
    avg_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    if 6 <= avg_len <= 18:
        kw_score += 1.5
    # Normalise. Empirically, ~12 keyword hits is a strong moment.
    return min(100.0, (kw_score / 12.0) * 100.0)


def _audio_score_at(energies: List[Tuple[float, float]], start: float, end: float) -> float:
    if not energies:
        return 50.0  # neutral fallback
    window = [e for t, e in energies if start <= t <= end]
    if not window:
        return 50.0
    avg = sum(window) / len(window)
    # Scale 0..1 loudness → 0..100 score, with a bias toward the loud half.
    return min(100.0, max(0.0, (avg - 0.3) / 0.7 * 100.0))


# --------------------------------------------------------------------------- #
# Sliding window candidate generator
# --------------------------------------------------------------------------- #
@dataclass
class _Window:
    start: float
    end: float
    text: str
    kw_score: float
    audio_score: float
    combined: float


def _generate_windows(
    transcript: Dict,
    energies: List[Tuple[float, float]],
    min_score: float,
) -> List[_Window]:
    """Slide across the transcript and produce scored candidate windows."""
    buckets = _build_transcript_text(transcript, window=60)
    windows: List[_Window] = []
    for b in buckets:
        kw = _keyword_score(b["text"])
        au = _audio_score_at(energies, b["start"], b["end"])
        # Weighted blend: keywords matter more for virality than volume.
        combined = 0.65 * kw + 0.35 * au
        if combined >= min_score:
            windows.append(_Window(
                start=b["start"], end=b["end"], text=b["text"],
                kw_score=kw, audio_score=au, combined=combined,
            ))
    windows.sort(key=lambda w: w.combined, reverse=True)
    return windows


def _suppress_overlaps(windows: List[_Window]) -> List[_Window]:
    """Greedy overlap suppression — keep highest-scored non-overlapping windows."""
    kept: List[_Window] = []
    for w in windows:
        overlap = False
        for k in kept:
            latest_start = max(w.start, k.start)
            earliest_end = min(w.end, k.end)
            if earliest_end - latest_start > 0.5 * (w.end - w.start):
                overlap = True
                break
        if not overlap:
            kept.append(w)
    return kept


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def detect_viral_moments(
    transcript: Dict,
    video_path: Optional[Path] = None,
    max_candidates: int = 10,
    min_score: float = 40.0,
) -> List[Dict]:
    """Run both scoring engines and return ranked candidate dicts.

    Output shape::

        {
            "id": str,
            "title": str,
            "start": float,
            "end": float,
            "score": int,
            "success_rate": float,
            "hook_sentence": str,
            "virality_reason": str,
            "snippet": str,
            "llm_picked": bool,
        }
    """
    log.info("detecting viral moments (max=%d, min=%.0f)", max_candidates, min_score)
    t0 = time.time()

    # ----- offline scoring (always) -----
    energies: List[Tuple[float, float]] = []
    if video_path and video_path.exists():
        energies = _audio_energy_peaks(video_path, transcript.get("duration", 0))
    offline_windows = _generate_windows(transcript, energies, min_score=min_score)
    offline_windows = _suppress_overlaps(offline_windows)[: max_candidates * 2]

    # ----- LLM scoring (optional) -----
    llm_fn = get_llm()
    llm_picks: List[Dict] = []
    if llm_fn is not None:
        try:
            llm_picks = _run_llm_scoring(transcript, llm_fn, max_candidates)
        except Exception as exc:  # noqa: BLE001
            log.warning("LLM scoring failed, continuing with audio only: %s", exc)
            llm_picks = []

    # ----- merge: LLM picks keep their score, offline fills the rest -----
    candidates: List[Dict] = []
    seen_ranges: List[Tuple[float, float]] = []

    def _overlap_ratio(s1, e1, s2, e2):
        latest_start = max(s1, s2)
        earliest_end = min(e1, e2)
        return max(0.0, earliest_end - latest_start) / max(min(e1 - s1, e2 - s2), 0.01)

    for pick in llm_picks:
        s = _coerce_float(pick.get("start_time"))
        e = _coerce_float(pick.get("end_time"))
        if e <= s:
            continue
        s, e = _clip_range(s, e, transcript.get("duration", 0))
        if any(_overlap_ratio(s, e, ss, ee) > 0.5 for ss, ee in seen_ranges):
            continue
        llm_score = max(0, min(100, _coerce_int(pick.get("score"))))
        # Blend with offline if available
        ow = _best_offline_match(s, e, offline_windows)
        if ow:
            offline_score = int(round(ow.combined))
            blended = int(round(0.7 * llm_score + 0.3 * offline_score))
        else:
            blended = llm_score
        snippet = _snippet(transcript, s, e)
        candidates.append({
            "title": (pick.get("title") or "Highlight").strip()[:80],
            "start": s,
            "end": e,
            "score": blended,
            "llm_score": llm_score,
            "hook_sentence": (pick.get("hook_sentence") or "").strip(),
            "virality_reason": (pick.get("virality_reason") or "").strip(),
            "snippet": snippet,
            "llm_picked": True,
        })
        seen_ranges.append((s, e))

    for ow in offline_windows:
        if len(candidates) >= max_candidates:
            break
        if any(_overlap_ratio(ow.start, ow.end, ss, ee) > 0.5 for ss, ee in seen_ranges):
            continue
        snippet = _snippet(transcript, ow.start, ow.end)
        candidates.append({
            "title": _auto_title(ow.text),
            "start": ow.start,
            "end": ow.end,
            "score": int(round(ow.combined)),
            "llm_score": None,
            "hook_sentence": _first_punchy_line(ow.text),
            "virality_reason": _reason_from_offline(ow),
            "snippet": snippet,
            "llm_picked": False,
        })
        seen_ranges.append((ow.start, ow.end))

    # Sort by score, attach stable ids
    candidates.sort(key=lambda c: c["score"], reverse=True)
    for i, c in enumerate(candidates, 1):
        c["id"] = f"c{i:02d}"
        c["duration"] = round(c["end"] - c["start"], 2)
        c["success_rate"] = float(c["score"])

    log.info("viral detection done in %.1fs: %d candidates", time.time() - t0, len(candidates))
    return candidates[:max_candidates]


def _run_llm_scoring(transcript: Dict, llm_fn: LLMFn, max_candidates: int) -> List[Dict]:
    """Call the LLM. For long videos we chunk and merge."""
    duration = transcript.get("duration", 0)
    chunk_seconds = max(5, config.LLM_CHUNK_MINUTES) * 60

    if duration <= chunk_seconds * 1.2:
        return _llm_chunk(transcript, llm_fn, max_candidates, offset=0.0)

    # Long video — chunk with overlap, merge.
    all_picks: List[Dict] = []
    seen_ranges: List[Tuple[float, float]] = []
    pos = 0.0
    while pos < duration:
        end = min(pos + chunk_seconds, duration)
        chunk = _slice_transcript(transcript, pos, end)
        if not chunk["segments"]:
            pos = end
            continue
        picks = _llm_chunk(chunk, llm_fn, max_candidates, offset=pos)
        for p in picks:
            s = _coerce_float(p.get("start_time"))
            e = _coerce_float(p.get("end_time"))
            if e <= s:
                continue
            s2 = s + pos
            e2 = e + pos
            if any(
                max(0.0, min(e2, ee) - max(s2, ss)) > 0.5 * (e2 - s2)
                for ss, ee in seen_ranges
            ):
                continue
            p["start_time"] = s2
            p["end_time"] = e2
            all_picks.append(p)
            seen_ranges.append((s2, e2))
        pos += chunk_seconds * 0.75  # 25% overlap
    return all_picks


def _llm_chunk(chunk: Dict, llm_fn: LLMFn, max_candidates: int, offset: float) -> List[Dict]:
    """Score one chunk with the LLM. ``offset`` is unused inside the prompt —
    the LLM sees only relative timestamps because that's what the transcript
    contains for that chunk."""
    # We rewrite timestamps to be relative-to-chunk for cleaner output.
    rel_segments = []
    for s in chunk["segments"]:
        rel_segments.append({
            "start": round(s["start"] - offset, 2),
            "end": round(s["end"] - offset, 2),
            "text": s["text"],
        })
    text = "\n".join(
        f"[{s['start']:.1f}s] {s['text']}" for s in rel_segments
    )
    if not text.strip():
        return []
    prompt = SYSTEM_PROMPT + "\n\n" + _build_user_prompt(text, max_candidates)
    raw = llm_fn(prompt)
    return _parse_llm_json(raw)


def _slice_transcript(transcript: Dict, start: float, end: float) -> Dict:
    segments = [s for s in transcript.get("segments", []) if s["end"] > start and s["start"] < end]
    return {
        "language": transcript.get("language", "en"),
        "duration": end - start,
        "segments": segments,
    }


def _clip_range(start: float, end: float, total: float):
    if start < 0:
        start = 0.0
    if total and end > total:
        end = total
    if end - start < 20:
        # expand to minimum 20s
        centre = (start + end) / 2
        start = max(0.0, centre - 10)
        end = min(total or centre + 10, centre + 10)
    if end - start > 180:
        end = start + 180
    return start, end


def _best_offline_match(start: float, end: float, offline: List[_Window]) -> Optional[_Window]:
    best = None
    best_overlap = 0.0
    for w in offline:
        latest = max(start, w.start)
        earliest = min(end, w.end)
        ov = max(0.0, earliest - latest)
        if ov > best_overlap:
            best_overlap = ov
            best = w
    return best if best_overlap > 0.1 * (end - start) else None


def _snippet(transcript: Dict, start: float, end: float, max_chars: int = 220) -> str:
    segments = transcript.get("segments", [])
    parts = []
    for s in segments:
        if s["end"] <= start:
            continue
        if s["start"] >= end:
            break
        parts.append(s["text"].strip())
    snippet = " ".join(parts).strip()
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 1] + "…"
    return snippet


def _first_punchy_line(text: str) -> str:
    """Pick the most hook-y sentence from a text block."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if not sentences:
        return text[:120]
    sentences = [s.strip() for s in sentences if len(s.strip()) > 6]
    if not sentences:
        return text[:120]
    # Score by viral keywords
    def score(s: str) -> float:
        words = re.findall(r"\b[\w'-]+\b", s.lower())
        return sum(VIRAL_KEYWORDS.get(w, 0) for w in words) + (1.0 if "?" in s else 0)
    return max(sentences, key=score)[:140]


def _auto_title(text: str) -> str:
    s = _first_punchy_line(text)
    # Capitalise and trim
    if len(s) > 60:
        s = s[:57] + "..."
    return s.capitalize()


def _reason_from_offline(w: _Window) -> str:
    bits = []
    if w.kw_score >= 60:
        bits.append("strong viral keywords")
    if w.audio_score >= 60:
        bits.append("audio energy peak")
    if LAUGHTER_RE.search(w.text):
        bits.append("audience reaction")
    if APPLAUSE_RE.search(w.text):
        bits.append("applause moment")
    if not bits:
        bits.append("punchy phrasing")
    return "Detected via " + ", ".join(bits)


def to_candidate(c: Dict, caption_style: str, caption_position: int) -> Candidate:
    return Candidate(
        id=c["id"],
        index=int(c["id"].lstrip("c") or 0),
        title=c["title"],
        start=c["start"],
        end=c["end"],
        duration=c["duration"],
        score=int(c["score"]),
        success_rate=float(c.get("success_rate", c["score"])),
        hook_sentence=c.get("hook_sentence", ""),
        virality_reason=c.get("virality_reason", ""),
        snippet=c.get("snippet", ""),
        caption_style=caption_style,
        caption_position=caption_position,
    )
