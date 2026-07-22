"""Vision enrichment from keyframes / short clips."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from tutorial_mapper.config import MapperConfig
from tutorial_mapper.llm import call_vision_json

VISION_SYSTEM = """你是美妆视觉分析助手。根据步骤关键帧/截图，补全 visual_layer 等视觉字段。
只输出合法 JSON：
{
  "steps": [
    {
      "step_id": "与输入相同",
      "visual_layer": {
        "shape": "soft_oval|wing|line|diffuse|other",
        "color": "#RRGGBB",
        "opacity": 0.0到1.0,
        "position": "中文位置描述"
      },
      "product_keywords": ["可选补充关键词"]
    }
  ],
  "eye_detail": {}
}
约束：只填能从画面判断的字段；不确定则省略该 step。不要编造时间轴。
"""

SUBPROCESS_CAPTURE = {
    "capture_output": True,
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
}


def _resolve_ffmpeg(config: MapperConfig) -> str:
    if config.ffmpeg_path:
        return config.ffmpeg_path
    found = shutil.which("ffmpeg")
    if found:
        return found
    local = Path.home() / ".local" / "ffmpeg" / "bin" / "ffmpeg.exe"
    if local.is_file():
        return str(local)
    raise RuntimeError("未找到 ffmpeg")


def _visual_layer_incomplete(vl: dict[str, Any] | None) -> bool:
    if not vl or not isinstance(vl, dict):
        return True
    return not (vl.get("color") and vl.get("position"))


def _instruction_short(step: dict[str, Any], threshold: int) -> bool:
    return len((step.get("instruction") or "").strip()) < threshold


def _product_weak(step: dict[str, Any]) -> bool:
    prod = step.get("product") or {}
    name = (prod.get("name") or "unknown").strip()
    kws = prod.get("keywords") or []
    return name == "unknown" and not kws


def needs_vision(step: dict[str, Any], config: MapperConfig) -> bool:
    return (
        _visual_layer_incomplete(step.get("visual_layer"))
        or _instruction_short(step, config.short_instruction_chars)
        or _product_weak(step)
    )


def _pick_keyframe_paths(step: dict[str, Any], keyframes_dir: Path) -> list[Path]:
    refs = step.get("keyframe_refs") or []
    preferred_roles = ("makeup_detail", "step_end_face", "step_start_face")
    ranked: list[tuple[int, Path]] = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        fname = ref.get("filename")
        if not fname:
            continue
        path = keyframes_dir / fname
        if not path.is_file():
            continue
        role = ref.get("role") or ""
        try:
            rank = preferred_roles.index(role)
        except ValueError:
            rank = 99
        ranked.append((rank, path))
    ranked.sort(key=lambda x: x[0])
    out: list[Path] = []
    seen: set[Path] = set()
    for _, p in ranked:
        if p not in seen:
            seen.add(p)
            out.append(p)
        if len(out) >= 2:
            break
    return out


def _extract_clip_frame(
    ffmpeg: str,
    video_path: Path,
    clip: dict[str, Any],
    out_path: Path,
    clip_sec: float,
) -> Path | None:
    start = float(clip.get("start") or 0)
    end = float(clip.get("end") or start)
    mid = (start + end) / 2.0
    # 取 clip 中点附近一帧
    ts = max(0.0, mid)
    out_path.parent.mkdir(parents=True, exist_ok=True)
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
        str(out_path),
    ]
    proc = subprocess.run(cmd, **SUBPROCESS_CAPTURE)
    if proc.returncode != 0 or not out_path.is_file():
        return None
    # clip_sec 预留：未来可扩成短视频；当前用单帧即可
    _ = clip_sec
    return out_path


def _resolve_source_video(analysis: dict[str, Any], parse_run_dir: Path) -> Path | None:
    video = analysis.get("video") or {}
    sp = video.get("source_path")
    if sp and Path(sp).is_file():
        return Path(sp)
    # 偶有代理文件
    proxy = parse_run_dir / "upload_proxy.mp4"
    if proxy.is_file():
        return proxy
    return None


def enrich_from_vision(
    config: MapperConfig,
    tutorial: dict[str, Any],
    *,
    parse_run_dir: Path,
    analysis: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not config.api_key:
        raise RuntimeError("视觉 enrichment 需要 DASHSCOPE_API_KEY")

    keyframes_dir = parse_run_dir / "keyframes"
    candidates = [s for s in (tutorial.get("steps") or []) if needs_vision(s, config)]
    meta: dict[str, Any] = {
        "source": "vision_llm",
        "model": config.vision_model,
        "steps_considered": [s["step_id"] for s in candidates],
        "steps_with_images": [],
        "fields_touched": [],
        "skipped_no_image": [],
    }
    if not candidates:
        return {"steps": {}, "eye_detail": {}}, meta

    video_path = _resolve_source_video(analysis, parse_run_dir)
    ffmpeg = None
    try:
        ffmpeg = _resolve_ffmpeg(config)
    except RuntimeError:
        ffmpeg = None

    clip_dir = parse_run_dir / "enrichment_frames"
    clip_dir.mkdir(parents=True, exist_ok=True)

    image_paths: list[Path] = []
    step_image_map: list[dict[str, Any]] = []
    for step in candidates:
        paths = _pick_keyframe_paths(step, keyframes_dir) if keyframes_dir.is_dir() else []
        if not paths and video_path and ffmpeg:
            out = clip_dir / f"{step['step_id']}_mid.jpg"
            extracted = _extract_clip_frame(
                ffmpeg,
                video_path,
                step.get("video_clip") or {},
                out,
                config.clip_extract_sec,
            )
            if extracted:
                paths = [extracted]
        if not paths:
            meta["skipped_no_image"].append(step["step_id"])
            continue
        meta["steps_with_images"].append(step["step_id"])
        # 每步最多 1 张，控制请求体积
        img = paths[0]
        image_paths.append(img)
        step_image_map.append(
            {
                "step_id": step["step_id"],
                "part": step.get("part"),
                "taxonomy_primary": step.get("taxonomy_primary"),
                "image_file": img.name,
                "instruction_seed": (step.get("instruction") or "")[:200],
            }
        )

    if not image_paths:
        return {"steps": {}, "eye_detail": {}}, meta

    user = (
        "以下图片按顺序对应 steps 列表中的条目。请为缺 visual_layer 的步骤补全 JSON：\n"
        + json.dumps(step_image_map, ensure_ascii=False, indent=2)
    )
    raw = call_vision_json(
        config,
        system=VISION_SYSTEM,
        user_text=user,
        image_paths=image_paths,
        run_dir=parse_run_dir,
        dump_name="raw_vision_enrichment.json",
    )

    known = {s["step_id"] for s in tutorial.get("steps") or []}
    patch: dict[str, Any] = {"steps": {}, "eye_detail": {}}
    for item in raw.get("steps") or []:
        if not isinstance(item, dict):
            continue
        sid = item.get("step_id")
        if sid not in known:
            continue
        step_patch: dict[str, Any] = {}
        vl = item.get("visual_layer")
        if isinstance(vl, dict) and (vl.get("color") or vl.get("position") or vl.get("shape")):
            cleaned: dict[str, Any] = {}
            if vl.get("shape"):
                cleaned["shape"] = str(vl["shape"])
            if vl.get("color"):
                cleaned["color"] = str(vl["color"])
            if vl.get("opacity") is not None:
                try:
                    cleaned["opacity"] = float(vl["opacity"])
                except (TypeError, ValueError):
                    pass
            if vl.get("position"):
                cleaned["position"] = str(vl["position"])
            if cleaned:
                step_patch["visual_layer"] = cleaned
        kws = item.get("product_keywords")
        if isinstance(kws, list) and kws:
            step_patch["product_keywords"] = [str(k).strip() for k in kws if str(k).strip()]
        if step_patch:
            patch["steps"][sid] = step_patch
            meta["fields_touched"].append(f"step:{sid}")

    eye = raw.get("eye_detail")
    if isinstance(eye, dict) and eye:
        patch["eye_detail"] = eye
        meta["fields_touched"].append("eye_detail")

    return patch, meta
