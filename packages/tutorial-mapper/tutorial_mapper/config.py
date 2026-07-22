"""Mapper job configuration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ProgressCallback = Callable[[int, str], None]


@dataclass
class MapperConfig:
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    text_model: str = "qwen3.5-flash"
    vision_model: str = "qwen3.7-plus"
    repair_model: str = "qwen3.5-flash"
    ffmpeg_path: str | None = None
    enable_text_enrich: bool = True
    enable_vision_enrich: bool = True
    short_instruction_chars: int = 10
    clip_extract_sec: float = 3.0
    on_progress: ProgressCallback | None = field(default=None, repr=False)


@dataclass
class MapperJobResult:
    parse_run_dir: Path
    tutorial_path: Path
    tutorial: dict[str, Any]
    enrichment_meta_path: Path
    enrichment_meta: dict[str, Any]
