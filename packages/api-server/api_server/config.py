from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PARSE_SKILL = REPO_ROOT / "skills" / "beauty-video-parse"
PREVIEW_SKILL = REPO_ROOT / "skills" / "kol-makeup-preview"
TASKS_ROOT = REPO_ROOT / "outputs" / "tasks"
PARSE_OUTPUT_ROOT = REPO_ROOT / "outputs" / "runs"
PREVIEW_OUTPUT_ROOT = REPO_ROOT / "outputs" / "makeup-preview"
JOBS_OUTPUT_ROOT = REPO_ROOT / "outputs" / "jobs"

MAX_VIDEO_BYTES = 500 * 1024 * 1024
VIDEO_EXTENSIONS = {".mp4", ".mov"}
VIDEO_MIMES = {"video/mp4", "video/quicktime"}

API_PUBLIC_BASE_URL = os.environ.get("API_PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
SKIP_TRANSFER = os.environ.get("SKIP_TRANSFER", "").strip().lower() in {"1", "true", "yes", "on"}
PARSE_MODE = os.environ.get("PARSE_MODE", "fast").strip().lower()
if PARSE_MODE not in {"full", "fast"}:
    PARSE_MODE = "fast"

CORS_ORIGINS = [
    "http://127.0.0.1:5174",
    "http://localhost:5174",
]
