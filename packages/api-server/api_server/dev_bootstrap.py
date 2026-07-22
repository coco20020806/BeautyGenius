from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api_server.config import DEV_PINNED_RUNS_PATH, REPO_ROOT
from api_server.errors import ApiError
from api_server.preview_assembler import publish_media_files
from api_server.store import TaskStore, new_task_id


class DevRunsNotPinnedError(ApiError):
    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__(409, "DEV_RUNS_NOT_PINNED", message, request_id=request_id)


def _resolve_repo_path(rel_or_abs: str) -> Path:
    raw = Path(rel_or_abs)
    if raw.is_absolute():
        return raw
    return (REPO_ROOT / raw).resolve()


def load_pinned_runs(
    pinned_path: Path = DEV_PINNED_RUNS_PATH,
    *,
    request_id: str | None = None,
) -> tuple[Path, Path]:
    if not pinned_path.is_file():
        raise DevRunsNotPinnedError(
            f"缺少固定 run 配置：{pinned_path}。请运行 scripts/pin-latest-dev-runs.py",
            request_id=request_id,
        )
    try:
        doc = json.loads(pinned_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DevRunsNotPinnedError(
            f"固定 run 配置无效：{pinned_path}",
            request_id=request_id,
        ) from exc

    parse_raw = (doc.get("parse_run_dir") or "").strip()
    preview_raw = (doc.get("preview_run_dir") or "").strip()
    if not parse_raw or not preview_raw:
        raise DevRunsNotPinnedError("固定 run 配置缺少 parse_run_dir 或 preview_run_dir", request_id=request_id)

    parse_run = _resolve_repo_path(parse_raw)
    preview_run = _resolve_repo_path(preview_raw)

    if not parse_run.is_dir() or not (parse_run / "analysis.json").is_file():
        raise DevRunsNotPinnedError(
            f"video parse run 无效或缺少 analysis.json：{parse_run}",
            request_id=request_id,
        )
    preview_ok = (preview_run / "preview.json").is_file() or (preview_run / "preview_01.jpg").is_file()
    if not preview_run.is_dir() or not preview_ok:
        raise DevRunsNotPinnedError(
            f"makeup preview run 无效或缺少 preview 产物：{preview_run}",
            request_id=request_id,
        )
    return parse_run, preview_run


def bootstrap_preview_task(
    store: TaskStore,
    *,
    parse_run: Path,
    preview_run: Path,
) -> dict[str, Any]:
    task_id = new_task_id()
    analysis_path = parse_run / "analysis.json"
    tutorial_path = parse_run / "tutorial.json"
    tutorial_str = str(tutorial_path.resolve()) if tutorial_path.is_file() else None

    task = store.create_uploaded(
        file_name="dev-skip-placeholder.mp4",
        file_size=0,
        video_path=str(analysis_path.resolve()),
        task_id=task_id,
        parse_mode="fast",
        skip_transfer=False,
    )
    store.set_photo_ready(task_id, photo_path=None, skipped=True, photo_id=None)

    task_dir = store.task_dir(task_id)
    media_dir = publish_media_files(task_id, preview_run, task_dir)

    store.mark_completed(
        task_id,
        parse_run_dir=str(parse_run.resolve()),
        preview_run_dir=str(preview_run.resolve()),
        tutorial_path=tutorial_str,
        media_dir=str(media_dir.resolve()),
    )

    return {
        "taskId": task_id,
        "status": "completed",
        "parseRunDir": str(parse_run.resolve()),
        "previewRunDir": str(preview_run.resolve()),
    }


def bootstrap_from_pinned_file(
    store: TaskStore,
    *,
    pinned_path: Path = DEV_PINNED_RUNS_PATH,
    request_id: str | None = None,
) -> dict[str, Any]:
    parse_run, preview_run = load_pinned_runs(pinned_path, request_id=request_id)
    return bootstrap_preview_task(store, parse_run=parse_run, preview_run=preview_run)
