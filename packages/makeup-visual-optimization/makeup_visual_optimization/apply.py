"""Apply optimization JSON patches onto tutorial.steps[]."""

from __future__ import annotations

import copy
from typing import Any

# visual_layer_patch fields that change drawable geometry/placement
_GEOMETRY_KEYS = frozenset(
    {
        "shape",
        "position",
        "position_description",
        "opacity",
        "color",
        "blend_edge",
        "type",
        "layer_id",
    }
)


def apply_optimization(
    tutorial: dict[str, Any],
    optimization: dict[str, Any],
) -> dict[str, Any]:
    """Return a deep-copied tutorial with step patches merged."""

    result = copy.deepcopy(tutorial)
    steps = result.get("steps")
    if not isinstance(steps, list):
        return result

    by_id = {
        str(step.get("step_id")): step
        for step in steps
        if isinstance(step, dict) and step.get("step_id")
    }

    for adj in optimization.get("step_adjustments") or []:
        if not isinstance(adj, dict):
            continue
        step_id = str(adj.get("step_id") or "").strip()
        step = by_id.get(step_id)
        if not step:
            continue

        adapted = adj.get("adapted")
        if isinstance(adapted, str) and adapted.strip():
            step["instruction"] = adapted.strip()

        note = adj.get("adaptation_note")
        if isinstance(note, str) and note.strip():
            step["adaptation_note"] = note.strip()

        patch = adj.get("visual_layer_patch")
        if isinstance(patch, dict) and patch:
            step["visual_layer"] = _merge_visual_layer(step.get("visual_layer"), patch)

    checklist = optimization.get("practice_checklist_patches") or []
    for item in checklist:
        if not isinstance(item, dict):
            continue
        step_id = str(item.get("step_id") or "").strip()
        step = by_id.get(step_id)
        if not step:
            continue
        instruction = item.get("instruction")
        if isinstance(instruction, str) and instruction.strip() and not step.get("instruction"):
            step["instruction"] = instruction.strip()

    summary = optimization.get("optimization_summary")
    if isinstance(summary, dict):
        result["optimization_summary"] = summary

    return result


def _merge_visual_layer(existing: Any, patch: dict[str, Any]) -> dict[str, Any]:
    base: dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    for key, value in patch.items():
        if key not in _GEOMETRY_KEYS and key not in {"color", "opacity", "blend_edge", "type", "shape", "layer_id"}:
            continue
        if value is None:
            continue
        if key == "position_description":
            text = str(value).strip()
            if text:
                base["position"] = text
            continue
        if isinstance(value, str):
            text = value.strip()
            if text:
                base[key] = text
            continue
        base[key] = value
    return base
