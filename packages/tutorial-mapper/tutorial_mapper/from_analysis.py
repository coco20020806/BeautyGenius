"""Deterministic mapping: analysis.json → half-filled Tutorial."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from tutorial_mapper.parts import part_step_slug, primary_to_part
from tutorial_mapper.schema import CONTRACT_VERSION

_PRODUCT_HINT = re.compile(
    r"(腮红|眼影|粉底|遮瑕|定妆粉|散粉|口红|唇釉|眼线|睫毛膏|修容|高光|"
    r"气垫|霜|膏|液|笔|粉饼|眉笔|染眉膏)",
    re.UNICODE,
)


def _join_step_text(text_obj: dict[str, Any] | None) -> str:
    if not text_obj:
        return ""
    chunks: list[str] = []
    for key in ("voiceover", "subtitles", "on_screen"):
        items = text_obj.get(key) or []
        for item in items:
            if not isinstance(item, dict):
                continue
            t = (item.get("text") or "").strip()
            if t:
                chunks.append(t)
    # 去重保序
    seen: set[str] = set()
    out: list[str] = []
    for c in chunks:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return " ".join(out).strip()


def _weak_product_keywords(instruction: str) -> list[str]:
    if not instruction:
        return []
    found = _PRODUCT_HINT.findall(instruction)
    # 保序去重
    seen: set[str] = set()
    keys: list[str] = []
    for w in found:
        if w not in seen:
            seen.add(w)
            keys.append(w)
    return keys[:8]


def _tutorial_id_from_run(parse_run_dir: Path) -> str:
    name = parse_run_dir.name.strip() or "unknown"
    safe = re.sub(r"[^A-Za-z0-9_\-]", "_", name)
    return f"tutorial_{safe}"


def map_step(
    raw: dict[str, Any],
    *,
    part_counters: dict[str, int],
) -> dict[str, Any]:
    taxonomy = raw.get("taxonomy") or {}
    primary = (taxonomy.get("primary") or raw.get("step_name") or "").strip()
    part = primary_to_part(primary)
    part_counters[part] = part_counters.get(part, 0) + 1
    seq = part_counters[part]
    slug = part_step_slug(part)
    step_id = f"{slug}_{seq:02d}"

    tr = raw.get("time_range") or {}
    start = float(tr.get("start_sec") or 0)
    end = float(tr.get("end_sec") or start)
    instruction = _join_step_text(raw.get("text"))
    keywords = _weak_product_keywords(instruction)

    keyframe_refs: list[dict[str, Any]] = []
    for kf in raw.get("keyframes") or []:
        if not isinstance(kf, dict):
            continue
        ref: dict[str, Any] = {}
        for key in ("role", "timestamp_sec", "filename", "label"):
            val = kf.get(key)
            if val is not None:
                ref[key] = val
        if ref.get("filename") or ref.get("role"):
            keyframe_refs.append(ref)

    return {
        "step_id": step_id,
        "part": part,
        "taxonomy_primary": primary,
        "taxonomy_sub_steps": list(taxonomy.get("sub_steps") or []),
        "product": {
            "name": "unknown",
            "keywords": keywords,
        },
        "visual_layer": {},
        "instruction": instruction,
        "adaptation_note": "",
        "video_clip": {"start": start, "end": end},
        "keyframe_refs": keyframe_refs,
    }


def build_assets(
    tutorial_id: str,
    steps: list[dict[str, Any]],
    *,
    style_tags: list[str] | None = None,
    occasion_tags: list[str] | None = None,
    difficulty: str = "unknown",
) -> list[dict[str, Any]]:
    by_part: dict[str, list[dict[str, Any]]] = {}
    for step in steps:
        part = step.get("part") or "other"
        by_part.setdefault(part, []).append(step)

    assets: list[dict[str, Any]] = []
    for part, part_steps in by_part.items():
        products: list[str] = []
        for s in part_steps:
            prod = s.get("product") or {}
            name = (prod.get("name") or "").strip()
            if name and name != "unknown" and name not in products:
                products.append(name)
            for kw in prod.get("keywords") or []:
                if kw and kw not in products:
                    products.append(kw)

        assets.append(
            {
                "asset_id": f"{part}_001",
                "source_tutorial_id": tutorial_id,
                "part": part,
                "style_tags": list(style_tags or []),
                "occasion_tags": list(occasion_tags or []),
                "suitable_features": [],
                "avoid_features": [],
                "difficulty": difficulty,
                "products": products,
                "visual_layers": [
                    vl
                    for s in part_steps
                    if (vl := s.get("visual_layer")) and isinstance(vl, dict) and vl
                ],
                "video_clips": [
                    dict(s["video_clip"])
                    for s in part_steps
                    if isinstance(s.get("video_clip"), dict)
                ],
                "practice_notes": [],
                "step_ids": [s["step_id"] for s in part_steps],
            }
        )
    return assets


def from_analysis(
    analysis: dict[str, Any],
    *,
    parse_run_dir: Path,
) -> dict[str, Any]:
    """Build a deterministic (possibly half-filled) tutorial object."""
    video = analysis.get("video") or {}
    duration_f = float(video.get("duration_sec") or 0)
    duration = int(round(duration_f))
    estimated_time = int(math.ceil(duration / 10)) if duration > 0 else 0
    tutorial_id = _tutorial_id_from_run(parse_run_dir)
    source_path = str(video.get("source_path") or "")

    part_counters: dict[str, int] = {}
    steps: list[dict[str, Any]] = []
    for raw in analysis.get("steps") or []:
        if not isinstance(raw, dict):
            continue
        if (raw.get("taxonomy") or {}).get("skipped"):
            continue
        steps.append(map_step(raw, part_counters=part_counters))

    assets = build_assets(tutorial_id, steps)

    return {
        "contract_version": CONTRACT_VERSION,
        "tutorial_id": tutorial_id,
        "title": "",
        "source_video": "local_upload",
        "source_path": source_path,
        "duration": duration,
        "difficulty": "unknown",
        "estimated_time": estimated_time,
        "style_tags": [],
        "occasion_tags": [],
        "steps": steps,
        "eye_detail": {},
        "practice_checklist": [],
        "assets": assets,
        "parse_run_id": parse_run_dir.name,
    }
