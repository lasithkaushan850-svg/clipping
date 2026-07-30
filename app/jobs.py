"""Persistent job state.

Each job gets a UUID and a directory under ``data/jobs/<job_id>``. The
directory contains:

    meta.json        — serialized JobState (status, candidates, settings…)
    source.mp4       — downloaded YouTube video (only after download phase)
    highlights/      — raw cut MP4s
    shorts/          — final reframed 9:16 MP4s (no captions)
    captioned/       — final captioned MP4s ready to download
    log.txt          — human-readable progress log

We deliberately keep state on disk (not in memory) so the app survives a
restart while a long 2-hour video is being processed.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config


# --------------------------------------------------------------------------- #
# Status enum
# --------------------------------------------------------------------------- #
class Status:
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    SCORING = "scoring"
    READY = "ready"               # user can preview candidates
    RENDERING = "rendering"       # clipping + captioning
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# --------------------------------------------------------------------------- #
# Job model
# --------------------------------------------------------------------------- #
@dataclass
class Candidate:
    """A viral-moment candidate returned by the AI scorer."""
    id: str
    index: int
    title: str
    start: float
    end: float
    duration: float
    score: int                          # 0-100 raw virality score
    success_rate: float                 # 0-100 normalised display score
    hook_sentence: str
    virality_reason: str
    snippet: str                        # ~120 chars of transcript preview
    rendered_clip_path: Optional[str] = None       # 9:16 reframe, no captions
    captioned_clip_path: Optional[str] = None      # with burned-in captions
    render_status: str = "pending"                 # pending / rendering / done / failed
    render_error: Optional[str] = None
    caption_style: Optional[str] = None
    caption_position: int = 10

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JobState:
    job_id: str
    created_at: float
    updated_at: float
    source: str                         # youtube URL or "upload:<file>"
    source_kind: str                    # "youtube" | "upload"
    source_title: str = ""
    source_channel: str = ""
    source_duration: float = 0.0
    source_thumbnail: str = ""
    language: str = "auto"
    status: str = Status.QUEUED
    phase: str = ""
    progress: int = 0
    error: Optional[str] = None
    log_lines: List[str] = field(default_factory=list)
    candidates: List[Candidate] = field(default_factory=list)
    aspect_ratio: str = "9:16"
    resolution: str = "720"
    min_score: int = 40
    max_candidates: int = 10
    caption_style: str = "hormozi"
    caption_position: int = 10
    num_clips_to_render: int = 3

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["candidates"] = [c if isinstance(c, dict) else c.to_dict() for c in self.candidates]
        return d

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "JobState":
        cands_raw = raw.pop("candidates", [])
        job = cls(**raw)
        job.candidates = [Candidate(**c) for c in cands_raw]
        return job


# --------------------------------------------------------------------------- #
# JobStore
# --------------------------------------------------------------------------- #
class JobStore:
    """Filesystem-backed job store. Thread-safe within a single process."""

    def __init__(self, root: Path = config.JOBS_DIR):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # -- creation ---------------------------------------------------------- #
    def create(self, source: str, source_kind: str) -> JobState:
        job_id = uuid.uuid4().hex[:12]
        job_dir = self.root / job_id
        (job_dir / "highlights").mkdir(parents=True, exist_ok=True)
        (job_dir / "shorts").mkdir(parents=True, exist_ok=True)
        (job_dir / "captioned").mkdir(parents=True, exist_ok=True)
        now = time.time()
        job = JobState(
            job_id=job_id,
            created_at=now,
            updated_at=now,
            source=source,
            source_kind=source_kind,
        )
        self._write(job)
        return job

    # -- read / write ------------------------------------------------------ #
    def get(self, job_id: str) -> JobState:
        meta_path = self.root / job_id / "meta.json"
        if not meta_path.exists():
            raise KeyError(f"Job {job_id!r} not found")
        with meta_path.open("r", encoding="utf-8") as fh:
            return JobState.from_dict(json.load(fh))

    def _write(self, job: JobState) -> None:
        job.updated_at = time.time()
        meta_path = self.root / job.job_id / "meta.json"
        tmp = meta_path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(job.to_dict(), fh, indent=2)
        os.replace(tmp, meta_path)

    def save(self, job: JobState) -> None:
        self._write(job)

    # -- helpers ----------------------------------------------------------- #
    def append_log(self, job: JobState, line: str) -> None:
        ts = time.strftime("%H:%M:%S")
        msg = f"[{ts}] {line}"
        job.log_lines.append(msg)
        # Keep at most last 500 lines in memory + log file.
        if len(job.log_lines) > 500:
            job.log_lines = job.log_lines[-500:]
        log_path = self.root / job.job_id / "log.txt"
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
        self.save(job)

    def job_dir(self, job_id: str) -> Path:
        d = self.root / job_id
        d.mkdir(parents=True, exist_ok=True)
        return d


# --------------------------------------------------------------------------- #
# Convenience: a single module-level store
# --------------------------------------------------------------------------- #
STORE = JobStore()
