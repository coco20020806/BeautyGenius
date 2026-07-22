"""Orchestrate tutorial.json understanding enrichment."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from makeup_understanding.config import UnderstandingConfig, UnderstandingJobResult
from makeup_understanding.llm import call_text_json
from makeup_understanding.merge import apply_understanding_patch, build_user_payload
from makeup_understanding.prompt import SYSTEM_PROMPT


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_tutorial(parse_run_dir: Path) -> tuple[Path, dict[str, Any]]:
    path = parse_run_dir / "tutorial.json"
    if not path.is_file():
        raise FileNotFoundError(f"缺少 tutorial.json: {path}")
    return path, json.loads(path.read_text(encoding="utf-8"))


def run_understanding_job(
    parse_run_dir: Path,
    config: UnderstandingConfig | None = None,
) -> UnderstandingJobResult:
    config = config or UnderstandingConfig()
    parse_run_dir = parse_run_dir.resolve()
    tutorial_path, tutorial = _load_tutorial(parse_run_dir)
    meta: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parse_run_id": parse_run_dir.name,
        "model": config.text_model,
        "steps_touched": [],
        "ok": True,
        "error": None,
        "skipped": False,
    }

    def progress(stage: int, message: str) -> None:
        if config.on_progress:
            config.on_progress(stage, message)

    if not config.enabled:
        meta["skipped"] = True
        meta_path = parse_run_dir / "understanding_meta.json"
        _write_json(meta_path, meta)
        return UnderstandingJobResult(
            parse_run_dir=parse_run_dir,
            tutorial_path=tutorial_path,
            tutorial=tutorial,
            meta_path=meta_path,
            meta=meta,
        )

    if not (config.api_key or "").strip():
        raise RuntimeError("makeup-understanding 需要 DASHSCOPE_API_KEY")

    progress(1, "组装步骤文本…")
    user = build_user_payload(tutorial)
    progress(2, "LLM 提取产品与手法…")
    try:
        patch = call_text_json(
            config,
            system=SYSTEM_PROMPT,
            user=user,
            run_dir=parse_run_dir,
            dump_name="understanding_raw.json",
        )
        progress(3, "合并补丁…")
        touched = apply_understanding_patch(tutorial, patch)
        meta["steps_touched"] = touched
        _write_json(tutorial_path, tutorial)
    except Exception as exc:  # noqa: BLE001 — surface to meta + re-raise for pipeline
        meta["ok"] = False
        meta["error"] = str(exc)
        meta_path = parse_run_dir / "understanding_meta.json"
        _write_json(meta_path, meta)
        raise

    meta_path = parse_run_dir / "understanding_meta.json"
    _write_json(meta_path, meta)
    progress(4, "完成")
    return UnderstandingJobResult(
        parse_run_dir=parse_run_dir,
        tutorial_path=tutorial_path,
        tutorial=tutorial,
        meta_path=meta_path,
        meta=meta,
    )
