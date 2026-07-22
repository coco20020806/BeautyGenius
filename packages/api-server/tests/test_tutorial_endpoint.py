"""Tutorial document loading from completed tasks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from api_server.errors import ApiError
from api_server.store import TaskStore
from api_server.tutorial_loader import load_tutorial_document


def test_load_tutorial_document_success(tmp_path: Path) -> None:
    tutorial_file = tmp_path / "tutorial.json"
    tutorial_doc = {
        "contract_version": "tutorial.v1",
        "tutorial_id": "tutorial_test",
        "title": "测试妆",
        "steps": [{"step_id": "blush_01"}],
    }
    tutorial_file.write_text(json.dumps(tutorial_doc, ensure_ascii=False), encoding="utf-8")

    task = {
        "status": "completed",
        "tutorial_path": str(tutorial_file),
    }
    loaded = load_tutorial_document(task, request_id="req_test")
    assert loaded["title"] == "测试妆"


def test_load_tutorial_document_not_ready(tmp_path: Path) -> None:
    store = TaskStore(root=tmp_path / "tasks")
    task = store.create_uploaded(
        file_name="v.mp4",
        file_size=10,
        video_path=str(tmp_path / "v.mp4"),
    )
    store.set_photo_ready(task["taskId"], photo_path=None, skipped=True, photo_id=None)
    store.mark_processing(task["taskId"])
    loaded_task = store.load(task["taskId"])

    with pytest.raises(ApiError) as exc:
        load_tutorial_document(loaded_task, request_id="req_wait")
    assert exc.value.api_code == "TUTORIAL_NOT_READY"
