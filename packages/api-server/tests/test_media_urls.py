"""Tests for public media URL helpers."""

from __future__ import annotations

from pathlib import Path

from api_server.media_urls import resolve_task_video_url


def test_resolve_task_video_url_ok(tmp_path: Path) -> None:
    video = tmp_path / "video.mp4"
    video.write_bytes(b"x")
    url = resolve_task_video_url("task_1", {"video_path": str(video)})
    assert url == "http://127.0.0.1:8000/media/task_1/video.mp4"


def test_resolve_task_video_url_missing_file(tmp_path: Path) -> None:
    url = resolve_task_video_url("task_1", {"video_path": str(tmp_path / "nope.mp4")})
    assert url is None


def test_resolve_task_video_url_no_path() -> None:
    assert resolve_task_video_url("task_1", {}) is None
