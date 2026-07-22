#!/usr/bin/env python3
"""Package latest 示例视频1 pipeline outputs into archive + frontend fixture."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_ROOT = REPO_ROOT / "outputs" / "tasks"


def _latest_sample1_task() -> Path:
    candidates: list[Path] = []
    for task_dir in TASKS_ROOT.iterdir():
        task_json = task_dir / "task.json"
        if not task_json.is_file():
            continue
        try:
            doc = json.loads(task_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if doc.get("fileName") != "示例视频1.mp4":
            continue
        if doc.get("status") != "completed":
            continue
        if not doc.get("parse_run_dir") or not doc.get("preview_run_dir"):
            continue
        if doc.get("step_diagrams_status") != "completed":
            continue
        candidates.append(task_dir)
    if not candidates:
        raise SystemExit("未找到已完成的示例视频1任务（需 parse + preview + step-diagrams）")
    return max(candidates, key=lambda p: (p / "task.json").stat().st_mtime)


def _fmt_slice(clip: object) -> str:
    if not isinstance(clip, dict):
        return "00:00–00:00"
    start = float(clip.get("start") or 0)
    end = float(clip.get("end") or 0)

    def mmss(sec: float) -> str:
        value = max(0, int(round(sec)))
        return f"{value // 60:02d}:{value % 60:02d}"

    return f"{mmss(start)}–{mmss(end)}"


def _duration_label(sec: object) -> str:
    try:
        value = float(sec)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "约 15 分钟"
    if value <= 0:
        return "约 15 分钟"
    if value < 60:
        return f"约 {int(value)} 秒"
    return f"约 {max(1, round(value / 60))} 分钟"


def main() -> int:
    task_dir = _latest_sample1_task()
    task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    task_id = task["taskId"]
    parse_run = Path(task["parse_run_dir"])
    preview_run = Path(task["preview_run_dir"])
    picture_run = Path(task["step_diagrams_run_dir"])
    task_media = task_dir / "media"
    tutorial_src = Path(task.get("tutorial_path") or (parse_run / "tutorial.json"))

    archive = REPO_ROOT / "示例视频1解析结果"
    fixture = REPO_ROOT / "frontend" / "src" / "fixtures" / "collected" / "sample-1"

    for dest in (archive, fixture):
        if dest.exists():
            shutil.rmtree(dest)
        (dest / "media").mkdir(parents=True)

    media_names = [
        "target_display.jpg",
        "preview_display.jpg",
        "preview_01.jpg",
        "target.jpg",
        *[p.name for p in sorted(task_media.glob("diagram_*.jpg"))],
    ]
    for name in media_names:
        src = task_media / name
        if not src.is_file():
            raise SystemExit(f"缺少媒体文件：{src}")
        shutil.copy2(src, archive / "media" / name)
        shutil.copy2(src, fixture / "media" / name)

    shutil.copy2(tutorial_src, archive / "tutorial.json")
    shutil.copy2(tutorial_src, fixture / "tutorial.json")
    shutil.copy2(preview_run / "preview.json", archive / "preview.json")
    shutil.copy2(preview_run / "preview.json", fixture / "preview.json")
    shutil.copy2(picture_run / "manifest.json", archive / "picture_makeup_manifest.json")
    shutil.copy2(picture_run / "manifest.json", fixture / "picture_makeup_manifest.json")

    tutorial = json.loads(tutorial_src.read_text(encoding="utf-8"))
    preview = json.loads((preview_run / "preview.json").read_text(encoding="utf-8"))
    alignment = preview.get("alignment") or {}
    display_size = alignment.get("display_size") or alignment.get("target_size")
    object_position = alignment.get("object_position")

    part_map = {
        "prep": "base",
        "base": "base",
        "set": "base",
        "concealer": "base",
        "brow": "brows",
        "eye": "eyes",
        "cheek": "blush",
        "contour": "contour",
        "highlight": "highlight",
        "lip": "lips",
    }
    colors = {
        "base": "#ead6cf",
        "brows": "#8d7167",
        "eyes": "#c98586",
        "blush": "#d3787d",
        "contour": "#b18b7b",
        "highlight": "#f2dfc3",
        "lips": "#a94f5b",
    }

    illustrated: list[dict[str, object]] = []
    for index, step in enumerate(tutorial.get("steps") or [], start=1):
        sid = step.get("step_id") or f"step_{index}"
        raw_part = str(step.get("part") or "other").strip()
        part = part_map.get(raw_part, "base")
        title = str(step.get("display_title") or step.get("taxonomy_primary") or sid).strip()
        product = str(step.get("display_product") or "").strip()
        if not product:
            prod = step.get("product") or {}
            if isinstance(prod, dict):
                product = str(prod.get("name") or "").strip()
                if product == "unknown":
                    product = ""
            if not product:
                product = str(step.get("taxonomy_primary") or "待补充产品").strip()
        instruction = str(step.get("instruction") or "").strip() or title
        tip = str(step.get("technique") or step.get("adaptation_note") or "").strip() or "按步骤循序渐进。"
        diagram_name = f"diagram_{sid}.jpg"
        illustrated.append(
            {
                "id": sid,
                "order": index,
                "title": title,
                "part": part,
                "product": product,
                "color": colors[part],
                "instruction": instruction,
                "expertTip": tip,
                "videoSlice": _fmt_slice(step.get("video_clip")),
                "hasEyeGuide": part == "eyes",
                "diagramImage": f"media/{diagram_name}" if (task_media / diagram_name).is_file() else "",
            }
        )

    difficulty_map = {
        "beginner": "新手",
        "intermediate": "进阶",
        "advanced": "进阶",
        "unknown": "—",
    }
    style_tags = tutorial.get("style_tags") or []
    occasion_tags = tutorial.get("occasion_tags") or []
    style = style_tags[0] if style_tags else "自然妆感"
    occasion = " · ".join(occasion_tags) if occasion_tags else "日常"
    difficulty = difficulty_map.get(str(tutorial.get("difficulty") or "unknown"), "—")
    duration = _duration_label(tutorial.get("duration"))

    hints = [
        {
            "title": "平均脸预览",
            "description": "此为平均脸底图预览，不代表你的脸型；上传照片可获得更贴近个人的效果。",
            "tone": "adjust",
        },
        {
            "title": "适配说明",
            "description": "根据教程步骤生成的妆效预览，实际上妆时请按步骤循序渐进。",
            "tone": "neutral",
        },
    ]

    comparison: dict[str, object] = {
        "width": int(display_size[0]) if isinstance(display_size, list) and len(display_size) == 2 else 1254,
        "height": int(display_size[1]) if isinstance(display_size, list) and len(display_size) == 2 else 1254,
    }
    if isinstance(object_position, str) and object_position.strip():
        comparison["objectPosition"] = object_position.strip()

    detail = {
        "id": "collected-sample-1",
        "title": "示例视频1",
        "previewTitle": str(tutorial.get("title") or "").strip() or "教程妆容预览",
        "style": style,
        "occasion": occasion,
        "difficulty": difficulty,
        "duration": duration,
        "hints": hints,
        "beforeImage": "media/target_display.jpg",
        "afterImage": "media/preview_display.jpg",
        "coverImage": "media/preview_display.jpg",
        "comparison": comparison,
        "illustratedSteps": illustrated,
        "tutorialJsonPath": "tutorial.json",
    }

    manifest = {
        "sample_id": "collected-sample-1",
        "title": "示例视频1",
        "source_video": "示例视频1.mp4",
        "task_id": task_id,
        "packaged_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "parse_run_dir": parse_run.relative_to(REPO_ROOT).as_posix(),
            "preview_run_dir": preview_run.relative_to(REPO_ROOT).as_posix(),
            "picture_makeup_run_dir": picture_run.relative_to(REPO_ROOT).as_posix(),
            "task_dir": f"outputs/tasks/{task_id}",
            "tutorial_json": tutorial_src.relative_to(REPO_ROOT).as_posix(),
        },
        "materials": {
            "before_image": "media/target_display.jpg",
            "after_image": "media/preview_display.jpg",
            "cover_image": "media/preview_display.jpg",
            "tutorial_json": "tutorial.json",
            "diagrams": [s["diagramImage"] for s in illustrated if s["diagramImage"]],
            "preview_json": "preview.json",
            "picture_makeup_manifest": "picture_makeup_manifest.json",
        },
        "detail": {k: v for k, v in detail.items() if k != "illustratedSteps"},
        "step_count": len(illustrated),
    }

    for dest in (archive, fixture):
        (dest / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (dest / "detail.json").write_text(
            json.dumps(detail, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    zip_stem = REPO_ROOT / "示例视频1解析结果"
    zip_path = REPO_ROOT / "示例视频1解析结果.zip"
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_stem), "zip", archive)

    print(archive)
    print(fixture)
    print(zip_path)
    print(json.dumps({"task_id": task_id, "steps": len(illustrated)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
