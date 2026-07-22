"""Makeup step taxonomy (skill: beauty-video-parse)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_taxonomy_enums(skill_dir: Path) -> dict[str, Any]:
    path = skill_dir / "taxonomy-enums.json"
    return json.loads(path.read_text(encoding="utf-8"))


def taxonomy_summary_for_prompt(skill_dir: Path, max_sub: int = 8) -> str:
    data = load_taxonomy_enums(skill_dir)
    lines = [
        "一级 step_name 只能从以下 12 类中选择（按视频时间顺序，未出现的「眉毛」「睫毛」可不输出步骤）：",
        "、".join(data["primaries"]),
        "",
        "每步必须包含 taxonomy 对象：",
        '{"primary":"<与step_name相同>","sub_steps":["来自该主类下的细分名，可多选"],"skipped":false}',
        "",
        "makeup_detail 的 label 必须使用 taxonomy.sub_steps 中的细分名（如 外V区、卧蚕-中段），不要用泛称「眼影特写」。",
        "",
        "各主类允许的 sub_steps（节选，完整以 taxonomy 为准）：",
    ]
    for primary in data["primaries"]:
        subs = data["sub_steps"].get(primary, [])
        sample = subs[:max_sub]
        suffix = "…" if len(subs) > max_sub else ""
        lines.append(f"- {primary}: {', '.join(sample)}{suffix}")
    return "\n".join(lines)


def repair_taxonomy_hint(skill_dir: Path) -> str:
    data = load_taxonomy_enums(skill_dir)
    return (
        "step_name 必须是以下之一: "
        + "、".join(data["primaries"])
        + "。每步含 taxonomy.primary、taxonomy.sub_steps 数组。"
        "makeup_detail.label 用 sub_steps 中的名称。"
    )


def normalize_taxonomy_on_step(step: dict[str, Any], enums: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    primaries = set(enums["primaries"])
    tax = step.get("taxonomy") or {}
    primary = (tax.get("primary") or step.get("step_name") or "").strip()
    if primary not in primaries:
        warnings.append(f"非法主类: {primary}")
        primary = step.get("step_name", "妆前")
        if primary not in primaries:
            primary = "妆前"
    step["step_name"] = primary
    allowed = set(enums["sub_steps"].get(primary, []))
    raw_subs = tax.get("sub_steps") or []
    clean_subs: list[str] = []
    for s in raw_subs:
        name = str(s).strip()
        if name in allowed:
            clean_subs.append(name)
        elif name:
            warnings.append(f"未知 sub_step [{primary}]: {name}")
    step["taxonomy"] = {
        "primary": primary,
        "sub_steps": clean_subs,
        "skipped": bool(tax.get("skipped", False)),
    }
    return warnings


def align_makeup_detail_labels(steps: list[dict[str, Any]]) -> None:
    for step in steps:
        subs = (step.get("taxonomy") or {}).get("sub_steps") or []
        sub_iter = iter(subs)
        for kf in step.get("keyframes") or []:
            if kf.get("role") != "makeup_detail":
                continue
            label = (kf.get("label") or "").strip()
            if label and label not in ("步骤开始脸部", "步骤结束脸部", "眼影特写"):
                continue
            try:
                kf["label"] = next(sub_iter)
            except StopIteration:
                if subs:
                    kf["label"] = subs[0]
                break


def build_taxonomy_coverage(steps: list[dict[str, Any]], enums: dict[str, Any]) -> dict[str, Any]:
    present = {s["step_name"] for s in steps}
    skip_default = set(enums.get("skip_by_default", []))
    skipped = sorted(skip_default - present)
    sub_by_primary: dict[str, list[str]] = {}
    for step in steps:
        p = step["step_name"]
        subs = (step.get("taxonomy") or {}).get("sub_steps") or []
        sub_by_primary[p] = subs
    return {
        "taxonomy_version": enums.get("taxonomy_version", "v1"),
        "present_primaries": sorted(present),
        "skipped_primaries": skipped,
        "sub_steps_by_primary": sub_by_primary,
        "all_primaries_enum": enums["primaries"],
    }
