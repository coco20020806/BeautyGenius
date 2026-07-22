"""Dev bootstrap from pinned local runs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from api_server.dev_bootstrap import (
    DevRunsNotPinnedError,
    bootstrap_preview_task,
    load_pinned_runs,
)
from api_server.store import TaskStore


def test_load_pinned_runs_success(tmp_path: Path) -> None:
    parse_run = tmp_path / "parse"
    preview_run = tmp_path / "preview"
    parse_run.mkdir()
    preview_run.mkdir()
    (parse_run / "analysis.json").write_text("{}", encoding="utf-8")
    (preview_run / "preview_01.jpg").write_bytes(b"fake")

    pinned = tmp_path / "pinned.json"
    pinned.write_text(
        json.dumps(
            {
                "parse_run_dir": str(parse_run),
                "preview_run_dir": str(preview_run),
            }
        ),
        encoding="utf-8",
    )
    loaded_parse, loaded_preview = load_pinned_runs(pinned)
    assert loaded_parse == parse_run.resolve()
    assert loaded_preview == preview_run.resolve()


def test_load_pinned_runs_missing_config(tmp_path: Path) -> None:
    with pytest.raises(DevRunsNotPinnedError) as exc:
        load_pinned_runs(tmp_path / "missing.json")
    assert exc.value.api_code == "DEV_RUNS_NOT_PINNED"


def test_bootstrap_preview_task_copies_media(tmp_path: Path) -> None:
    parse_run = tmp_path / "parse"
    preview_run = tmp_path / "preview"
    parse_run.mkdir()
    preview_run.mkdir()
    (parse_run / "analysis.json").write_text("{}", encoding="utf-8")
    (parse_run / "tutorial.json").write_text('{"steps":[]}', encoding="utf-8")
    (preview_run / "target.jpg").write_bytes(b"before")
    (preview_run / "preview_01.jpg").write_bytes(b"after")
    (preview_run / "preview.json").write_text("{}", encoding="utf-8")
    source_video = tmp_path / "示例视频1.mp4"
    source_video.write_bytes(b"fake-video-bytes")

    store = TaskStore(root=tmp_path / "tasks")
    result = bootstrap_preview_task(
        store,
        parse_run=parse_run,
        preview_run=preview_run,
        source_video=source_video,
    )
    task_id = result["taskId"]
    task = store.load(task_id)
    assert task["status"] == "completed"
    assert Path(task["media_dir"], "preview_01.jpg").is_file()
    assert Path(task["media_dir"], "target.jpg").is_file()
    assert task["tutorial_path"] is not None
    installed = Path(task["video_path"])
    assert installed.name == "video.mp4"
    assert installed.is_file()
    assert installed.read_bytes() == b"fake-video-bytes"
    assert (store.task_dir(task_id) / "upload" / "video.mp4").is_file()
    from api_server.media_urls import resolve_task_video_url

    assert resolve_task_video_url(task_id, task) == f"http://127.0.0.1:8000/media/{task_id}/video.mp4"


def test_bootstrap_preview_task_missing_source_video(tmp_path: Path) -> None:
    parse_run = tmp_path / "parse"
    preview_run = tmp_path / "preview"
    parse_run.mkdir()
    preview_run.mkdir()
    (parse_run / "analysis.json").write_text("{}", encoding="utf-8")
    (preview_run / "preview_01.jpg").write_bytes(b"after")

    store = TaskStore(root=tmp_path / "tasks")
    with pytest.raises(DevRunsNotPinnedError) as exc:
        bootstrap_preview_task(
            store,
            parse_run=parse_run,
            preview_run=preview_run,
            source_video=tmp_path / "missing.mp4",
        )
    assert exc.value.api_code == "DEV_RUNS_NOT_PINNED"
