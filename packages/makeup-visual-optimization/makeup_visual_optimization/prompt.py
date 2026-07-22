"""Build system/user prompts from skill markdown references."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_system_prompt(skill_dir: Path) -> str:
    skill_md = _read(skill_dir / "SKILL.md")
    rules = _read(skill_dir / "references" / "optimization-rules.md")
    contract = _read(skill_dir / "references" / "output-contract.md")
    return (
        "你是美妆图示优化助手。根据用户问卷与现有教程步骤，输出符合契约的 JSON。"
        "只返回 JSON 对象，不要 markdown 围栏。\n\n"
        "## Skill\n"
        f"{skill_md}\n\n"
        "## Optimization Rules\n"
        f"{rules}\n\n"
        "## Output Contract\n"
        f"{contract}"
    )


def build_user_message(
    tutorial: dict[str, Any],
    optimization_input: dict[str, Any],
) -> str:
    steps = tutorial.get("steps") or []
    compact_steps: list[dict[str, Any]] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        compact_steps.append(
            {
                "step_id": step.get("step_id"),
                "part": step.get("part"),
                "taxonomy_primary": step.get("taxonomy_primary"),
                "display_title": step.get("display_title"),
                "instruction": step.get("instruction"),
                "adaptation_note": step.get("adaptation_note"),
                "product": step.get("product"),
                "visual_layer": step.get("visual_layer"),
                "video_clip": step.get("video_clip"),
            }
        )

    payload = {
        "tutorial_id": tutorial.get("tutorial_id"),
        "title": tutorial.get("title"),
        "steps": compact_steps,
        "optimization_input": optimization_input,
    }
    return (
        "请根据 optimization_input 优化下列教程步骤，返回符合 output-contract 的 JSON。\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
