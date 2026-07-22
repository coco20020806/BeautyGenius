from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from makeup_preview.config import PreviewConfig, resolve_image_size
from makeup_preview.face_landmarks import FaceGeometry
from makeup_preview.preview_align import harmonize_preview_pair


def test_resolve_image_size_portrait():
    assert resolve_image_size(720, 1280) == "720*1280"


def test_resolve_image_size_landscape():
    assert resolve_image_size(1280, 720) == "1280*720"


def test_resolve_image_size_square():
    assert resolve_image_size(1000, 1000) == "1280*1280"


def test_resolve_image_size_invalid_defaults():
    assert resolve_image_size(0, 100, default="2K") == "2K"


def _fake_geom(w: int, h: int, lx: float, ly: float, rx: float, ry: float) -> FaceGeometry:
    class _Lm:
        def __init__(self, x: float, y: float):
            self.x = x
            self.y = y

    landmarks = [_Lm(0, 0)] * 300
    landmarks[33] = _Lm(lx / w, ly / h)
    landmarks[263] = _Lm(rx / w, ry / h)
    return FaceGeometry(
        width=w,
        height=h,
        left_eye=(lx, ly),
        right_eye=(rx, ry),
        roll_deg=0.0,
        landmarks=landmarks,
    )


@pytest.fixture
def preview_config(tmp_path: Path) -> PreviewConfig:
    skill = tmp_path / "skill"
    skill.mkdir()
    return PreviewConfig(api_key="test", skill_dir=skill)


def test_harmonize_resize_only_when_no_face(tmp_path: Path, preview_config: PreviewConfig):
    target = tmp_path / "target.jpg"
    preview = tmp_path / "preview_01.jpg"
    Image.new("RGB", (400, 600), color=(200, 180, 170)).save(target, format="JPEG")
    Image.new("RGB", (800, 800), color=(180, 160, 150)).save(preview, format="JPEG")

    with patch("makeup_preview.preview_align.detect_primary_face", return_value=None):
        with patch("makeup_preview.preview_align.create_face_landmarker") as mock_lm:
            mock_lm.return_value.close = lambda: None
            result = harmonize_preview_pair(target, preview, preview_config)

    assert result["method"] == "resize_only"
    assert "preview_align_fallback_resize_only" in result["warnings"]
    with Image.open(preview) as im:
        assert im.size == (400, 600)


def test_harmonize_landmark_path_resizes_to_target(tmp_path: Path, preview_config: PreviewConfig):
    target = tmp_path / "target.jpg"
    preview = tmp_path / "preview_01.jpg"
    Image.new("RGB", (500, 500), color=(210, 190, 180)).save(target, format="JPEG")
    Image.new("RGB", (1000, 1000), color=(190, 170, 160)).save(preview, format="JPEG")

    def _detect(path: Path, config, *, landmarker=None):
        with Image.open(path) as im:
            w, h = im.size
        mid_y = h * 0.44
        return _fake_geom(w, h, w * 0.36, mid_y, w * 0.64, mid_y)

    with patch("makeup_preview.preview_align.detect_primary_face", side_effect=_detect):
        with patch("makeup_preview.preview_align.create_face_landmarker") as mock_lm:
            mock_lm.return_value.close = lambda: None
            result = harmonize_preview_pair(target, preview, preview_config)

    assert result["method"] == "landmark_similarity"
    with Image.open(preview) as im:
        dw, dh = result["display_size"]
        assert im.size == (dw, dh)
    assert (tmp_path / "target_display.jpg").is_file()
    assert result.get("display_crop") is True
