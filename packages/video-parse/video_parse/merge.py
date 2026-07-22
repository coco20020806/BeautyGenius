"""Merge vision + ASR into analysis structure."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from video_parse.config import CONTRACT_VERSION, TAXONOMY_VERSION, ParseConfig
from video_parse.taxonomy import (
    align_makeup_detail_labels,
    build_taxonomy_coverage,
    load_taxonomy_enums,
    normalize_taxonomy_on_step,
)

INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def sec_to_label(sec: float) -> str:
    sec = max(0.0, sec)
    total = int(round(sec))
    m, s = divmod(total, 60)
    return f"{m}:{s:02d}"


def sec_to_hhmmss(sec: float) -> str:
    sec = max(0.0, sec)
    total = int(round(sec))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}{m:02d}{s:02d}"


def sanitize_step_name(name: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("_", name.strip())
    return cleaned or "步骤"


def overlap_duration(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    return max(0.0, end - start)


def assign_voiceover_to_steps(
    steps: list[dict[str, Any]], segments: list[dict[str, Any]]
) -> None:
    for step in steps:
        tr = step.setdefault("text", {})
        tr["voiceover"] = []
    for seg in segments:
        best_idx = -1
        best_overlap = 0.0
        for i, step in enumerate(steps):
            r = step["time_range"]
            ov = overlap_duration(
                seg["start_sec"], seg["end_sec"], r["start_sec"], r["end_sec"]
            )
            if ov > best_overlap:
                best_overlap = ov
                best_idx = i
        if best_idx >= 0 and best_overlap > 0:
            steps[best_idx]["text"]["voiceover"].append(
                {
                    "start_sec": seg["start_sec"],
                    "end_sec": seg["end_sec"],
                    "text": seg["text"],
                }
            )


def normalize_steps(
    raw_steps: list[dict[str, Any]], duration_sec: float, enums: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str]]:
    steps: list[dict[str, Any]] = []
    warnings: list[str] = []
    for i, raw in enumerate(raw_steps, start=1):
        tr = raw.get("time_range") or {}
        start = float(tr.get("start_sec", 0))
        end = float(tr.get("end_sec", start + 1))
        if duration_sec > 0:
            end = min(end, duration_sec)
            start = min(start, end)
        text = raw.get("text") or {}
        step: dict[str, Any] = {
            "step_index": int(raw.get("step_index", i)),
            "step_name": str(raw.get("step_name") or f"步骤{i}"),
            "time_range": {
                "start_sec": start,
                "end_sec": end,
                "start_label": tr.get("start_label") or sec_to_label(start),
                "end_label": tr.get("end_label") or sec_to_label(end),
            },
            "text": {
                "subtitles": text.get("subtitles") or [],
                "on_screen": text.get("on_screen") or [],
                "voiceover": [],
            },
            "keyframes": list(raw.get("keyframes") or []),
            "taxonomy": raw.get("taxonomy") or {},
        }
        warnings.extend(normalize_taxonomy_on_step(step, enums))
        steps.append(step)
    return steps, warnings


def ensure_keyframes(steps: list[dict[str, Any]], duration_sec: float) -> None:
    for step in steps:
        kfs = step.get("keyframes") or []
        roles = {k.get("role") for k in kfs}
        start = step["time_range"]["start_sec"]
        end = step["time_range"]["end_sec"]
        if duration_sec > 0:
            end = min(end, duration_sec - 0.01)
            start = min(start, end)
        if "step_start_face" not in roles:
            kfs.append(
                {
                    "role": "step_start_face",
                    "timestamp_sec": start,
                    "label": "步骤开始脸部",
                }
            )
        if "step_end_face" not in roles:
            kfs.append(
                {
                    "role": "step_end_face",
                    "timestamp_sec": end,
                    "label": "步骤结束脸部",
                }
            )
        step["keyframes"] = kfs


def dedupe_keyframe_times(kfs: list[dict[str, Any]], tol: float = 0.5) -> list[dict[str, Any]]:
    seen: list[float] = []
    out: list[dict[str, Any]] = []
    for kf in sorted(kfs, key=lambda k: float(k.get("timestamp_sec", 0))):
        ts = float(kf.get("timestamp_sec", 0))
        if any(abs(ts - s) <= tol for s in seen):
            continue
        seen.append(ts)
        out.append(kf)
    return out


def build_keyframe_filenames(steps: list[dict[str, Any]]) -> None:
    for step in steps:
        name = sanitize_step_name(step["step_name"])
        kfs = dedupe_keyframe_times(step.get("keyframes") or [])
        for idx, kf in enumerate(kfs, start=1):
            ts = float(kf.get("timestamp_sec", 0))
            kf["index_in_step"] = idx
            kf["timestamp_sec"] = ts
            kf["filename"] = f"{name}-{idx:02d}-{sec_to_hhmmss(ts)}.jpg"
        step["keyframes"] = kfs


def build_analysis(
    config: ParseConfig,
    source_path: Path,
    analysis_video: Path,
    probe: dict[str, Any],
    vision_payload: dict[str, Any],
    asr_segments: list[dict[str, Any]],
    compressed: bool,
) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    raw_steps = vision_payload.get("steps") or []
    if not raw_steps:
        raise ValueError("模型未返回任何步骤")
    enums = load_taxonomy_enums(config.skill_dir)
    duration = probe["duration_sec"]
    steps, tax_warnings = normalize_steps(raw_steps, duration, enums)
    assign_voiceover_to_steps(steps, asr_segments)
    ensure_keyframes(steps, duration)
    align_makeup_detail_labels(steps)
    build_keyframe_filenames(steps)
    coverage = build_taxonomy_coverage(steps, enums)
    analysis = {
        "contract_version": CONTRACT_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "skipped_primaries": coverage["skipped_primaries"],
        "video": {
            "source_path": str(source_path.resolve()),
            "duration_sec": duration,
            "fps": probe.get("fps"),
            "analysis_path": str(analysis_video.resolve()),
            "upload_compressed": compressed,
        },
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": config.vision_model,
        "asr_model": config.asr_model,
        "steps": steps,
    }
    return analysis, tax_warnings, coverage
