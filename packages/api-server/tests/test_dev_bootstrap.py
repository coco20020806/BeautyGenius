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

    store = TaskStore(root=tmp_path / "tasks")
    result = bootstrap_preview_task(store, parse_run=parse_run, preview_run=preview_run)
    task_id = result["taskId"]
    task = store.load(task_id)
    assert task["status"] == "completed"
    assert Path(task["media_dir"], "preview_01.jpg").is_file()
    assert Path(task["media_dir"], "target.jpg").is_file()
    assert task["tutorial_path"] is not None
