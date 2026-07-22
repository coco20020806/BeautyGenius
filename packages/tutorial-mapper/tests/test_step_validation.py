"""Tests for tutorial step semantic validation."""

from __future__ import annotations

from tutorial_mapper.step_validation import validate_tutorial_steps


def _lip_step(step_id: str, start: float, end: float, instruction: str) -> dict:
    return {
        "step_id": step_id,
        "part": "lip",
        "taxonomy_primary": "唇妆",
        "instruction": instruction,
        "video_clip": {"start": start, "end": end},
    }


def test_two_lip_steps_sequential_pass():
    """Same primary, non-overlapping clips — valid multi-step (mouth tutorial pattern)."""
    tutorial = {
        "duration": 83,
        "steps": [
            _lip_step("lip_01", 0.0, 36.0, "先用唇线笔在上唇画个U型"),
            _lip_step("lip_02", 36.0, 80.0, "口红先用浅色的打底再叠涂唇釉"),
        ],
    }
    result = validate_tutorial_steps(tutorial)
    assert result["pass"] is True
    assert result["by_primary"]["唇妆"]["step_count"] == 2
    assert not any(i["severity"] == "error" for i in result["issues"])


def test_same_clip_error():
    tutorial = {
        "duration": 80,
        "steps": [
            _lip_step("lip_01", 0.0, 40.0, "步骤 A"),
            _lip_step("lip_02", 0.5, 40.5, "完全不同的另一段文案"),
        ],
    }
    result = validate_tutorial_steps(tutorial)
    assert result["pass"] is False
    codes = {i["code"] for i in result["issues"]}
    assert "duplicate_step_same_clip" in codes


def test_overlap_and_same_instruction_error():
    text = "同样的口播内容重复解析两次同样的口播内容"
    tutorial = {
        "duration": 80,
        "steps": [
            _lip_step("lip_01", 0.0, 50.0, text),
            _lip_step("lip_02", 10.0, 60.0, text),
        ],
    }
    result = validate_tutorial_steps(tutorial)
    assert result["pass"] is False
    assert any(
        i["code"] == "duplicate_step_overlap_and_instruction"
        for i in result["issues"]
    )


def test_duplicate_step_id():
    tutorial = {
        "duration": 60,
        "steps": [
            _lip_step("lip_01", 0.0, 30.0, "a"),
            _lip_step("lip_01", 30.0, 60.0, "b"),
        ],
    }
    result = validate_tutorial_steps(tutorial)
    assert result["pass"] is False
    assert any(i["code"] == "duplicate_step_id" for i in result["issues"])
