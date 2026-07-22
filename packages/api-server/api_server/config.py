from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PARSE_SKILL = REPO_ROOT / "skills" / "beauty-video-parse"
PREVIEW_SKILL = REPO_ROOT / "skills" / "kol-makeup-preview"
PICTURE_MAKEUP_SKILL = REPO_ROOT / "skills" / "picture_makeup"
PICTURE_MAKEUP_OUTPUT_ROOT = REPO_ROOT / "outputs" / "picture-makeup"
TASKS_ROOT = REPO_ROOT / "outputs" / "tasks"
PARSE_OUTPUT_ROOT = REPO_ROOT / "outputs" / "runs"
PREVIEW_OUTPUT_ROOT = REPO_ROOT / "outputs" / "makeup-preview"
JOBS_OUTPUT_ROOT = REPO_ROOT / "outputs" / "jobs"
DEV_PINNED_RUNS_PATH = REPO_ROOT / "configs" / "dev-pinned-runs.json"

_app_env = os.environ.get("APP_ENV", "").strip().lower()
_production = _app_env == "production"
_dev_flag = os.environ.get("ENABLE_DEV_SHORTCUTS", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
_dev_disabled = os.environ.get("ENABLE_DEV_SHORTCUTS", "").strip().lower() in {
    "0",
    "false",
    "no",
    "off",
}
# 本地仓库默认开启；生产请设 APP_ENV=production 或 ENABLE_DEV_SHORTCUTS=0
ENABLE_DEV_SHORTCUTS = (
    _dev_flag
    or _app_env == "development"
    or (not _production and not _dev_disabled)
)

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
