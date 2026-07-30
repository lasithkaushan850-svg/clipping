#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# ClipForge launcher — installs deps, prepares data dirs, starts the server.
# ----------------------------------------------------------------------------
set -e

cd "$(dirname "$0")"

# -- 1. python venv ---------------------------------------------------------
if [ ! -d ".venv" ]; then
  echo "→ creating Python virtual environment (.venv)"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# -- 2. dependencies --------------------------------------------------------
echo "→ installing Python requirements (this is a one-time setup, may take a minute)"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# -- 3. ffmpeg --------------------------------------------------------------
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "⚠ ffmpeg not found. Install it with your system package manager."
  echo "   macOS:   brew install ffmpeg"
  echo "   Debian:  sudo apt install ffmpeg"
  echo "   Windows: choco install ffmpeg"
fi

# -- 4. env -----------------------------------------------------------------
if [ ! -f ".env" ]; then
  echo "→ creating .env from template (edit it to add your LLM API key)"
  cp .env.example .env
fi

# -- 5. data dir ------------------------------------------------------------
mkdir -p data/jobs data/uploads data/outputs data/sources

# -- 6. run -----------------------------------------------------------------
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
echo "→ starting ClipForge on http://$HOST:$PORT"
exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
