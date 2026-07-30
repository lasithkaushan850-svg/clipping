@echo off
REM ============================================================================
REM ClipForge launcher for Windows
REM ============================================================================

cd /d "%~dp0"

REM ---- 1. Create venv if missing ---------------------------------------------
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERROR: Could not create virtual environment.
        echo Make sure Python 3.10+ is installed from https://www.python.org/
        echo and that you checked "Add Python to PATH" during install.
        echo.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

REM ---- 2. Install requirements -----------------------------------------------
echo.
echo Installing Python requirements (one-time setup, may take a few minutes)...
echo (you'll see lots of text scrolling by — that's normal)
echo.
python -m pip install --quiet --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install some requirements.
    echo Try running this script again, or run it manually:
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo Requirements installed.

REM ---- 3. Check ffmpeg --------------------------------------------------------
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo.
    echo ============================================================
    echo  WARNING: ffmpeg not found in PATH.
    echo  The app will start but video processing will fail.
    echo  Install from https://www.gyan.dev/ffmpeg/builds/
    echo  and add the bin folder to your PATH.
    echo ============================================================
    echo.
)

REM ---- 4. .env setup ----------------------------------------------------------
if not exist ".env" (
    echo.
    echo Creating .env from template...
    copy /Y .env.example .env >nul
    echo.
    echo ============================================================
    echo  IMPORTANT: Open .env in VS Code and add your GEMINI_API_KEY!
    echo  Get a free key at: https://aistudio.google.com/apikey
    echo  Look for the line: GEMINI_API_KEY=PASTE_YOUR_KEY_HERE
    echo ============================================================
    echo.
    echo Press any key to continue, then add your key, then re-run this script.
    pause
)

REM ---- 5. Make sure data dirs exist ------------------------------------------
if not exist "data\jobs"      mkdir data\jobs
if not exist "data\uploads"   mkdir data\uploads
if not exist "data\outputs"   mkdir data\outputs
if not exist "data\sources"   mkdir data\sources

REM ---- 6. Start the server ---------------------------------------------------
echo.
echo ============================================================
echo  Starting ClipForge on http://localhost:8000
echo  Press Ctrl+C to stop.
echo ============================================================
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
