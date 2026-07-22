"""Orchestrate analysis → tutorial mapping pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tutorial_mapper.config import MapperConfig, MapperJobResult
from tutorial_mapper.display_grouping import apply_display_grouping
from tutorial_mapper.from_analysis import from_analysis
from tutorial_mapper.merge import apply_text_patch, apply_vision_patch, refresh_assets_from_steps
from tutorial_mapper.schema import validate_tutorial
from tutorial_mapper.step_validation import validate_tutorial_steps
from tutorial_mapper.text_enrich import enrich_from_text
from tutorial_mapper.vision_enrich import enrich_from_vision


def _progress(config: MapperConfig, stage: int, message: str) -> None:
    if config.on_progress:
        config.on_progress(stage, message)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_mapper_job(parse_run_dir: Path, config: MapperConfig) -> MapperJobResult:
    parse_run_dir = parse_run_dir.resolve()
    analysis_path = parse_run_dir / "analysis.json"
    if not analysis_path.is_file():
        raise FileNotFoundError(f"未找到 analysis.json: {analysis_path}")

    _progress(config, 1, "读取 analysis.json…")
    analysis = _load_json(analysis_path)

    _progress(config, 2, "确定性映射…")
    tutorial = from_analysis(analysis, parse_run_dir=parse_run_dir)
    enrichment_meta: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parse_run_id": parse_run_dir.name,
        "stages": {
            "deterministic": {"ok": True, "fields": ["tutorial_id", "duration", "steps", "video_clip", "assets"]},
        },
        "applied": [],
    }

    if config.enable_text_enrich:
        _progress(config, 3, "文本 enrichment…")
        try:
            text_patch, text_meta = enrich_from_text(
                config, tutorial, parse_run_dir=parse_run_dir
            )
            applied = apply_text_patch(tutorial, text_patch)
            enrichment_meta["stages"]["text"] = {**text_meta, "ok": True, "applied": applied}
            enrichment_meta["applied"].extend(applied)
        except Exception as exc:  # noqa: BLE001 — 记录后继续视觉
            enrichment_meta["stages"]["text"] = {"ok": False, "error": str(exc)}
    else:
        _progress(config, 3, "跳过文本 enrichment")
        enrichment_meta["stages"]["text"] = {"ok": True, "skipped": True}

    if config.enable_vision_enrich:
        _progress(config, 4, "视觉 enrichment…")
        try:
            vision_patch, vision_meta = enrich_from_vision(
                config, tutorial, parse_run_dir=parse_run_dir, analysis=analysis
            )
            applied = apply_vision_patch(tutorial, vision_patch)
            enrichment_meta["stages"]["vision"] = {
                **vision_meta,
                "ok": True,
                "applied": applied,
            }
            enrichment_meta["applied"].extend(applied)
        except Exception as exc:  # noqa: BLE001
            enrichment_meta["stages"]["vision"] = {"ok": False, "error": str(exc)}
    else:
        _progress(config, 4, "跳过视觉 enrichment")
        enrichment_meta["stages"]["vision"] = {"ok": True, "skipped": True}

    _progress(config, 5, "刷新 assets + 展示分组 + schema 校验…")
    refresh_assets_from_steps(tutorial)
    apply_display_grouping(tutorial)
    validate_tutorial(tutorial)
    _progress(config, 6, "步骤语义校验…")
    step_validation = validate_tutorial_steps(tutorial)
    enrichment_meta["tutorial_step_validation"] = step_validation
    issues = step_validation.get("issues") or []
    error_count = sum(1 for i in issues if i.get("severity") == "error")
    warning_count = sum(1 for i in issues if i.get("severity") == "warning")
    enrichment_meta["stages"]["step_validation"] = {
        "ok": True,
        "pass": bool(step_validation.get("pass")),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": warning_count,
    }

    tutorial_path = parse_run_dir / "tutorial.json"
    meta_path = parse_run_dir / "enrichment_meta.json"
    _write_json(tutorial_path, tutorial)
    _write_json(meta_path, enrichment_meta)
    _progress(config, 7, "写盘完成")

    return MapperJobResult(
        parse_run_dir=parse_run_dir,
        tutorial_path=tutorial_path,
        tutorial=tutorial,
        enrichment_meta_path=meta_path,
        enrichment_meta=enrichment_meta,
    )
