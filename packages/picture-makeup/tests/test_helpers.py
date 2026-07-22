"""Unit tests for picture-makeup helpers."""

from __future__ import annotations

from pathlib import Path

from picture_makeup.prompt_enrich import merge_final_prompt, pick_keyframe_paths
from picture_makeup.prompt_loader import compose_diagram_full_text, load_diagram_prompt

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / "skills" / "picture_makeup"


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


def test_load_diagram_prompt_from_skill_md() -> None:
    assert SKILL_DIR.is_dir()
    loaded = load_diagram_prompt(SKILL_DIR)
    assert loaded.prompt_text_version == "diagram-2"
    assert loaded.used_fallback is False
    assert "半透明范围标注" in loaded.static_text
    assert "不得出现评价用户长相的文字" in loaded.static_text


def test_compose_diagram_full_text_uses_optimized_heading() -> None:
    text = compose_diagram_full_text("STATIC", "FINAL")
    assert "本步骤优化图示要求" in text
    assert text.endswith("FINAL")
