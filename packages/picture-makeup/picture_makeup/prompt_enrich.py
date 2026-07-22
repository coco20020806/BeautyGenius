"""Keyframe enrich (append-only appendix)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from picture_makeup.config import PictureMakeupConfig
from picture_makeup.llm import call_vision_json
from picture_makeup.prompt_loader import load_enrich_system

PREFERRED_ROLES = ("makeup_detail", "step_end_face", "step_start_face")


def pick_keyframe_paths(step: dict[str, Any], keyframes_dir: Path) -> list[Path]:
    refs = step.get("keyframe_refs") or []
    ranked: list[tuple[int, Path]] = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        fname = ref.get("filename")
        if not fname:
            continue
        path = keyframes_dir / fname
        if not path.is_file():
            continue
        role = ref.get("role") or ""
        try:
            rank = PREFERRED_ROLES.index(role)
        except ValueError:
            rank = 99
        ranked.append((rank, path))
    ranked.sort(key=lambda x: x[0])
    out: list[Path] = []
    seen: set[Path] = set()
    for _rank, p in ranked:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
        if len(out) >= 3:
            break
    return out


def merge_final_prompt(base_prompt: str, appendix: str | None) -> str:
    base = base_prompt.strip()
    app = (appendix or "").strip()
    final = base + app
    if not final.startswith(base):
        raise ValueError("final_prompt must start with base_prompt")
    return final


def enrich_from_keyframes(
    config: PictureMakeupConfig,
    step: dict[str, Any],
    base_prompt: str,
    keyframes_dir: Path,
    step_dir: Path,
) -> tuple[str, dict[str, Any]]:
    paths = pick_keyframe_paths(step, keyframes_dir)
    step_id = step.get("step_id") or "unknown"
    if not paths:
        enrich = {
            "base_prompt": base_prompt,
            "appendix": "",
            "final_prompt": base_prompt,
            "conflict": False,
            "notes": "no keyframes",
            "keyframe_files": [],
            "skipped": True,
        }
        (step_dir / "enrich.json").write_text(
            json.dumps(enrich, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (step_dir / "final_prompt.txt").write_text(base_prompt, encoding="utf-8")
        return base_prompt, enrich

    user_text = (
        f"step_id: {step_id}\n"
        f"part: {step.get('part', '')}\n"
        f"instruction: {step.get('instruction', '')}\n"
        f"base_prompt（禁止修改，仅用于校对）:\n{base_prompt}\n\n"
        "请根据附带的关键帧，输出 appendix 等 JSON 字段。"
    )
    system = load_enrich_system(config.skill_dir)
    doc = call_vision_json(
        config,
        system=system,
        user_text=user_text,
        image_paths=paths,
        run_dir=step_dir,
        dump_name="enrich_raw.json",
    )
    appendix = (doc.get("appendix") or "").strip()
    final_prompt = merge_final_prompt(base_prompt, appendix)
    enrich = {
        "base_prompt": base_prompt,
        "appendix": appendix,
        "final_prompt": final_prompt,
        "conflict": bool(doc.get("conflict")),
        "notes": doc.get("notes") or "",
        "keyframe_files": [p.name for p in paths],
        "keyframe_roles_used": doc.get("keyframe_roles_used") or [],
        "skipped": False,
    }
    (step_dir / "enrich.json").write_text(
        json.dumps(enrich, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (step_dir / "final_prompt.txt").write_text(final_prompt, encoding="utf-8")
    return final_prompt, enrich
