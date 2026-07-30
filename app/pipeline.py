"""End-to-end orchestration: download → transcribe → score → render.

This is the function the FastAPI handlers call. It runs in a background
thread so the HTTP request can return immediately with a job id; the
frontend then polls ``GET /api/jobs/{id}`` for progress.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Optional

from . import config, downloader
from .captions import render_captioned_clip
from .clipper import cut_subclip, overlay_hook_text, reframe_aspect
from .highlights import detect_viral_moments, to_candidate
from .jobs import (
    Candidate,
    JobState,
    Status,
    STORE,
)

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #
def start_job(source: str, source_kind: str, settings: Optional[dict] = None) -> JobState:
    """Create the job, kick off a background worker, return immediately."""
    settings = settings or {}
    job = STORE.create(source=source, source_kind=source_kind)
    if source_kind == "youtube":
        # Fetch metadata up-front so the UI can show the title before download.
        try:
            meta = downloader.probe_metadata(source)
            job.source_title = meta.title
            job.source_channel = meta.channel
            job.source_duration = meta.duration
            job.source_thumbnail = meta.thumbnail
        except Exception as exc:  # noqa: BLE001
            STORE.append_log(job, f"metadata probe failed: {exc}")

    # Apply settings
    job.aspect_ratio = settings.get("aspect_ratio", config.DEFAULT_ASPECT_RATIO)
    job.resolution = settings.get("resolution", config.DEFAULT_RESOLUTION)
    job.min_score = int(settings.get("min_score", config.MIN_SCORE))
    job.max_candidates = int(settings.get("max_candidates", config.MAX_CANDIDATES))
    job.caption_style = settings.get("caption_style", "hormozi")
    job.caption_position = int(settings.get("caption_position", 10))
    job.num_clips_to_render = int(settings.get("num_clips_to_render", config.CLIPS_TO_RENDER))
    STORE.save(job)

    t = threading.Thread(target=run_job, args=(job.job_id,), daemon=True, name=f"job-{job.job_id}")
    t.start()
    return job


def start_render(job_id: str, candidate_ids: list[str], settings: Optional[dict] = None) -> None:
    """Kick off the render step for a list of selected candidate ids."""
    job = STORE.get(job_id)
    if not job.candidates:
        raise ValueError("No candidates to render")
    if settings:
        if "caption_style" in settings:
            job.caption_style = settings["caption_style"]
        if "caption_position" in settings:
            job.caption_position = int(settings["caption_position"])
        if "aspect_ratio" in settings:
            job.aspect_ratio = settings["aspect_ratio"]
        STORE.save(job)

    t = threading.Thread(
        target=_render_selected,
        args=(job_id, candidate_ids),
        daemon=True,
        name=f"render-{job_id}",
    )
    t.start()


# --------------------------------------------------------------------------- #
# Worker
# --------------------------------------------------------------------------- #
def run_job(job_id: str) -> None:
    """Download → transcribe → score. Ends with status=ready."""
    job = STORE.get(job_id)
    try:
        # ---- 1. download / copy source ----
        job.status = Status.DOWNLOADING
        job.phase = "Downloading source"
        job.progress = 2
        STORE.save(job)
        STORE.append_log(job, f"Downloading source: {job.source}")
        source_path = _acquire_source(job)

        if not job.source_duration:
            job.source_duration = downloader.probe_local_duration(source_path)
        STORE.save(job)
        STORE.append_log(
            job,
            f"Source ready: {source_path.name} ({job.source_duration/60:.1f} min)",
        )

        # ---- 2. transcribe ----
        job.status = Status.TRANSCRIBING
        job.phase = "Transcribing audio"
        job.progress = 15
        STORE.save(job)
        STORE.append_log(job, "Transcribing with Whisper…")
        from . import transcriber
        transcript = transcriber.transcribe(source_path, language=config.WHISPER_LANGUAGE)
        job.language = transcript.get("language", "en")

        # Persist transcript
        transcript_path = STORE.job_dir(job_id) / "transcript.json"
        import json
        transcript_path.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
        STORE.append_log(
            job,
            f"Transcription done: {len(transcript['segments'])} segments, "
            f"lang={transcript.get('language')}",
        )

        # ---- 3. detect viral moments ----
        job.status = Status.SCORING
        job.phase = "Detecting viral moments"
        job.progress = 55
        STORE.save(job)
        STORE.append_log(job, "Scoring moments with LLM + audio analysis…")
        picks = detect_viral_moments(
            transcript,
            video_path=source_path,
            max_candidates=job.max_candidates,
            min_score=job.min_score,
        )
        # Persist picks
        (STORE.job_dir(job_id) / "candidates.json").write_text(
            json.dumps(picks, indent=2), encoding="utf-8"
        )

        # Convert to Candidate objects
        job.candidates = [
            to_candidate(p, job.caption_style, job.caption_position) for p in picks
        ]
        STORE.append_log(
            job,
            f"Found {len(picks)} viral candidates. Ready for preview!",
        )

        # ---- done ----
        job.status = Status.READY
        job.phase = "Ready"
        job.progress = 100
        STORE.save(job)

    except Exception as exc:  # noqa: BLE001
        log.exception("job %s failed", job_id)
        STORE.append_log(job, f"ERROR: {exc}")
        job.status = Status.FAILED
        job.error = str(exc)
        job.progress = 100
        STORE.save(job)


def _acquire_source(job: JobState) -> Path:
    """Download YouTube or copy an upload. Returns the local file path."""
    src_dir = Path(config.SOURCES_DIR) / job.job_id
    if job.source_kind == "youtube":
        return downloader.download_youtube(
            job.source, job.resolution, src_dir
        )
    # uploaded file (path was passed in `source` as ``upload:/abs/path``)
    if job.source.startswith("upload:"):
        src = Path(job.source[len("upload:"):])
        return downloader.copy_uploaded_file(src, src_dir)
    raise ValueError(f"Unknown source kind: {job.source_kind}")


# --------------------------------------------------------------------------- #
# Render selected candidates
# --------------------------------------------------------------------------- #
def _render_selected(job_id: str, candidate_ids: list[str]) -> None:
    job = STORE.get(job_id)
    try:
        job.status = Status.RENDERING
        job.phase = "Rendering clips"
        job.progress = 0
        STORE.save(job)

        # Load transcript
        import json
        transcript_path = STORE.job_dir(job_id) / "transcript.json"
        transcript = json.loads(transcript_path.read_text(encoding="utf-8"))

        # Source video
        source_path = _find_source(job_id)

        # Validate candidates
        wanted = [c for c in job.candidates if c.id in candidate_ids]
        if not wanted:
            raise ValueError("None of the requested candidates exist")

        # Apply per-clip style/position overrides
        for c in job.candidates:
            if c.id in candidate_ids:
                c.render_status = "rendering"
        STORE.save(job)

        total = len(wanted)
        highlights_dir = STORE.job_dir(job_id) / "highlights"
        shorts_dir = STORE.job_dir(job_id) / "shorts"
        captioned_dir = STORE.job_dir(job_id) / "captioned"

        for i, cand in enumerate(wanted, 1):
            STORE.append_log(
                job,
                f"Rendering {i}/{total}: {cand.title} "
                f"[{cand.start:.1f}s → {cand.end:.1f}s]",
            )
            job.phase = f"Rendering clip {i}/{total}"
            job.progress = int(5 + (i - 1) / total * 90)
            STORE.save(job)

            try:
                # 1. cut subclip
                cut_path = highlights_dir / f"{cand.id}.cut.mp4"
                cut_subclip(source_path, cand.start, cand.end, cut_path)

                # 2. reframe to target aspect
                short_path = shorts_dir / f"{cand.id}.mp4"
                reframe_aspect(cut_path, short_path, job.aspect_ratio)
                cut_path.unlink(missing_ok=True)

                # 3. overlay hook banner (first 2.5s)
                if cand.hook_sentence:
                    hooked = shorts_dir / f"{cand.id}.hooked.mp4"
                    overlay_hook_text(short_path, hooked, cand.hook_sentence, duration=2.5)
                    short_path.unlink()
                    short_path = hooked

                # 4. burn in captions
                captioned_path = captioned_dir / f"{cand.id}.mp4"
                style = cand.caption_style or job.caption_style
                position = cand.caption_position or job.caption_position
                render_captioned_clip(
                    short_path, transcript, cand.start, cand.end,
                    captioned_path, style_id=style, caption_position=position,
                )
                short_path.unlink(missing_ok=True)

                cand.rendered_clip_path = str(short_path)
                cand.captioned_clip_path = str(captioned_path)
                cand.render_status = "done"
                STORE.append_log(job, f"  ✓ clip {cand.id} ready")

            except Exception as exc:  # noqa: BLE001
                STORE.append_log(job, f"  ✗ clip {cand.id} failed: {exc}")
                cand.render_status = "failed"
                cand.render_error = str(exc)
            STORE.save(job)

        job.status = Status.COMPLETED
        job.phase = "Completed"
        job.progress = 100
        STORE.save(job)
        STORE.append_log(job, f"All {total} clips rendered. You can now download them.")

    except Exception as exc:  # noqa: BLE001
        log.exception("render job %s failed", job_id)
        STORE.append_log(job, f"ERROR: {exc}")
        job.status = Status.FAILED
        job.error = str(exc)
        STORE.save(job)


def _find_source(job_id: str) -> Path:
    src_dir = Path(config.SOURCES_DIR) / job_id
    candidates = sorted(src_dir.glob("source.*"))
    if not candidates:
        raise RuntimeError(f"Source video not found for job {job_id}")
    return max(candidates, key=lambda p: p.stat().st_size)
