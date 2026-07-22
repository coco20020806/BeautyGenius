"""Unit tests for understanding merge (no API)."""

from __future__ import annotations

from makeup_understanding.merge import apply_understanding_patch, build_user_payload


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
                    "display_range": "全脸均匀薄涂，边缘自然过渡",
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
    assert step["display_range"] == "全脸均匀薄涂，边缘自然过渡"
    assert step["product"]["name"] == "珂岸面部素颜霜"


def test_none_clears_display() -> None:
    tutorial = {
        "steps": [
            {
                "step_id": "x",
                "product": {"name": "unknown", "keywords": []},
                "display_range": "旧范围文案",
            }
        ]
    }
    apply_understanding_patch(
        tutorial,
        {
            "steps": [
                {
                    "step_id": "x",
                    "display_product": "should clear",
                    "display_product_tier": "none",
                    "technique": "",
                    "display_range": "",
                }
            ]
        },
    )
    assert tutorial["steps"][0]["display_product"] == ""
    assert tutorial["steps"][0]["display_product_tier"] == "none"
    assert tutorial["steps"][0]["display_range"] == ""


def test_display_range_truncated() -> None:
    tutorial = {"steps": [{"step_id": "lip_01", "product": {"name": "unknown", "keywords": []}}]}
    long_range = "唇" * 200
    apply_understanding_patch(
        tutorial,
        {
            "steps": [
                {
                    "step_id": "lip_01",
                    "display_product_tier": "none",
                    "display_product": "",
                    "technique": "",
                    "display_range": long_range,
                }
            ]
        },
    )
    assert len(tutorial["steps"][0]["display_range"]) == 160


def test_build_user_payload_includes_visual_layer() -> None:
    tutorial = {
        "tutorial_id": "t1",
        "title": "demo",
        "steps": [
            {
                "step_id": "lip_01",
                "part": "lip",
                "product": {"name": "口红", "keywords": []},
                "visual_layer": {
                    "position": "全唇薄涂",
                    "shape": "gradient_inner_dark_outer_light",
                    "color": "#9E6B6B",
                    "opacity": 0.6,
                },
                "instruction": "打底",
                "adaptation_note": "",
            }
        ],
    }
    payload = build_user_payload(tutorial)
    assert "gradient_inner_dark_outer_light" in payload
    assert "#9E6B6B" in payload
    assert "全唇薄涂" in payload
