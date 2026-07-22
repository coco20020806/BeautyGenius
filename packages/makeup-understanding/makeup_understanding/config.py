"""Job configuration for makeup-understanding."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ProgressCallback = Callable[[int, str], None]


@dataclass
class UnderstandingConfig:
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    text_model: str = "qwen3.7-plus"
    repair_model: str = "qwen3.7-plus"
    enabled: bool = True
    on_progress: ProgressCallback | None = field(default=None, repr=False)


@dataclass
class UnderstandingJobResult:
    parse_run_dir: Path
    tutorial_path: Path
    tutorial: dict[str, Any]
    meta_path: Path
    meta: dict[str, Any]
