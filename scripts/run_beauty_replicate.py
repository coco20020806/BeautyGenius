#!/usr/bin/env python3
"""End-to-end: beauty video parse → tutorial map → KOL makeup preview."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from makeup_preview import PreviewConfig, StrictReplicationError, UserPhotoRejected, run_preview_job
from makeup_understanding import UnderstandingConfig, run_understanding_job
from tutorial_mapper import MapperConfig, run_mapper_job
from video_parse import ParseConfig, run_parse_job

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PARSE_SKILL = REPO_ROOT / "skills" / "beauty-video-parse"
PREVIEW_SKILL = REPO_ROOT / "skills" / "kol-makeup-preview"

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
    sys.exit(2)


def _env_quiet() -> bool:
    return os.environ.get("BEAUTY_PARSE_QUIET", "").strip().lower() in _QUIET_TRUTHY


def write_manifest(
    job_dir: Path,
    *,
    parse_run_dir: Path | None,
    preview_run_dir: Path | None,
    preview: dict | None,
    tutorial_path: Path | None = None,
    tutorial_id: str | None = None,
) -> Path:
    job_dir.mkdir(parents=True, exist_ok=True)
    upstream = None
    target = None
    if preview:
        ref = preview.get("reference") or {}
        upstream = {
            "tier": ref.get("reference_tier"),
            "filename": ref.get("filename"),
            "parse_contract_version": ref.get("parse_contract_version"),
            "replication_pair_pass": ref.get("replication_pair_pass"),
        }
        target = preview.get("target")
    doc = {
        "job_version": "1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parse_run_dir": str(parse_run_dir.resolve()) if parse_run_dir else None,
        "preview_run_dir": str(preview_run_dir.resolve()) if preview_run_dir else None,
        "tutorial_path": str(tutorial_path.resolve()) if tutorial_path else None,
        "tutorial_id": tutorial_id,
        "upstream_reference": upstream,
        "target": target,
    }
    path = job_dir / "manifest.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="视频解析 → Tutorial 映射 → 妆容预览 串联")
    parser.add_argument("--video", help="美妆教程视频（与 --parse-run 二选一）")
    parser.add_argument("--parse-run", help="已有 parse run，跳过解析")
    parser.add_argument("--user-photo", help="用户正脸自拍")
    parser.add_argument("--use-baseline", action="store_true", help="使用平均脸底图")
    parser.add_argument(
        "--baseline",
        choices=("female", "male"),
        default="female",
    )
    parser.add_argument("--reference-step", help="指定 parse 步骤选参考帧")
    parser.add_argument("--reference-image", help="手动参考妆面图（覆盖 parse 选帧）")
    parser.add_argument("--skip-preview", action="store_true", help="仅解析（+可选 Tutorial 映射）")
    parser.add_argument("--skip-transfer", action="store_true", help="预览但不调 wan 图像生成")
    parser.add_argument("--strict-replication", action="store_true")
    parser.add_argument(
        "--mode",
        choices=("full", "fast"),
        default="full",
        help="parse 模式：full=L2 关键帧 QA；fast=跳过 L2。"
        "fast 时 Tutorial 映射仅确定性（关 enrich）",
    )
    parser.add_argument(
        "--skip-keyframe-qa",
        action="store_true",
        help="跳过 L2 关键帧 QA（与 --mode fast 叠加；仅 --video 时生效）",
    )
    parser.add_argument(
        "--skip-replication-refs",
        action="store_true",
        help="跳过片尾复刻参考对（仅 --video 时生效）",
    )
    parser.add_argument(
        "--skip-tutorial-map",
        action="store_true",
        help="跳过 Tutorial/Step/Asset 映射",
    )
    parser.add_argument(
        "--skip-text-enrich",
        action="store_true",
        help="Tutorial 映射跳过文本 enrichment（full 下可用；fast 已默认跳过）",
    )
    parser.add_argument(
        "--skip-vision-enrich",
        action="store_true",
        help="Tutorial 映射跳过视觉 enrichment（full 下可用；fast 已默认跳过）",
    )
    parser.add_argument(
        "--skip-understanding",
        action="store_true",
        help="跳过 makeup-understanding（display_product / technique）",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="关闭 stderr 阶段进度（也可用 BEAUTY_PARSE_QUIET=1）",
    )
    parser.add_argument("--parse-output-root", default="outputs/runs")
    parser.add_argument("--preview-output-root", default="outputs/makeup-preview")
    parser.add_argument("--job-output-root", default="outputs/jobs")
    args = parser.parse_args()

    if args.video and args.parse_run:
        sys.stderr.write("不能同时指定 --video 与 --parse-run\n")
        sys.exit(2)
    if not args.video and not args.parse_run and not args.reference_image:
        sys.stderr.write("需要 --video、--parse-run 或 --reference-image\n")
        sys.exit(2)
    if not args.skip_preview and not args.user_photo and not args.use_baseline:
        sys.stderr.write("预览阶段需要 --user-photo 或 --use-baseline\n")
        sys.exit(2)

    quiet = bool(args.quiet) or _env_quiet()
    t0 = time.monotonic()
    on_progress = None

    def job_log(message: str) -> None:
        if quiet:
            return
        elapsed = time.monotonic() - t0
        sys.stderr.write(f"[job] {message} ({elapsed:.0f}s)\n")
        sys.stderr.flush()

    if not quiet:

        def on_progress(stage: int, message: str) -> None:
            elapsed = time.monotonic() - t0
            sys.stderr.write(f"[{stage}/10] {message} ({elapsed:.0f}s)\n")
            sys.stderr.flush()

        def on_map_progress(stage: int, message: str) -> None:
            elapsed = time.monotonic() - t0
            sys.stderr.write(f"[map {stage}/6] {message} ({elapsed:.0f}s)\n")
            sys.stderr.flush()

    else:
        on_map_progress = None

    api_key = load_api_key()
    parse_run_dir = Path(args.parse_run).resolve() if args.parse_run else None
    job_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_dir = (REPO_ROOT / args.job_output_root / job_stamp).resolve()

    tutorial_path: Path | None = None
    tutorial_id: str | None = None

    try:
        if args.video:
            video_path = Path(args.video).resolve()
            parse_root = (REPO_ROOT / args.parse_output_root).resolve()
            enable_keyframe_qa = not (args.mode == "fast" or args.skip_keyframe_qa)
            if not quiet:
                sys.stderr.write(
                    f"parse mode={args.mode}"
                    f"（L2 关键帧 QA={'开' if enable_keyframe_qa else '关'}）\n"
                )
                sys.stderr.flush()
            parse_config = ParseConfig(
                api_key=api_key,
                skill_dir=PARSE_SKILL,
                mode=args.mode,
                enable_keyframe_qa=enable_keyframe_qa,
                enable_replication_refs=not args.skip_replication_refs,
                on_progress=on_progress,
            )
            parse_result = run_parse_job(video_path, parse_root, config=parse_config)
            parse_run_dir = parse_result.run_dir
            if not quiet:
                sys.stderr.write(f"parse_run: {parse_run_dir}\n")
                sys.stderr.flush()
            job_log("解析完成")
        elif args.parse_run:
            job_log(f"使用已有 parse run（跳过解析）: {parse_run_dir}")

        # parse → map → preview
        if parse_run_dir and not args.skip_tutorial_map:
            enable_text = args.mode != "fast" and not args.skip_text_enrich
            enable_vision = args.mode != "fast" and not args.skip_vision_enrich
            if enable_text or enable_vision:
                if not api_key:
                    raise RuntimeError(
                        "Tutorial enrichment 需要 DASHSCOPE_API_KEY；"
                        "或使用 --mode fast / --skip-text-enrich --skip-vision-enrich"
                    )
            job_log(
                "Tutorial 映射…"
                + (
                    "（确定性）"
                    if not enable_text and not enable_vision
                    else f"（text={'开' if enable_text else '关'} vision={'开' if enable_vision else '关'}）"
                )
            )
            mapper_result = run_mapper_job(
                parse_run_dir,
                MapperConfig(
                    api_key=api_key,
                    enable_text_enrich=enable_text,
                    enable_vision_enrich=enable_vision,
                    on_progress=on_map_progress,
                ),
            )
            tutorial_path = mapper_result.tutorial_path
            tutorial_id = (mapper_result.tutorial or {}).get("tutorial_id")
            job_log(f"Tutorial 映射完成: {tutorial_path}")
            if not args.skip_understanding:
                if not api_key:
                    raise RuntimeError("makeup-understanding 需要 DASHSCOPE_API_KEY；或使用 --skip-understanding")
                job_log("理解产品与手法…")
                run_understanding_job(
                    parse_run_dir,
                    UnderstandingConfig(api_key=api_key, enabled=True),
                )
                job_log("理解完成")
            else:
                job_log("跳过 makeup-understanding")
        elif args.skip_tutorial_map:
            job_log("跳过 Tutorial 映射")
            if parse_run_dir and not args.skip_understanding:
                tutorial_candidate = parse_run_dir / "tutorial.json"
                if tutorial_candidate.is_file():
                    if not api_key:
                        raise RuntimeError("makeup-understanding 需要 DASHSCOPE_API_KEY")
                    job_log("理解产品与手法（已有 tutorial.json）…")
                    run_understanding_job(
                        parse_run_dir,
                        UnderstandingConfig(api_key=api_key, enabled=True),
                    )
                    tutorial_path = tutorial_candidate
                    job_log("理解完成")
        else:
            job_log("无 parse run，跳过 Tutorial 映射")

        preview_result = None
        if not args.skip_preview:
            job_log("妆容预览（选帧/底图/transfer）…")
            preview_root = (REPO_ROOT / args.preview_output_root).resolve()
            preview_config = PreviewConfig(api_key=api_key, skill_dir=PREVIEW_SKILL)
            reference_image = (
                Path(args.reference_image).resolve() if args.reference_image else None
            )
            user_photo = Path(args.user_photo).resolve() if args.user_photo else None
            preview_result = run_preview_job(
                parse_run_dir=parse_run_dir,
                reference_image=reference_image,
                user_photo=user_photo,
                use_baseline=args.use_baseline,
                baseline=args.baseline,
                reference_step=args.reference_step,
                output_root=preview_root,
                config=preview_config,
                skip_transfer=args.skip_transfer,
                strict_replication=args.strict_replication,
            )
            job_log("预览完成")
        else:
            job_log("跳过 preview")

        job_log("写入 manifest…")
        manifest_path = write_manifest(
            job_dir,
            parse_run_dir=parse_run_dir,
            preview_run_dir=preview_result.run_dir if preview_result else None,
            preview=preview_result.preview if preview_result else None,
            tutorial_path=tutorial_path,
            tutorial_id=tutorial_id,
        )
        job_log("完成")
    except UserPhotoRejected as e:
        sys.stderr.write((e.qa_doc.get("reason") or "用户照片未通过质检") + "\n")
        sys.exit(1)
    except StrictReplicationError as e:
        sys.stderr.write(f"strict-replication: {e}\n")
        sys.exit(3)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(2)

    print(job_dir)
    print(manifest_path)
    if parse_run_dir:
        print(parse_run_dir)
    if tutorial_path:
        print(tutorial_path)
    if preview_result:
        print(preview_result.run_dir)
        print(preview_result.preview_path)


if __name__ == "__main__":
    main()
