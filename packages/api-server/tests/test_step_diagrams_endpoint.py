from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api_server.main import app
from api_server.store import store


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_step_diagrams_idle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    tutorial_file = tmp_path / "tutorial.json"
    tutorial_doc = {
        "contract_version": "tutorial.v1",
        "tutorial_id": "t1",
        "title": "Test",
        "steps": [
            {
                "step_id": "blush_01",
                "part": "cheek",
                "taxonomy_primary": "腮红",
                "product": {"name": "x", "keywords": []},
                "visual_layer": {},
                "instruction": "扫腮红",
                "adaptation_note": "",
                "video_clip": {"start": 0, "end": 1},
            }
        ],
    }
    tutorial_file.write_text(json.dumps(tutorial_doc, ensure_ascii=False), encoding="utf-8")
    task = store.create_uploaded(
        file_name="v.mp4",
        file_size=100,
        video_path=str(tmp_path / "v.mp4"),
    )
    (tmp_path / "v.mp4").write_bytes(b"x")
    task["status"] = "completed"
    task["parse_run_dir"] = str(tmp_path)
    task["tutorial_path"] = str(tutorial_file)
    task["media_dir"] = str(tmp_path / "media")
    store.save(task)

    client = TestClient(app)
    resp = client.get(f"/api/v1/makeup/tasks/{task['taskId']}/step-diagrams")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "idle"
    assert len(body["steps"]) == 1
    assert body["steps"][0]["stepId"] == "blush_01"
    assert body["steps"][0]["imageUrl"] is None
    assert body["steps"][0]["videoClip"] == {"start": 0.0, "end": 1.0}
    assert body["videoUrl"] == f"http://127.0.0.1:8000/media/{task['taskId']}/v.mp4"


def test_post_step_diagrams_starts_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    tutorial_file = tmp_path / "tutorial.json"
    tutorial_file.write_text(
        json.dumps(
            {
                "contract_version": "tutorial.v1",
                "tutorial_id": "t1",
                "title": "Test",
                "steps": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    task = store.create_uploaded(file_name="v.mp4", file_size=1, video_path=str(tmp_path / "v.mp4"))
    (tmp_path / "v.mp4").write_bytes(b"x")
    task["status"] = "completed"
    task["parse_run_dir"] = str(tmp_path)
    task["tutorial_path"] = str(tutorial_file)
    store.save(task)

    with patch("api_server.main.run_step_diagrams_job") as mock_job:
        client = TestClient(app)
        resp = client.post(f"/api/v1/makeup/tasks/{task['taskId']}/step-diagrams")
        assert resp.status_code == 202
        assert resp.json()["status"] == "processing"

    loaded = store.load(task["taskId"])
    assert loaded["step_diagrams_status"] == "processing"


def test_get_step_diagrams_exposes_step_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    tutorial_file = tmp_path / "tutorial.json"
    tutorial_file.write_text(
        json.dumps(
            {
                "contract_version": "tutorial.v1",
                "tutorial_id": "t1",
                "title": "Test",
                "steps": [
                    {
                        "step_id": "blush_01",
                        "part": "cheek",
                        "taxonomy_primary": "腮红",
                        "product": {"name": "x", "keywords": []},
                        "visual_layer": {},
                        "instruction": "扫腮红",
                        "adaptation_note": "",
                        "video_clip": {"start": 0, "end": 1},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    run_dir = tmp_path / "diagram_run"
    (run_dir / "steps" / "blush_01").mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "step_id": "blush_01",
                        "status": "failed",
                        "error": "文本 API 失败: url error",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    task = store.create_uploaded(file_name="v.mp4", file_size=1, video_path=str(tmp_path / "v.mp4"))
    (tmp_path / "v.mp4").write_bytes(b"x")
    task["status"] = "completed"
    task["parse_run_dir"] = str(tmp_path)
    task["tutorial_path"] = str(tutorial_file)
    task["media_dir"] = str(tmp_path / "media")
    task["step_diagrams_status"] = "completed"
    task["step_diagrams_run_dir"] = str(run_dir)
    store.save(task)

    client = TestClient(app)
    resp = client.get(f"/api/v1/makeup/tasks/{task['taskId']}/step-diagrams")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert "url error" in body["failureReason"]
    assert body["steps"][0]["status"] == "failed"
    assert body["steps"][0]["error"] == "文本 API 失败: url error"
