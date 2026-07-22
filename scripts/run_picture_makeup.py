#!/usr/bin/env python3
"""CLI for picture-makeup step diagrams."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from picture_makeup import PictureMakeupConfig, run_picture_makeup_job

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SKILL = REPO_ROOT / "skills" / "picture_makeup"


def load_api_key() -> str:
    import os

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
    sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description="教程步骤模块图示（picture-makeup）")
    parser.add_argument("--parse-run", required=True, help="含 tutorial.json 与 keyframes 的 run 目录")
    parser.add_argument(
        "--tutorial",
        help="tutorial.json 路径（默认 parse-run/tutorial.json）",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/picture-makeup",
        help="输出根目录（相对仓库根）",
    )
    parser.add_argument(
        "--step-id",
        action="append",
        dest="step_ids",
        help="仅处理指定 step_id（可重复）",
    )
    parser.add_argument(
        "--skip-diagram",
        action="store_true",
        help="仅生成 prompt，不调用 wan",
    )
    args = parser.parse_args()

    parse_run = Path(args.parse_run).resolve()
    tutorial_path = Path(args.tutorial).resolve() if args.tutorial else parse_run / "tutorial.json"
    output_root = (REPO_ROOT / args.output_root).resolve()

    config = PictureMakeupConfig(
        api_key=load_api_key(),
        skill_dir=DEFAULT_SKILL,
        skip_diagram=args.skip_diagram,
    )

    try:
        result = run_picture_makeup_job(
            parse_run_dir=parse_run,
            tutorial_path=tutorial_path,
            output_root=output_root,
            config=config,
            step_ids=args.step_ids,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(2)

    print(result.run_dir)
    print(result.manifest_path)


if __name__ == "__main__":
    main()
