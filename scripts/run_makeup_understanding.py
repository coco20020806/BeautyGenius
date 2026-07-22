#!/usr/bin/env python3
"""CLI: run makeup-understanding on a parse run's tutorial.json."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


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
    raise RuntimeError("缺少 DASHSCOPE_API_KEY")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract display_product / technique for tutorial steps")
    parser.add_argument("--parse-run", required=True, help="parse run 目录（含 tutorial.json）")
    args = parser.parse_args()
    parse_run = Path(args.parse_run)
    if not parse_run.is_absolute():
        parse_run = (REPO_ROOT / parse_run).resolve()

    from makeup_understanding import UnderstandingConfig, run_understanding_job

    def on_progress(stage: int, message: str) -> None:
        print(f"[{stage}] {message}", file=sys.stderr)

    result = run_understanding_job(
        parse_run,
        UnderstandingConfig(api_key=load_api_key(), on_progress=on_progress),
    )
    print(result.tutorial_path)
    print(result.meta_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
