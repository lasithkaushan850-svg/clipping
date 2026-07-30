"""Centralised configuration loaded from environment variables.

We keep the env-var surface small and stable so users can deploy by editing
``.env`` rather than touching code.
"""
from __future__ import annotations

import os
from pathlib import Path

# Make sure relative imports work when the file is imported by both the
# FastAPI server and the worker threads.
BASE_DIR = Path(__file__).resolve().parent.parent
VENDOR_DIR = BASE_DIR / "vendor"

# Where runtime artefacts (downloads, jobs, rendered clips) live.
DATA_DIR = Path(os.environ.get("CLIPFORGE_DATA_DIR", BASE_DIR / "data"))
JOBS_DIR = DATA_DIR / "jobs"
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
SOURCES_DIR = DATA_DIR / "sources"
for _d in (DATA_DIR, JOBS_DIR, UPLOADS_DIR, OUTPUTS_DIR, SOURCES_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# ---- LLM --------------------------------------------------------------------
LLM_PROVIDER = (os.environ.get("LLM_PROVIDER", "gemini") or "gemini").strip().lower()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
LLM_OFFLINE_ONLY = os.environ.get("LLM_OFFLINE_ONLY", "false").lower() in (
    "1", "true", "yes", "on"
)


def require_gemini_key() -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file, or set "
            "LLM_OFFLINE_ONLY=true to skip the LLM entirely."
        )
    return GEMINI_API_KEY


def require_openai_key() -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file, or set "
            "LLM_OFFLINE_ONLY=true to skip the LLM entirely."
        )
    return OPENAI_API_KEY


# ---- Whisper ----------------------------------------------------------------
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base").strip()
WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE", "auto").strip() or "auto"


# ---- Pipeline defaults ------------------------------------------------------
MAX_CANDIDATES = int(os.environ.get("MAX_CANDIDATES", "10"))
MIN_SCORE = int(os.environ.get("MIN_SCORE", "40"))
CLIPS_TO_RENDER = int(os.environ.get("CLIPS_TO_RENDER", "3"))
DEFAULT_ASPECT_RATIO = os.environ.get("DEFAULT_ASPECT_RATIO", "9:16").strip()
DEFAULT_RESOLUTION = os.environ.get("DEFAULT_RESOLUTION", "720").strip()
LLM_CHUNK_MINUTES = int(os.environ.get("LLM_CHUNK_MINUTES", "20"))


# ---- Server -----------------------------------------------------------------
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
APP_SECRET = os.environ.get("APP_SECRET", "change-me-in-production")
