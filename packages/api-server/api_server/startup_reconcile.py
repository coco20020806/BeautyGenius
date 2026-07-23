from __future__ import annotations

import logging

from api_server.store import store

logger = logging.getLogger(__name__)

_ZOMBIE_REASON = "任务已中断（服务重启或进程退出），请重新开始解析"
_ZOMBIE_CODE = "PIPELINE_INTERRUPTED"


def reconcile_zombie_processing_tasks() -> int:
    """Mark disk `processing` tasks as failed after API restart (no in-memory slots)."""
    count = 0
    root = store.root
    if not root.is_dir():
        return 0
    for task_dir in root.glob("task_*"):
        path = task_dir / "task.json"
        if not path.is_file():
            continue
        try:
            task = store.load(task_dir.name)
        except Exception:  # noqa: BLE001
            continue
        if task.get("status") != "processing":
            # Also clear stuck step-diagrams processing
            if task.get("step_diagrams_status") == "processing":
                try:
                    store.mark_step_diagrams_failed(task_dir.name, reason=_ZOMBIE_REASON)
                    count += 1
                except Exception:  # noqa: BLE001
                    logger.exception("failed to reconcile step diagrams %s", task_dir.name)
            continue
        try:
            store.mark_failed(task_dir.name, reason=_ZOMBIE_REASON, code=_ZOMBIE_CODE)
            count += 1
        except Exception:  # noqa: BLE001
            logger.exception("failed to reconcile task %s", task_dir.name)
    if count:
        logger.warning("reconciled %s interrupted task(s) on startup", count)
    return count
