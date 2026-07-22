"""Generate base_prompt from tutorial step fields."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from picture_makeup.config import PictureMakeupConfig
from picture_makeup.llm import call_text_json
from picture_makeup.prompt_loader import load_base_prompt_system


def _format_user_message(step: dict[str, Any]) -> str:
    prod = step.get("product") or {}
    vl = step.get("visual_layer") or {}
    subs = step.get("taxonomy_sub_steps") or []
    kws = prod.get("keywords") or []
    return (
        "请为以下教程步骤生成 base_prompt：\n\n"
        f"step_id: {step.get('step_id', '')}\n"
        f"part: {step.get('part', '')}\n"
        f"taxonomy_primary: {step.get('taxonomy_primary', '')}\n"
        f"taxonomy_sub_steps: {json.dumps(subs, ensure_ascii=False)}\n"
        f"instruction: {step.get('instruction', '')}\n"
        f"adaptation_note: {step.get('adaptation_note', '')}\n"
        f"product.name: {prod.get('name', '')}\n"
        f"product.keywords: {json.dumps(kws, ensure_ascii=False)}\n"
        f"visual_layer: {json.dumps(vl, ensure_ascii=False)}"
    )


def generate_base_prompt(
    config: PictureMakeupConfig,
    step: dict[str, Any],
    step_dir: Path,
) -> str:
    system = load_base_prompt_system(config.skill_dir)
    doc = call_text_json(
        config,
        system=system,
        user=_format_user_message(step),
        run_dir=step_dir,
        dump_name="base_prompt_raw.json",
    )
    base = (doc.get("base_prompt") or "").strip()
    if not base:
        raise RuntimeError(f"base_prompt 为空: step_id={step.get('step_id')}")
    (step_dir / "base_prompt.txt").write_text(base, encoding="utf-8")
    return base
