from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api_server.main import app
from api_server.store import store
from makeup_preview import UserPhotoRejected


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _task_with_video(tmp_path: Path) -> dict:
    video = tmp_path / "v.mp4"
    video.write_bytes(b"x")
    return store.create_uploaded(
        file_name="v.mp4",
        file_size=1,
        video_path=str(video),
    )


def test_photo_upload_rejects_invalid_face(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    task = _task_with_video(tmp_path)
    qa = {"pass": False, "reason": "照片不符合平视正脸要求（NO_FACE）", "codes": ["NO_FACE"]}

    with patch(
        "api_server.main.validate_user_photo_for_upload",
        side_effect=UserPhotoRejected(qa),
    ):
        client = TestClient(app)
        resp = client.post(
            f"/api/v1/makeup/tasks/{task['taskId']}/photo",
            data={"skipped": "false"},
            files={"photo": ("face.jpg", b"fake-image-bytes", "image/jpeg")},
        )

    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "USER_PHOTO_REJECTED"
    assert "NO_FACE" in body["message"] or "不符合" in body["message"]

    reloaded = store.load(task["taskId"])
    assert reloaded["status"] == "uploaded"
    assert reloaded.get("photo_path") is None


def test_photo_upload_passes_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    task = _task_with_video(tmp_path)
    qa = {"pass": True, "reason": "", "codes": [], "run_dir": str(tmp_path / "qa-run")}

    with patch("api_server.main.validate_user_photo_for_upload", return_value=qa):
        client = TestClient(app)
        resp = client.post(
            f"/api/v1/makeup/tasks/{task['taskId']}/photo",
            data={"skipped": "false"},
            files={"photo": ("face.jpg", b"fake-image-bytes", "image/jpeg")},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["skipped"] is False
    assert body["validationPass"] is True
    assert body["photoId"]

    reloaded = store.load(task["taskId"])
    assert reloaded["status"] == "photo_ready"
    assert reloaded["photo_qa"]["pass"] is True
    assert reloaded["photo_path"]


def test_photo_skip_bypasses_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    task = _task_with_video(tmp_path)

    with patch("api_server.main.validate_user_photo_for_upload") as validate:
        client = TestClient(app)
        resp = client.post(
            f"/api/v1/makeup/tasks/{task['taskId']}/photo",
            data={"skipped": "true"},
        )

    assert resp.status_code == 200
    assert resp.json()["skipped"] is True
    validate.assert_not_called()
    reloaded = store.load(task["taskId"])
    assert reloaded["status"] == "photo_ready"
    assert reloaded.get("photo_qa") is None
