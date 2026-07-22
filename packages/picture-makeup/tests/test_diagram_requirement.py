"""Tests for diagram_requirement formatting."""

from __future__ import annotations

from picture_makeup.diagram_requirement import format_diagram_requirement
from picture_makeup.prompt_loader import compose_diagram_full_text


def test_format_diagram_requirement_with_visual_layer() -> None:
    step = {
        "step_id": "blush_01",
        "part": "cheek",
        "taxonomy_primary": "腮红",
        "visual_layer": {
            "color": "#EFA3A8",
            "position": "面中偏上横向平铺",
            "opacity": 0.36,
            "shape": "soft_oval",
        },
    }
    final = "在两颊横向扫腮红，请在原始图片上用色块标注着色范围"
    out = format_diagram_requirement(step, final)
    assert out.startswith(final)
    assert "【可绘制字段】" in out
    assert "#EFA3A8" in out
    assert "面中偏上横向平铺" in out
    assert "0.36" in out
    assert "blush" in out
    assert "soft_oval" in out
    composed = compose_diagram_full_text("STATIC", out)
    assert "本步骤优化图示要求" in composed
    assert "#EFA3A8" in composed


def test_format_diagram_requirement_without_visual_layer() -> None:
    step = {"step_id": "base_01", "part": "base"}
    final = "全脸轻铺底妆，请在原始图片上用色块标注作用区域"
    out = format_diagram_requirement(step, final)
    assert final in out
    assert "part / 步骤: base / base_01" in out
    assert "图层类型: base" in out
    assert "颜色:" not in out
