"""On-demand step diagram job and API assembly."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from picture_makeup import PictureMakeupConfig, run_picture_makeup_job

from api_server.config import API_PUBLIC_BASE_URL, PICTURE_MAKEUP_OUTPUT_ROOT, PICTURE_MAKEUP_SKILL
from api_server.media_urls import resolve_task_video_url
from api_server.pipeline import load_api_key
from api_server.store import store


def _safe_diagram_filename(step_id: str) -> str:
    safe = re.sub(r"[^\w.-]+", "_", step_id.strip())
    return f"diagram_{safe or 'step'}.jpg"


def step_heading(step: dict[str, Any], index: int) -> str:
    display = (step.get("display_title") or "").strip()
    if display:
        return f"步骤 {index + 1} · {display}"
    primary = (step.get("taxonomy_primary") or "").strip()
    if primary:
        return f"步骤 {index + 1} · {primary}"
    sid = step.get("step_id") or f"step_{index}"
    return f"步骤 {index + 1} · {sid}"


def publish_step_diagram(task_id: str, step_id: str, step_dir: Path) -> None:
    task = store.load(task_id)
    media_raw = task.get("media_dir")
    if not media_raw:
        return
    media_dir = Path(media_raw)
    src = step_dir / "diagram_01.jpg"
    if not src.is_file():
        return
    media_dir.mkdir(parents=True, exist_ok=True)
    dest = media_dir / _safe_diagram_filename(step_id)
    shutil.copy2(src, dest)


def run_step_diagrams_job(task_id: str) -> None:
    task = store.load(task_id)
    parse_run = task.get("parse_run_dir")
    tutorial_path = task.get("tutorial_path")
    if not parse_run or not tutorial_path:
        raise RuntimeError("缺少 parse_run_dir 或 tutorial_path")
    parse_run_dir = Path(parse_run)
    tutorial_file = Path(tutorial_path)
    if not tutorial_file.is_file():
        raise FileNotFoundError(f"tutorial 不存在: {tutorial_file}")

    api_key = load_api_key()
    config = PictureMakeupConfig(api_key=api_key, skill_dir=PICTURE_MAKEUP_SKILL)

    tutorial = json.loads(tutorial_file.read_text(encoding="utf-8"))
    total = len(tutorial.get("steps") or [])

    def on_progress(step_id: str, index: int, _total: int) -> None:
        store.update_step_diagrams_progress(
            task_id,
            done=index,
            total=_total or total,
            current_step_id=step_id,
        )

    def on_step_complete(step_id: str, step_dir: Path, entry: dict[str, Any]) -> None:
        if entry.get("status") == "ok":
            publish_step_diagram(task_id, step_id, step_dir)

    result = run_picture_makeup_job(
        parse_run_dir=parse_run_dir,
        tutorial_path=tutorial_file,
        output_root=PICTURE_MAKEUP_OUTPUT_ROOT,
        config=config,
        on_progress=on_progress,
        on_step_complete=on_step_complete,
    )
    steps = (result.manifest or {}).get("steps") or []
    ok = sum(1 for s in steps if s.get("status") == "ok")
    failed = [s for s in steps if s.get("status") == "failed"]
    if steps and ok == 0 and failed:
        first_err = next((str(s.get("error") or "") for s in failed if s.get("error")), "")
        reason = f"全部 {len(failed)} 步示例图生成失败" + (f"：{first_err}" if first_err else "")
        store.mark_step_diagrams_failed(task_id, reason=reason)
        task = store.load(task_id)
        task["step_diagrams_run_dir"] = str(result.run_dir.resolve())
        store.save(task)
        return
    store.mark_step_diagrams_completed(task_id, run_dir=str(result.run_dir.resolve()))
    if failed:
        task = store.load(task_id)
        task["step_diagrams_failure"] = f"{len(failed)}/{len(steps)} 步生成失败"
        store.save(task)


def _read_prompt_file(step_dir: Path, name: str) -> str | None:
    path = step_dir / name
    if path.is_file():
        return path.read_text(encoding="utf-8").strip() or None
    return None


def _read_final_prompt(step_dir: Path) -> str | None:
    return _read_prompt_file(step_dir, "final_prompt.txt")


def _read_base_prompt(step_dir: Path) -> str | None:
    return _read_prompt_file(step_dir, "base_prompt.txt")


def _manifest_step_map(run_dir: Path | None) -> dict[str, dict[str, Any]]:
    if run_dir is None or not run_dir.is_dir():
        return {}
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        return {}
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for item in doc.get("steps") or []:
        sid = item.get("step_id")
        if sid:
            out[str(sid)] = item
    return out


def assemble_step_diagrams(task_id: str, task: dict[str, Any], tutorial: dict[str, Any]) -> dict[str, Any]:
    base = API_PUBLIC_BASE_URL
    status = task.get("step_diagrams_status") or "idle"
    run_dir: Path | None = None
    if task.get("step_diagrams_run_dir"):
        run_dir = Path(task["step_diagrams_run_dir"])
    manifest_by_step = _manifest_step_map(run_dir)

    steps_out: list[dict[str, Any]] = []
    for index, step in enumerate(tutorial.get("steps") or []):
        step_id = str(step.get("step_id") or f"step_{index}")
        mentry = manifest_by_step.get(step_id) or {}
        step_status = mentry.get("status")
        if status == "processing" and not step_status:
            item_status = "pending"
        elif step_status == "ok":
            item_status = "ok"
        elif step_status == "failed":
            item_status = "failed"
        elif step_status == "skipped":
            item_status = "skipped"
        elif status == "idle":
            item_status = "pending"
        else:
            item_status = "pending"

        media_name = _safe_diagram_filename(step_id)
        image_url: str | None = None
        media_dir = task.get("media_dir")
        if media_dir and (Path(media_dir) / media_name).is_file():
            image_url = f"{base}/media/{task_id}/{media_name}"

        final_prompt: str | None = None
        base_prompt: str | None = None
        if run_dir:
            step_out_dir = run_dir / "steps" / step_id
            final_prompt = _read_final_prompt(step_out_dir)
            base_prompt = _read_base_prompt(step_out_dir)

        item: dict[str, Any] = {
            "stepId": step_id,
            "index": index,
            "heading": step_heading(step, index),
            "imageUrl": image_url,
            "status": item_status,
        }
        clip = step.get("video_clip")
        if isinstance(clip, dict) and "start" in clip and "end" in clip:
            try:
                item["videoClip"] = {"start": float(clip["start"]), "end": float(clip["end"])}
            except (TypeError, ValueError):
                pass
        if final_prompt:
            item["finalPrompt"] = final_prompt
        if base_prompt:
            item["basePrompt"] = base_prompt
        err = mentry.get("error")
        if err:
            item["error"] = str(err)
        steps_out.append(item)

    progress = task.get("step_diagrams_progress")
    payload: dict[str, Any] = {
        "taskId": task_id,
        "status": status,
        "steps": steps_out,
    }
    video_url = resolve_task_video_url(task_id, task)
    if video_url:
        payload["videoUrl"] = video_url
    if progress:
        payload["progress"] = progress

    failure = task.get("step_diagrams_failure")
    if not failure and steps_out:
        failed_items = [s for s in steps_out if s.get("status") == "failed"]
        ok_items = [s for s in steps_out if s.get("status") == "ok"]
        if failed_items and not ok_items:
            first_err = next((s.get("error") for s in failed_items if s.get("error")), None)
            failure = (
                f"全部 {len(failed_items)} 步示例图生成失败"
                + (f"：{first_err}" if first_err else "")
            )
            payload["status"] = "failed"
        elif failed_items:
            failure = f"{len(failed_items)}/{len(steps_out)} 步生成失败"
    if failure:
        payload["failureReason"] = failure
    return payload


def ensure_task_ready_for_diagrams(task: dict[str, Any], *, request_id: str) -> None:
    from api_server.errors import ApiError

    if task.get("status") != "completed":
        raise ApiError(
            409,
            "STEP_DIAGRAMS_NOT_READY",
            "主任务尚未完成，无法生成示例图",
            request_id=request_id,
        )
    if not task.get("tutorial_path") or not task.get("parse_run_dir"):
        raise ApiError(409, "TUTORIAL_NOT_READY", "教程尚未就绪", request_id=request_id)
