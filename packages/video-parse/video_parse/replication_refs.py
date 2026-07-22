"""Step-boundary before/after replication refs (skill makeup-replication-refs.md v1.2)."""

from __future__ import annotations

import json
import shutil
import subprocess
from http import HTTPStatus
from pathlib import Path
from typing import Any

import dashscope
from dashscope import MultiModalConversation

from video_parse.config import CONTRACT_VERSION_V21, ParseConfig
from video_parse.keyframes import (
    RETRY_OFFSETS_SEC,
    extract_single_frame,
    l1_check,
)
from video_parse.preprocess import SUBPROCESS_CAPTURE

REFS_VERSION = "1"
TAIL_SPAN_MAX_SEC = 90.0
TAIL_SPAN_RATIO = 0.25
LAST_STEP_SCAN_CAP_SEC = 15.0
LAST_STEP_SCAN_MIN_SEC = 3.0

MAKEUP_PRIMARIES = frozenset(
    {
        "妆前",
        "底妆",
        "遮瑕",
        "定妆",
        "眉毛",
        "眼睛",
        "眼线",
        "睫毛",
        "修容",
        "腮红",
        "高光",
        "唇妆",
    }
)


def _sec_to_hhmmss(sec: float) -> str:
    total = int(round(max(0.0, sec)))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}{m:02d}{s:02d}"


def _to_file_uri(path: Path) -> str:
    return f"file://{path.resolve().as_posix()}"


def _progress(config: ParseConfig, message: str) -> None:
    cb = config.on_progress
    if cb is not None:
        cb(8, message)


def _step_start(step: dict[str, Any]) -> float:
    return float((step.get("time_range") or {}).get("start_sec") or 0.0)


def _step_end(step: dict[str, Any]) -> float:
    return float((step.get("time_range") or {}).get("end_sec") or 0.0)


def _step_primary(step: dict[str, Any]) -> str:
    return str(
        (step.get("taxonomy") or {}).get("primary") or step.get("step_name") or ""
    )


def _is_skipped(step: dict[str, Any]) -> bool:
    return bool((step.get("taxonomy") or {}).get("skipped"))


def active_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [s for s in steps if not _is_skipped(s)]


def pick_first_step(steps: list[dict[str, Any]]) -> dict[str, Any] | None:
    active = active_steps(steps)
    if not active:
        return None
    return min(active, key=_step_start)


def pick_last_makeup_step(steps: list[dict[str, Any]]) -> dict[str, Any] | None:
    makeup = [
        s
        for s in active_steps(steps)
        if _step_primary(s) in MAKEUP_PRIMARIES
    ]
    if not makeup:
        return None
    return max(makeup, key=_step_end)


def find_keyframe(step: dict[str, Any], role: str) -> dict[str, Any] | None:
    for kf in step.get("keyframes") or []:
        if kf.get("role") == role:
            return kf
    return None


def compute_tail_window(
    duration_sec: float, steps: list[dict[str, Any]]
) -> tuple[float, float]:
    tutorial_end = 0.0
    for step in steps:
        tutorial_end = max(tutorial_end, _step_end(step))
    tail_span = min(TAIL_SPAN_RATIO * duration_sec, TAIL_SPAN_MAX_SEC)
    window_start = max(tutorial_end, duration_sec - tail_span)
    window_end = duration_sec
    return window_start, window_end


def _in_tail(ts: float, window_start: float, window_end: float) -> bool:
    return window_start <= ts <= window_end


def _filename(prefix: str, ts: float) -> str:
    return f"{prefix}-01-{_sec_to_hhmmss(ts)}.jpg"


def extract_with_l1(
    ffmpeg: str,
    ffprobe: str,
    video_path: Path,
    duration_sec: float,
    ts: float,
    out_path: Path,
) -> tuple[float, dict[str, Any]]:
    best_ts = ts
    best_l1: dict[str, Any] = {"pass": False, "reason": "未抽帧"}
    for off in RETRY_OFFSETS_SEC:
        attempt_ts = ts + off
        extract_single_frame(
            ffmpeg, video_path, attempt_ts, out_path, duration_sec
        )
        result = l1_check(out_path, ffprobe)
        if result["pass"]:
            return attempt_ts, result
        best_ts = attempt_ts
        best_l1 = result
    return best_ts, best_l1


def _ensure_frame_from_kf_or_extract(
    ffmpeg: str,
    ffprobe: str,
    video_path: Path,
    duration_sec: float,
    kf: dict[str, Any] | None,
    ts: float,
    out_path: Path,
    keyframes_dir: Path,
) -> tuple[float, dict[str, Any]]:
    if kf and kf.get("filename"):
        src = keyframes_dir / str(kf["filename"])
        if src.is_file():
            shutil.copy2(src, out_path)
            l1 = l1_check(out_path, ffprobe)
            if l1["pass"]:
                return float(kf.get("timestamp_sec", ts)), l1
    return extract_with_l1(
        ffmpeg, ffprobe, video_path, duration_sec, ts, out_path
    )


def ffmpeg_crop_half(ffmpeg: str, src: Path, dst: Path, side: str) -> None:
    side = side.lower()
    if side == "left":
        vf = "crop=iw/2:ih:0:0"
    elif side == "right":
        vf = "crop=iw/2:ih:iw/2:0"
    elif side == "top":
        vf = "crop=iw:ih/2:0:0"
    elif side == "bottom":
        vf = "crop=iw:ih/2:0:ih/2"
    else:
        raise ValueError(f"unknown crop side: {side}")
    cmd = [ffmpeg, "-y", "-i", str(src), "-vf", vf, "-q:v", "2", str(dst)]
    subprocess.run(cmd, **SUBPROCESS_CAPTURE, check=True)


def vision_split_sides(
    config: ParseConfig, image_path: Path, run_dir: Path
) -> dict[str, str] | None:
    if not image_path.is_file():
        return None
    prompt = (
        "这是美妆教程片尾可能的妆前妆后分屏对比图。只输出 JSON："
        '{"before_side":"left|right|top|bottom","after_side":"left|right|top|bottom",'
        '"is_split_comparison":true|false,"reason":"..."} '
        "before_side 为更素颜一侧，after_side 为完成全妆一侧。"
    )
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    response = MultiModalConversation.call(
        api_key=config.api_key,
        model=config.vision_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"image": _to_file_uri(image_path)},
                    {"text": prompt},
                ],
            }
        ],
        response_format={"type": "json_object"},
    )
    if response.status_code != HTTPStatus.OK:
        return None
    text = response.output.choices[0].message.content
    if isinstance(text, list):
        text = text[0].get("text", "{}")
    (run_dir / "replication_split_raw.json").write_text(str(text), encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not payload.get("is_split_comparison"):
        return None
    b = payload.get("before_side")
    a = payload.get("after_side")
    if b in ("left", "right", "top", "bottom") and a in (
        "left",
        "right",
        "top",
        "bottom",
    ):
        return {"before_side": b, "after_side": a}
    return None


def vision_single_replication_frame(
    config: ParseConfig,
    image_path: Path,
    *,
    role: str,
    run_dir: Path,
    raw_name: str,
) -> dict[str, Any]:
    """Single-frame L2 for replication_before / replication_after."""
    default = {
        "pass": False,
        "has_face": False,
        "face_sufficient": False,
        "makeup_complete": False,
        "makeup_minimal": False,
        "reason": "未执行单帧 L2",
    }
    if not image_path.is_file():
        default["reason"] = "文件不存在"
        return default
    if role == "replication_after":
        rules = (
            "须清晰全脸、脸部占比足够，且为教程完成全妆展示（makeup_complete=true）；"
            "禁止产品卡、文字卡、片尾对比中的素颜/更素一侧。"
        )
    else:
        rules = (
            "须清晰全脸、脸部占比足够，且为素颜或明显更素（makeup_minimal=true）；"
            "禁止成妆展示。"
        )
    prompt = (
        f"你是美妆复刻参考帧质检员。角色: {role}。\n"
        f"规则: {rules}\n"
        "只输出 JSON: "
        '{"has_face":true,"face_sufficient":true,"makeup_complete":false,'
        '"makeup_minimal":true,"pass":true,"reason":"..."}'
    )
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    response = MultiModalConversation.call(
        api_key=config.api_key,
        model=config.vision_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"image": _to_file_uri(image_path)},
                    {"text": prompt},
                ],
            }
        ],
        response_format={"type": "json_object"},
    )
    if response.status_code != HTTPStatus.OK:
        default["reason"] = "单帧 L2 API 失败"
        return default
    text = response.output.choices[0].message.content
    if isinstance(text, list):
        text = text[0].get("text", "{}")
    (run_dir / raw_name).write_text(str(text), encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        default["reason"] = "单帧 L2 JSON 解析失败"
        return default

    has_face = bool(payload.get("has_face"))
    face_ok = bool(payload.get("face_sufficient"))
    complete = bool(payload.get("makeup_complete"))
    minimal = bool(payload.get("makeup_minimal"))
    if role == "replication_after":
        passed = has_face and face_ok and complete
    else:
        passed = has_face and face_ok and minimal
    if payload.get("pass") is False:
        passed = False
    return {
        "pass": passed,
        "has_face": has_face,
        "face_sufficient": face_ok,
        "makeup_complete": complete,
        "makeup_minimal": minimal,
        "reason": str(payload.get("reason") or ""),
    }


def vision_pair_validation(
    config: ParseConfig,
    before_path: Path,
    after_path: Path,
    run_dir: Path,
) -> dict[str, Any]:
    default = {
        "same_person": False,
        "before_is_bareer": False,
        "after_is_full_makeup": False,
        "pass": False,
        "reason": "未执行 L2",
    }
    if not before_path.is_file() or not after_path.is_file():
        default["reason"] = "缺少 before/after 文件"
        return default
    prompt = (
        "图1是妆前基线，图2是完成妆容。只输出 JSON："
        '{"same_person":true,"before_is_bareer":true,"after_is_full_makeup":true,'
        '"pass":true,"reason":"..."}'
    )
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    response = MultiModalConversation.call(
        api_key=config.api_key,
        model=config.vision_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"image": _to_file_uri(before_path)},
                    {"image": _to_file_uri(after_path)},
                    {"text": prompt},
                ],
            }
        ],
        response_format={"type": "json_object"},
    )
    if response.status_code != HTTPStatus.OK:
        default["reason"] = "Pair L2 API 失败"
        return default
    text = response.output.choices[0].message.content
    if isinstance(text, list):
        text = text[0].get("text", "{}")
    (run_dir / "replication_pair_raw.json").write_text(str(text), encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        default["reason"] = "Pair L2 JSON 解析失败"
        return default
    passed = bool(payload.get("pass"))
    if passed:
        passed = (
            bool(payload.get("same_person"))
            and bool(payload.get("before_is_bareer"))
            and bool(payload.get("after_is_full_makeup"))
        )
    return {
        "same_person": bool(payload.get("same_person")),
        "before_is_bareer": bool(payload.get("before_is_bareer")),
        "after_is_full_makeup": bool(payload.get("after_is_full_makeup")),
        "pass": passed,
        "reason": str(payload.get("reason") or ""),
    }


def pick_after_timestamp_tail(
    hints: dict[str, Any], window_start: float, window_end: float
) -> tuple[float, str]:
    layout = (hints.get("tail_layout") or "none").lower()
    split_sec = hints.get("split_frame_sec")
    if layout == "split" and split_sec is not None:
        ts = float(split_sec)
        if _in_tail(ts, window_start, window_end):
            return ts, "tail_split"
    tail_after = hints.get("tail_after_sec")
    if tail_after is not None:
        ts = float(tail_after)
        if _in_tail(ts, window_start, window_end):
            return ts, "tail_segment"
    mid = (window_start + window_end) / 2.0
    return mid, "tail_segment_fallback"


def _merge_keyframe_qa(run_dir: Path, replication_doc: dict[str, Any]) -> None:
    path = run_dir / "keyframe-qa.json"
    doc: dict[str, Any] = {}
    if path.is_file():
        doc = json.loads(path.read_text(encoding="utf-8"))
    doc["replication_pair"] = replication_doc
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def _rename_to_ts(path: Path, prefix: str, ts: float, keyframes_dir: Path) -> Path:
    new_name = _filename(prefix, ts)
    dest = keyframes_dir / new_name
    if not path.is_file():
        return dest
    if path.name == new_name:
        return path
    if path.resolve() != dest.resolve():
        if dest.exists():
            dest.unlink()
        path.replace(dest)
    return dest


def _build_val(
    l1: dict[str, Any],
    single: dict[str, Any] | None,
    *,
    l2_skipped: bool,
    role: str,
) -> dict[str, Any]:
    if l2_skipped:
        return {
            "pass": bool(l1.get("pass")),
            "l1_pass": bool(l1.get("pass")),
            "reason": l1.get("reason", ""),
            "l2_skipped": True,
        }
    single = single or {}
    passed = bool(l1.get("pass")) and bool(single.get("pass"))
    out: dict[str, Any] = {
        "pass": passed,
        "l1_pass": bool(l1.get("pass")),
        "has_face": single.get("has_face"),
        "face_sufficient": single.get("face_sufficient"),
        "reason": single.get("reason") or l1.get("reason", ""),
        "l2_skipped": False,
    }
    if role == "replication_after":
        out["makeup_complete"] = single.get("makeup_complete")
    else:
        out["makeup_minimal"] = single.get("makeup_minimal")
    return out


def _try_before_first_step(
    config: ParseConfig,
    ffmpeg: str,
    ffprobe: str,
    video_path: Path,
    duration_sec: float,
    steps: list[dict[str, Any]],
    keyframes_dir: Path,
    run_dir: Path,
    before_path: Path,
    *,
    do_l2: bool,
) -> tuple[float, str, dict[str, Any], dict[str, Any] | None, bool]:
    """Returns ts, source, l1, single_l2, ok."""
    first = pick_first_step(steps)
    if not first:
        return 0.0, "first_step_start", {"pass": False, "reason": "无步骤"}, None, False
    kf = find_keyframe(first, "step_start_face")
    ts = float(kf["timestamp_sec"]) if kf else _step_start(first)
    _progress(config, f"复刻妆前（首步 start）{first.get('step_name', '')}…")
    ts, l1 = _ensure_frame_from_kf_or_extract(
        ffmpeg,
        ffprobe,
        video_path,
        duration_sec,
        kf,
        ts,
        before_path,
        keyframes_dir,
    )
    if not do_l2:
        return ts, "first_step_start", l1, None, bool(l1.get("pass"))

    if not l1.get("pass"):
        return ts, "first_step_start", l1, None, False

    single = vision_single_replication_frame(
        config,
        before_path,
        role="replication_before",
        run_dir=run_dir,
        raw_name="replication_before_l2_raw.json",
    )
    if single.get("pass"):
        return ts, "first_step_start", l1, single, True

    # ±1.5s retries（与 L1 候选合计最多约 3 次语义验收）
    best_ts, best_l1, best_single = ts, l1, single
    for off in (1.5, -1.5):
        attempt_ts = ts + off
        extract_single_frame(
            ffmpeg, video_path, attempt_ts, before_path, duration_sec
        )
        l1 = l1_check(before_path, ffprobe)
        if not l1["pass"]:
            continue
        single = vision_single_replication_frame(
            config,
            before_path,
            role="replication_before",
            run_dir=run_dir,
            raw_name="replication_before_l2_raw.json",
        )
        best_ts, best_l1, best_single = attempt_ts, l1, single
        if single.get("pass"):
            return attempt_ts, "first_step_start", l1, single, True
    return best_ts, "first_step_start", best_l1, best_single, False


def _try_after_last_step(
    config: ParseConfig,
    ffmpeg: str,
    ffprobe: str,
    video_path: Path,
    duration_sec: float,
    steps: list[dict[str, Any]],
    keyframes_dir: Path,
    run_dir: Path,
    after_path: Path,
    *,
    do_l2: bool,
) -> tuple[float, str, dict[str, Any], dict[str, Any] | None, bool, list[str]]:
    warnings: list[str] = []
    last = pick_last_makeup_step(steps)
    if not last:
        warnings.append("after_no_makeup_step")
        return 0.0, "last_step_end", {"pass": False, "reason": "无化妆步骤"}, None, False, warnings

    step_name = last.get("step_name") or ""
    end_sec = _step_end(last)
    start_sec = _step_start(last)
    duration = max(0.0, end_sec - start_sec)
    kf = find_keyframe(last, "step_end_face")
    _progress(config, f"复刻妆后（末化妆步 end）{step_name}…")

    ts = float(kf["timestamp_sec"]) if kf else end_sec
    ts, l1 = _ensure_frame_from_kf_or_extract(
        ffmpeg,
        ffprobe,
        video_path,
        duration_sec,
        kf,
        ts,
        after_path,
        keyframes_dir,
    )
    if not do_l2:
        return ts, "last_step_end", l1, None, bool(l1.get("pass")), warnings

    if not l1.get("pass"):
        # Still attempt end-window scan below
        single = {
            "pass": False,
            "has_face": False,
            "face_sufficient": False,
            "makeup_complete": False,
            "makeup_minimal": False,
            "reason": l1.get("reason") or "L1 未通过",
        }
    else:
        single = vision_single_replication_frame(
            config,
            after_path,
            role="replication_after",
            run_dir=run_dir,
            raw_name="replication_after_l2_raw.json",
        )
        if single.get("pass"):
            return ts, "last_step_end", l1, single, True, warnings

    # Scan [end-W, end]
    w = min(LAST_STEP_SCAN_CAP_SEC, max(LAST_STEP_SCAN_MIN_SEC, duration))
    scan_start = max(start_sec, end_sec - w)
    _progress(config, f"复刻妆后步末扫描 {step_name}…")
    t = end_sec
    best_ts, best_l1, best_single = ts, l1, single
    while t >= scan_start - 1e-6:
        extract_single_frame(ffmpeg, video_path, t, after_path, duration_sec)
        l1 = l1_check(after_path, ffprobe)
        if l1["pass"]:
            single = vision_single_replication_frame(
                config,
                after_path,
                role="replication_after",
                run_dir=run_dir,
                raw_name="replication_after_l2_raw.json",
            )
            best_ts, best_l1, best_single = t, l1, single
            if single.get("pass"):
                return t, "last_step_scan", l1, single, True, warnings
        t -= 1.0
    return best_ts, "last_step_scan", best_l1, best_single, False, warnings


def _tail_fallback(
    config: ParseConfig,
    ffmpeg: str,
    ffprobe: str,
    video_path: Path,
    duration_sec: float,
    steps: list[dict[str, Any]],
    hints: dict[str, Any],
    keyframes_dir: Path,
    run_dir: Path,
    before_path: Path,
    after_path: Path,
    *,
    need_before: bool,
    need_after: bool,
    do_l2: bool,
    before_ts: float,
    before_source: str,
    b_l1: dict[str, Any],
    b_single: dict[str, Any] | None,
    after_ts: float,
    after_source: str,
    a_l1: dict[str, Any],
    a_single: dict[str, Any] | None,
) -> tuple[
    float,
    str,
    dict[str, Any],
    dict[str, Any] | None,
    float,
    str,
    dict[str, Any],
    dict[str, Any] | None,
    list[str],
]:
    warnings = ["after_fallback_tail"] if need_after else []
    if need_before:
        warnings.append("before_fallback_hint")
    window_start, window_end = compute_tail_window(duration_sec, steps)
    layout = (hints.get("tail_layout") or "none").lower()

    if need_after or need_before:
        cand_ts, cand_source = pick_after_timestamp_tail(
            hints, window_start, window_end
        )
        if layout == "split" and cand_source == "tail_split" and need_after and need_before:
            full_tmp = run_dir / "replication_split_full.jpg"
            extract_single_frame(
                ffmpeg, video_path, cand_ts, full_tmp, duration_sec
            )
            sides = (
                vision_split_sides(config, full_tmp, run_dir) if do_l2 else None
            )
            if sides:
                try:
                    ffmpeg_crop_half(
                        ffmpeg, full_tmp, before_path, sides["before_side"]
                    )
                    ffmpeg_crop_half(
                        ffmpeg, full_tmp, after_path, sides["after_side"]
                    )
                    b_l1 = l1_check(before_path, ffprobe)
                    a_l1 = l1_check(after_path, ffprobe)
                    if b_l1["pass"] and a_l1["pass"]:
                        before_ts, before_source = cand_ts, "tail_split"
                        after_ts, after_source = cand_ts, "tail_split"
                        need_before = need_after = False
                        if do_l2:
                            b_single = vision_single_replication_frame(
                                config,
                                before_path,
                                role="replication_before",
                                run_dir=run_dir,
                                raw_name="replication_before_l2_raw.json",
                            )
                            a_single = vision_single_replication_frame(
                                config,
                                after_path,
                                role="replication_after",
                                run_dir=run_dir,
                                raw_name="replication_after_l2_raw.json",
                            )
                except subprocess.CalledProcessError:
                    pass

    if need_before:
        tb = hints.get("tail_before_sec")
        if layout == "sequence" and tb is not None:
            tbf = float(tb)
            if _in_tail(tbf, window_start - 5.0, window_end):
                before_ts, b_l1 = extract_with_l1(
                    ffmpeg, ffprobe, video_path, duration_sec, tbf, before_path
                )
                before_source = "tail_sequence"
                if do_l2 and b_l1["pass"]:
                    b_single = vision_single_replication_frame(
                        config,
                        before_path,
                        role="replication_before",
                        run_dir=run_dir,
                        raw_name="replication_before_l2_raw.json",
                    )
                need_before = False
        if need_before:
            baseline = hints.get("baseline_before_sec")
            ts = float(baseline) if baseline is not None else before_ts
            before_ts, b_l1 = extract_with_l1(
                ffmpeg, ffprobe, video_path, duration_sec, ts, before_path
            )
            before_source = "tutorial_baseline"
            if do_l2 and b_l1["pass"]:
                b_single = vision_single_replication_frame(
                    config,
                    before_path,
                    role="replication_before",
                    run_dir=run_dir,
                    raw_name="replication_before_l2_raw.json",
                )

    if need_after:
        after_ts, after_source = pick_after_timestamp_tail(
            hints, window_start, window_end
        )
        after_ts, a_l1 = extract_with_l1(
            ffmpeg, ffprobe, video_path, duration_sec, after_ts, after_path
        )
        if do_l2 and a_l1["pass"]:
            a_single = vision_single_replication_frame(
                config,
                after_path,
                role="replication_after",
                run_dir=run_dir,
                raw_name="replication_after_l2_raw.json",
            )
            if not a_single.get("pass") and after_source == "tail_segment":
                warnings.append("after_hint_rejected_by_l2")
                # 1s scan in tail window
                t = window_end
                while t >= window_start - 1e-6:
                    extract_single_frame(
                        ffmpeg, video_path, t, after_path, duration_sec
                    )
                    a_l1 = l1_check(after_path, ffprobe)
                    if a_l1["pass"]:
                        a_single = vision_single_replication_frame(
                            config,
                            after_path,
                            role="replication_after",
                            run_dir=run_dir,
                            raw_name="replication_after_l2_raw.json",
                        )
                        after_ts = t
                        after_source = "tail_segment"
                        if a_single.get("pass"):
                            break
                    t -= 1.0
                else:
                    mid = (window_start + window_end) / 2.0
                    after_ts, a_l1 = extract_with_l1(
                        ffmpeg, ffprobe, video_path, duration_sec, mid, after_path
                    )
                    after_source = "tail_segment_fallback"
                    if do_l2 and a_l1["pass"]:
                        a_single = vision_single_replication_frame(
                            config,
                            after_path,
                            role="replication_after",
                            run_dir=run_dir,
                            raw_name="replication_after_l2_raw.json",
                        )

    return (
        before_ts,
        before_source,
        b_l1,
        b_single,
        after_ts,
        after_source,
        a_l1,
        a_single,
        warnings,
    )


def run_replication_refs(
    config: ParseConfig,
    ffmpeg: str,
    ffprobe: str,
    video_path: Path,
    duration_sec: float,
    steps: list[dict[str, Any]],
    hints: dict[str, Any],
    keyframes_dir: Path,
    run_dir: Path,
    analysis: dict[str, Any],
) -> dict[str, Any]:
    keyframes_dir.mkdir(parents=True, exist_ok=True)
    window_start, window_end = compute_tail_window(duration_sec, steps)
    do_l2 = bool(config.enable_keyframe_qa)
    warnings: list[str] = []

    before_path = keyframes_dir / _filename("复刻-妆前", 0.0)
    after_path = keyframes_dir / _filename("复刻-妆后", 0.0)

    before_ts, before_source, b_l1, b_single, before_ok = _try_before_first_step(
        config,
        ffmpeg,
        ffprobe,
        video_path,
        duration_sec,
        steps,
        keyframes_dir,
        run_dir,
        before_path,
        do_l2=do_l2,
    )
    before_path = _rename_to_ts(
        before_path, "复刻-妆前", before_ts, keyframes_dir
    )

    after_ts, after_source, a_l1, a_single, after_ok, w2 = _try_after_last_step(
        config,
        ffmpeg,
        ffprobe,
        video_path,
        duration_sec,
        steps,
        keyframes_dir,
        run_dir,
        after_path,
        do_l2=do_l2,
    )
    warnings.extend(w2)
    after_path = _rename_to_ts(after_path, "复刻-妆后", after_ts, keyframes_dir)

    need_before = not before_ok
    need_after = not after_ok
    if need_before or need_after:
        _progress(config, "复刻参考片尾回退…")
        (
            before_ts,
            before_source,
            b_l1,
            b_single,
            after_ts,
            after_source,
            a_l1,
            a_single,
            w3,
        ) = _tail_fallback(
            config,
            ffmpeg,
            ffprobe,
            video_path,
            duration_sec,
            steps,
            hints,
            keyframes_dir,
            run_dir,
            before_path,
            after_path,
            need_before=need_before,
            need_after=need_after,
            do_l2=do_l2,
            before_ts=before_ts,
            before_source=before_source,
            b_l1=b_l1,
            b_single=b_single,
            after_ts=after_ts,
            after_source=after_source,
            a_l1=a_l1,
            a_single=a_single,
        )
        warnings.extend(w3)
        before_path = _rename_to_ts(before_path, "复刻-妆前", before_ts, keyframes_dir)
        after_path = _rename_to_ts(after_path, "复刻-妆后", after_ts, keyframes_dir)

    # Ensure final filenames exist at expected paths
    final_before = keyframes_dir / _filename("复刻-妆前", before_ts)
    final_after = keyframes_dir / _filename("复刻-妆后", after_ts)
    if before_path.is_file() and before_path.resolve() != final_before.resolve():
        before_path = _rename_to_ts(before_path, "复刻-妆前", before_ts, keyframes_dir)
    else:
        before_path = final_before if final_before.is_file() else before_path
    if after_path.is_file() and after_path.resolve() != final_after.resolve():
        after_path = _rename_to_ts(after_path, "复刻-妆后", after_ts, keyframes_dir)
    else:
        after_path = final_after if final_after.is_file() else after_path

    b_val = _build_val(
        b_l1, b_single, l2_skipped=not do_l2, role="replication_before"
    )
    a_val = _build_val(
        a_l1, a_single, l2_skipped=not do_l2, role="replication_after"
    )

    if do_l2 and b_val["pass"] and a_val["pass"]:
        pair_validation = vision_pair_validation(
            config, before_path, after_path, run_dir
        )
    elif do_l2:
        pair_validation = {
            "same_person": False,
            "before_is_bareer": bool((b_single or {}).get("makeup_minimal")),
            "after_is_full_makeup": bool((a_single or {}).get("makeup_complete")),
            "pass": False,
            "reason": "单帧 L2 未全部通过，跳过 Pair",
        }
    else:
        pair_validation = {
            "same_person": True,
            "before_is_bareer": True,
            "after_is_full_makeup": True,
            "pass": b_l1.get("pass") and a_l1.get("pass"),
            "reason": "L2 已跳过",
            "l2_skipped": True,
        }

    # Deduplicate warnings
    warnings = list(dict.fromkeys(warnings))

    refs = {
        "refs_version": REFS_VERSION,
        "after": {
            "role": "replication_after",
            "timestamp_sec": after_ts,
            "label": "步骤结束完成妆容",
            "filename": after_path.name,
            "source": after_source,
            "validation": a_val,
        },
        "before": {
            "role": "replication_before",
            "timestamp_sec": before_ts,
            "label": "复刻基线妆前",
            "filename": before_path.name,
            "source": before_source,
            "validation": b_val,
        },
        "pair_validation": {
            k: pair_validation[k]
            for k in (
                "same_person",
                "before_is_bareer",
                "after_is_full_makeup",
                "pass",
                "reason",
            )
            if k in pair_validation
        },
    }

    analysis["contract_version"] = CONTRACT_VERSION_V21
    analysis["makeup_replication_refs"] = refs

    qa_doc = {
        "items": [
            {
                "role": "replication_before",
                "filename": before_path.name,
                "l1": b_l1,
                "validation": b_val,
            },
            {
                "role": "replication_after",
                "filename": after_path.name,
                "l1": a_l1,
                "validation": a_val,
            },
        ],
        "pair_validation": refs["pair_validation"],
    }
    _merge_keyframe_qa(run_dir, qa_doc)

    summary: dict[str, Any] = {
        "pass": refs["pair_validation"]["pass"],
        "after_source": after_source,
        "before_source": before_source,
        "reason": refs["pair_validation"]["reason"],
        "window_start_sec": window_start,
        "window_end_sec": window_end,
    }
    if warnings:
        summary["warnings"] = warnings
    return summary
