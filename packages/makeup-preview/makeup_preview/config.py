"""Preview job configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

CONTRACT_VERSION = "v1"
PROMPT_VERSION = "v2"  # default when tutorial before is available; pipeline writes actual v1|v2
PROMPT_TEXT_VERSION_DEFAULT = "wan-long-1"

BaselineGender = Literal["female", "male"]

# face-validation.md
MIN_FILE_BYTES = 4 * 1024
MAX_USER_PHOTO_BYTES = 8 * 1024 * 1024
MIN_SHORT_SIDE = 480
MAX_LONG_SIDE = 4096
FACE_AREA_RATIO_MIN = 0.08
FACE_AREA_RATIO_MAX = 0.75
MAX_YAW_DEG = 15.0
MAX_PITCH_DEG = 15.0
MAX_ROLL_DEG = 10.0
MAX_UPLOAD_LONG_SIDE = 2048

PREFERRED_PRIMARIES = ("定妆", "唇妆", "眼妆", "底妆", "遮瑕")

FACE_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)

TRANSFER_PROMPT_V1 = (
    "图1为美妆教程中的完成妆面参考。图2为需要上妆的人脸。请将图1的**完整妆容风格**"
    "（唇色、眼妆、腮红、修容等）自然迁移到图2上，**保持图2的身份特征、脸型与发型不变**，"
    "光照与肤色协调，真实美妆照片效果，不要换脸，不要改变图2的五官结构。"
)

TRANSFER_PROMPT_V2 = (
    "图1为美妆教程中的**完成妆面**参考。图2为同一教程中的**妆前/素颜对照**"
    "（用于区分妆面变化，勿把图2当作上妆目标）。图3为需要上妆的人脸。"
    "请将图1相对图2所体现的**完整妆容风格**（唇色、眼妆、腮红、修容等）自然迁移到图3上，"
    "**保持图3的身份特征、脸型与发型不变**，光照与肤色协调，真实美妆照片效果，"
    "不要换脸，不要改变图3的五官结构。"
)

# wan2.7-image-pro size strings (fixed aspect presets + 2K fallback)
SUPPORTED_IMAGE_SIZES: list[tuple[str, int, int]] = [
    ("1280*1280", 1.0, 1280),
    ("1280*720", 16 / 9, 1280),
    ("720*1280", 9 / 16, 720),
    ("1024*1024", 1.0, 1024),
    ("2K", 0.0, 0),
]


def resolve_image_size(width: int, height: int, *, default: str = "2K") -> str:
    """Pick API size string closest to target aspect ratio."""
    if width <= 0 or height <= 0:
        return default
    aspect = width / height
    best = default
    best_delta = float("inf")
    for label, ratio, _long in SUPPORTED_IMAGE_SIZES:
        if label == "2K":
            continue
        delta = abs(aspect - ratio)
        if delta < best_delta:
            best_delta = delta
            best = label
    if best_delta > 0.35:
        return default
    return best


@dataclass
class PreviewConfig:
    api_key: str
    skill_dir: Path
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    vision_model: str = "qwen3.7-plus"
    image_model: str = "wan2.7-image-pro"
    image_size: str = "2K"
    image_watermark: bool = False
    landmarker_model_path: Path | None = None
    max_user_photo_bytes: int = MAX_USER_PHOTO_BYTES


@dataclass
class PreviewJobResult:
    run_dir: Path
    preview_path: Path
    preview: dict[str, Any]
    meta: dict[str, Any]
    validation_pass: bool | None = None
