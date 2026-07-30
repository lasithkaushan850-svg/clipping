"""Whisper transcription with word-level timestamps.

We use ``faster-whisper`` because it runs comfortably on CPU for the
``base`` model while still emitting the word-level timestamps the caption
renderer needs.

Long videos (anything > 2h, which the user mentioned) are handled by
``faster-whisper``'s built-in VAD-driven segmentation — no manual
chunking required at the audio level. We still chunk the *text* on the
LLM side, in :mod:`app.highlights`.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from . import config

log = logging.getLogger(__name__)

# Cache one model per process. Loading faster-whisper takes 5-20 s, so
# reusing it across jobs is a big win.
_MODEL_CACHE: Dict[str, "WhisperModel"] = {}


def _get_model():
    from faster_whisper import WhisperModel  # type: ignore

    size = config.WHISPER_MODEL_SIZE
    if size not in _MODEL_CACHE:
        log.info("loading faster-whisper model %s", size)
        _MODEL_CACHE[size] = WhisperModel(size, compute_type="int8")
    return _MODEL_CACHE[size]


def transcribe(video_path: Path, language: Optional[str] = None) -> Dict:
    """Transcribe ``video_path`` and return the structured transcript.

    Output shape::

        {
          "language": "en",
          "duration": 1834.5,
          "segments": [
              {
                  "start": 0.0,
                  "end": 3.4,
                  "text": "Hello world",
                  "words": [
                      {"word": "Hello", "start": 0.0, "end": 0.6},
                      {"word": "world", "start": 0.7, "end": 1.2},
                  ],
              },
              ...
          ],
        }
    """
    model = _get_model()
    lang = language or config.WHISPER_LANGUAGE
    if lang == "auto":
        lang = None

    segments_iter, info = model.transcribe(
        str(video_path),
        word_timestamps=True,
        language=lang,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    segments: List[Dict] = []
    for seg in segments_iter:
        words: List[Dict] = []
        for w in (seg.words or []):
            if w.start is None or w.end is None:
                continue
            words.append({
                "word": w.word,
                "start": float(w.start),
                "end": float(w.end),
            })
        if not words and seg.text:
            # fall back to one "word" = the whole segment so captioning still works
            words.append({
                "word": seg.text.strip(),
                "start": float(seg.start or 0.0),
                "end": float(seg.end or 0.0),
            })
        segments.append({
            "start": float(seg.start or 0.0),
            "end": float(seg.end or 0.0),
            "text": (seg.text or "").strip(),
            "words": words,
        })

    return {
        "language": info.language,
        "duration": float(info.duration or (segments[-1]["end"] if segments else 0.0)),
        "segments": segments,
    }
