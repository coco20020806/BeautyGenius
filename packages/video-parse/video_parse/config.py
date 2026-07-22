"""Parse job configuration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "v2"
CONTRACT_VERSION_V21 = "v2.1"
TAXONOMY_VERSION = "v1"

ProgressCallback = Callable[[int, str], None]


@dataclass
class ParseConfig:
    api_key: str
    skill_dir: Path
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    vision_model: str = "qwen3.7-plus"
    asr_model: str = "fun-asr"
    repair_model: str = "qwen3.7-plus"
    max_upload_bytes: int = 100 * 1024 * 1024
    video_fps: float = 1.5
    ffmpeg_path: str | None = None
    ffprobe_path: str | None = None
    # full：开启 L2 关键帧 QA；fast：跳过 L2（仍 L1 抽帧）
    mode: str = "full"
    enable_keyframe_qa: bool = True
    enable_replication_refs: bool = True
    on_progress: ProgressCallback | None = field(default=None, repr=False)


@dataclass
class ParseJobResult:
    run_dir: Path
    analysis_path: Path
    analysis: dict[str, Any]
    meta: dict[str, Any]
    coverage_path: Path
    keyframe_qa_path: Path | None
