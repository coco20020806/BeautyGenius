"""Unit tests for understanding merge (no API)."""

from __future__ import annotations

from makeup_understanding.merge import apply_understanding_patch


def test_apply_understanding_patch_specific() -> None:
    tutorial = {
        "steps": [
            {
                "step_id": "base_01",
                "part": "base",
                "product": {"name": "unknown", "keywords": ["霜"]},
                "instruction": "珂岸面部素颜霜 全脸推开",
                "adaptation_note": "",
            }
        ]
    }
    touched = apply_understanding_patch(
        tutorial,
        {
            "steps": [
                {
                    "step_id": "base_01",
                    "display_product": "珂岸面部素颜霜",
                    "display_product_tier": "specific",
                    "technique": "全脸推开",
                    "product_name": "珂岸面部素颜霜",
                }
            ]
        },
    )
    assert touched == ["base_01"]
    step = tutorial["steps"][0]
    assert step["display_product"] == "珂岸面部素颜霜"
    assert step["display_product_tier"] == "specific"
    assert step["technique"] == "全脸推开"
    assert step["product"]["name"] == "珂岸面部素颜霜"


def test_none_clears_display() -> None:
    tutorial = {"steps": [{"step_id": "x", "product": {"name": "unknown", "keywords": []}}]}
    apply_understanding_patch(
        tutorial,
        {
            "steps": [
                {
                    "step_id": "x",
                    "display_product": "should clear",
                    "display_product_tier": "none",
                    "technique": "",
                }
            ]
        },
    )
    assert tutorial["steps"][0]["display_product"] == ""
    assert tutorial["steps"][0]["display_product_tier"] == "none"
