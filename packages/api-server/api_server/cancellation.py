from __future__ import annotations

import os
import signal
import threading
from typing import Any


class TaskCancelled(Exception):
    """Raised when a makeup pipeline should stop due to preempt/cancel."""


class CancellationRegistry:
    """Process-local cancel flags and optional child PIDs per task."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[str, threading.Event] = {}
        self._pids: dict[str, set[int]] = {}

    def request_cancel(self, task_id: str) -> None:
        with self._lock:
            event = self._events.setdefault(task_id, threading.Event())
            event.set()

    def is_cancelled(self, task_id: str) -> bool:
        with self._lock:
            event = self._events.get(task_id)
            return bool(event and event.is_set())

    def clear(self, task_id: str) -> None:
        with self._lock:
            self._events.pop(task_id, None)
            self._pids.pop(task_id, None)

    def register_pid(self, task_id: str, pid: int) -> None:
        with self._lock:
            self._pids.setdefault(task_id, set()).add(pid)

    def kill_task_processes(self, task_id: str) -> list[int]:
        with self._lock:
            pids = list(self._pids.get(task_id) or [])
        killed: list[int] = []
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
                killed.append(pid)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        # Best-effort: any ffmpeg still holding this task path (Linux demo box).
        try:
            import subprocess

            subprocess.run(
                ["pkill", "-f", f"outputs/tasks/{task_id}/"],
                check=False,
                capture_output=True,
            )
        except OSError:
            pass
        return killed

    def ensure_not_cancelled(self, task_id: str) -> None:
        if self.is_cancelled(task_id):
            raise TaskCancelled("任务已被取消（演示优先通道）")

    def reset(self) -> None:
        """Test helper."""
        with self._lock:
            self._events.clear()
            self._pids.clear()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "cancelled": [tid for tid, ev in self._events.items() if ev.is_set()],
                "trackedPids": {tid: sorted(pids) for tid, pids in self._pids.items()},
            }


cancellation = CancellationRegistry()
