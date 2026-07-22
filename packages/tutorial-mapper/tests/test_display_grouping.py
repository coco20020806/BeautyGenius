"""Unit tests for display_grouping."""

from __future__ import annotations

from tutorial_mapper.display_grouping import apply_display_grouping, build_step_groups


def _step(
    step_id: str,
    primary: str,
    *,
    subs: list[str] | None = None,
) -> dict:
    return {
        "step_id": step_id,
        "part": "other",
        "taxonomy_primary": primary,
        "taxonomy_sub_steps": list(subs or []),
        "product": {"name": "unknown", "keywords": []},
        "visual_layer": {},
        "instruction": "",
        "adaptation_note": "",
        "video_clip": {"start": 0, "end": 1},
    }


def test_consecutive_same_primary_merges_into_one_group():
    tutorial = {
        "steps": [
            _step("contour_01", "修容", subs=["鼻头两侧", "山根两侧"]),
            _step("contour_02", "修容", subs=["颧骨下方", "下颌线下方"]),
            _step("eye_01", "眼睛", subs=["下眼前段"]),
            _step("lip_01", "唇妆", subs=["唇线"]),
        ]
    }
    apply_display_grouping(tutorial)
    groups = tutorial["step_groups"]
    assert len(groups) == 3
    assert groups[0] == {
        "group_id": "group_01",
        "title": "修容",
        "index": 1,
        "step_ids": ["contour_01", "contour_02"],
    }
    assert groups[1]["title"] == "眼睛"
    assert groups[1]["index"] == 2
    assert groups[2]["title"] == "唇妆"
    assert groups[2]["index"] == 3

    steps = {s["step_id"]: s for s in tutorial["steps"]}
    assert steps["contour_01"]["display_title"] == "修容 · 鼻头两侧"
    assert steps["contour_02"]["display_title"] == "修容 · 颧骨下方"
    assert steps["eye_01"]["display_title"] == "眼睛"
    assert steps["lip_01"]["display_title"] == "唇妆"
    assert steps["contour_01"]["display_group_id"] == "group_01"
    assert steps["contour_02"]["display_group_id"] == "group_01"


def test_same_sub_step_collision_gets_suffix():
    tutorial = {
        "steps": [
            _step("lip_01", "唇妆", subs=["唇线"]),
            _step("lip_02", "唇妆", subs=["唇线"]),
        ]
    }
    apply_display_grouping(tutorial)
    titles = [s["display_title"] for s in tutorial["steps"]]
    assert titles[0] == "唇妆 · 唇线"
    assert titles[1] == "唇妆 · 唇线 · 2"
    assert len(set(titles)) == 2


def test_multi_step_without_subs_uses_ordinal():
    tutorial = {
        "steps": [
            _step("contour_01", "修容"),
            _step("contour_02", "修容"),
        ]
    }
    apply_display_grouping(tutorial)
    assert tutorial["steps"][0]["display_title"] == "修容 · 1"
    assert tutorial["steps"][1]["display_title"] == "修容 · 2"


def test_non_adjacent_same_primary_not_merged():
    groups = build_step_groups(
        [
            _step("contour_01", "修容"),
            _step("eye_01", "眼睛"),
            _step("contour_02", "修容"),
        ]
    )
    assert len(groups) == 3
    assert [g["title"] for g in groups] == ["修容", "眼睛", "修容"]
