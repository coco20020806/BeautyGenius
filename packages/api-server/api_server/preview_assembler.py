from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from api_server.config import API_PUBLIC_BASE_URL

# 妆浓淡色块：浅→深 / opacity 低→高（见 skills/kol-makeup-preview/display-contract.md）
INTENSITY_LEVELS: list[dict[str, Any]] = [
    {"id": "L1", "color": "#ead6cf", "opacity": 0.2},
    {"id": "L2", "color": "#d8aaa0", "opacity": 0.4},
    {"id": "L3", "color": "#b87870", "opacity": 0.6},
    {"id": "L4", "color": "#8e554f", "opacity": 0.8},
    {"id": "L5", "color": "#5c3a36", "opacity": 1.0},
]

DEFAULT_PALETTE = [level["color"] for level in INTENSITY_LEVELS]

DIFFICULTY_LABELS = {
    "easy": "新手友好",
    "medium": "进阶",
    "hard": "高阶",
    "unknown": "—",
}


def format_video_duration_label(duration_sec: Any) -> str:
    """上传视频真实时长标签；禁止用 estimated_time。"""
    try:
        sec = int(duration_sec)
    except (TypeError, ValueError):
        return "约 15 分钟"
    if sec <= 0:
        return "约 15 分钟"
    if sec < 60:
        return f"约 {sec} 秒"
    return f"约 {max(1, round(sec / 60))} 分钟"


def intensity_levels() -> list[dict[str, Any]]:
    return [dict(level) for level in INTENSITY_LEVELS]


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if not path or not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_palette(_tutorial: dict[str, Any] | None) -> list[str]:
    """兼容字段：与 intensityLevels 同序颜色（浓淡控件，非配色摘要）。"""
    return list(DEFAULT_PALETTE)


def _generation_failure_reason(*, transfer_skipped: bool) -> str:
    if transfer_skipped:
        return "妆容预览已跳过，未生成适配图"
    return "妆容生成失败，暂无适配预览"


def _hints_from_tutorial(
    tutorial: dict[str, Any] | None,
    *,
    average_baseline: bool,
    transfer_skipped: bool = False,
    generation_failed: bool = False,
) -> list[dict[str, str]]:
    hints: list[dict[str, str]] = []
    if generation_failed:
        hints.append(
            {
                "title": "妆容生成失败",
                "description": _generation_failure_reason(transfer_skipped=transfer_skipped),
                "tone": "adjust",
            }
        )
    if tutorial:
        for item in (tutorial.get("practice_checklist") or [])[:3]:
            if isinstance(item, str) and item.strip():
                hints.append(
                    {
                        "title": "跟练提示",
                        "description": item.strip(),
                        "tone": "neutral",
                    }
                )
    if average_baseline and not generation_failed:
        hints.insert(
            0,
            {
                "title": "平均脸预览",
                "description": "此为平均脸底图预览，不代表你的脸型；上传照片可获得更贴近个人的效果。",
                "tone": "adjust",
            },
        )
    if not hints:
        hints.append(
            {
                "title": "适配说明",
                "description": "根据教程步骤生成的妆效预览，实际上妆时请按步骤循序渐进。",
                "tone": "neutral",
            }
        )
    return hints


def before_image_filename(preview_run_dir: Path) -> str:
    """妆前对比图：优先人脸裁切后的 target_display.jpg（与 preview_display 同尺寸）。"""
    if (preview_run_dir / "target_display.jpg").is_file():
        return "target_display.jpg"
    return "target.jpg"


def after_image_filename(preview_run_dir: Path) -> str | None:
    """妆后对比图：优先 preview_display.jpg；否则 preview_01.jpg；皆无则 None（禁止用 reference 占位）。"""
    if (preview_run_dir / "preview_display.jpg").is_file():
        return "preview_display.jpg"
    if (preview_run_dir / "preview_01.jpg").is_file():
        return "preview_01.jpg"
    return None


def comparison_from_alignment(alignment: dict[str, Any] | None) -> dict[str, Any] | None:
    """对比框优先用 display_size（展示裁切对），否则回退 target_size。"""
    if not alignment:
        return None
    size = alignment.get("display_size")
    if isinstance(size, list) and len(size) == 2:
        w, h = int(size[0]), int(size[1])
    else:
        target_size = alignment.get("target_size")
        if not (isinstance(target_size, list) and len(target_size) == 2):
            return None
        w, h = int(target_size[0]), int(target_size[1])
    out: dict[str, Any] = {"width": w, "height": h}
    obj = alignment.get("object_position")
    if isinstance(obj, str) and obj.strip():
        out["objectPosition"] = obj.strip()
    return out


def assemble_makeup_preview(
    task_id: str,
    *,
    tutorial_path: Path | None,
    preview_run_dir: Path,
    preview_doc: dict[str, Any] | None,
) -> dict[str, Any]:
    tutorial = _load_json(tutorial_path)
    title = (tutorial or {}).get("title") or "教程妆容预览"
    style_tags = (tutorial or {}).get("style_tags") or []
    occasion_tags = (tutorial or {}).get("occasion_tags") or []
    style = style_tags[0] if style_tags else "自然妆感"
    occasion = " · ".join(occasion_tags) if occasion_tags else "日常"
    difficulty_key = (tutorial or {}).get("difficulty") or "unknown"
    difficulty = DIFFICULTY_LABELS.get(difficulty_key, "—")
    duration = format_video_duration_label((tutorial or {}).get("duration"))
    levels = intensity_levels()

    target = (preview_doc or {}).get("target") or {}
    average_baseline = target.get("type") == "average_baseline"
    transfer = (preview_doc or {}).get("transfer") or {}
    transfer_skipped = bool(transfer.get("skipped"))

    base = API_PUBLIC_BASE_URL
    before_name = before_image_filename(preview_run_dir)
    after_name = after_image_filename(preview_run_dir)
    before_image = f"{base}/media/{task_id}/{before_name}"
    generation_failed = after_name is None
    after_image = f"{base}/media/{task_id}/{after_name}" if after_name else None
    failure_reason = (
        _generation_failure_reason(transfer_skipped=transfer_skipped) if generation_failed else None
    )

    alignment = (preview_doc or {}).get("alignment")
    comparison = comparison_from_alignment(alignment if isinstance(alignment, dict) else None)

    payload: dict[str, Any] = {
        "taskId": task_id,
        "title": title,
        "style": style,
        "occasion": occasion,
        "difficulty": difficulty,
        "duration": duration,
        "beforeImage": before_image,
        "afterImage": after_image,
        "generationFailed": generation_failed,
        "palette": _extract_palette(tutorial),
        "intensityLevels": levels,
        "hints": _hints_from_tutorial(
            tutorial,
            average_baseline=average_baseline,
            transfer_skipped=transfer_skipped,
            generation_failed=generation_failed,
        ),
    }
    if failure_reason:
        payload["generationFailureReason"] = failure_reason
    if comparison and not generation_failed:
        payload["comparison"] = comparison
    return payload


def publish_media_files(task_id: str, preview_run_dir: Path, task_dir: Path) -> Path:
    media_dir = task_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "target.jpg": preview_run_dir / "target.jpg",
        "target_display.jpg": preview_run_dir / "target_display.jpg",
        "preview_01.jpg": preview_run_dir / "preview_01.jpg",
        "preview_display.jpg": preview_run_dir / "preview_display.jpg",
    }
    for name, src in mapping.items():
        if src.is_file():
            shutil.copy2(src, media_dir / name)
    return media_dir
