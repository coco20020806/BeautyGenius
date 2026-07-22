"""Picture makeup job configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "v1"
PROMPT_TEXT_VERSION_DEFAULT = "diagram-2"

SUPPORTED_IMAGE_SIZES: list[tuple[str, int, int]] = [
    ("1280*1280", 1.0, 1280),
    ("1280*720", 16 / 9, 1280),
    ("720*1280", 9 / 16, 720),
    ("1024*1024", 1.0, 1024),
    ("2K", 0.0, 0),
]


def resolve_image_size(width: int, height: int, *, default: str = "2K") -> str:
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
class PictureMakeupConfig:
    api_key: str
    skill_dir: Path
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    text_model: str = "qwen3.7-plus"
    vision_model: str = "qwen3.7-plus"
    image_model: str = "wan2.7-image-pro"
    image_size: str = "2K"
    image_watermark: bool = False
    skip_diagram: bool = False


@dataclass
class PictureMakeupJobResult:
    run_dir: Path
    manifest: dict[str, Any]
    manifest_path: Path
