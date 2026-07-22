"""Relaxed face landmark detection for preview alignment."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from makeup_preview.config import PreviewConfig
from makeup_preview.face_gate import (
    _IDX_LEFT_EYE,
    _IDX_RIGHT_EYE,
    _lm_xy,
    ensure_landmarker_model,
    reraise_if_libgl_missing,
)


@dataclass(frozen=True)
class FaceGeometry:
    width: int
    height: int
    left_eye: tuple[float, float]
    right_eye: tuple[float, float]
    roll_deg: float
    landmarks: Any


def _estimate_roll_deg(landmarks: Any, w: int, h: int) -> float:
    lx, ly = _lm_xy(landmarks, _IDX_LEFT_EYE, w, h)
    rx, ry = _lm_xy(landmarks, _IDX_RIGHT_EYE, w, h)
    return math.degrees(math.atan2(ry - ly, rx - lx))


def _face_bbox(landmarks: Any, w: int, h: int) -> tuple[float, float, float, float]:
    xs = [landmarks[i].x * w for i in range(len(landmarks))]
    ys = [landmarks[i].y * h for i in range(len(landmarks))]
    return min(xs), min(ys), max(xs), max(ys)


def create_face_landmarker(config: PreviewConfig):
    try:
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        model_path = ensure_landmarker_model(config)
        base_options = mp_python.BaseOptions(model_asset_path=str(model_path))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=2,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        return vision.FaceLandmarker.create_from_options(options)
    except (ImportError, OSError) as e:
        reraise_if_libgl_missing(e)
        raise


def detect_primary_face(
    path: Path,
    config: PreviewConfig,
    *,
    landmarker=None,
) -> FaceGeometry | None:
    if not path.is_file():
        return None
    try:
        import mediapipe as mp
    except (ImportError, OSError) as e:
        reraise_if_libgl_missing(e)
        raise

    close_landmarker = False
    if landmarker is None:
        landmarker = create_face_landmarker(config)
        close_landmarker = True
    try:
        try:
            with Image.open(path) as im:
                w, h = im.size
            mp_image = mp.Image.create_from_file(str(path))
            result = landmarker.detect(mp_image)
        except (ImportError, OSError) as e:
            reraise_if_libgl_missing(e)
            raise
        n = len(result.face_landmarks or [])
        if n != 1:
            return None
        lm = result.face_landmarks[0]
        lx, ly = _lm_xy(lm, _IDX_LEFT_EYE, w, h)
        rx, ry = _lm_xy(lm, _IDX_RIGHT_EYE, w, h)
        roll = _estimate_roll_deg(lm, w, h)
        return FaceGeometry(
            width=w,
            height=h,
            left_eye=(lx, ly),
            right_eye=(rx, ry),
            roll_deg=roll,
            landmarks=lm,
        )
    finally:
        if close_landmarker:
            landmarker.close()


def face_square_crop_box(
    geom: FaceGeometry,
    *,
    padding_factor: float = 1.35,
) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) square crop clamped to image."""
    w, h = geom.width, geom.height
    x0, y0, x1, y1 = _face_bbox(geom.landmarks, w, h)
    face_h = max(y1 - y0, 1.0)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    side = face_h * padding_factor
    side = max(side, x1 - x0, y1 - y0)
    half = side / 2
    left = int(round(cx - half))
    top = int(round(cy - half))
    right = int(round(cx + half))
    bottom = int(round(cy + half))
    if right - left > w:
        left, right = 0, w
    if bottom - top > h:
        top, bottom = 0, h
    left = max(0, left)
    top = max(0, top)
    right = min(w, right)
    bottom = min(h, bottom)
    cw, ch = right - left, bottom - top
    if cw <= 0 or ch <= 0:
        return 0, 0, w, h
    if cw != ch:
        side_i = min(cw, ch)
        cx_i = (left + right) // 2
        cy_i = (top + bottom) // 2
        left = max(0, cx_i - side_i // 2)
        top = max(0, cy_i - side_i // 2)
        right = min(w, left + side_i)
        bottom = min(h, top + side_i)
        if right - left < side_i:
            left = max(0, right - side_i)
        if bottom - top < side_i:
            top = max(0, bottom - side_i)
    return left, top, right, bottom


def eye_midpoint(geom: FaceGeometry) -> tuple[float, float]:
    return (
        (geom.left_eye[0] + geom.right_eye[0]) / 2,
        (geom.left_eye[1] + geom.right_eye[1]) / 2,
    )


def inter_eye_distance(geom: FaceGeometry) -> float:
    lx, ly = geom.left_eye
    rx, ry = geom.right_eye
    return max(math.hypot(rx - lx, ry - ly), 1.0)


def face_bbox(geom: FaceGeometry) -> tuple[float, float, float, float]:
    return _face_bbox(geom.landmarks, geom.width, geom.height)


def face_height(geom: FaceGeometry) -> float:
    x0, y0, x1, y1 = face_bbox(geom)
    return max(y1 - y0, 1.0)
