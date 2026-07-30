"""FastAPI HTTP layer for ClipForge.

Routes:
    GET  /                       — web UI
    GET  /api/styles             — caption styles list
    GET  /api/health             — health probe
    POST /api/jobs               — create a new job (YouTube URL or upload)
    GET  /api/jobs               — list all jobs
    GET  /api/jobs/{id}          — full job state (for polling)
    GET  /api/jobs/{id}/log      — text log for a job
    POST /api/jobs/{id}/render   — render selected candidates
    GET  /api/jobs/{id}/clips/{cid}/file  — download a rendered MP4
    GET  /api/jobs/{id}/clips/{cid}/preview — stream the MP4 inline
    DELETE /api/jobs/{id}        — delete a job and its files
"""
from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from typing import List, Optional

from fastapi import (
    BackgroundTasks,
    Body,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import captions, config, downloader, pipeline
from .jobs import STORE, Status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("clipforge")


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
APP_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = APP_DIR / "web"

app = FastAPI(
    title="ClipForge",
    description=(
        "Turn long YouTube videos into viral short-form clips with AI "
        "moment detection, animated captions, and one-click downloads."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static + templates
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_page(request: Request, job_id: str):
    return templates.TemplateResponse(
        request, "job.html", {"job_id": job_id}
    )


@app.get("/templates", response_class=HTMLResponse)
def templates_page(request: Request):
    return templates.TemplateResponse(request, "templates.html")


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    return {
        "ok": True,
        "llm_provider": config.LLM_PROVIDER,
        "llm_configured": (
            (config.LLM_PROVIDER == "gemini" and bool(config.GEMINI_API_KEY))
            or (config.LLM_PROVIDER == "openai" and bool(config.OPENAI_API_KEY))
            or config.LLM_OFFLINE_ONLY
        ),
        "whisper_model": config.WHISPER_MODEL_SIZE,
    }


@app.get("/api/styles")
def get_styles():
    return {
        "styles": captions.list_styles(),
        "default": "hormozi",
        "position": {"min": 5, "max": 50, "default": 10},
        "output_formats": [
            {"id": "vertical", "name": "Vertical 9:16", "ratio": "9:16"},
            {"id": "square", "name": "Square 1:1", "ratio": "1:1"},
            {"id": "landscape", "name": "Landscape 16:9", "ratio": "16:9"},
        ],
    }


@app.get("/api/templates")
def get_templates():
    """Curated clip templates the user can apply when rendering."""
    return {
        "templates": [
            {
                "id": "tiktok_viral",
                "name": "TikTok Viral",
                "description": "9:16, fast cuts, Hormozi captions",
                "settings": {
                    "aspect_ratio": "9:16",
                    "caption_style": "hormozi",
                    "caption_position": 12,
                },
            },
            {
                "id": "reels_clean",
                "name": "Instagram Reels (Clean)",
                "description": "9:16, minimal captions, lower-third",
                "settings": {
                    "aspect_ratio": "9:16",
                    "caption_style": "minimal",
                    "caption_position": 18,
                },
            },
            {
                "id": "yt_short_bold",
                "name": "YouTube Shorts (Bold)",
                "description": "9:16, MrBeast style, big yellow text",
                "settings": {
                    "aspect_ratio": "9:16",
                    "caption_style": "mrbeast",
                    "caption_position": 15,
                },
            },
            {
                "id": "podcast_karaoke",
                "name": "Podcast Karaoke",
                "description": "1:1, blue karaoke-style captions",
                "settings": {
                    "aspect_ratio": "1:1",
                    "caption_style": "karaoke",
                    "caption_position": 20,
                },
            },
            {
                "id": "youtube_landscape",
                "name": "YouTube Landscape Highlight",
                "description": "16:9, classic captions, no reframe",
                "settings": {
                    "aspect_ratio": "16:9",
                    "caption_style": "classic",
                    "caption_position": 10,
                },
            },
            {
                "id": "fun_bounce",
                "name": "Fun Bounce",
                "description": "9:16, neon bounce animation, energetic content",
                "settings": {
                    "aspect_ratio": "9:16",
                    "caption_style": "bounce",
                    "caption_position": 12,
                },
            },
        ]
    }


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
@app.post("/api/jobs")
async def create_job(
    request: Request,
    background: BackgroundTasks,
):
    """Create a job from either a YouTube URL (form) or a file upload."""
    content_type = (request.headers.get("content-type") or "").lower()

    source: Optional[str] = None
    source_kind: Optional[str] = None
    settings: dict = {}

    if "multipart/form-data" in content_type:
        form = await request.form()
        url = (form.get("youtube_url") or "").strip()
        upload = form.get("video")
        if url and downloader.is_youtube_url(url):
            source = url
            source_kind = "youtube"
        elif upload is not None and getattr(upload, "filename", ""):
            tmp_path = config.UPLOADS_DIR / upload.filename
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            data = await upload.read()
            tmp_path.write_bytes(data)
            source = f"upload:{tmp_path}"
            source_kind = "upload"
        else:
            raise HTTPException(400, "Provide a YouTube URL or a video upload")
        # Read optional settings
        for k in (
            "aspect_ratio", "resolution", "caption_style",
            "caption_position", "min_score", "max_candidates",
            "num_clips_to_render",
        ):
            v = form.get(k)
            if v not in (None, ""):
                try:
                    settings[k] = int(v) if k in (
                        "caption_position", "min_score",
                        "max_candidates", "num_clips_to_render",
                    ) else v
                except (TypeError, ValueError):
                    settings[k] = v
    else:
        body = await request.json()
        url = (body.get("youtube_url") or "").strip()
        if not url or not downloader.is_youtube_url(url):
            raise HTTPException(400, "Provide a valid YouTube URL")
        source = url
        source_kind = "youtube"
        settings = {k: v for k, v in body.items() if k != "youtube_url"}

    job = pipeline.start_job(source=source, source_kind=source_kind, settings=settings)
    return job.to_dict()


@app.get("/api/jobs")
def list_jobs():
    out = []
    for child in sorted(STORE.root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        meta = child / "meta.json"
        if not meta.exists():
            continue
        try:
            j = STORE.get(child.name)
        except Exception:  # noqa: BLE001
            continue
        out.append({
            "job_id": j.job_id,
            "status": j.status,
            "source": j.source,
            "source_title": j.source_title,
            "source_channel": j.source_channel,
            "source_duration": j.source_duration,
            "source_thumbnail": j.source_thumbnail,
            "created_at": j.created_at,
            "updated_at": j.updated_at,
            "progress": j.progress,
            "phase": j.phase,
            "candidate_count": len(j.candidates),
        })
    return {"jobs": out[:50]}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    try:
        j = STORE.get(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    return j.to_dict()


@app.get("/api/jobs/{job_id}/log", response_class=PlainTextResponse)
def get_log(job_id: str):
    log_path = STORE.root / job_id / "log.txt"
    if not log_path.exists():
        return ""
    return log_path.read_text(encoding="utf-8")


@app.post("/api/jobs/{job_id}/render")
def render_job(job_id: str, body: dict = Body(...)):
    try:
        STORE.get(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    candidate_ids = body.get("candidate_ids") or []
    settings = body.get("settings") or {}
    if not candidate_ids:
        raise HTTPException(400, "candidate_ids is required")
    pipeline.start_render(job_id, candidate_ids, settings=settings)
    return {"ok": True}


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    import shutil
    try:
        STORE.get(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    for path in (
        STORE.root / job_id,
        config.SOURCES_DIR / job_id,
    ):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Clip download / preview
# --------------------------------------------------------------------------- #
def _resolve_clip_path(job_id: str, candidate_id: str, prefer_captioned: bool = True) -> Path:
    try:
        j = STORE.get(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    cand = next((c for c in j.candidates if c.id == candidate_id), None)
    if cand is None:
        raise HTTPException(404, "Candidate not found")
    path_str = cand.captioned_clip_path if prefer_captioned else cand.rendered_clip_path
    if not path_str:
        raise HTTPException(404, "Clip not rendered yet")
    p = Path(path_str)
    if not p.exists():
        raise HTTPException(404, "Clip file missing on disk")
    return p


@app.get("/api/jobs/{job_id}/clips/{candidate_id}/download")
def download_clip(job_id: str, candidate_id: str, captioned: bool = Query(True)):
    p = _resolve_clip_path(job_id, candidate_id, prefer_captioned=captioned)
    return FileResponse(
        path=str(p),
        media_type="video/mp4",
        filename=f"clipforge_{job_id}_{candidate_id}.mp4",
    )


@app.get("/api/jobs/{job_id}/clips/{candidate_id}/preview")
def preview_clip(job_id: str, candidate_id: str, captioned: bool = Query(True)):
    p = _resolve_clip_path(job_id, candidate_id, prefer_captioned=captioned)
    return FileResponse(
        path=str(p),
        media_type="video/mp4",
        headers={"Cache-Control": "no-cache"},
    )
