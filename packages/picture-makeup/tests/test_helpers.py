"""Unit tests for picture-makeup helpers."""

from __future__ import annotations

from pathlib import Path

from picture_makeup.prompt_enrich import merge_final_prompt, pick_keyframe_paths


def test_merge_final_prompt_append_only() -> None:
    base = "在两颊扫腮红，请在原始图片上用色块标注着色范围"
    final = merge_final_prompt(base, "，色块略呈椭圆形")
    assert final.startswith(base)
    assert final == base + "，色块略呈椭圆形"


def test_pick_keyframe_paths_priority(tmp_path: Path) -> None:
    kf = tmp_path / "keyframes"
    kf.mkdir()
    (kf / "a.jpg").write_bytes(b"x" * 5000)
    (kf / "b.jpg").write_bytes(b"x" * 5000)
    (kf / "c.jpg").write_bytes(b"x" * 5000)
    step = {
        "keyframe_refs": [
            {"role": "step_start_face", "filename": "a.jpg"},
            {"role": "makeup_detail", "filename": "b.jpg"},
            {"role": "step_end_face", "filename": "c.jpg"},
        ]
    }
    paths = pick_keyframe_paths(step, kf)
    assert paths[0].name == "b.jpg"
    assert len(paths) == 3
