"""Merge enrichment patches onto deterministic tutorial (fill empties only)."""

from __future__ import annotations

from typing import Any

from tutorial_mapper.from_analysis import build_assets
from tutorial_mapper.parts import DIFFICULTIES


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _fill(dst: dict[str, Any], key: str, value: Any, *, overwrite_unknown: bool = False) -> bool:
    """Fill dst[key] if blank; optionally replace difficulty/product unknown."""
    if value is None:
        return False
    cur = dst.get(key)
    if _is_blank(cur):
        dst[key] = value
        return True
    if overwrite_unknown and key == "difficulty" and cur == "unknown" and value in DIFFICULTIES and value != "unknown":
        dst[key] = value
        return True
    return False


def apply_text_patch(tutorial: dict[str, Any], patch: dict[str, Any]) -> list[str]:
    touched: list[str] = []
    for key in ("title", "style_tags", "occasion_tags", "practice_checklist", "eye_detail"):
        if key in patch and _fill(tutorial, key, patch[key]):
            touched.append(key)
    if "difficulty" in patch and _fill(
        tutorial, "difficulty", patch["difficulty"], overwrite_unknown=True
    ):
        touched.append("difficulty")

    by_id = {s["step_id"]: s for s in tutorial.get("steps") or []}
    for sid, sp in (patch.get("steps") or {}).items():
        step = by_id.get(sid)
        if not step or not isinstance(sp, dict):
            continue
        if "instruction" in sp:
            # 文本指令：若现有过短则替换
            cur = (step.get("instruction") or "").strip()
            new = (sp.get("instruction") or "").strip()
            if new and (len(cur) < 10 or not cur):
                step["instruction"] = new
                touched.append(f"step:{sid}:instruction")
        if "adaptation_note" in sp and _fill(step, "adaptation_note", sp["adaptation_note"]):
            touched.append(f"step:{sid}:adaptation_note")
        if "product" in sp and isinstance(sp["product"], dict):
            prod = step.setdefault("product", {"name": "unknown", "keywords": []})
            new_name = (sp["product"].get("name") or "").strip()
            if new_name and new_name != "unknown" and (
                not prod.get("name") or prod.get("name") == "unknown"
            ):
                prod["name"] = new_name
                touched.append(f"step:{sid}:product.name")
            new_kws = sp["product"].get("keywords") or []
            if new_kws:
                existing = list(prod.get("keywords") or [])
                for k in new_kws:
                    if k and k not in existing:
                        existing.append(k)
                if existing != (prod.get("keywords") or []):
                    prod["keywords"] = existing
                    touched.append(f"step:{sid}:product.keywords")

    # asset tags by part
    assets_by_part = {
        a["part"]: a for a in tutorial.get("assets") or [] if isinstance(a, dict)
    }
    for part, ap in (patch.get("assets_by_part") or {}).items():
        asset = assets_by_part.get(part)
        if not asset or not isinstance(ap, dict):
            continue
        for key in (
            "style_tags",
            "occasion_tags",
            "suitable_features",
            "avoid_features",
            "practice_notes",
        ):
            if key in ap and _fill(asset, key, ap[key]):
                touched.append(f"asset:{part}:{key}")
        if "difficulty" in ap and _fill(
            asset, "difficulty", ap["difficulty"], overwrite_unknown=True
        ):
            touched.append(f"asset:{part}:difficulty")

    return touched


def apply_vision_patch(tutorial: dict[str, Any], patch: dict[str, Any]) -> list[str]:
    touched: list[str] = []
    by_id = {s["step_id"]: s for s in tutorial.get("steps") or []}
    for sid, sp in (patch.get("steps") or {}).items():
        step = by_id.get(sid)
        if not step or not isinstance(sp, dict):
            continue
        vl = sp.get("visual_layer")
        if isinstance(vl, dict) and vl:
            cur = step.get("visual_layer")
            if not isinstance(cur, dict) or not cur:
                step["visual_layer"] = dict(vl)
                touched.append(f"step:{sid}:visual_layer")
            else:
                for k, v in vl.items():
                    if v is not None and _is_blank(cur.get(k)):
                        cur[k] = v
                        touched.append(f"step:{sid}:visual_layer.{k}")
        kws = sp.get("product_keywords") or []
        if kws:
            prod = step.setdefault("product", {"name": "unknown", "keywords": []})
            existing = list(prod.get("keywords") or [])
            changed = False
            for k in kws:
                if k and k not in existing:
                    existing.append(k)
                    changed = True
            if changed:
                prod["keywords"] = existing
                touched.append(f"step:{sid}:product.keywords")

    eye = patch.get("eye_detail")
    if isinstance(eye, dict) and eye and _fill(tutorial, "eye_detail", eye):
        touched.append("eye_detail")

    return touched


def refresh_assets_from_steps(tutorial: dict[str, Any]) -> None:
    """Rebuild assets' products / visual_layers / clips from current steps; keep enrich tags."""
    old_by_part = {
        a["part"]: a for a in tutorial.get("assets") or [] if isinstance(a, dict)
    }
    rebuilt = build_assets(
        tutorial["tutorial_id"],
        tutorial.get("steps") or [],
        style_tags=tutorial.get("style_tags") or [],
        occasion_tags=tutorial.get("occasion_tags") or [],
        difficulty=tutorial.get("difficulty") or "unknown",
    )
    for asset in rebuilt:
        prev = old_by_part.get(asset["part"])
        if not prev:
            continue
        for key in (
            "style_tags",
            "occasion_tags",
            "suitable_features",
            "avoid_features",
            "practice_notes",
            "difficulty",
        ):
            if not _is_blank(prev.get(key)):
                asset[key] = prev[key]
        # 若 tutorial 级标签非空而 asset 仍空，继承
        if _is_blank(asset.get("style_tags")) and tutorial.get("style_tags"):
            asset["style_tags"] = list(tutorial["style_tags"])
        if _is_blank(asset.get("occasion_tags")) and tutorial.get("occasion_tags"):
            asset["occasion_tags"] = list(tutorial["occasion_tags"])
    tutorial["assets"] = rebuilt
