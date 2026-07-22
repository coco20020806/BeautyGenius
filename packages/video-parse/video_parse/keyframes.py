"""Keyframe extract + QA (see skill keyframe-validation.md)."""

from __future__ import annotations

import json
import re
import subprocess
from http import HTTPStatus
from pathlib import Path
from typing import Any

import dashscope
from dashscope import MultiModalConversation

from video_parse.config import ParseConfig
from video_parse.preprocess import SUBPROCESS_CAPTURE

MIN_FILE_BYTES = 4 * 1024
MIN_DIMENSION = 320
RETRY_OFFSETS_SEC = (0.0, 1.5, -1.5)

_INVALID = re.compile(r'[\\/:*?"<>|]')


def _to_file_uri(path: Path) -> str:
    return f"file://{path.resolve().as_posix()}"


def probe_image(ffprobe: str, path: Path) -> tuple[int, int] | None:
    if not path.is_file():
        return None
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(path),
    ]
    proc = subprocess.run(cmd, **SUBPROCESS_CAPTURE)
    if proc.returncode != 0:
        return None
    data = json.loads(proc.stdout)
    streams = data.get("streams") or []
    if not streams:
        return None
    return int(streams[0].get("width", 0)), int(streams[0].get("height", 0))


def l1_check(path: Path, ffprobe: str) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "exists": path.is_file(),
        "size_ok": False,
        "resolution_ok": False,
        "width": 0,
        "height": 0,
    }
    if not checks["exists"]:
        return {"pass": False, "checks": checks, "reason": "文件不存在"}
    size = path.stat().st_size
    checks["size_ok"] = size >= MIN_FILE_BYTES
    dims = probe_image(ffprobe, path)
    if dims:
        checks["width"], checks["height"] = dims
        checks["resolution_ok"] = (
            dims[0] >= MIN_DIMENSION and dims[1] >= MIN_DIMENSION
        )
    passed = checks["exists"] and checks["size_ok"] and checks["resolution_ok"]
    reason = "L1通过" if passed else "L1未通过(体积或分辨率)"
    return {"pass": passed, "checks": checks, "reason": reason}


def extract_single_frame(
    ffmpeg: str, video_path: Path, ts: float, out: Path, duration_sec: float
) -> None:
    ts = max(0.0, min(ts, max(0.0, duration_sec - 0.05)))
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-ss",
        f"{ts:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(out),
    ]
    subprocess.run(cmd, **SUBPROCESS_CAPTURE, check=True)


def ensure_frame_l1(
    ffmpeg: str,
    ffprobe: str,
    video_path: Path,
    duration_sec: float,
    kf: dict[str, Any],
    out_path: Path,
) -> int:
    base_ts = float(kf["timestamp_sec"])
    attempts = 0
    for off in RETRY_OFFSETS_SEC:
        attempts += 1
        ts = base_ts + off
        extract_single_frame(ffmpeg, video_path, ts, out_path, duration_sec)
        result = l1_check(out_path, ffprobe)
        if result["pass"]:
            kf["timestamp_sec"] = ts
            return attempts
    return attempts


def _sec_to_hhmmss(sec: float) -> str:
    total = int(round(max(0.0, sec)))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}{m:02d}{s:02d}"


def refresh_keyframe_filename(step_name: str, kf: dict[str, Any]) -> None:
    name = _INVALID.sub("_", step_name.strip()) or "步骤"
    idx = kf.get("index_in_step", 1)
    stamp = _sec_to_hhmmss(float(kf.get("timestamp_sec", 0)))
    kf["filename"] = f"{name}-{idx:02d}-{stamp}.jpg"


def _l1_extract_all(
    ffmpeg: str,
    ffprobe: str,
    video_path: Path,
    duration_sec: float,
    steps: list[dict[str, Any]],
    keyframes_dir: Path,
) -> list[dict[str, Any]]:
    keyframes_dir.mkdir(parents=True, exist_ok=True)
    report_items: list[dict[str, Any]] = []
    for step in steps:
        for kf in step.get("keyframes") or []:
            out_path = keyframes_dir / kf["filename"]
            attempts = ensure_frame_l1(
                ffmpeg, ffprobe, video_path, duration_sec, kf, out_path
            )
            refresh_keyframe_filename(step.get("step_name", ""), kf)
            if out_path.name != kf["filename"]:
                out_path = keyframes_dir / kf["filename"]
                extract_single_frame(
                    ffmpeg,
                    video_path,
                    float(kf["timestamp_sec"]),
                    out_path,
                    duration_sec,
                )
            l1 = l1_check(keyframes_dir / kf["filename"], ffprobe)
            kf["validation"] = {
                "pass": l1["pass"],
                "l1_pass": l1["pass"],
                "l2_skipped": True,
                "skipped": True,
                "reason": l1["reason"],
            }
            report_items.append(
                {
                    "step_name": step.get("step_name"),
                    "filename": kf["filename"],
                    "role": kf.get("role"),
                    "l1": l1,
                    "pass": l1["pass"],
                    "extract_attempts": attempts,
                }
            )
    return report_items


def vision_validate_step_keyframes(
    config: ParseConfig,
    step: dict[str, Any],
    keyframes_dir: Path,
    run_dir: Path,
) -> list[dict[str, Any]]:
    kfs = step.get("keyframes") or []
    if not kfs:
        return []
    primary = step.get("step_name", "")
    subs = (step.get("taxonomy") or {}).get("sub_steps") or []
    content: list[dict[str, Any]] = []
    for kf in kfs:
        img = keyframes_dir / kf["filename"]
        if img.is_file():
            content.append({"image": _to_file_uri(img)})
    meta_lines = [
        f"图{i}: role={kf.get('role')}, label={kf.get('label')}, file={kf.get('filename')}"
        for i, kf in enumerate(kfs, start=1)
    ]
    prompt = (
        "你是美妆教程关键帧质检员。以上图片按顺序对应同一化妆步骤的关键帧。\n"
        f"步骤主类: {primary}\n"
        f"细分 sub_steps: {', '.join(subs) if subs else '无'}\n"
        + "\n".join(meta_lines)
        + "\n\n"
        "规则: step_start_face/step_end_face 需清晰可见人脸且脸部占比足够; "
        "makeup_detail 需人脸且画面聚焦 label 对应妆容区域。\n"
        "只输出 JSON: {\"results\":[{\"index\":1,\"has_face\":true,\"face_sufficient\":true,"
        "\"region_match\":true,\"pass\":true,\"reason\":\"...\"}, ...]}"
        " index 从 1 开始，与图片顺序一致。"
    )
    content.append({"text": prompt})
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    response = MultiModalConversation.call(
        api_key=config.api_key,
        model=config.vision_model,
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
    )
    if response.status_code != HTTPStatus.OK:
        (run_dir / "keyframe_qa_vision_error.txt").write_text(
            str(getattr(response, "message", response)), encoding="utf-8"
        )
        return [
            {
                "index": i,
                "pass": False,
                "reason": "视觉质检 API 失败",
                "has_face": None,
                "face_sufficient": None,
                "region_match": None,
            }
            for i in range(1, len(kfs) + 1)
        ]
    text = response.output.choices[0].message.content
    if isinstance(text, list):
        text = text[0].get("text", "{}")
    (run_dir / "keyframe_qa_vision_raw.json").write_text(str(text), encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [
            {"index": i, "pass": False, "reason": "质检 JSON 解析失败"}
            for i in range(1, len(kfs) + 1)
        ]
    return payload.get("results") or []


def run_keyframe_pipeline(
    config: ParseConfig,
    ffmpeg: str,
    ffprobe: str,
    video_path: Path,
    duration_sec: float,
    steps: list[dict[str, Any]],
    keyframes_dir: Path,
    run_dir: Path,
) -> dict[str, Any]:
    def _p(message: str) -> None:
        cb = config.on_progress
        if cb is not None:
            cb(7, message)

    if not config.enable_keyframe_qa:
        _p("关键帧 L1（跳过 L2）…")
        items = _l1_extract_all(
            ffmpeg, ffprobe, video_path, duration_sec, steps, keyframes_dir
        )
        passed = sum(1 for i in items if i.get("pass"))
        summary = {
            "total": len(items),
            "passed": passed,
            "failed": len(items) - passed,
            "retried_extracts": sum(i.get("extract_attempts", 1) for i in items),
            "l2_skipped": True,
        }
        doc = {"summary": summary, "items": items, "vision_by_step": {}}
        (run_dir / "keyframe-qa.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return summary

    report_items: list[dict[str, Any]] = []
    for step in steps:
        for kf in step.get("keyframes") or []:
            out_path = keyframes_dir / kf["filename"]
            attempts = ensure_frame_l1(
                ffmpeg, ffprobe, video_path, duration_sec, kf, out_path
            )
            l1 = l1_check(out_path, ffprobe)
            report_items.append(
                {
                    "step_name": step.get("step_name"),
                    "filename": kf["filename"],
                    "role": kf.get("role"),
                    "label": kf.get("label"),
                    "timestamp_sec": kf.get("timestamp_sec"),
                    "l1": l1,
                    "extract_attempts": attempts,
                }
            )

    for step in steps:
        for kf in step.get("keyframes") or []:
            refresh_keyframe_filename(step.get("step_name", ""), kf)
            new_path = keyframes_dir / kf["filename"]
            if not new_path.is_file():
                extract_single_frame(
                    ffmpeg,
                    video_path,
                    float(kf["timestamp_sec"]),
                    new_path,
                    duration_sec,
                )

    vision_by_step: dict[str, list[dict[str, Any]]] = {}
    n_steps = len(steps)
    for step_i, step in enumerate(steps, start=1):
        step_name = step.get("step_name") or ""
        _p(f"关键帧 QA（步骤 {step_i}/{n_steps}）{step_name}…")
        results = vision_validate_step_keyframes(config, step, keyframes_dir, run_dir)
        vision_by_step[step_name] = results
        kfs = step.get("keyframes") or []
        for res in results:
            idx = int(res.get("index", 0)) - 1
            if idx < 0 or idx >= len(kfs):
                continue
            role = kfs[idx].get("role")
            passed = bool(res.get("pass"))
            if role in ("step_start_face", "step_end_face"):
                passed = passed and bool(res.get("has_face")) and bool(
                    res.get("face_sufficient")
                )
            elif role == "makeup_detail":
                passed = passed and bool(res.get("has_face")) and bool(
                    res.get("region_match")
                )
            kfs[idx]["validation"] = {
                "pass": passed,
                "has_face": res.get("has_face"),
                "face_sufficient": res.get("face_sufficient"),
                "region_match": res.get("region_match"),
                "reason": res.get("reason") or "",
                "l1_pass": True,
            }

    for item in report_items:
        fname = item["filename"]
        for step in steps:
            for kf in step.get("keyframes") or []:
                if kf.get("filename") == fname or item["filename"] in kf.get(
                    "filename", ""
                ):
                    v = kf.get("validation") or {}
                    item["filename"] = kf["filename"]
                    item["validation"] = v
                    item["pass"] = item["l1"]["pass"] and v.get("pass", False)
                    break

    for step in steps:
        for kf in step.get("keyframes") or []:
            if "validation" not in kf:
                kf["validation"] = {
                    "pass": False,
                    "reason": "未完成 L2 质检",
                    "l1_pass": l1_check(
                        keyframes_dir / kf["filename"], ffprobe
                    ).get("pass", False),
                }

    passed = sum(1 for i in report_items if i.get("pass"))
    summary = {
        "total": len(report_items),
        "passed": passed,
        "failed": len(report_items) - passed,
        "retried_extracts": sum(i.get("extract_attempts", 1) for i in report_items),
        "l2_skipped": False,
    }
    doc = {"summary": summary, "items": report_items, "vision_by_step": vision_by_step}
    (run_dir / "keyframe-qa.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary
