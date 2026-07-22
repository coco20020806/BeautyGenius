"""Merge understanding patch onto tutorial steps."""

from __future__ import annotations

from typing import Any

from makeup_understanding.prompt import TIERS


def apply_understanding_patch(
    tutorial: dict[str, Any],
    patch: dict[str, Any],
) -> list[str]:
    """Apply patch in-place. Returns list of touched step_ids."""
    by_id = {s["step_id"]: s for s in tutorial.get("steps") or [] if isinstance(s, dict) and s.get("step_id")}
    touched: list[str] = []
    for item in patch.get("steps") or []:
        if not isinstance(item, dict):
            continue
        sid = (item.get("step_id") or "").strip()
        step = by_id.get(sid)
        if not step:
            continue
        tier = (item.get("display_product_tier") or "none").strip().lower()
        if tier not in TIERS:
            tier = "none"
        display = (item.get("display_product") or "").strip()
        if tier == "none":
            display = ""
        technique = (item.get("technique") or "").strip()
        # keep technique short-ish if model rambles
        if len(technique) > 40:
            technique = technique[:40].rstrip()

        step["display_product"] = display
        step["display_product_tier"] = tier
        step["technique"] = technique

        product_name = (item.get("product_name") or "").strip()
        if product_name and product_name != "unknown" and tier == "specific":
            prod = step.setdefault("product", {"name": "unknown", "keywords": []})
            if not isinstance(prod, dict):
                prod = {"name": "unknown", "keywords": []}
                step["product"] = prod
            old = (prod.get("name") or "unknown").strip()
            if old in {"", "unknown"}:
                prod["name"] = product_name

        touched.append(sid)
    return touched


def build_user_payload(tutorial: dict[str, Any]) -> str:
    import json

    slim = []
    for s in tutorial.get("steps") or []:
        if not isinstance(s, dict):
            continue
        slim.append(
            {
                "step_id": s.get("step_id"),
                "part": s.get("part"),
                "taxonomy_primary": s.get("taxonomy_primary"),
                "taxonomy_sub_steps": s.get("taxonomy_sub_steps"),
                "product": s.get("product"),
                "instruction": (s.get("instruction") or "")[:1200],
                "adaptation_note": (s.get("adaptation_note") or "")[:400],
            }
        )
    return json.dumps(
        {
            "tutorial_id": tutorial.get("tutorial_id"),
            "title": tutorial.get("title"),
            "steps": slim,
        },
        ensure_ascii=False,
        indent=2,
    )
