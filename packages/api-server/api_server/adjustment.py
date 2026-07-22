"""Questionnaire adjustment → visual optimization → patched tutorial."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from makeup_visual_optimization import OptimizationConfig, run_optimization_job

from api_server.config import VISUAL_OPT_OUTPUT_ROOT, VISUAL_OPT_SKILL
from api_server.errors import ApiError
from api_server.pipeline import load_api_key
from api_server.store import store
from api_server.tutorial_loader import effective_tutorial_path


def ensure_task_ready_for_adjustment(task: dict[str, Any], *, request_id: str) -> None:
    if task.get("status") != "completed":
        raise ApiError(
            409,
            "ADJUSTMENT_NOT_READY",
            "主任务尚未完成，无法微调",
            request_id=request_id,
        )
    if not task.get("tutorial_path"):
        raise ApiError(409, "TUTORIAL_NOT_READY", "教程尚未就绪", request_id=request_id)
    source = Path(task["tutorial_path"])
    if not source.is_file():
        raise ApiError(409, "TUTORIAL_NOT_READY", "教程尚未就绪", request_id=request_id)


def run_adjustment_job(task_id: str, adjustment: dict[str, Any]) -> dict[str, Any]:
    task = store.load(task_id)
    source_path = Path(task["tutorial_path"])
    api_key = load_api_key()
    config = OptimizationConfig(api_key=api_key, skill_dir=VISUAL_OPT_SKILL)

    result = run_optimization_job(
        tutorial_path=source_path,
        adjustment=adjustment,
        output_root=VISUAL_OPT_OUTPUT_ROOT,
        config=config,
    )

    summary = None
    if isinstance(result.optimization, dict):
        summary = result.optimization.get("optimization_summary")

    store.save_adjustment(
        task_id,
        adjustment=adjustment,
        optimized_tutorial_path=str(result.optimized_tutorial_path.resolve()),
        optimization_run_dir=str(result.run_dir.resolve()),
        summary=summary if isinstance(summary, dict) else None,
    )
    return {
        "taskId": task_id,
        "status": "completed",
        "optimizedTutorialPath": str(result.optimized_tutorial_path.resolve()),
        "optimizationRunDir": str(result.run_dir.resolve()),
        "summary": summary if isinstance(summary, dict) else None,
        "effectiveTutorialPath": str(
            effective_tutorial_path(store.load(task_id)) or result.optimized_tutorial_path
        ),
    }
