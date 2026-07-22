from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api_server.errors import ApiError


def effective_tutorial_path(task: dict[str, Any]) -> Path | None:
    """Prefer optimized tutorial when present; otherwise original tutorial_path."""
    for key in ("optimized_tutorial_path", "tutorial_path"):
        raw = task.get(key)
        if not raw:
            continue
        path = Path(raw)
        if path.is_file():
            return path
    return None


def load_tutorial_document(task: dict[str, Any], *, request_id: str) -> dict[str, Any]:
    if task.get("status") != "completed":
        raise ApiError(409, "TUTORIAL_NOT_READY", "教程尚未就绪", request_id=request_id)

    tutorial_path = effective_tutorial_path(task)
    if tutorial_path is None:
        raise ApiError(409, "TUTORIAL_NOT_READY", "教程尚未就绪", request_id=request_id)

    return json.loads(tutorial_path.read_text(encoding="utf-8"))
