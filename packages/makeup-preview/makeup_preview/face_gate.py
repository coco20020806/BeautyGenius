"""User photo L0/L1 validation (MediaPipe)."""

from __future__ import annotations

import math
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image

from makeup_preview.config import (
    FACE_AREA_RATIO_MAX,
    FACE_AREA_RATIO_MIN,
    FACE_LANDMARKER_URL,
    MAX_LONG_SIDE,
    MAX_PITCH_DEG,
    MAX_ROLL_DEG,
    MAX_USER_PHOTO_BYTES,
    MAX_YAW_DEG,
    MIN_FILE_BYTES,
    MIN_SHORT_SIDE,
    PreviewConfig,
)

# MediaPipe face mesh landmark indices (subset)
_IDX_LEFT_EYE = 33
_IDX_RIGHT_EYE = 263
_IDX_NOSE = 1
_IDX_MOUTH_L = 61
_IDX_MOUTH_R = 291


class FaceValidationError(Exception):
    def __init__(self, codes: list[str], l1: dict[str, Any] | None = None):
        self.codes = codes
        self.l1 = l1
        super().__init__(", ".join(codes))


_LIBGL_HINT = (
    "缺少系统库 libGL.so.1（MediaPipe/OpenCV 在无桌面 Linux 上需要）。"
    "Debian/Ubuntu 请执行: sudo apt-get install -y libgl1 libglib2.0-0"
    "（或 sudo bash scripts/install-linux-deps.sh），然后重启 API 服务。"
)


def reraise_if_libgl_missing(exc: BaseException) -> None:
    """If *exc* is the common headless OpenCV libGL error, raise a clearer RuntimeError."""
    msg = str(exc)
    if "libGL" in msg or "libgl.so" in msg.lower():
        raise RuntimeError(_LIBGL_HINT) from exc


def ensure_landmarker_model(config: PreviewConfig) -> Path:
    if config.landmarker_model_path and config.landmarker_model_path.is_file():
        return config.landmarker_model_path
    cache = config.skill_dir / ".cache"
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / "face_landmarker.task"
    if not dest.is_file():
        urllib.request.urlretrieve(FACE_LANDMARKER_URL, dest)
    return dest


def l0_check(path: Path, max_bytes: int) -> tuple[int, int]:
    if not path.is_file():
        raise FaceValidationError(["UNREADABLE_IMAGE"])
    size = path.stat().st_size
    if size < MIN_FILE_BYTES:
        raise FaceValidationError(["UNREADABLE_IMAGE"])
    if size > max_bytes:
        raise FaceValidationError(["FILE_TOO_LARGE"])
    suffix = path.suffix.lower()
    if suffix not in (".jpg", ".jpeg", ".png", ".webp"):
        raise FaceValidationError(["INVALID_FORMAT"])
    try:
        with Image.open(path) as im:
            w, h = im.size
            im.verify()
    except OSError:
        raise FaceValidationError(["UNREADABLE_IMAGE"]) from None
    with Image.open(path) as im:
        w, h = im.size
    short, long = min(w, h), max(w, h)
    if short < MIN_SHORT_SIDE or long > MAX_LONG_SIDE:
        raise FaceValidationError(["RESOLUTION_OUT_OF_RANGE"])
    return w, h


def _lm_xy(landmarks: Any, idx: int, w: int, h: int) -> tuple[float, float]:
    lm = landmarks[idx]
    return lm.x * w, lm.y * h


def _estimate_pose_deg(
    landmarks: Any, w: int, h: int
) -> tuple[float, float, float, float]:
    lx, ly = _lm_xy(landmarks, _IDX_LEFT_EYE, w, h)
    rx, ry = _lm_xy(landmarks, _IDX_RIGHT_EYE, w, h)
    nx, ny = _lm_xy(landmarks, _IDX_NOSE, w, h)
    roll = math.degrees(math.atan2(ry - ly, rx - lx))
    eye_mid_x = (lx + rx) / 2
    eye_mid_y = (ly + ry) / 2
    inter_eye = max(math.hypot(rx - lx, ry - ly), 1.0)
    yaw = math.degrees(math.atan2(nx - eye_mid_x, inter_eye)) * 2
    pitch = math.degrees(math.atan2(ny - eye_mid_y, inter_eye)) * 2
    xs = [landmarks[i].x * w for i in range(len(landmarks))]
    ys = [landmarks[i].y * h for i in range(len(landmarks))]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    area_ratio = (x1 - x0) * (y1 - y0) / (w * h)
    return yaw, pitch, roll, area_ratio


def _landmarks_in_frame(landmarks: Any, w: int, h: int) -> bool:
    for idx in (_IDX_NOSE, _IDX_LEFT_EYE, _IDX_RIGHT_EYE, _IDX_MOUTH_L, _IDX_MOUTH_R):
        x, y = _lm_xy(landmarks, idx, w, h)
        if x < 0 or y < 0 or x > w or y > h:
            return False
    return True


def l1_mediapipe(path: Path, config: PreviewConfig) -> dict[str, Any]:
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
    except (ImportError, OSError) as e:
        reraise_if_libgl_missing(e)
        raise

    model_path = ensure_landmarker_model(config)
    w, h = l0_check(path, config.max_user_photo_bytes)

    try:
        base_options = mp_python.BaseOptions(model_asset_path=str(model_path))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=2,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        landmarker = vision.FaceLandmarker.create_from_options(options)

        mp_image = mp.Image.create_from_file(str(path))
        result = landmarker.detect(mp_image)
    except (ImportError, OSError) as e:
        reraise_if_libgl_missing(e)
        raise
    n = len(result.face_landmarks or [])
    if n == 0:
        raise FaceValidationError(["NO_FACE"])
    if n > 1:
        raise FaceValidationError(["MULTIPLE_FACES"])

    lm = result.face_landmarks[0]
    if not _landmarks_in_frame(lm, w, h):
        raise FaceValidationError(["FACE_CROPPED"])

    yaw, pitch, roll, area_ratio = _estimate_pose_deg(lm, w, h)
    l1 = {
        "yaw_deg": round(yaw, 2),
        "pitch_deg": round(pitch, 2),
        "roll_deg": round(roll, 2),
        "face_area_ratio": round(area_ratio, 4),
        "width": w,
        "height": h,
    }
    codes: list[str] = []
    if area_ratio < FACE_AREA_RATIO_MIN:
        codes.append("FACE_TOO_SMALL")
    if area_ratio > FACE_AREA_RATIO_MAX:
        codes.append("FACE_TOO_LARGE")
    if abs(yaw) > MAX_YAW_DEG:
        codes.append("YAW_TOO_LARGE")
    if abs(pitch) > MAX_PITCH_DEG:
        codes.append("PITCH_NOT_EYE_LEVEL")
    if abs(roll) > MAX_ROLL_DEG:
        codes.append("ROLL_TOO_LARGE")
    if codes:
        raise FaceValidationError(codes, l1=l1)
    return l1


def run_l0_l1(path: Path, config: PreviewConfig) -> dict[str, Any]:
    l0_check(path, config.max_user_photo_bytes)
    return l1_mediapipe(path, config)
