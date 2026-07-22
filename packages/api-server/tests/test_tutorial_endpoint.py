"""Tutorial document loading from completed tasks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api_server.errors import ApiError
from api_server.main import app
from api_server.store import TaskStore, store
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
    local_store = TaskStore(root=tmp_path / "tasks")
    task = local_store.create_uploaded(
        file_name="v.mp4",
        file_size=10,
        video_path=str(tmp_path / "v.mp4"),
    )
    local_store.set_photo_ready(task["taskId"], photo_path=None, skipped=True, photo_id=None)
    local_store.mark_processing(task["taskId"])
    loaded_task = local_store.load(task["taskId"])

    with pytest.raises(ApiError) as exc:
        load_tutorial_document(loaded_task, request_id="req_wait")
    assert exc.value.api_code == "TUTORIAL_NOT_READY"


def test_get_tutorial_appends_video_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    video = tmp_path / "video.mp4"
    video.write_bytes(b"x")
    tutorial_file = tmp_path / "tutorial.json"
    tutorial_file.write_text(
        json.dumps(
            {
                "contract_version": "tutorial.v1",
                "tutorial_id": "t1",
                "title": "测试妆",
                "steps": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    task = store.create_uploaded(file_name="v.mp4", file_size=1, video_path=str(video))
    task["status"] = "completed"
    task["tutorial_path"] = str(tutorial_file)
    store.save(task)

    client = TestClient(app)
    resp = client.get(f"/api/v1/makeup/tasks/{task['taskId']}/tutorial")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "测试妆"
    assert body["videoUrl"] == f"http://127.0.0.1:8000/media/{task['taskId']}/video.mp4"
    disk = json.loads(tutorial_file.read_text(encoding="utf-8"))
    assert "videoUrl" not in disk
