from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from makeup_preview import PreviewConfig, UserPhotoRejected, run_preview_job
from tutorial_mapper import MapperConfig, run_mapper_job
from video_parse import ParseConfig, run_parse_job
from video_parse.preprocess import probe_video, resolve_ffmpeg, resolve_ffprobe

from api_server.config import (
    JOBS_OUTPUT_ROOT,
    PARSE_OUTPUT_ROOT,
    PARSE_SKILL,
    PREVIEW_OUTPUT_ROOT,
    PREVIEW_SKILL,
    REPO_ROOT,
    SKIP_TRANSFER,
)
from api_server.eta import estimate_eta_total
from api_server.preview_assembler import publish_media_files
from api_server.progress import map_map_stage, map_parse_stage
from api_server.store import store


def load_api_key() -> str:
    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if key:
        return key
    scripts = REPO_ROOT / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        from _qwen_local import DASHSCOPE_API_KEY  # type: ignore

        return DASHSCOPE_API_KEY.strip()
    except ImportError:
        pass
    raise RuntimeError("缺少 DASHSCOPE_API_KEY")


def _resolve_parse_mode(task: dict) -> str:
    mode = (task.get("parse_mode") or os.environ.get("PARSE_MODE") or "fast").lower()
    return mode if mode in {"fast", "full"} else "fast"


def run_task_pipeline(task_id: str) -> None:
    try:
        task = store.load(task_id)
        video_path = Path(task["video_path"])
        if not video_path.is_file():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        parse_mode = _resolve_parse_mode(task)
        api_key = load_api_key()
        use_baseline = bool(task.get("photo_skipped"))
        user_photo = Path(task["photo_path"]) if task.get("photo_path") else None
        baseline = task.get("baseline") or "female"
        skip_transfer = bool(task.get("skip_transfer")) or SKIP_TRANSFER

        qa_on = parse_mode != "fast"
        mode_line = (
            f"parse mode={parse_mode}（L2 关键帧 QA={'开' if qa_on else '关'}）"
        )
        store.append_log_only(task_id, f"[job] {mode_line}", skip_transfer=skip_transfer)

        ffmpeg = resolve_ffmpeg(ParseConfig(api_key=api_key, skill_dir=PARSE_SKILL))
        ffprobe = resolve_ffprobe(ParseConfig(api_key=api_key, skill_dir=PARSE_SKILL), ffmpeg)
        probe = probe_video(ffprobe, video_path)
        duration_sec = float(probe.get("duration_sec") or 0)
        eta_total = estimate_eta_total(
            parse_mode=parse_mode,
            skip_transfer=skip_transfer,
            duration_sec=duration_sec,
            file_size_bytes=int(task.get("fileSize") or 0),
        )
        store.set_eta_context(task_id, video_duration_sec=duration_sec, eta_total_seconds=eta_total)

        def on_parse_progress(stage: int, message: str) -> None:
            active_index, pct = map_parse_stage(stage)
            line = f"[{stage}/10] {message}"
            store.update_pipeline_step(
                task_id,
                active_index=active_index,
                progress=pct,
                micro_step_id=f"parse:{stage}",
                log_line=line,
                skip_transfer=skip_transfer,
            )

        store.update_pipeline_step(
            task_id,
            active_index=0,
            progress=8,
            micro_step_id="parse:1",
            log_line="[1/10] 准备解析…",
            skip_transfer=skip_transfer,
        )
        enable_keyframe_qa = parse_mode != "fast"
        parse_config = ParseConfig(
            api_key=api_key,
            skill_dir=PARSE_SKILL,
            mode=parse_mode,
            enable_keyframe_qa=enable_keyframe_qa,
            enable_replication_refs=True,
            on_progress=on_parse_progress,
        )
        parse_result = run_parse_job(video_path, PARSE_OUTPUT_ROOT, config=parse_config)
        parse_run_dir = parse_result.run_dir

        def on_map_progress(stage: int, message: str) -> None:
            active_index, pct = map_map_stage(stage)
            line = f"[map {stage}/6] {message}"
            store.update_pipeline_step(
                task_id,
                active_index=active_index,
                progress=pct,
                micro_step_id=f"map:{stage}",
                log_line=line,
                skip_transfer=skip_transfer,
            )

        enable_text = parse_mode != "fast"
        enable_vision = parse_mode != "fast"
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

        store.update_pipeline_step(
            task_id,
            active_index=2,
            progress=58,
            micro_step_id="preview:pick",
            log_line="[job] 妆容预览（选帧/底图/transfer）…",
            skip_transfer=skip_transfer,
        )
        preview_config = PreviewConfig(api_key=api_key, skill_dir=PREVIEW_SKILL)
        store.update_pipeline_step(
            task_id,
            active_index=2,
            progress=62,
            micro_step_id="preview:target",
            log_line="[job] 准备目标脸与参考妆面…",
            skip_transfer=skip_transfer,
        )
        preview_result = run_preview_job(
            parse_run_dir=parse_run_dir,
            reference_image=None,
            user_photo=user_photo,
            use_baseline=use_baseline,
            baseline=baseline,
            reference_step=None,
            output_root=PREVIEW_OUTPUT_ROOT,
            config=preview_config,
            skip_transfer=skip_transfer,
            strict_replication=False,
        )
        transfer_line = "[job] transfer 完成" if not skip_transfer else "[job] 已跳过 wan transfer（跳过妆容预览）"
        store.update_pipeline_step(
            task_id,
            active_index=2,
            progress=88,
            micro_step_id="preview:transfer",
            log_line=transfer_line,
            skip_transfer=skip_transfer,
        )
        store.update_pipeline_step(
            task_id,
            active_index=3,
            progress=92,
            micro_step_id="preview:write",
            log_line="[job] 预览写盘…",
            skip_transfer=skip_transfer,
        )

        task_dir = store.task_dir(task_id)
        media_dir = publish_media_files(task_id, preview_result.run_dir, task_dir)

        store.update_pipeline_step(
            task_id,
            active_index=3,
            progress=96,
            micro_step_id="hint:done",
            log_line="[job] 整理适配建议…",
            skip_transfer=skip_transfer,
        )

        job_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_dir = JOBS_OUTPUT_ROOT / job_stamp
        job_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "job_version": "1",
            "task_id": task_id,
            "parse_run_dir": str(parse_run_dir),
            "tutorial_path": str(tutorial_path),
            "preview_run_dir": str(preview_result.run_dir),
        }
        (job_dir / "manifest.json").write_text(
            __import__("json").dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        store.mark_completed(
            task_id,
            parse_run_dir=str(parse_run_dir),
            preview_run_dir=str(preview_result.run_dir),
            tutorial_path=str(tutorial_path) if tutorial_path else None,
            media_dir=str(media_dir),
        )
    except UserPhotoRejected as exc:
        reason = exc.qa_doc.get("reason") or "用户照片未通过质检，请按拍摄指引重新上传"
        store.mark_failed(task_id, reason=reason, code="USER_PHOTO_REJECTED")
    except Exception as exc:  # noqa: BLE001 — surface pipeline errors to task store
        store.mark_failed(task_id, reason=str(exc) or "解析失败")
