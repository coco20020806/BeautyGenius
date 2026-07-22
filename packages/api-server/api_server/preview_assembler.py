from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from api_server.config import API_PUBLIC_BASE_URL

DEFAULT_PALETTE = ["#ead6cf", "#d8aaa0", "#b87870", "#8e554f", "#f2e5dd"]

DIFFICULTY_LABELS = {
    "easy": "新手友好",
    "medium": "进阶",
    "hard": "高阶",
    "unknown": "—",
}


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if not path or not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_palette(tutorial: dict[str, Any] | None) -> list[str]:
    if not tutorial:
        return list(DEFAULT_PALETTE)
    found: list[str] = []
    for step in tutorial.get("steps") or []:
        for key in ("hex", "color", "shade"):
            val = step.get(key)
            if isinstance(val, str) and val.startswith("#"):
                found.append(val)
        product = step.get("product") or {}
        for kw in product.get("keywords") or []:
            if isinstance(kw, str) and kw.startswith("#"):
                found.append(kw)
    if len(found) >= 3:
        return found[:5]
    tags = (tutorial.get("style_tags") or []) + (tutorial.get("occasion_tags") or [])
    if tags:
        return list(DEFAULT_PALETTE)
    return list(DEFAULT_PALETTE)


def _hints_from_tutorial(
    tutorial: dict[str, Any] | None,
    *,
    average_baseline: bool,
    transfer_skipped: bool = False,
) -> list[dict[str, str]]:
    hints: list[dict[str, str]] = []
    if transfer_skipped:
        hints.append(
            {
                "title": "已跳过妆容生成",
                "description": "未调用 AI 适配；对比图右侧为教程参考妆面，非个人妆效预览。",
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
    if average_baseline:
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
    display = preview_run_dir / "target_display.jpg"
    if display.is_file():
        return "target_display.jpg"
    return "target.jpg"


def comparison_from_alignment(alignment: dict[str, Any] | None) -> dict[str, Any] | None:
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
    est = (tutorial or {}).get("estimated_time")
    if isinstance(est, int) and est > 0:
        duration = f"约 {est} 分钟"
    else:
        dur_sec = (tutorial or {}).get("duration")
        if isinstance(dur_sec, int) and dur_sec > 0:
            duration = f"约 {max(1, round(dur_sec / 60))} 分钟"
        else:
            duration = "约 15 分钟"

    target = (preview_doc or {}).get("target") or {}
    average_baseline = target.get("type") == "average_baseline"
    transfer = (preview_doc or {}).get("transfer") or {}
    transfer_skipped = bool(transfer.get("skipped"))

    base = API_PUBLIC_BASE_URL
    before_name = before_image_filename(preview_run_dir)
    before_image = f"{base}/media/{task_id}/{before_name}"
    after_image = f"{base}/media/{task_id}/preview_01.jpg"

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
        "palette": _extract_palette(tutorial),
        "hints": _hints_from_tutorial(
            tutorial,
            average_baseline=average_baseline,
            transfer_skipped=transfer_skipped,
        ),
    }
    if comparison:
        payload["comparison"] = comparison
    return payload


def publish_media_files(task_id: str, preview_run_dir: Path, task_dir: Path) -> Path:
    media_dir = task_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "target.jpg": preview_run_dir / "target.jpg",
        "target_display.jpg": preview_run_dir / "target_display.jpg",
        "preview_01.jpg": preview_run_dir / "preview_01.jpg",
    }
    for name, src in mapping.items():
        if src.is_file():
            shutil.copy2(src, media_dir / name)
        elif name == "preview_01.jpg" and (preview_run_dir / "reference.jpg").is_file():
            shutil.copy2(preview_run_dir / "reference.jpg", media_dir / name)
    return media_dir
