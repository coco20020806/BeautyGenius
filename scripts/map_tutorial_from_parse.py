#!/usr/bin/env python3
"""CLI: map a beauty-video-parse run to tutorial.json."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from tutorial_mapper import MapperConfig, run_mapper_job
from tutorial_mapper.step_validation import format_step_validation_summary

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

_QUIET_TRUTHY = frozenset({"1", "true", "yes", "on"})


def load_api_key() -> str:
    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if key:
        return key
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        from _qwen_local import DASHSCOPE_API_KEY  # type: ignore

        return DASHSCOPE_API_KEY.strip()
    except ImportError:
        return ""


def _env_quiet() -> bool:
    return os.environ.get("BEAUTY_PARSE_QUIET", "").strip().lower() in _QUIET_TRUTHY


def main() -> None:
    parser = argparse.ArgumentParser(
        description="将 beauty-video-parse 的 analysis.json 映射为 Tutorial/Step/Asset"
    )
    parser.add_argument(
        "--parse-run",
        required=True,
        help="parse run 目录（含 analysis.json）",
    )
    parser.add_argument(
        "--skip-text-enrich",
        action="store_true",
        help="跳过文本 LLM enrichment（仅确定性映射）",
    )
    parser.add_argument(
        "--skip-vision-enrich",
        action="store_true",
        help="跳过关键帧/视觉 enrichment",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="关闭 stderr 进度",
    )
    args = parser.parse_args()

    parse_run = Path(args.parse_run)
    if not parse_run.is_absolute():
        parse_run = (REPO_ROOT / parse_run).resolve()

    need_api = not (args.skip_text_enrich and args.skip_vision_enrich)
    api_key = load_api_key()
    if need_api and not api_key:
        sys.stderr.write(
            "缺少 DASHSCOPE_API_KEY：请设置环境变量或创建 scripts/_qwen_local.py；"
            "或同时使用 --skip-text-enrich --skip-vision-enrich\n"
        )
        sys.exit(1)

    quiet = bool(args.quiet) or _env_quiet()
    on_progress = None
    if not quiet:
        t0 = time.monotonic()

        def on_progress(stage: int, message: str) -> None:
            elapsed = time.monotonic() - t0
            sys.stderr.write(f"[{stage}/7] {message} ({elapsed:.0f}s)\n")
            sys.stderr.flush()

    config = MapperConfig(
        api_key=api_key,
        enable_text_enrich=not args.skip_text_enrich,
        enable_vision_enrich=not args.skip_vision_enrich,
        on_progress=on_progress,
    )
    result = run_mapper_job(parse_run, config)
    block = result.enrichment_meta.get("tutorial_step_validation") or {}
    if not quiet and block:
        sys.stderr.write(format_step_validation_summary(block) + "\n")
        if not block.get("pass"):
            sys.stderr.write(
                "tutorial_step_validation 未通过，仍已写入 tutorial.json；"
                "详见 enrichment_meta.json\n"
            )
        sys.stderr.flush()
    print(str(result.tutorial_path))


if __name__ == "__main__":
    main()
