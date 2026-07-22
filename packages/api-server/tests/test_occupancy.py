from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api_server.main import app
from api_server.occupancy import OccupancyManager, occupancy
from api_server.store import store


@pytest.fixture(autouse=True)
def _reset_occupancy() -> None:
    occupancy.reset()
    yield
    occupancy.reset()


def test_acquire_allows_two_then_blocks_third() -> None:
    mgr = OccupancyManager(max_concurrent=2, stale_seconds=3600)
    assert mgr.try_acquire("task_a", "analysis") is True
    assert mgr.try_acquire("task_b", "analysis") is True
    assert mgr.try_acquire("task_c", "analysis") is False
    snap = mgr.snapshot()
    assert snap["busy"] is True
    assert snap["activeCount"] == 2
    assert snap["maxConcurrent"] == 2


def test_same_task_idempotent() -> None:
    mgr = OccupancyManager(max_concurrent=2, stale_seconds=3600)
    assert mgr.try_acquire("task_a", "analysis") is True
    assert mgr.try_acquire("task_a", "analysis") is True
    assert mgr.try_acquire("task_b", "adjustment") is True
    assert mgr.snapshot()["activeCount"] == 2


def test_release_frees_slot() -> None:
    mgr = OccupancyManager(max_concurrent=2, stale_seconds=3600)
    assert mgr.try_acquire("task_a", "analysis") is True
    assert mgr.try_acquire("task_b", "analysis") is True
    mgr.release("task_a", "analysis")
    assert mgr.try_acquire("task_c", "step_diagrams") is True
    assert mgr.snapshot()["activeCount"] == 2
    assert mgr.snapshot()["busy"] is True


def test_stale_slots_purged() -> None:
    mgr = OccupancyManager(max_concurrent=2, stale_seconds=10)
    assert mgr.try_acquire("task_a", "analysis") is True
    assert mgr.try_acquire("task_b", "analysis") is True
    with mgr._lock:
        mgr._slots["task_a"]["startedAt"] = time.time() - 100
        mgr._slots["task_b"]["startedAt"] = time.time() - 100
    assert mgr.try_acquire("task_c", "analysis") is True
    assert mgr.snapshot()["activeCount"] == 1


def test_server_status_endpoint() -> None:
    client = TestClient(app)
    occupancy.try_acquire("task_x", "analysis")
    resp = client.get("/api/v1/makeup/server/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["activeCount"] == 1
    assert body["maxConcurrent"] == 2
    assert body["busy"] is False


def test_analysis_returns_server_busy_when_full(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    occupancy.try_acquire("holder_1", "analysis")
    occupancy.try_acquire("holder_2", "analysis")

    task = store.create_uploaded(
        file_name="v.mp4",
        file_size=1,
        video_path=str(tmp_path / "v.mp4"),
    )
    (tmp_path / "v.mp4").write_bytes(b"x")
    store.set_photo_ready(task["taskId"], photo_path=None, skipped=True, photo_id=None)

    client = TestClient(app)
    with patch("api_server.main.run_task_pipeline"):
        resp = client.post(f"/api/v1/makeup/tasks/{task['taskId']}/analysis")
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "SERVER_BUSY"
    assert "排队中" in body["message"]
