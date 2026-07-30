# 🎬 ClipForge

> Turn long YouTube videos (or any local video up to 2+ hours) into
> **viral short-form clips** with AI moment detection, animated
> word-by-word captions, and one-click downloads. **100% free, 100% local.**

```
┌──────────────────────────────────────────────────────────────────┐
│  Paste YouTube link   →   AI finds 5-10 viral moments            │
│  →  rank by success rate   →  pick the ones you like             │
│  →  reframe to 9:16 (face-tracking)                              │
│  →  burn in Hormozi / MrBeast captions                           │
│  →  Download MP4 🎉                                              │
└──────────────────────────────────────────────────────────────────┘
```

## Why ClipForge?

| ClipForge | Opus Clip / Klap / Munch |
| --- | --- |
| **Free & unlimited** | $20-$100/mo + minute caps |
| **100% local** — your videos never leave your machine | Uploaded to third-party cloud |
| **AI + audio analysis** (Gemini / OpenAI + keyword scoring) | Black-box AI |
| **6 trending caption styles** | Limited library |
| **Works with 2-hour videos** (chunked LLM scoring) | Minute limits |
| **Templates** for one-click TikTok / Reels / YouTube presets | None |

## What it does

1. **Download** — fetches the full YouTube video with `yt-dlp` (works for
   anything, including 2+ hour videos).
2. **Transcribe** — `faster-whisper` produces a word-level transcript of
   the entire video. Language auto-detected (or forced via env).
3. **Detect viral moments** — combines two scoring engines:
   - **LLM scoring** (Gemini or OpenAI) — reads the transcript and picks
     out hooks, emotional peaks, revelations, opinion bombs, conflicts,
     quotable one-liners, story payoffs, and practical value.
   - **Offline audio + keyword scoring** — ffmpeg loudness peaks +
     viral-keyword spotting + laughter/applause detection. Always runs,
     so the final score is a blend.
4. **Show ranked candidates** with a 0-100 **success rate** so you can
   pick the best ones. Nothing is downloaded or rendered until you
   explicitly say "render these".
5. **Render** — for each selected candidate:
   - Hard-cut subclip with `ffmpeg`
   - Reframe to 9:16 (or 1:1 / 16:9) with OpenCV face tracking
   - Burn in the hook line as a 2.5s banner overlay
   - Burn in the chosen animated caption style
6. **Download** — each rendered MP4 has its own download button.

## Project structure

```
clipping/
├── app/                       # FastAPI backend
│   ├── main.py                # HTTP routes
│   ├── pipeline.py            # Worker thread orchestration
│   ├── transcriber.py         # faster-whisper wrapper
│   ├── downloader.py          # yt-dlp wrapper
│   ├── highlights.py          # LLM + audio scoring engine
│   ├── clipper.py             # ffmpeg + OpenCV reframe
│   ├── captions.py            # ASS generation + burn-in
│   ├── jobs.py                # Persistent job state
│   ├── config.py              # .env loading
│   └── caption_styles.json    # 6 trending styles
├── web/                       # Single-page web UI
│   ├── templates/             # Jinja2 pages (index, job, templates)
│   └── static/                # CSS + JS
├── vendor/                    # The three open-source projects
│   ├── AI-Youtube-Shorts-Generator/   # LLM highlight-scoring logic
│   ├── ViralCutter/                   # Face-tracking reference
│   └── ai-video-captions/             # Caption style reference
├── data/                      # Runtime artefacts (gitignored)
├── requirements.txt
├── .env.example
├── run.sh                     # one-line launcher
└── README.md
```

## Quick start

### 1. Install system dependencies

| Tool | Why | Install |
| --- | --- | --- |
| `ffmpeg` | video cutting, reframe, audio mux, burn-in | `brew install ffmpeg` (mac) / `apt install ffmpeg` (Debian) / `choco install ffmpeg` (Win) |
| `python 3.10+` | backend | https://python.org |
| `node` *(optional)* | only if you want to rebuild the front-end | https://nodejs.org |

### 2. Configure the LLM (optional but recommended)

Copy the env template and add your key:

```bash
cp .env.example .env
$EDITOR .env
```

- **Gemini (free tier)** — set `LLM_PROVIDER=gemini` and
  `GEMINI_API_KEY=…`. Get a key at <https://aistudio.google.com/apikey>.
- **OpenAI** — set `LLM_PROVIDER=openai` and `OPENAI_API_KEY=…`.
- **No LLM** — set `LLM_OFFLINE_ONLY=true`. The audio/keyword engine
  still produces decent results, just without the deep semantic scoring.

### 3. Launch

```bash
./run.sh
```

Then open <http://localhost:8000>.

> First run downloads the Whisper `base` model (~150 MB). After that it's
> cached and reused across jobs.

## Using the app

1. **Home page** — paste a YouTube link (or upload a file), pick an aspect
   ratio, source resolution, caption style, and max candidates. Click
   **Find viral moments**.
2. **Job page** — wait ~30 s for a 10-min video (faster for short ones).
   The progress bar will move through **Downloading → Transcribing →
   Scoring**. The 3 vendored repos each contribute one of those stages.
3. **Pick the winners** — each candidate shows its **success rate**
   (0-100), a hook sentence, the reason it was picked, and a transcript
   snippet. Use **Select top 3** or pick manually. You can change the
   caption style per candidate.
4. **Render** — click **Render selected (N)**. Each clip is cut, reframed,
   banner-overlaid, and captioned. ~5-15 s per clip.
5. **Download** — only after the render finishes does the **Download MP4**
   button appear. The video file is never downloadable until you ask.

## Templates

Visit `/templates` for one-click presets:

| Template | Aspect | Style | Position |
| --- | --- | --- | --- |
| TikTok Viral | 9:16 | Hormozi | 12% |
| Reels Clean | 9:16 | Minimal | 18% |
| YouTube Shorts Bold | 9:16 | MrBeast | 15% |
| Podcast Karaoke | 1:1 | Karaoke | 20% |
| YouTube Landscape | 16:9 | Classic | 10% |
| Fun Bounce | 9:16 | Bounce | 12% |

Click a template → it pre-fills the home-page form.

## How the three repos are combined

| Repo | Role in ClipForge |
| --- | --- |
| [Anil-matcha/AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) | Prompt design, content-type detection, chunking for long videos, dedupe-with-overlap suppression. Our `app/highlights.py` is a clean re-implementation. |
| [RafaelGodoyEbert/ViralCutter](https://github.com/RafaelGodoyEbert/ViralCutter) | Reference for the OpenCV face-tracking vertical reframe. Our `app/clipper.py` is a clean re-implementation. |
| [nicolaigaina/ai-video-captions](https://github.com/nicolaigaina/ai-video-captions) | Reference for the ASS-based word-by-word animated caption style configuration. Our `app/captions.py` and `app/caption_styles.json` are a clean re-implementation. |

We deliberately **did not import the three repos as libraries** — their
dependencies (Gradio, OpenCV face detection, Next.js, etc.) would drag
hundreds of MB of packages into every install. Instead we re-implemented
the same algorithms against our own thin module surface so the install
is fast and the deploy is one `uvicorn` process.

## Configuration reference

See [`.env.example`](.env.example) for the full list. Key knobs:

```ini
LLM_PROVIDER=gemini                # gemini | openai
LLM_OFFLINE_ONLY=false             # true = skip LLM, use only audio scoring
WHISPER_MODEL_SIZE=base            # tiny | base | small | medium | large-v3
MAX_CANDIDATES=10                  # how many viral candidates to return
MIN_SCORE=40                       # hide candidates below this success rate
CLIPS_TO_RENDER=3                  # default render count for "render all"
DEFAULT_ASPECT_RATIO=9:16
DEFAULT_RESOLUTION=720
LLM_CHUNK_MINUTES=20               # for long videos, score N min at a time
```

## License

MIT. The three vendored projects are MIT-licensed and credited in
`vendor/`.

## Credits

- [Anil-matcha/AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) — prompt + scoring
- [RafaelGodoyEbert/ViralCutter](https://github.com/RafaelGodoyEbert/ViralCutter) — face tracking
- [nicolaigaina/ai-video-captions](https://github.com/nicolaigaina/ai-video-captions) — caption styles
- [OpenAI Whisper](https://github.com/openai/whisper) — transcription
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube downloader
- [ffmpeg](https://ffmpeg.org/) — video engine
- [OpenCV](https://opencv.org/) — face detection
