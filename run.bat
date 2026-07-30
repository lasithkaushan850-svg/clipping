@echo off
REM ============================================================================
REM ClipForge launcher for Windows
REM ============================================================================

cd /d "%~dp0"

REM ---- 1. Create venv if missing ---------------------------------------------
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

REM ---- 2. Install requirements -----------------------------------------------
echo Installing Python requirements (one-time setup, may take a minute)...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

REM ---- 3. Check ffmpeg --------------------------------------------------------
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: ffmpeg not found in PATH.
    echo Install it from https://www.gyan.dev/ffmpeg/builds/
    echo and add the bin folder to your PATH, then re-run this script.
    echo.
)

REM ---- 4. .env setup ----------------------------------------------------------
if not exist ".env" (
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo ============================================================
    echo  IMPORTANT: Open .env and add your GEMINI_API_KEY first!
    echo  Get a free key at: https://aistudio.google.com/apikey
    echo ============================================================
    echo.
    pause
)

REM ---- 5. Make sure data dirs exist ------------------------------------------
if not exist "data\jobs"      mkdir data\jobs
if not exist "data\uploads"   mkdir data\uploads
if not exist "data\outputs"   mkdir data\outputs
if not exist "data\sources"   mkdir data\sources

REM ---- 6. Start the server ---------------------------------------------------
echo.
echo Starting ClipForge on http://localhost:8000
echo Press Ctrl+C to stop.
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000
