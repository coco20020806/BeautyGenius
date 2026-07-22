"""Task skip_transfer persistence."""

from __future__ import annotations

from pathlib import Path

from api_server.store import TaskStore


def test_create_uploaded_skip_transfer(tmp_path: Path) -> None:
    store = TaskStore(root=tmp_path / "tasks")
    task = store.create_uploaded(
        file_name="v.mp4",
        file_size=100,
        video_path=str(tmp_path / "v.mp4"),
        skip_transfer=True,
    )
    assert task["skip_transfer"] is True
    loaded = store.load(task["taskId"])
    assert loaded["skip_transfer"] is True

    task2 = store.create_uploaded(
        file_name="v2.mp4",
        file_size=200,
        video_path=str(tmp_path / "v2.mp4"),
    )
    assert task2["skip_transfer"] is False
