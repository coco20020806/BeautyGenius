from __future__ import annotations

from makeup_visual_optimization.apply import apply_optimization
from makeup_visual_optimization.normalize import normalize_adjustment


def test_normalize_adjustment_maps_camel_case() -> None:
    result = normalize_adjustment(
        {
            "styles": ["清透自然", "清透自然"],
            "occasions": ["通勤工作"],
            "retainedParts": ["腮红"],
            "skinType": "混合性肌肤",
            "concerns": ["缩短中庭"],
            "constraints": ["早上时间少"],
        }
    )
    assert result["preferred_styles"] == ["清透自然"]
    assert result["occasions"] == ["通勤工作"]
    assert result["retained_modules"] == ["腮红"]
    assert result["skin_type"] == "混合性肌肤"
    assert result["makeup_goals"] == ["缩短中庭"]
    assert result["execution_limits"] == ["早上时间少"]
    assert result["face_shape"] == "不确定"
    assert result["target_areas"] == []
    assert result["free_text"] == ""


def test_apply_optimization_merges_visual_layer_and_instruction() -> None:
    tutorial = {
        "contract_version": "tutorial.v1",
        "tutorial_id": "t1",
        "steps": [
            {
                "step_id": "blush_01",
                "part": "cheek",
                "instruction": "原腮红斜扫",
                "adaptation_note": "",
                "visual_layer": {"color": "#EFA3A8", "position": "苹果肌外侧"},
            },
            {
                "step_id": "lip_01",
                "part": "lip",
                "instruction": "薄涂唇",
                "adaptation_note": "",
                "visual_layer": {},
            },
        ],
    }
    optimization = {
        "optimization_summary": {
            "primary_goal": "缩短中庭",
            "retained_modules": ["腮红"],
        },
        "step_adjustments": [
            {
                "step_id": "blush_01",
                "adapted": "腮红改为面中横向轻铺",
                "adaptation_note": "横向平铺缩短中庭视觉",
                "visual_layer_patch": {
                    "layer_id": "layer_blush_01",
                    "type": "blush",
                    "shape": "soft_horizontal_oval",
                    "color": "#EFA3A8",
                    "opacity": 0.36,
                    "position_description": "面中偏上，最低点不低于鼻翼",
                    "blend_edge": "soft",
                },
            }
        ],
    }

    result = apply_optimization(tutorial, optimization)
    blush = result["steps"][0]
    assert blush["instruction"] == "腮红改为面中横向轻铺"
    assert blush["adaptation_note"] == "横向平铺缩短中庭视觉"
    assert blush["visual_layer"]["position"] == "面中偏上，最低点不低于鼻翼"
    assert blush["visual_layer"]["opacity"] == 0.36
    assert blush["visual_layer"]["shape"] == "soft_horizontal_oval"
    assert result["steps"][1]["instruction"] == "薄涂唇"
    assert result["optimization_summary"]["primary_goal"] == "缩短中庭"
    # original untouched
    assert tutorial["steps"][0]["instruction"] == "原腮红斜扫"
