from __future__ import annotations

from pathlib import Path

from api_server.preview_assembler import (
    INTENSITY_LEVELS,
    _hints_from_tutorial,
    after_image_filename,
    assemble_makeup_preview,
    before_image_filename,
    comparison_from_alignment,
    format_video_duration_label,
    intensity_levels,
)


def test_before_after_filenames_prefer_display_pair(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "target.jpg").write_bytes(b"x")
    (run / "preview_01.jpg").write_bytes(b"y")
    assert before_image_filename(run) == "target.jpg"
    assert after_image_filename(run) == "preview_01.jpg"
    (run / "target_display.jpg").write_bytes(b"display-before")
    (run / "preview_display.jpg").write_bytes(b"display-after")
    assert before_image_filename(run) == "target_display.jpg"
    assert after_image_filename(run) == "preview_display.jpg"


def test_comparison_from_alignment_prefers_display_size():
    out = comparison_from_alignment(
        {
            "target_size": [1254, 1254],
            "display_size": [780, 780],
            "object_position": "50% 37.1%",
        }
    )
    assert out == {"width": 780, "height": 780, "objectPosition": "50% 37.1%"}


def test_comparison_from_alignment_falls_back_to_target_size():
    assert comparison_from_alignment({}) is None
    out = comparison_from_alignment({"target_size": [1024, 1536]})
    assert out == {"width": 1024, "height": 1536}


def test_hints_when_transfer_skipped():
    hints = _hints_from_tutorial(None, average_baseline=False, transfer_skipped=True)
    assert hints[0]["title"] == "已跳过妆容生成"


def test_format_video_duration_label_uses_real_seconds():
    assert format_video_duration_label(45) == "约 45 秒"
    assert format_video_duration_label(89) == "约 1 分钟"
    assert format_video_duration_label(90) == "约 2 分钟"
    assert format_video_duration_label(0) == "约 15 分钟"
    assert format_video_duration_label(None) == "约 15 分钟"


def test_assemble_duration_ignores_estimated_time(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "target.jpg").write_bytes(b"x")
    (run / "preview_01.jpg").write_bytes(b"y")
    tutorial_path = tmp_path / "tutorial.json"
    tutorial_path.write_text(
        '{"duration": 89, "estimated_time": 9, "style_tags": [], "occasion_tags": []}',
        encoding="utf-8",
    )
    payload = assemble_makeup_preview(
        "task-1",
        tutorial_path=tutorial_path,
        preview_run_dir=run,
        preview_doc={"target": {"type": "average_baseline"}},
    )
    assert payload["duration"] == "约 1 分钟"
    assert payload["intensityLevels"] == intensity_levels()
    assert payload["palette"] == [level["color"] for level in INTENSITY_LEVELS]
    assert len(payload["intensityLevels"]) == 5
    assert payload["intensityLevels"][0]["opacity"] == 0.2
    assert payload["intensityLevels"][-1]["opacity"] == 1.0
