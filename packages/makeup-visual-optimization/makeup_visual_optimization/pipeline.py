"""Orchestrate makeup visual optimization job."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from makeup_visual_optimization.apply import apply_optimization
from makeup_visual_optimization.config import (
    CONTRACT_VERSION,
    OptimizationConfig,
    OptimizationJobResult,
)
from makeup_visual_optimization.io_util import make_run_dir
from makeup_visual_optimization.llm import call_optimization_json
from makeup_visual_optimization.normalize import normalize_adjustment
from makeup_visual_optimization.prompt import build_user_message, load_system_prompt


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_optimization_job(
    *,
    tutorial_path: Path,
    adjustment: dict[str, Any],
    output_root: Path,
    config: OptimizationConfig,
) -> OptimizationJobResult:
    tutorial_path = tutorial_path.resolve()
    if not tutorial_path.is_file():
        raise FileNotFoundError(f"tutorial.json 不存在: {tutorial_path}")

    skill_dir = config.skill_dir.resolve()
    if not (skill_dir / "SKILL.md").is_file():
        raise FileNotFoundError(f"缺少 skill: {skill_dir / 'SKILL.md'}")

    tutorial = json.loads(tutorial_path.read_text(encoding="utf-8"))
    if tutorial.get("contract_version") != "tutorial.v1":
        raise ValueError("tutorial contract_version 必须为 tutorial.v1")

    optimization_input = normalize_adjustment(adjustment)
    t0 = time.perf_counter()
    run_dir = make_run_dir(output_root)

    (run_dir / "optimization_input.json").write_text(
        json.dumps(optimization_input, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    system = load_system_prompt(skill_dir)
    user = build_user_message(tutorial, optimization_input)
    optimization = call_optimization_json(
        config,
        system=system,
        user=user,
        run_dir=run_dir,
    )
    (run_dir / "optimization.json").write_text(
        json.dumps(optimization, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    optimized = apply_optimization(tutorial, optimization)
    optimized_path = run_dir / "tutorial_optimized.json"
    optimized_path.write_text(
        json.dumps(optimized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = optimization.get("optimization_summary") if isinstance(optimization, dict) else None
    manifest: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "skill_dir": str(skill_dir),
        "source_tutorial_path": str(tutorial_path),
        "optimized_tutorial_path": str(optimized_path.resolve()),
        "text_model": config.text_model,
        "elapsed_sec": round(time.perf_counter() - t0, 3),
        "step_adjustment_count": len(optimization.get("step_adjustments") or [])
        if isinstance(optimization, dict)
        else 0,
        "optimization_summary": summary,
    }
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return OptimizationJobResult(
        run_dir=run_dir,
        optimized_tutorial_path=optimized_path,
        optimization=optimization if isinstance(optimization, dict) else {},
        manifest=manifest,
        manifest_path=manifest_path,
    )
