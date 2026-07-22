from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api_server.main import app
from api_server.store import store
from api_server.tutorial_loader import effective_tutorial_path, load_tutorial_document


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _seed_completed_task(tmp_path: Path) -> dict:
    tutorial_file = tmp_path / "tutorial.json"
    tutorial_file.write_text(
        json.dumps(
            {
                "contract_version": "tutorial.v1",
                "tutorial_id": "t1",
                "title": "Original",
                "steps": [
                    {
                        "step_id": "blush_01",
                        "part": "cheek",
                        "taxonomy_primary": "腮红",
                        "instruction": "斜扫",
                        "adaptation_note": "",
                        "visual_layer": {"position": "颧骨"},
                        "video_clip": {"start": 0, "end": 1},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
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
    task["step_diagrams_status"] = "completed"
    task["step_diagrams_run_dir"] = str(tmp_path / "old-diagrams")
    store.save(task)
    return task


def test_effective_tutorial_path_prefers_optimized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    task = _seed_completed_task(tmp_path)
    optimized = tmp_path / "tutorial_optimized.json"
    optimized.write_text(
        json.dumps(
            {
                "contract_version": "tutorial.v1",
                "tutorial_id": "t1",
                "title": "Optimized",
                "steps": [
                    {
                        "step_id": "blush_01",
                        "instruction": "横向轻铺",
                        "adaptation_note": "缩短中庭",
                        "visual_layer": {"position": "面中"},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    task["optimized_tutorial_path"] = str(optimized)
    store.save(task)
    loaded = store.load(task["taskId"])
    assert effective_tutorial_path(loaded) == optimized
    doc = load_tutorial_document(loaded, request_id="r1")
    assert doc["steps"][0]["instruction"] == "横向轻铺"


def test_post_adjustment_writes_optimized_and_resets_diagrams(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    task = _seed_completed_task(tmp_path)

    optimized_path = tmp_path / "run" / "tutorial_optimized.json"
    optimized_path.parent.mkdir(parents=True)
    optimized_path.write_text(
        json.dumps(
            {
                "contract_version": "tutorial.v1",
                "tutorial_id": "t1",
                "title": "Optimized",
                "steps": [
                    {
                        "step_id": "blush_01",
                        "instruction": "横向轻铺",
                        "adaptation_note": "缩短中庭",
                        "visual_layer": {"position": "面中"},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class FakeResult:
        optimized_tutorial_path = optimized_path
        run_dir = optimized_path.parent
        optimization = {
            "optimization_summary": {"primary_goal": "缩短中庭", "retained_modules": ["腮红"]}
        }

    with patch("api_server.adjustment.run_optimization_job", return_value=FakeResult()):
        with patch("api_server.adjustment.load_api_key", return_value="test-key"):
            client = TestClient(app)
            resp = client.post(
                f"/api/v1/makeup/tasks/{task['taskId']}/adjustment",
                json={
                    "styles": ["清透自然"],
                    "occasions": ["通勤工作"],
                    "retainedParts": ["腮红"],
                    "skinType": "混合性肌肤",
                    "concerns": ["缩短中庭"],
                    "constraints": [],
                },
            )

            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "completed"
            assert body["summary"]["primary_goal"] == "缩短中庭"

            loaded = store.load(task["taskId"])
            assert loaded["optimized_tutorial_path"] == str(optimized_path.resolve())
            assert loaded["adjustment"]["concerns"] == ["缩短中庭"]
            assert loaded["step_diagrams_status"] == "idle"
            assert loaded["step_diagrams_run_dir"] is None

            tutorial_resp = client.get(f"/api/v1/makeup/tasks/{task['taskId']}/tutorial")
            assert tutorial_resp.status_code == 200
            assert tutorial_resp.json()["steps"][0]["instruction"] == "横向轻铺"
