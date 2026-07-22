"""Parse job configuration."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "v2"
CONTRACT_VERSION_V21 = "v2.1"
TAXONOMY_VERSION = "v1"

ProgressCallback = Callable[[int, str], None]

# (scale, preset, crf)
CompressAttempt = tuple[str, str, int]


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
    # 上传代理压缩：None 表示按 mode 默认，可用环境变量覆盖
    compress_preset: str | None = None
    compress_scale: str | None = None
    compress_crf: int | None = None
    compress_max_attempts: int = 2
    on_progress: ProgressCallback | None = field(default=None, repr=False)


@dataclass
class ParseJobResult:
    run_dir: Path
    analysis_path: Path
    analysis: dict[str, Any]
    meta: dict[str, Any]
    coverage_path: Path
    keyframe_qa_path: Path | None


def _env_str(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def _env_int(name: str) -> int | None:
    raw = _env_str(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def resolve_compress_plan(config: ParseConfig) -> list[CompressAttempt]:
    """Build up to N compress attempts for upload_proxy.

    Mode defaults:
      fast — (-2:480, ultrafast, 28) then (-2:360, ultrafast, 32)
      full — (-2:720, veryfast, 28) then (-2:480, veryfast, 32)

    Config fields / env (PARSE_COMPRESS_*) override the first attempt only;
    the second attempt keeps the built-in step-down when max_attempts >= 2.
    """
    mode = (config.mode or "full").lower()
    if mode == "fast":
        first: CompressAttempt = ("-2:480", "ultrafast", 28)
        second: CompressAttempt = ("-2:360", "ultrafast", 32)
    else:
        first = ("-2:720", "veryfast", 28)
        second = ("-2:480", "veryfast", 32)

    scale = config.compress_scale or _env_str("PARSE_COMPRESS_SCALE") or first[0]
    preset = config.compress_preset or _env_str("PARSE_COMPRESS_PRESET") or first[1]
    env_crf = _env_int("PARSE_COMPRESS_CRF")
    if config.compress_crf is not None:
        crf = config.compress_crf
    elif env_crf is not None:
        crf = env_crf
    else:
        crf = first[2]
    first = (scale, preset, int(crf))

    env_max = _env_int("PARSE_COMPRESS_MAX_ATTEMPTS")
    max_attempts = env_max if env_max is not None else config.compress_max_attempts
    max_attempts = max(1, min(int(max_attempts), 2))

    plan: list[CompressAttempt] = [first]
    if max_attempts >= 2:
        # Keep step-down scale/crf; reuse overridden preset from first attempt.
        plan.append((second[0], first[1], second[2]))
    return plan
