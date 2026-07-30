# 🎬 ClipForge — Beginner Setup Guide (no coding knowledge needed)

This guide assumes you've never used Python, the terminal, or anything like
that. Just follow the steps in order.

---

## Part 1: Get your free Gemini API key (3 minutes)

The app needs an "API key" to talk to Google's AI (Gemini). It's **free**.

1. Open your web browser and go to:
   **https://aistudio.google.com/apikey**

2. Sign in with your Google account (Gmail works).

3. Click the blue **"Create API key"** button (top right).

4. A small popup will appear. Click **"Create key in new project"**.

5. You'll see a long string that looks like:
   ```
   AIzaSyD-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

6. **Click the copy icon** next to it. That long string is your API key.

7. Keep that key handy — you'll paste it in a moment.

---

## Part 2: Set up the app (5 minutes)

### Step 1: Open the project in Cursor or VS Code

- Open **Cursor** (or VS Code)
- Click **File → Open Folder**
- Navigate to where this `clipping` folder is
- Select the `clipping` folder
- Click **Open**

You should see the project files in the left sidebar.

### Step 2: Open the `.env` file

- In the left sidebar, find the file called **`.env`**
  (It might be hidden — if so, click the three-dot menu at the top
  of the file panel and turn on "Show Hidden Files")
- Click on `.env` to open it

It will look like this:
```
GEMINI_API_KEY=PASTE_YOUR_KEY_HERE
```

### Step 3: Paste your API key

- Delete the text `PASTE_YOUR_KEY_HERE`
- Paste your copied key (Ctrl+V on Windows, Cmd+V on Mac)
- The line should now look like:
  ```
  GEMINI_API_KEY=AIzaSyD-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```
- **Save the file** with `Ctrl+S` (Windows) or `Cmd+S` (Mac)

### Step 4: Open the terminal

In Cursor / VS Code:
- Click **Terminal → New Terminal** in the top menu
- A black box will appear at the bottom. That's the terminal.

### Step 5: Run the app

In the terminal, type this and press Enter:
```
./run.sh
```

> **Windows users:** if `./run.sh` doesn't work, try `bash run.sh`

The first time you run this, it will:
- Download and install Python packages (1-3 minutes)
- Download the Whisper AI model (about 150 MB)
- Start a web server

When it's ready, you'll see:
```
→ starting ClipForge on http://0.0.0.0:8000
```

### Step 6: Open the app in your browser

Open your web browser and go to:
**http://localhost:8000**

You should see the ClipForge home page! 🎉

---

## Part 3: Install ffmpeg (one-time, 2 minutes)

The app needs a free tool called **ffmpeg** to process videos.

### On Mac:
Open the **Terminal** app (search "Terminal" in Spotlight) and paste:
```
brew install ffmpeg
```
(If you don't have `brew`, install it from https://brew.sh first)

### On Windows:
1. Open https://www.gyan.dev/ffmpeg/builds/
2. Download the "essentials" build (a `.zip` file)
3. Extract it
4. Add the `bin` folder inside to your PATH (search Windows for "Edit environment variables" → PATH → add the path)

### On Linux (Ubuntu / Debian):
```
sudo apt install ffmpeg
```

---

## Part 4: Use the app

1. **Paste a YouTube link** in the box on the home page
   (works for any video, up to 2+ hours long)

2. Click **"Find viral moments"**

3. **Wait** — a progress bar will show:
   - Downloading the video
   - Transcribing the audio
   - Detecting viral moments

4. **See the results** — each moment shows:
   - A **success rate** (0-100, like a virality score)
   - The hook sentence
   - Why the AI picked it
   - A snippet of the transcript

5. **Pick the ones you like** — click the checkbox on each card, or click
   **"Select top 3"** to auto-pick the best ones

6. Click **"Render selected (3)"**

7. **Wait again** — the app will:
   - Cut the clips
   - Reframe to 9:16 (vertical, for TikTok/Reels)
   - Add animated captions

8. **Download!** Each finished clip gets a green **"⬇ Download MP4"** button.
   Click it to save the video to your computer.

---

## Common beginner problems

### "python: command not found"
You need to install Python from https://www.python.org/downloads/
(Pick Python 3.11 or newer. On Windows, check "Add Python to PATH" during install.)

### "ffmpeg: command not found"
See Part 3 above.

### "permission denied" when running ./run.sh (Mac/Linux)
In the terminal, type:
```
chmod +x run.sh
```
Then try again.

### The app starts but videos don't process
- Make sure you set your GEMINI_API_KEY in `.env` (Part 2)
- Check the bottom of the app page for an error log
- Visit http://localhost:8000/api/health — it should show
  `"llm_configured": true`

### The first run is very slow
That's normal! It downloads the Whisper AI model (~150 MB) the first time.
After that, processing is much faster.

---

## Quick reference

| What | Where |
|------|-------|
| Your API key | `.env` file |
| Your settings | `.env` file |
| The web app | http://localhost:8000 |
| Help / docs | `README.md` |
| Style guide | `web/static/app.css` |
| Templates | http://localhost:8000/templates |

Happy clipping! 🎉
