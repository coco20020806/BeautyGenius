#!/usr/bin/env python3
"""Thin CLI for beauty tutorial video parsing."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from video_parse import ParseConfig, run_parse_job

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SKILL = REPO_ROOT / "skills" / "beauty-video-parse"

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
        pass
    sys.stderr.write(
        "缺少 DASHSCOPE_API_KEY：请设置环境变量或创建 scripts/_qwen_local.py\n"
    )
    sys.exit(1)


def _env_quiet() -> bool:
    return os.environ.get("BEAUTY_PARSE_QUIET", "").strip().lower() in _QUIET_TRUTHY


def main() -> None:
    parser = argparse.ArgumentParser(description="解析美妆教程视频")
    parser.add_argument("--video", required=True, help="本地视频路径")
    parser.add_argument(
        "--output-root",
        default="outputs/runs",
        help="输出根目录（相对仓库根，默认 outputs/runs）",
    )
    parser.add_argument(
        "--mode",
        choices=("full", "fast"),
        default="full",
        help="full=开启 L2 关键帧 QA（默认）；fast=跳过 L2（仍 L1 抽帧）",
    )
    parser.add_argument(
        "--skip-keyframe-qa",
        action="store_true",
        help="跳过 L2 关键帧视觉质检（仍执行 L1 抽帧；与 --mode fast 等价叠加）",
    )
    parser.add_argument(
        "--skip-replication-refs",
        action="store_true",
        help="跳过片尾复刻参考对（契约保持 v2）",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="关闭 stderr 阶段进度（也可用 BEAUTY_PARSE_QUIET=1）",
    )
    args = parser.parse_args()

    quiet = bool(args.quiet) or _env_quiet()
    on_progress = None
    if not quiet:
        t0 = time.monotonic()

        def on_progress(stage: int, message: str) -> None:
            elapsed = time.monotonic() - t0
            sys.stderr.write(f"[{stage}/10] {message} ({elapsed:.0f}s)\n")
            sys.stderr.flush()

    # mode=fast 或显式 --skip-keyframe-qa 任一为真则关 L2
    enable_keyframe_qa = not (args.mode == "fast" or args.skip_keyframe_qa)
    if not quiet:
        sys.stderr.write(
            f"mode={args.mode}"
            f"（L2 关键帧 QA={'开' if enable_keyframe_qa else '关'}）\n"
        )
        sys.stderr.flush()

    video_path = Path(args.video)
    output_root = (REPO_ROOT / args.output_root).resolve()
    config = ParseConfig(
        api_key=load_api_key(),
        skill_dir=DEFAULT_SKILL,
        mode=args.mode,
        enable_keyframe_qa=enable_keyframe_qa,
        enable_replication_refs=not args.skip_replication_refs,
        on_progress=on_progress,
    )

    result = run_parse_job(video_path, output_root, config=config)
    print(result.run_dir)
    print(result.analysis_path)
    print(result.meta.get("keyframe_qa"))
    if result.meta.get("replication_refs") is not None:
        print(result.meta.get("replication_refs"))


if __name__ == "__main__":
    main()
