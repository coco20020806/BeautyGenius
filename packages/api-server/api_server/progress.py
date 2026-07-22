from __future__ import annotations

from typing import Any

from api_server.eta import compute_remaining_seconds

STAGE_DEFS: list[tuple[str, str]] = [
    ("quality-check", "检查视频质量"),
    ("step-detection", "识别妆容步骤"),
    ("preview-generation", "生成适配预览"),
    ("hint-generation", "整理关键建议"),
]


def initial_stages() -> list[dict[str, str]]:
    stages: list[dict[str, str]] = []
    for index, (stage_id, label) in enumerate(STAGE_DEFS):
        status = "active" if index == 0 else "pending"
        stages.append({"id": stage_id, "label": label, "status": status})
    return stages


def stages_for_active(active_index: int) -> list[dict[str, str]]:
    stages: list[dict[str, str]] = []
    for index, (stage_id, label) in enumerate(STAGE_DEFS):
        if index < active_index:
            status = "completed"
        elif index == active_index:
            status = "active"
        else:
            status = "pending"
        stages.append({"id": stage_id, "label": label, "status": status})
    return stages


def progress_payload(
    task_id: str,
    *,
    active_index: int,
    progress: int,
    status: str = "processing",
    failure_reason: str | None = None,
    detail_message: str | None = None,
    log_lines: list[str] | None = None,
    eta_total_seconds: float | None = None,
    completed_weight: float | None = None,
    processing_started_at: str | None = None,
    prior_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    label = STAGE_DEFS[min(active_index, len(STAGE_DEFS) - 1)][1]
    prior = prior_doc or {}

    eta_total = eta_total_seconds if eta_total_seconds is not None else prior.get("etaTotalSeconds")
    weight = completed_weight if completed_weight is not None else prior.get("completedWeight", 0.0)
    started_at = processing_started_at if processing_started_at is not None else prior.get("processingStartedAt")

    if status in {"completed", "failed"}:
        remaining = 0
    elif eta_total is not None:
        remaining = compute_remaining_seconds(
            eta_total_seconds=float(eta_total),
            completed_weight=float(weight or 0.0),
            processing_started_at=started_at,
        )
    else:
        remaining = 120

    lines = list(log_lines if log_lines is not None else prior.get("logLines") or [])
    detail = detail_message if detail_message is not None else prior.get("detailMessage")

    doc: dict[str, Any] = {
        "taskId": task_id,
        "progress": progress,
        "currentStage": label,
        "remainingSeconds": remaining,
        "status": status,
        "stages": stages_for_active(active_index if status == "processing" else len(STAGE_DEFS)),
    }
    if detail:
        doc["detailMessage"] = detail
    if lines:
        doc["logLines"] = lines[-50:]
    if eta_total is not None:
        doc["etaTotalSeconds"] = int(round(float(eta_total)))
    if weight is not None:
        doc["completedWeight"] = round(float(weight), 4)
    if started_at:
        doc["processingStartedAt"] = started_at
    if failure_reason:
        doc["failureReason"] = failure_reason
    if status == "completed":
        doc["progress"] = 100
        doc["currentStage"] = STAGE_DEFS[-1][1]
        doc["remainingSeconds"] = 0
    return doc


def map_parse_stage(parse_stage: int) -> tuple[int, int]:
    """Map parse on_progress stage (1-10) to (active_index, progress percent)."""
    if parse_stage <= 2:
        return 0, min(15, 5 + parse_stage * 4)
    if parse_stage <= 6:
        return 1, min(40, 18 + parse_stage * 3)
    return 1, min(48, 35 + parse_stage)


def map_map_stage(map_stage: int) -> tuple[int, int]:
    return 1, min(55, 45 + map_stage * 2)
