from __future__ import annotations

import os
import threading
import time
from typing import Any, Literal

JobKind = Literal["analysis", "adjustment", "step_diagrams"]
Cohort = Literal["public", "judge"]

_DEFAULT_MAX = 2
_DEFAULT_STALE_SECONDS = 45 * 60


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


class OccupancyManager:
    """Process-local concurrent slots for heavy makeup jobs (single uvicorn worker)."""

    def __init__(
        self,
        *,
        max_concurrent: int | None = None,
        stale_seconds: int | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self.max_concurrent = max_concurrent if max_concurrent is not None else _env_int(
            "OCCUPANCY_MAX_CONCURRENT", _DEFAULT_MAX
        )
        self.stale_seconds = stale_seconds if stale_seconds is not None else _env_int(
            "OCCUPANCY_STALE_SECONDS", _DEFAULT_STALE_SECONDS
        )
        self._slots: dict[str, dict[str, Any]] = {}

    def _purge_stale_unlocked(self, now: float | None = None) -> None:
        now = time.time() if now is None else now
        stale_ids = [
            task_id
            for task_id, slot in self._slots.items()
            if now - float(slot["startedAt"]) > self.stale_seconds
        ]
        for task_id in stale_ids:
            del self._slots[task_id]

    def try_acquire(
        self,
        task_id: str,
        job: JobKind,
        *,
        cohort: Cohort = "public",
    ) -> bool:
        with self._lock:
            self._purge_stale_unlocked()
            if task_id in self._slots:
                self._slots[task_id] = {
                    "job": job,
                    "startedAt": time.time(),
                    "cohort": cohort,
                }
                return True
            if len(self._slots) >= self.max_concurrent:
                return False
            self._slots[task_id] = {
                "job": job,
                "startedAt": time.time(),
                "cohort": cohort,
            }
            return True

    def release(self, task_id: str, job: JobKind | None = None) -> None:
        with self._lock:
            slot = self._slots.get(task_id)
            if slot is None:
                return
            if job is not None and slot.get("job") != job:
                return
            del self._slots[task_id]

    def preempt_public(self) -> list[dict[str, Any]]:
        """Remove all non-judge slots. Returns list of {taskId, job, cohort}."""
        with self._lock:
            self._purge_stale_unlocked()
            removed: list[dict[str, Any]] = []
            keep: dict[str, dict[str, Any]] = {}
            for task_id, slot in self._slots.items():
                cohort = slot.get("cohort") or "public"
                if cohort == "judge":
                    keep[task_id] = slot
                else:
                    removed.append(
                        {
                            "taskId": task_id,
                            "job": slot.get("job"),
                            "cohort": cohort,
                        }
                    )
            self._slots = keep
            return removed

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            self._purge_stale_unlocked()
            slots = [
                {
                    "taskId": task_id,
                    "job": slot["job"],
                    "startedAt": slot["startedAt"],
                    "cohort": slot.get("cohort") or "public",
                }
                for task_id, slot in self._slots.items()
            ]
            active_count = len(slots)
            return {
                "busy": active_count >= self.max_concurrent,
                "activeCount": active_count,
                "maxConcurrent": self.max_concurrent,
                "slots": slots,
            }

    def reset(self) -> None:
        """Test helper: clear all slots."""
        with self._lock:
            self._slots.clear()


occupancy = OccupancyManager()
