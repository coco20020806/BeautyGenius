from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api_server.cancellation import cancellation
from api_server.main import app
from api_server.occupancy import OccupancyManager, occupancy
from api_server.store import store
from api_server.vip import (
    PREEMPTED_CODE,
    apply_public_preempt,
    busy_message,
    is_vip,
    resolve_cohort,
)


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch: pytest.MonkeyPatch) -> None:
    occupancy.reset()
    cancellation.reset()
    monkeypatch.setenv("VIP_PASSPHRASE", "judge-secret")
    yield
    occupancy.reset()
    cancellation.reset()


def test_is_vip_compare() -> None:
    assert is_vip("judge-secret") is True
    assert is_vip("wrong") is False
    assert is_vip(None) is False
    assert resolve_cohort("judge-secret") == "judge"
    assert resolve_cohort("nope") == "public"


def test_busy_messages() -> None:
    assert "评委通道" in busy_message(cohort="judge")
    assert "排队中" in busy_message(cohort="public")


def test_preempt_public_keeps_judge_slots() -> None:
    occupancy.try_acquire("pub_a", "analysis", cohort="public")
    occupancy.try_acquire("judge_a", "analysis", cohort="judge")
    removed = occupancy.preempt_public()
    assert [r["taskId"] for r in removed] == ["pub_a"]
    snap = occupancy.snapshot()
    assert snap["activeCount"] == 1
    assert snap["slots"][0]["taskId"] == "judge_a"
    assert snap["slots"][0]["cohort"] == "judge"


def test_judge_full_blocks_third_judge() -> None:
    mgr = OccupancyManager(max_concurrent=2, stale_seconds=3600)
    assert mgr.try_acquire("j1", "analysis", cohort="judge") is True
    assert mgr.try_acquire("j2", "analysis", cohort="judge") is True
    assert mgr.try_acquire("j3", "analysis", cohort="judge") is False
    assert {s["taskId"] for s in mgr.snapshot()["slots"]} == {"j1", "j2"}


def test_apply_public_preempt_marks_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    store.root.mkdir(parents=True, exist_ok=True)
    task = store.create_uploaded(
        file_name="p.mp4", file_size=1, video_path=str(tmp_path / "p.mp4")
    )
    store.set_photo_ready(task["taskId"], photo_path=None, skipped=True, photo_id=None)
    store.mark_processing(task["taskId"])
    occupancy.try_acquire(task["taskId"], "analysis", cohort="public")
    running: set[str] = {task["taskId"]}
    diagram: set[str] = set()
    ids = apply_public_preempt(running=running, diagram_running=diagram)
    assert task["taskId"] in ids
    assert running == set()
    loaded = store.load(task["taskId"])
    assert loaded["failureCode"] == PREEMPTED_CODE
    assert cancellation.is_cancelled(task["taskId"]) is True


def test_wrong_code_not_vip_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VIP_PASSPHRASE", raising=False)
    assert is_vip("judge-secret") is False


def test_vip_analysis_preempts_public(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    store.root.mkdir(parents=True, exist_ok=True)

    public = store.create_uploaded(
        file_name="p.mp4", file_size=1, video_path=str(tmp_path / "p.mp4")
    )
    (tmp_path / "p.mp4").write_bytes(b"x")
    store.set_photo_ready(public["taskId"], photo_path=None, skipped=True, photo_id=None)
    store.mark_processing(public["taskId"])
    occupancy.try_acquire(public["taskId"], "analysis", cohort="public")
    occupancy.try_acquire("holder_public_2", "analysis", cohort="public")

    vip_task = store.create_uploaded(
        file_name="v.mp4", file_size=1, video_path=str(tmp_path / "v.mp4")
    )
    (tmp_path / "v.mp4").write_bytes(b"x")
    store.set_photo_ready(vip_task["taskId"], photo_path=None, skipped=True, photo_id=None)

    client = TestClient(app)
    with patch("api_server.main.run_task_pipeline"):
        resp = client.post(
            f"/api/v1/makeup/tasks/{vip_task['taskId']}/analysis",
            headers={"X-Vip-Code": "judge-secret"},
        )
    assert resp.status_code == 202
    assert resp.json()["cohort"] == "judge"

    failed = store.load(public["taskId"])
    assert failed["status"] == "failed"
    assert failed["failureCode"] == PREEMPTED_CODE
    # Background task finishes immediately under TestClient mock → slot may already release.
    assert all(s.get("cohort") != "public" for s in occupancy.snapshot()["slots"])


def test_vip_queues_when_other_vips_full(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    store.root.mkdir(parents=True, exist_ok=True)

    occupancy.try_acquire("judge_1", "analysis", cohort="judge")
    occupancy.try_acquire("judge_2", "analysis", cohort="judge")

    vip_task = store.create_uploaded(
        file_name="v.mp4", file_size=1, video_path=str(tmp_path / "v.mp4")
    )
    (tmp_path / "v.mp4").write_bytes(b"x")
    store.set_photo_ready(vip_task["taskId"], photo_path=None, skipped=True, photo_id=None)

    client = TestClient(app)
    with patch("api_server.main.run_task_pipeline"):
        resp = client.post(
            f"/api/v1/makeup/tasks/{vip_task['taskId']}/analysis",
            headers={"X-Vip-Code": "judge-secret"},
        )
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "SERVER_BUSY"
    assert "评委通道" in body["message"]

    snap = occupancy.snapshot()
    assert snap["activeCount"] == 2
    assert {s["taskId"] for s in snap["slots"]} == {"judge_1", "judge_2"}


def test_wrong_vip_code_does_not_preempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store, "root", tmp_path)
    store.root.mkdir(parents=True, exist_ok=True)

    occupancy.try_acquire("holder_1", "analysis", cohort="public")
    occupancy.try_acquire("holder_2", "analysis", cohort="public")

    task = store.create_uploaded(
        file_name="v.mp4", file_size=1, video_path=str(tmp_path / "v.mp4")
    )
    (tmp_path / "v.mp4").write_bytes(b"x")
    store.set_photo_ready(task["taskId"], photo_path=None, skipped=True, photo_id=None)

    client = TestClient(app)
    with patch("api_server.main.run_task_pipeline"):
        resp = client.post(
            f"/api/v1/makeup/tasks/{task['taskId']}/analysis",
            headers={"X-Vip-Code": "wrong-code"},
        )
    assert resp.status_code == 409
    assert occupancy.snapshot()["activeCount"] == 2
