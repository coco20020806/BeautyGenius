from __future__ import annotations

from pathlib import Path

from api_server.preview_assembler import (
    _hints_from_tutorial,
    before_image_filename,
    comparison_from_alignment,
)


def test_before_image_filename_prefers_display(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "target.jpg").write_bytes(b"x")
    assert before_image_filename(run) == "target.jpg"
    (run / "target_display.jpg").write_bytes(b"y")
    assert before_image_filename(run) == "target_display.jpg"


def test_comparison_from_alignment_display_size():
    out = comparison_from_alignment(
        {
            "display_size": [900, 900],
            "object_position": "50% 48%",
        }
    )
    assert out == {"width": 900, "height": 900, "objectPosition": "50% 48%"}


def test_comparison_from_alignment_target_fallback():
    out = comparison_from_alignment({"target_size": [1024, 1536]})
    assert out == {"width": 1024, "height": 1536}


def test_hints_when_transfer_skipped():
    hints = _hints_from_tutorial(None, average_baseline=False, transfer_skipped=True)
    assert hints[0]["title"] == "已跳过妆容生成"
