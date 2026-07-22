"""Optimization job configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "visual-opt.v1"


@dataclass
class OptimizationConfig:
    api_key: str
    skill_dir: Path
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    text_model: str = "qwen3.7-plus"


@dataclass
class OptimizationJobResult:
    run_dir: Path
    optimized_tutorial_path: Path
    optimization: dict[str, Any]
    manifest: dict[str, Any]
    manifest_path: Path
