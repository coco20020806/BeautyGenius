"""Public media URL helpers for uploaded task assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from api_server.config import API_PUBLIC_BASE_URL


def resolve_task_video_url(task_id: str, task: dict[str, Any]) -> str | None:
    """Return public URL for the uploaded source video, or None if missing."""
    raw = task.get("video_path")
    if not raw:
        return None
    path = Path(raw)
    if not path.is_file():
        return None
    name = path.name
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        return None
    return f"{API_PUBLIC_BASE_URL}/media/{task_id}/{name}"
