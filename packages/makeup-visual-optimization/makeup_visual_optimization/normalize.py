"""Map frontend AdjustmentRequest fields to skill optimization_input."""

from __future__ import annotations

from typing import Any


def normalize_adjustment(request: dict[str, Any]) -> dict[str, Any]:
    """Convert camelCase questionnaire payload to skill ``optimization_input``."""

    styles = _str_list(request.get("styles") or request.get("preferred_styles"))
    occasions = _str_list(request.get("occasions"))
    retained = _str_list(request.get("retainedParts") or request.get("retained_modules"))
    concerns = _str_list(request.get("concerns") or request.get("makeup_goals"))
    constraints = _str_list(request.get("constraints") or request.get("execution_limits"))
    target_areas = _str_list(request.get("targetAreas") or request.get("target_areas"))
    skin = str(request.get("skinType") or request.get("skin_type") or "不确定").strip() or "不确定"
    face_shape = str(request.get("faceShape") or request.get("face_shape") or "不确定").strip() or "不确定"
    free_text = str(request.get("freeText") or request.get("free_text") or "").strip()

    return {
        "preferred_styles": styles,
        "occasions": occasions,
        "retained_modules": retained,
        "target_areas": target_areas,
        "skin_type": skin,
        "face_shape": face_shape,
        "makeup_goals": concerns,
        "execution_limits": constraints,
        "free_text": free_text,
    }


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = str(item).strip()
        if text and text not in out:
            out.append(text)
    return out
