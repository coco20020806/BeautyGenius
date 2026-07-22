from __future__ import annotations

from pathlib import Path

from api_server.preview_assembler import (
    _hints_from_tutorial,
    after_image_filename,
    before_image_filename,
    comparison_from_alignment,
)


def test_before_after_filenames_use_full_pair(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "target.jpg").write_bytes(b"x")
    (run / "preview_01.jpg").write_bytes(b"y")
    (run / "target_display.jpg").write_bytes(b"display-before")
    (run / "preview_display.jpg").write_bytes(b"display-after")
    assert before_image_filename(run) == "target.jpg"
    assert after_image_filename(run) == "preview_01.jpg"


def test_comparison_from_alignment_uses_target_size():
    out = comparison_from_alignment(
        {
            "target_size": [1254, 1254],
            "display_size": [780, 780],
            "object_position": "50% 37.1%",
        }
    )
    assert out == {"width": 1254, "height": 1254}


def test_comparison_from_alignment_requires_target_size():
    assert comparison_from_alignment({"display_size": [900, 900]}) is None
    out = comparison_from_alignment({"target_size": [1024, 1536]})
    assert out == {"width": 1024, "height": 1536}


def test_hints_when_transfer_skipped():
    hints = _hints_from_tutorial(None, average_baseline=False, transfer_skipped=True)
    assert hints[0]["title"] == "已跳过妆容生成"
