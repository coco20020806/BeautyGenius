"""Relaxed face-validation thresholds and L2 soft-pass behavior."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import makeup_preview.config as config
from makeup_preview.config import PreviewConfig
from makeup_preview.face_qa import FACE_QA_PROMPT, run_face_qa


def test_l1_thresholds_are_relaxed() -> None:
    assert config.MAX_YAW_DEG == 25.0
    assert config.MAX_PITCH_DEG == 25.0
    assert config.MAX_ROLL_DEG == 20.0
    assert config.FACE_AREA_RATIO_MIN == 0.05


def test_face_qa_prompt_allows_makeup() -> None:
    assert "素颜" not in FACE_QA_PROMPT
    assert "淡妆" in FACE_QA_PROMPT or "美颜" in FACE_QA_PROMPT


def test_run_face_qa_soft_passes_on_api_failure(tmp_path: Path) -> None:
    photo = tmp_path / "user.jpg"
    photo.write_bytes(b"fake")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    cfg = PreviewConfig(api_key="test", skill_dir=tmp_path)

    bad = SimpleNamespace(status_code=500, message="timeout")
    with patch("makeup_preview.face_qa.MultiModalConversation.call", return_value=bad):
        with patch("makeup_preview.face_qa.to_file_uri", return_value="file:///x.jpg"):
            result = run_face_qa(photo, cfg, run_dir)

    assert result["pass"] is True
    assert result["l2_soft_pass"] is True
    assert "已放行" in result["reason"]
    assert (run_dir / "face_qa_error.txt").is_file()


def test_run_face_qa_soft_passes_on_invalid_json(tmp_path: Path) -> None:
    photo = tmp_path / "user.jpg"
    photo.write_bytes(b"fake")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    cfg = PreviewConfig(api_key="test", skill_dir=tmp_path)

    ok_resp = SimpleNamespace(
        status_code=HTTPStatus.OK,
        output=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="not-json{{{"))]
        ),
    )
    with patch("makeup_preview.face_qa.MultiModalConversation.call", return_value=ok_resp):
        with patch("makeup_preview.face_qa.to_file_uri", return_value="file:///x.jpg"):
            result = run_face_qa(photo, cfg, run_dir)

    assert result["pass"] is True
    assert result["l2_soft_pass"] is True
    assert "已放行" in result["reason"]


def test_run_face_qa_accepts_suitable_with_makeup_fields(tmp_path: Path) -> None:
    photo = tmp_path / "user.jpg"
    photo.write_bytes(b"fake")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    cfg = PreviewConfig(api_key="test", skill_dir=tmp_path)

    payload = (
        '{"is_frontal":true,"is_eye_level":true,"occlusion_ok":true,'
        '"lighting_ok":true,"suitable_as_makeup_target":true,"pass":true,'
        '"reason":"已淡妆，仍可用作底图"}'
    )
    ok_resp = SimpleNamespace(
        status_code=HTTPStatus.OK,
        output=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=payload))]
        ),
    )
    with patch("makeup_preview.face_qa.MultiModalConversation.call", return_value=ok_resp):
        with patch("makeup_preview.face_qa.to_file_uri", return_value="file:///x.jpg"):
            result = run_face_qa(photo, cfg, run_dir)

    assert result["pass"] is True
    assert result.get("l2_soft_pass") is not True
    assert result["suitable_as_makeup_target"] is True
