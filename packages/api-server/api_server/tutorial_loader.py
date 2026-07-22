from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api_server.errors import ApiError


def load_tutorial_document(task: dict[str, Any], *, request_id: str) -> dict[str, Any]:
    if task.get("status") != "completed":
        raise ApiError(409, "TUTORIAL_NOT_READY", "教程尚未就绪", request_id=request_id)

    raw_path = task.get("tutorial_path")
    if not raw_path:
        raise ApiError(409, "TUTORIAL_NOT_READY", "教程尚未就绪", request_id=request_id)

    tutorial_path = Path(raw_path)
    if not tutorial_path.is_file():
        raise ApiError(409, "TUTORIAL_NOT_READY", "教程尚未就绪", request_id=request_id)

    return json.loads(tutorial_path.read_text(encoding="utf-8"))
