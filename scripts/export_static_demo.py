#!/usr/bin/env python3
"""Export latest completed makeup task into a standalone static HTML demo.

Selects the newest ``outputs/tasks/*/task.json`` with ``status=completed`` and
both ``parse_run_dir`` + ``preview_run_dir``. When ``step_diagrams_status`` is
``completed``, also packages picture-makeup diagrams into the demo.

Usage:
    python scripts/export_static_demo.py

Output (tracked for git-pull deploy; Vite serves at ``/demo/``)::

    frontend/public/demo/index.html
    frontend/public/demo/assets/{app.css,app.js,data.js}
    frontend/public/demo/media/{before.jpg,after.jpg,video.mp4,diagram_*.jpg}

After export, commit ``frontend/public/demo/``. On the server: ``git pull`` then
``npm run build`` in ``frontend/``. Open ``https://<host>/demo/``.

Local preview::

    cd frontend/public/demo
    python -m http.server 8765
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_ROOT = REPO_ROOT / "outputs" / "tasks"
TEMPLATE_DIR = Path(__file__).resolve().parent / "static_demo_templates"
OUT_DIR = REPO_ROOT / "frontend" / "public" / "demo"

INTENSITY_LEVELS: list[dict[str, Any]] = [
    {"id": "L1", "color": "#ead6cf", "opacity": 0.2},
    {"id": "L2", "color": "#d8aaa0", "opacity": 0.4},
    {"id": "L3", "color": "#b87870", "opacity": 0.6},
    {"id": "L4", "color": "#8e554f", "opacity": 0.8},
    {"id": "L5", "color": "#5c3a36", "opacity": 1.0},
]

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


def _format_video_duration_label(duration_sec: Any) -> str:
    try:
        sec = int(duration_sec)
    except (TypeError, ValueError):
        return "约 15 分钟"
    if sec <= 0:
        return "约 15 分钟"
    if sec < 60:
        return f"约 {sec} 秒"
    return f"约 {max(1, round(sec / 60))} 分钟"


def _before_image_src(preview_run_dir: Path) -> Path:
    display = preview_run_dir / "target_display.jpg"
    if display.is_file():
        return display
    return preview_run_dir / "target.jpg"


def _after_image_src(preview_run_dir: Path) -> Path | None:
    for name in ("preview_display.jpg", "preview_01.jpg"):
        path = preview_run_dir / name
        if path.is_file():
            return path
    return None


def _comparison_from_alignment(alignment: dict[str, Any] | None) -> dict[str, Any] | None:
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


def _hints_from_tutorial(
    tutorial: dict[str, Any] | None,
    *,
    average_baseline: bool,
    transfer_skipped: bool = False,
    generation_failed: bool = False,
) -> list[dict[str, str]]:
    hints: list[dict[str, str]] = []
    if generation_failed:
        reason = (
            "妆容预览已跳过，未生成适配图"
            if transfer_skipped
            else "妆容生成失败，暂无适配预览"
        )
        hints.append({"title": "妆容生成失败", "description": reason, "tone": "adjust"})
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


def _assemble_preview(
    task_id: str,
    *,
    tutorial: dict[str, Any] | None,
    preview_run_dir: Path,
    preview_doc: dict[str, Any] | None,
) -> dict[str, Any]:
    title = (tutorial or {}).get("title") or "教程妆容预览"
    style_tags = (tutorial or {}).get("style_tags") or []
    occasion_tags = (tutorial or {}).get("occasion_tags") or []
    style = style_tags[0] if style_tags else "自然妆感"
    occasion = " · ".join(occasion_tags) if occasion_tags else "日常"
    difficulty_key = (tutorial or {}).get("difficulty") or "unknown"
    difficulty = DIFFICULTY_LABELS.get(difficulty_key, "—")
    duration = _format_video_duration_label((tutorial or {}).get("duration"))

    target = (preview_doc or {}).get("target") or {}
    average_baseline = target.get("type") == "average_baseline"
    transfer = (preview_doc or {}).get("transfer") or {}
    transfer_skipped = bool(transfer.get("skipped"))

    after_src = _after_image_src(preview_run_dir)
    generation_failed = after_src is None
    failure_reason = None
    if generation_failed:
        failure_reason = (
            "妆容预览已跳过，未生成适配图"
            if transfer_skipped
            else "妆容生成失败，暂无适配预览"
        )

    alignment = (preview_doc or {}).get("alignment")
    comparison = _comparison_from_alignment(
        alignment if isinstance(alignment, dict) else None
    )

    payload: dict[str, Any] = {
        "taskId": task_id,
        "title": title,
        "style": style,
        "occasion": occasion,
        "difficulty": difficulty,
        "duration": duration,
        "beforeImage": "media/before.jpg",
        "afterImage": None if generation_failed else "media/after.jpg",
        "generationFailed": generation_failed,
        "palette": [level["color"] for level in INTENSITY_LEVELS],
        "intensityLevels": [dict(level) for level in INTENSITY_LEVELS],
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


def _latest_completed_task() -> Path:
    candidates: list[Path] = []
    if not TASKS_ROOT.is_dir():
        raise SystemExit(f"未找到任务目录: {TASKS_ROOT}")
    for task_dir in TASKS_ROOT.iterdir():
        if not task_dir.is_dir() or task_dir.name.startswith("_"):
            continue
        task_json = task_dir / "task.json"
        if not task_json.is_file():
            continue
        try:
            doc = json.loads(task_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if doc.get("status") != "completed":
            continue
        if not doc.get("parse_run_dir") or not doc.get("preview_run_dir"):
            continue
        candidates.append(task_dir)
    if not candidates:
        raise SystemExit("未找到已完成且含 parse + preview 的任务")
    return max(candidates, key=lambda p: (p / "task.json").stat().st_mtime)


def _resolve_video(task: dict[str, Any], task_dir: Path) -> Path | None:
    video_path = task.get("video_path")
    if isinstance(video_path, str) and video_path.strip():
        path = Path(video_path)
        if path.is_file():
            return path
    upload = task_dir / "upload" / "video.mp4"
    if upload.is_file():
        return upload
    return None


def _clear_output_dir(path: Path) -> None:
    """Remove export dir; on Windows retry when a viewer briefly locks files."""
    if not path.exists():
        return
    last_err: Exception | None = None
    for attempt in range(5):
        try:
            shutil.rmtree(path)
            return
        except OSError as exc:
            last_err = exc
            # Clear children first — cwd lock on the folder itself is common on Windows
            if path.is_dir():
                for child in list(path.iterdir()):
                    try:
                        if child.is_dir():
                            shutil.rmtree(child, ignore_errors=True)
                        else:
                            child.unlink(missing_ok=True)
                    except OSError:
                        pass
            import time

            time.sleep(0.35 * (attempt + 1))
    raise SystemExit(
        f"无法清空导出目录（仍被占用）: {path}\n"
        f"请先停止对该目录的静态服务（如 python -m http.server / npx serve），"
        f"并确保终端当前目录不在 frontend/public/demo。\n原始错误: {last_err}"
    ) from last_err


def _safe_diagram_filename(step_id: str) -> str:
    safe = re.sub(r"[^\w.-]+", "_", str(step_id).strip())
    return f"diagram_{safe or 'step'}.jpg"


def _step_heading(step: dict[str, Any], index: int) -> str:
    display = (step.get("display_title") or "").strip()
    if display:
        return f"步骤 {index + 1} · {display}"
    primary = (step.get("taxonomy_primary") or "").strip()
    if primary:
        return f"步骤 {index + 1} · {primary}"
    sid = step.get("step_id") or f"step_{index}"
    return f"步骤 {index + 1} · {sid}"


def _read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


def _manifest_step_map(run_dir: Path | None) -> dict[str, dict[str, Any]]:
    if not run_dir:
        return {}
    manifest_path = run_dir / "manifest.json"
    doc = _load_json(manifest_path)
    if not doc:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in doc.get("steps") or []:
        if not isinstance(item, dict):
            continue
        sid = item.get("step_id")
        if sid:
            out[str(sid)] = item
    return out


def _assemble_step_diagrams(
    task_id: str,
    task: dict[str, Any],
    tutorial: dict[str, Any],
    *,
    has_video: bool,
) -> dict[str, Any] | None:
    status = task.get("step_diagrams_status") or "idle"
    if status != "completed":
        return None
    run_dir: Path | None = None
    if task.get("step_diagrams_run_dir"):
        run_dir = Path(task["step_diagrams_run_dir"])
    manifest_by_step = _manifest_step_map(run_dir)
    task_media = Path(task["media_dir"]) if task.get("media_dir") else None

    steps_out: list[dict[str, Any]] = []
    for index, step in enumerate(tutorial.get("steps") or []):
        if not isinstance(step, dict):
            continue
        step_id = str(step.get("step_id") or f"step_{index}")
        mentry = manifest_by_step.get(step_id) or {}
        step_status = mentry.get("status")
        if step_status == "ok":
            item_status = "ok"
        elif step_status == "failed":
            item_status = "failed"
        elif step_status == "skipped":
            item_status = "skipped"
        else:
            item_status = "pending"

        media_name = _safe_diagram_filename(step_id)
        image_url: str | None = None
        if task_media and (task_media / media_name).is_file():
            image_url = f"media/{media_name}"

        item: dict[str, Any] = {
            "stepId": step_id,
            "index": index,
            "heading": _step_heading(step, index),
            "imageUrl": image_url,
            "status": item_status,
        }
        clip = step.get("video_clip")
        if isinstance(clip, dict) and "start" in clip and "end" in clip:
            try:
                item["videoClip"] = {"start": float(clip["start"]), "end": float(clip["end"])}
            except (TypeError, ValueError):
                pass
        if run_dir:
            step_out_dir = run_dir / "steps" / step_id
            final_prompt = _read_text(step_out_dir / "final_prompt.txt")
            base_prompt = _read_text(step_out_dir / "base_prompt.txt")
            if final_prompt:
                item["finalPrompt"] = final_prompt
            if base_prompt:
                item["basePrompt"] = base_prompt
        err = mentry.get("error")
        if err:
            item["error"] = str(err)
        steps_out.append(item)

    if not steps_out:
        return None

    payload: dict[str, Any] = {
        "taskId": task_id,
        "status": status,
        "steps": steps_out,
    }
    if has_video:
        payload["videoUrl"] = "media/video.mp4"
    if task.get("step_diagrams_progress"):
        payload["progress"] = task["step_diagrams_progress"]
    failure = task.get("step_diagrams_failure")
    if failure:
        payload["failureReason"] = failure
    return payload


def _copy_diagram_media(task: dict[str, Any], dest_media: Path) -> int:
    src_media = Path(task["media_dir"]) if task.get("media_dir") else None
    if not src_media or not src_media.is_dir():
        return 0
    count = 0
    for src in sorted(src_media.glob("diagram_*.jpg")):
        shutil.copy2(src, dest_media / src.name)
        count += 1
    return count


def main() -> int:
    for name in ("index.html", "app.css", "app.js"):
        path = TEMPLATE_DIR / name
        if not path.is_file():
            raise SystemExit(f"缺少模板: {path}")

    task_dir = _latest_completed_task()
    task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    task_id = str(task["taskId"])
    parse_run = Path(task["parse_run_dir"])
    preview_run = Path(task["preview_run_dir"])
    tutorial_path = Path(task.get("tutorial_path") or (parse_run / "tutorial.json"))
    if task.get("optimized_tutorial_path"):
        opt = Path(task["optimized_tutorial_path"])
        if opt.is_file():
            tutorial_path = opt

    if not tutorial_path.is_file():
        raise SystemExit(f"缺少 tutorial.json: {tutorial_path}")
    if not preview_run.is_dir():
        raise SystemExit(f"缺少 preview run: {preview_run}")

    tutorial = _load_json(tutorial_path) or {}
    preview_doc = _load_json(preview_run / "preview.json")
    before_src = _before_image_src(preview_run)
    after_src = _after_image_src(preview_run)
    if not before_src.is_file():
        raise SystemExit(f"缺少妆前图: {before_src}")

    video_src = _resolve_video(task, task_dir)

    _clear_output_dir(OUT_DIR)
    assets_dir = OUT_DIR / "assets"
    media_dir = OUT_DIR / "media"
    assets_dir.mkdir(parents=True)
    media_dir.mkdir(parents=True)

    shutil.copy2(TEMPLATE_DIR / "index.html", OUT_DIR / "index.html")
    shutil.copy2(TEMPLATE_DIR / "app.css", assets_dir / "app.css")
    shutil.copy2(TEMPLATE_DIR / "app.js", assets_dir / "app.js")
    shutil.copy2(before_src, media_dir / "before.jpg")
    if after_src and after_src.is_file():
        shutil.copy2(after_src, media_dir / "after.jpg")
    if video_src and video_src.is_file():
        shutil.copy2(video_src, media_dir / "video.mp4")
    diagram_count = _copy_diagram_media(task, media_dir)

    preview_payload = _assemble_preview(
        task_id,
        tutorial=tutorial,
        preview_run_dir=preview_run,
        preview_doc=preview_doc,
    )

    tutorial_out = dict(tutorial)
    has_video = bool(video_src and video_src.is_file())
    tutorial_out["videoUrl"] = "media/video.mp4" if has_video else ""
    if not (tutorial_out.get("title") or "").strip():
        tutorial_out["title"] = preview_payload["title"]

    progress_doc = task.get("progress_doc")
    if not isinstance(progress_doc, dict):
        progress_doc = {
            "taskId": task_id,
            "progress": 100,
            "currentStage": "整理关键建议",
            "remainingSeconds": 0,
            "status": "completed",
            "stages": [
                {"id": "quality-check", "label": "检查视频质量", "status": "completed"},
                {"id": "step-detection", "label": "识别妆容步骤", "status": "completed"},
                {"id": "preview-generation", "label": "生成适配预览", "status": "completed"},
                {"id": "hint-generation", "label": "整理关键建议", "status": "completed"},
            ],
            "detailMessage": "[job] 完成",
            "logLines": [],
        }
    else:
        # Keep demo payload lean: trim long log tails
        logs = progress_doc.get("logLines") or []
        if isinstance(logs, list) and len(logs) > 12:
            progress_doc = {**progress_doc, "logLines": logs[-12:]}

    upload_meta = {
        "fileName": task.get("fileName") or "video.mp4",
        "fileSize": int(task.get("fileSize") or 0),
        "parseMode": task.get("parse_mode") or "fast",
        "photoSkipped": bool(task.get("photo_skipped", True)),
        "baseline": task.get("baseline") or "female",
    }

    step_diagrams = _assemble_step_diagrams(
        task_id,
        task,
        tutorial,
        has_video=has_video,
    )

    sources: dict[str, Any] = {
        "task_id": task_id,
        "task_dir": task_dir.relative_to(REPO_ROOT).as_posix(),
        "parse_run_dir": parse_run.relative_to(REPO_ROOT).as_posix()
        if parse_run.is_relative_to(REPO_ROOT)
        else str(parse_run),
        "preview_run_dir": preview_run.relative_to(REPO_ROOT).as_posix()
        if preview_run.is_relative_to(REPO_ROOT)
        else str(preview_run),
        "tutorial_path": tutorial_path.relative_to(REPO_ROOT).as_posix()
        if tutorial_path.is_relative_to(REPO_ROOT)
        else str(tutorial_path),
        "file_name": upload_meta["fileName"],
    }
    if task.get("step_diagrams_run_dir"):
        picture_run = Path(task["step_diagrams_run_dir"])
        sources["picture_makeup_run_dir"] = (
            picture_run.relative_to(REPO_ROOT).as_posix()
            if picture_run.is_relative_to(REPO_ROOT)
            else str(picture_run)
        )

    payload: dict[str, Any] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
        "upload": upload_meta,
        "progress": progress_doc,
        "preview": preview_payload,
        "tutorial": tutorial_out,
    }
    if step_diagrams:
        payload["stepDiagrams"] = step_diagrams

    data_js = (
        "/* Generated by scripts/export_static_demo.py — do not edit by hand */\n"
        f"window.DEMO_DATA = {json.dumps(payload, ensure_ascii=False, indent=2)};\n"
    )
    (assets_dir / "data.js").write_text(data_js, encoding="utf-8")

    print(f"导出完成: {OUT_DIR}")
    print(f"  task: {task_id} ({task.get('fileName')})")
    print(f"  parse: {parse_run.name}")
    print(f"  preview: {preview_run.name}")
    print(f"  steps: {len(tutorial.get('steps') or [])}")
    print(f"  video: {'yes' if video_src else 'no'}")
    print(f"  diagrams: {diagram_count}" + (" (stepDiagrams page on)" if step_diagrams else ""))
    print("打开: /demo/ （Vite）或 cd frontend/public/demo && python -m http.server 8765")
    return 0


if __name__ == "__main__":
    sys.exit(main())
