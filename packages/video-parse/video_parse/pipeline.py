"""Orchestrate beauty video parse job (SKILL pipeline 1–9)."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

from video_parse.asr import run_asr
from video_parse.config import CONTRACT_VERSION, TAXONOMY_VERSION, ParseConfig, ParseJobResult
from video_parse.keyframes import run_keyframe_pipeline
from video_parse.merge import build_analysis
from video_parse.replication_refs import run_replication_refs
from video_parse.preprocess import (
    extract_audio,
    prepare_video_for_api,
    probe_video,
    resolve_ffmpeg,
    resolve_ffprobe,
)
from video_parse.schema import validate_analysis
from video_parse.vision import call_vision


def _progress(config: ParseConfig, stage: int, message: str) -> None:
    cb = config.on_progress
    if cb is not None:
        cb(stage, message)


def run_parse_job(
    video_path: Path,
    output_root: Path,
    *,
    config: ParseConfig,
) -> ParseJobResult:
    video_path = video_path.expanduser().resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f"文件不存在: {video_path}")

    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    keyframes_dir = run_dir / "keyframes"

    ffmpeg = resolve_ffmpeg(config)
    ffprobe = resolve_ffprobe(config, ffmpeg)

    _progress(config, 1, "Probe…")
    probe = probe_video(ffprobe, video_path)

    analysis_video, compressed = prepare_video_for_api(
        ffmpeg, video_path, run_dir, config.max_upload_bytes
    )
    if compressed:
        _progress(config, 2, "Prepare（已压缩上传代理）…")
    else:
        _progress(config, 2, "Prepare（跳过压缩）…")

    wav_path = run_dir / "audio.wav"
    _progress(config, 3, "抽取音频…")
    extract_audio(ffmpeg, video_path, wav_path)

    _progress(config, 4, "Vision 分析中…（并行）")
    _progress(config, 5, "ASR 转写中…（并行）")
    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_v = pool.submit(call_vision, config, analysis_video, run_dir)
        fut_a = pool.submit(run_asr, config, wav_path, run_dir)
        vision_payload, vision_meta = fut_v.result()
        asr_segments, asr_meta = fut_a.result()

    _progress(config, 6, "Merge + taxonomy…")
    analysis, tax_warnings, coverage = build_analysis(
        config,
        video_path,
        analysis_video,
        probe,
        vision_payload,
        asr_segments,
        compressed,
    )

    coverage_path = run_dir / "taxonomy-coverage.json"
    coverage_path.write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _progress(config, 7, "关键帧 QA…")
    qa_summary = run_keyframe_pipeline(
        config,
        ffmpeg,
        ffprobe,
        video_path,
        probe["duration_sec"],
        analysis["steps"],
        keyframes_dir,
        run_dir,
    )

    hints = vision_payload.get("replication_hints") or {}
    (run_dir / "replication_hints.json").write_text(
        json.dumps(hints, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    repl_summary: dict[str, Any] | None = None
    if config.enable_replication_refs:
        _progress(config, 8, "复刻参考对…")
        repl_summary = run_replication_refs(
            config,
            ffmpeg,
            ffprobe,
            video_path,
            probe["duration_sec"],
            analysis["steps"],
            hints,
            keyframes_dir,
            run_dir,
            analysis,
        )
    else:
        _progress(config, 8, "跳过复刻参考")

    _progress(config, 9, "Schema 校验…")
    validate_analysis(analysis)

    analysis_path = run_dir / "analysis.json"
    analysis_path.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    keyframe_qa_path = run_dir / "keyframe-qa.json"
    meta = {
        "run_dir": str(run_dir.resolve()),
        "source_path": str(video_path.resolve()),
        "compressed_for_upload": compressed,
        "contract_version": analysis.get("contract_version", CONTRACT_VERSION),
        "taxonomy_version": TAXONOMY_VERSION,
        "skill_dir": str(config.skill_dir.resolve()),
        "probe": probe,
        "vision_api": vision_meta,
        "asr_api": asr_meta,
        "taxonomy_warnings": tax_warnings,
        "keyframe_qa": qa_summary,
        "mode": getattr(config, "mode", "full") or "full",
        "enable_keyframe_qa": config.enable_keyframe_qa,
        "enable_replication_refs": config.enable_replication_refs,
        "replication_refs": repl_summary,
    }
    (run_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _progress(config, 10, "写盘完成")

    return ParseJobResult(
        run_dir=run_dir,
        analysis_path=analysis_path,
        analysis=analysis,
        meta=meta,
        coverage_path=coverage_path,
        keyframe_qa_path=keyframe_qa_path if keyframe_qa_path.is_file() else None,
    )
