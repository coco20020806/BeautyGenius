from __future__ import annotations

import hmac
import os
from typing import Any

from api_server.cancellation import cancellation
from api_server.occupancy import Cohort, JobKind, occupancy
from api_server.store import store

VIP_HEADER = "X-Vip-Code"
PREEMPTED_REASON = "演示优先：评委通道已启动，请稍后再试"
PREEMPTED_CODE = "PREEMPTED_BY_VIP"
JUDGE_BUSY_MESSAGE = "评委通道已满，请稍候再试（评委之间排队，不会互相中断）"
PUBLIC_BUSY_MESSAGE = "排队中，服务器已满（最多 {max} 人同时使用），请稍后再试"


def vip_passphrase() -> str:
    return os.environ.get("VIP_PASSPHRASE", "").strip()


def is_vip(code: str | None) -> bool:
    expected = vip_passphrase()
    if not expected or not code:
        return False
    provided = code.strip()
    if not provided:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


def resolve_cohort(code: str | None) -> Cohort:
    return "judge" if is_vip(code) else "public"


def apply_public_preempt(*, running: set[str], diagram_running: set[str]) -> list[str]:
    """Cancel and fail all public occupancy holders. Returns preempted task ids."""
    removed = occupancy.preempt_public()
    preempted_ids: list[str] = []
    for item in removed:
        task_id = str(item["taskId"])
        job = item.get("job")
        preempted_ids.append(task_id)
        cancellation.request_cancel(task_id)
        cancellation.kill_task_processes(task_id)
        running.discard(task_id)
        diagram_running.discard(task_id)
        try:
            if job == "step_diagrams":
                store.mark_step_diagrams_failed(task_id, reason=PREEMPTED_REASON)
                continue
            task = store.load(task_id)
            if task.get("status") == "processing":
                store.mark_failed(
                    task_id,
                    reason=PREEMPTED_REASON,
                    code=PREEMPTED_CODE,
                )
        except FileNotFoundError:
            pass
        except Exception:  # noqa: BLE001
            pass
    return preempted_ids


def busy_message(*, cohort: Cohort) -> str:
    if cohort == "judge":
        return JUDGE_BUSY_MESSAGE
    return PUBLIC_BUSY_MESSAGE.format(max=occupancy.max_concurrent)


def stamp_task_cohort(task_id: str, cohort: Cohort) -> None:
    try:
        task = store.load(task_id)
        task["cohort"] = cohort
        store.save(task)
    except FileNotFoundError:
        pass


def extract_vip_code(
    *,
    header_value: str | None = None,
    body_code: str | None = None,
) -> str | None:
    if header_value and header_value.strip():
        return header_value.strip()
    if body_code and body_code.strip():
        return body_code.strip()
    return None
