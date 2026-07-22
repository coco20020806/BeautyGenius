"""Orchestrate picture-makeup job."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from picture_makeup.config import CONTRACT_VERSION, PictureMakeupConfig, PictureMakeupJobResult
from picture_makeup.diagram import run_diagram
from picture_makeup.io_util import make_run_dir
from picture_makeup.prompt_enrich import enrich_from_keyframes
from picture_makeup.prompt_loader import load_diagram_prompt
from picture_makeup.prompt_text import generate_base_prompt

ProgressCallback = Callable[[str, int, int], None]
StepCompleteCallback = Callable[[str, Path, dict[str, Any]], None]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_picture_makeup_job(
    *,
    parse_run_dir: Path,
    tutorial_path: Path,
    output_root: Path,
    config: PictureMakeupConfig,
    step_ids: list[str] | None = None,
    on_progress: ProgressCallback | None = None,
    on_step_complete: StepCompleteCallback | None = None,
) -> PictureMakeupJobResult:
    parse_run_dir = parse_run_dir.resolve()
    tutorial_path = tutorial_path.resolve()
    if not tutorial_path.is_file():
        raise FileNotFoundError(f"tutorial.json 不存在: {tutorial_path}")

    base_image = config.skill_dir / "image_format.png"
    if not base_image.is_file():
        raise FileNotFoundError(f"缺少底图: {base_image}")

    keyframes_dir = parse_run_dir / "keyframes"
    tutorial = json.loads(tutorial_path.read_text(encoding="utf-8"))
    if tutorial.get("contract_version") != "tutorial.v1":
        raise ValueError("tutorial contract_version 必须为 tutorial.v1")

    steps: list[dict[str, Any]] = list(tutorial.get("steps") or [])
    if step_ids:
        wanted = set(step_ids)
        steps = [s for s in steps if s.get("step_id") in wanted]

    t0 = time.perf_counter()
    run_dir = make_run_dir(output_root)
    diagram_meta = load_diagram_prompt(config.skill_dir)
    manifest_steps: list[dict[str, Any]] = []
    run_warnings: list[str] = []

    total = len(steps)
    for index, step in enumerate(steps):
        step_id = str(step.get("step_id") or f"step_{index}")
        if on_progress:
            on_progress(step_id, index, total)

        step_dir = run_dir / "steps" / step_id
        step_dir.mkdir(parents=True, exist_ok=True)
        entry: dict[str, Any] = {
            "step_id": step_id,
            "part": step.get("part"),
            "index": index,
            "status": "pending",
            "warnings": [],
        }

        try:
            base_prompt = generate_base_prompt(config, step, step_dir)
            final_prompt, enrich = enrich_from_keyframes(
                config, step, base_prompt, keyframes_dir, step_dir
            )
            if enrich.get("skipped"):
                entry["warnings"].append("no_keyframes_for_enrich")
            if enrich.get("conflict"):
                entry["warnings"].append("enrich_conflict")

            if config.skip_diagram:
                entry["status"] = "skipped"
            else:
                run_diagram(
                    config,
                    base_image=base_image,
                    final_prompt=final_prompt,
                    step_dir=step_dir,
                )
                entry["status"] = "ok"
                entry["diagram_path"] = f"steps/{step_id}/diagram_01.jpg"
        except Exception as exc:  # noqa: BLE001 — record per-step failure
            entry["status"] = "failed"
            entry["error"] = str(exc)
            (step_dir / "step_error.txt").write_text(str(exc), encoding="utf-8")

        manifest_steps.append(entry)
        if on_step_complete:
            on_step_complete(step_id, step_dir, entry)

    if diagram_meta.used_fallback:
        run_warnings.append("diagram_prompt_fallback_static")

    manifest: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "generated_at": _utc_now(),
        "skill_dir": str(config.skill_dir.resolve()),
        "base_image": str(base_image.resolve()),
        "parse_run_dir": str(parse_run_dir),
        "tutorial_id": tutorial.get("tutorial_id"),
        "tutorial_path": str(tutorial_path),
        "text_model": config.text_model,
        "vision_model": config.vision_model,
        "image_model": config.image_model,
        "diagram": {"prompt_text_version": diagram_meta.prompt_text_version},
        "steps": manifest_steps,
        "warnings": run_warnings,
    }
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = {
        "time_used_ms": int((time.perf_counter() - t0) * 1000),
        "step_count": total,
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return PictureMakeupJobResult(run_dir=run_dir, manifest=manifest, manifest_path=manifest_path)
