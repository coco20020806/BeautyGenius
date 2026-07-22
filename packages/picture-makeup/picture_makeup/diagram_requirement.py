"""Build wan dynamic-section text from final_prompt + structured visual fields."""

from __future__ import annotations

from typing import Any

# tutorial part -> diagram layer type label
_PART_LAYER: dict[str, str] = {
    "prep": "prep",
    "base": "base",
    "concealer": "concealer",
    "set": "set",
    "brow": "brow",
    "eye": "eyeshadow",
    "contour": "contour",
    "highlight": "highlight",
    "cheek": "blush",
    "lip": "lip",
    "other": "other",
}


def _layer_type(step: dict[str, Any]) -> str:
    part = str(step.get("part") or "").strip()
    if part in _PART_LAYER:
        return _PART_LAYER[part]
    primary = str(step.get("taxonomy_primary") or "").strip()
    return primary or part or "unknown"


def _blend_hint(vl: dict[str, Any]) -> str | None:
    blend = vl.get("blend_edge")
    if blend is not None and str(blend).strip():
        return str(blend).strip()
    shape = vl.get("shape")
    if shape is not None and str(shape).strip():
        return f"{str(shape).strip()} / soft"
    return None


def format_diagram_requirement(step: dict[str, Any], final_prompt: str) -> str:
    """Compose the dynamic block under「本步骤优化图示要求」.

    Keeps ``final_prompt`` intact, then appends a structured drawable trailer
    from ``step.visual_layer`` / part / step_id when available.
    """
    body = (final_prompt or "").strip()
    step_id = str(step.get("step_id") or "").strip() or "unknown"
    part = str(step.get("part") or "").strip() or "unknown"
    vl = step.get("visual_layer") if isinstance(step.get("visual_layer"), dict) else {}

    lines: list[str] = ["【可绘制字段】", f"- part / 步骤: {part} / {step_id}"]
    lines.append(f"- 图层类型: {_layer_type(step)}")

    color = vl.get("color") if vl else None
    if color is not None and str(color).strip():
        lines.append(f"- 颜色: {str(color).strip()}")

    position = vl.get("position") if vl else None
    if position is not None and str(position).strip():
        lines.append(f"- 位置与边界: {str(position).strip()}")

    opacity = vl.get("opacity") if vl else None
    if opacity is not None and str(opacity).strip() != "":
        lines.append(f"- opacity: {opacity}")

    blend = _blend_hint(vl) if vl else None
    if blend:
        lines.append(f"- 形状/晕染: {blend}")

    trailer = "\n".join(lines)
    if not body:
        return trailer
    return f"{body}\n\n{trailer}"
