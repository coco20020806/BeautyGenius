#!/usr/bin/env python3
"""CLI for KOL makeup preview (kol-makeup-preview skill)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from makeup_preview import PreviewConfig, StrictReplicationError, UserPhotoRejected, run_preview_job

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SKILL = REPO_ROOT / "skills" / "kol-makeup-preview"


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
    parser = argparse.ArgumentParser(description="KOL 整妆个人预览")
    parser.add_argument("--parse-run", help="beauty-video-parse run 目录")
    parser.add_argument("--reference-image", help="手动 KOL 参考妆面图")
    parser.add_argument("--user-photo", help="用户正脸自拍")
    parser.add_argument(
        "--use-baseline",
        action="store_true",
        help="使用 Skill 内平均脸底图（不上传用户照）",
    )
    parser.add_argument(
        "--baseline",
        choices=("female", "male"),
        default="female",
        help="平均脸性别（默认 female）",
    )
    parser.add_argument("--reference-step", help="从 parse run 指定 step_name 选参考帧")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="仅质检用户照片，不生成预览",
    )
    parser.add_argument(
        "--skip-transfer",
        action="store_true",
        help="拷贝 reference/target 但不调用 wan 图像生成",
    )
    parser.add_argument(
        "--strict-replication",
        action="store_true",
        help="v2.1 复刻参考未通过 pair/after 验证时中止",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/makeup-preview",
        help="输出根目录（相对仓库根）",
    )
    args = parser.parse_args()

    parse_run = Path(args.parse_run).resolve() if args.parse_run else None
    reference_image = Path(args.reference_image).resolve() if args.reference_image else None
    user_photo = Path(args.user_photo).resolve() if args.user_photo else None
    output_root = (REPO_ROOT / args.output_root).resolve()

    config = PreviewConfig(
        api_key=load_api_key(),
        skill_dir=DEFAULT_SKILL,
    )

    try:
        result = run_preview_job(
            parse_run_dir=parse_run,
            reference_image=reference_image,
            user_photo=user_photo,
            use_baseline=args.use_baseline,
            baseline=args.baseline,
            reference_step=args.reference_step,
            output_root=output_root,
            config=config,
            validate_only=args.validate_only,
            skip_transfer=args.skip_transfer,
            strict_replication=args.strict_replication,
        )
    except UserPhotoRejected as e:
        sys.stderr.write((e.qa_doc.get("reason") or "用户照片未通过质检") + "\n")
        sys.exit(1)
    except StrictReplicationError as e:
        sys.stderr.write(f"strict-replication: {e}\n")
        sys.exit(3)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(2)

    print(result.run_dir)
    print(result.preview_path)
    ref = result.preview.get("reference") or {}
    tier = ref.get("reference_tier") or ref.get("source")
    if tier:
        sys.stderr.write(f"reference_tier: {tier}\n")
    if result.preview.get("outputs"):
        for item in result.preview["outputs"]:
            print(result.run_dir / item["filename"])


if __name__ == "__main__":
    main()
