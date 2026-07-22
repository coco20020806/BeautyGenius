from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from api_server.adjustment import ensure_task_ready_for_adjustment, run_adjustment_job
from api_server.config import (
    CORS_ORIGINS,
    ENABLE_DEV_SHORTCUTS,
    MAX_VIDEO_BYTES,
    TASKS_ROOT,
    VIDEO_EXTENSIONS,
    VIDEO_MIMES,
)
from api_server.dev_bootstrap import bootstrap_from_pinned_file
from api_server.errors import ApiError, api_error_handler, new_request_id
from api_server.media_urls import resolve_task_video_url
from api_server.occupancy import JobKind, occupancy
from api_server.pipeline import run_task_pipeline
from api_server.preview_assembler import assemble_makeup_preview
from api_server.step_diagrams import (
    assemble_step_diagrams,
    ensure_task_ready_for_diagrams,
    run_step_diagrams_job,
)
from api_server.store import store
from api_server.tutorial_loader import load_tutorial_document

app = FastAPI(title="Beauty Genius Makeup API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(ApiError, api_error_handler)

_running: set[str] = set()
_diagram_running: set[str] = set()

_SERVER_BUSY_MESSAGE = "排队中，服务器已满（最多 {max} 人同时使用），请稍后再试"


def _require_occupancy(task_id: str, job: JobKind, *, request_id: str) -> None:
    if occupancy.try_acquire(task_id, job):
        return
    raise ApiError(
        409,
        "SERVER_BUSY",
        _SERVER_BUSY_MESSAGE.format(max=occupancy.max_concurrent),
        request_id=request_id,
        details=occupancy.snapshot(),
    )


class AdjustmentBody(BaseModel):
    styles: list[str] = Field(default_factory=list)
    occasions: list[str] = Field(default_factory=list)
    retainedParts: list[str] = Field(default_factory=list)
    skinType: str = "混合性肌肤"
    concerns: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    baseTutorialId: str | None = None


def _parse_bool(value: str | bool | None, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@app.post("/api/v1/makeup/tasks")
async def upload_video(
    video: Annotated[UploadFile, File(...)],
    fastParse: Annotated[str | None, Form()] = None,
    skipMakeupPreview: Annotated[str | None, Form()] = None,
) -> dict:
    req_id = new_request_id()
    if video.content_type and video.content_type not in VIDEO_MIMES:
        ext = Path(video.filename or "").suffix.lower()
        if ext not in VIDEO_EXTENSIONS:
            raise ApiError(415, "VIDEO_FORMAT_UNSUPPORTED", "仅支持 MP4 或 MOV 视频", request_id=req_id)
    elif not video.content_type:
        ext = Path(video.filename or "").suffix.lower()
        if ext not in VIDEO_EXTENSIONS:
            raise ApiError(415, "VIDEO_FORMAT_UNSUPPORTED", "仅支持 MP4 或 MOV 视频", request_id=req_id)

    data = await video.read()
    if len(data) > MAX_VIDEO_BYTES:
        raise ApiError(413, "VIDEO_TOO_LARGE", "视频不能超过 500MB", request_id=req_id)
    if not data:
        raise ApiError(400, "VIDEO_EMPTY", "视频文件为空", request_id=req_id)

    file_name = video.filename or "upload.mp4"
    ext = Path(file_name).suffix.lower() or ".mp4"
    if ext not in VIDEO_EXTENSIONS:
        ext = ".mp4"

    from api_server.store import new_task_id

    tid = new_task_id()
    task_dir = TASKS_ROOT / tid / "upload"
    task_dir.mkdir(parents=True, exist_ok=True)
    video_path = task_dir / f"video{ext}"
    video_path.write_bytes(data)

    parse_mode = "fast" if _parse_bool(fastParse, default=True) else "full"
    skip_transfer = _parse_bool(skipMakeupPreview, default=False)

    task = store.create_uploaded(
        file_name=file_name,
        file_size=len(data),
        video_path=str(video_path.resolve()),
        task_id=tid,
        parse_mode=parse_mode,
        skip_transfer=skip_transfer,
    )
    return {
        "taskId": task["taskId"],
        "fileName": task["fileName"],
        "fileSize": task["fileSize"],
        "status": "uploaded",
        "parseMode": parse_mode,
        "skipMakeupPreview": skip_transfer,
    }


@app.post("/api/v1/makeup/tasks/{task_id}/photo")
async def upload_photo(
    task_id: str,
    skipped: Annotated[str, Form()] = "false",
    photo: Annotated[UploadFile | None, File()] = None,
) -> dict:
    req_id = new_request_id()
    try:
        task = store.load(task_id)
    except FileNotFoundError:
        raise ApiError(404, "TASK_NOT_FOUND", "任务不存在", request_id=req_id)

    if task["status"] not in {"uploaded", "photo_ready"}:
        raise ApiError(409, "TASK_STATE_CONFLICT", "当前任务状态不允许上传照片", request_id=req_id)

    skip = _parse_bool(skipped, default=False)
    photo_id: str | None = None
    preview_url: str | None = None
    photo_path: str | None = None

    if not skip:
        if not photo:
            raise ApiError(400, "PHOTO_REQUIRED", "请上传照片或选择跳过", request_id=req_id)
        content_type = photo.content_type or ""
        if not content_type.startswith("image/"):
            raise ApiError(415, "PHOTO_FORMAT_UNSUPPORTED", "请选择 JPG、PNG 或 WebP 照片", request_id=req_id)
        data = await photo.read()
        if not data:
            raise ApiError(400, "PHOTO_EMPTY", "照片文件为空", request_id=req_id)
        photo_id = f"photo_{uuid.uuid4().hex[:12]}"
        upload_dir = store.task_dir(task_id) / "upload"
        upload_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(photo.filename or "photo.jpg").suffix.lower() or ".jpg"
        dest = upload_dir / f"photo{ext}"
        dest.write_bytes(data)
        photo_path = str(dest.resolve())
        from api_server.config import API_PUBLIC_BASE_URL

        preview_url = f"{API_PUBLIC_BASE_URL}/media/{task_id}/{dest.name}"

    store.set_photo_ready(task_id, photo_path=photo_path, skipped=skip, photo_id=photo_id)
    return {"photoId": photo_id, "previewUrl": preview_url, "skipped": skip}


@app.post("/api/v1/makeup/tasks/{task_id}/analysis", status_code=202)
async def start_analysis(task_id: str, background_tasks: BackgroundTasks) -> dict:
    req_id = new_request_id()
    try:
        task = store.load(task_id)
    except FileNotFoundError:
        raise ApiError(404, "TASK_NOT_FOUND", "任务不存在", request_id=req_id)

    if task["status"] == "processing":
        return {"taskId": task_id, "status": "processing"}
    if task["status"] == "completed":
        return {"taskId": task_id, "status": "completed"}
    if task["status"] == "failed":
        task["status"] = "photo_ready"
        task["failureReason"] = None
        task["failureCode"] = None
        store.save(task)
    if task["status"] != "photo_ready":
        raise ApiError(400, "PHOTO_STEP_REQUIRED", "请先完成照片确认步骤", request_id=req_id)

    if task_id in _running:
        return {"taskId": task_id, "status": "processing"}

    _require_occupancy(task_id, "analysis", request_id=req_id)
    store.mark_processing(task_id)
    _running.add(task_id)

    def _run() -> None:
        try:
            run_task_pipeline(task_id)
        finally:
            _running.discard(task_id)
            occupancy.release(task_id, "analysis")

    background_tasks.add_task(_run)
    return {"taskId": task_id, "status": "processing"}


@app.get("/api/v1/makeup/tasks/{task_id}/analysis")
async def get_analysis(task_id: str) -> dict:
    req_id = new_request_id()
    try:
        return store.get_analysis_progress(task_id)
    except FileNotFoundError:
        raise ApiError(404, "TASK_NOT_FOUND", "任务不存在", request_id=req_id)


@app.get("/api/v1/makeup/tasks/{task_id}/preview")
async def get_preview(task_id: str) -> dict:
    req_id = new_request_id()
    try:
        task = store.load(task_id)
    except FileNotFoundError:
        raise ApiError(404, "TASK_NOT_FOUND", "任务不存在", request_id=req_id)

    if task["status"] != "completed":
        raise ApiError(409, "PREVIEW_NOT_READY", "预览尚未就绪", request_id=req_id)

    preview_run = Path(task["preview_run_dir"])
    preview_doc_path = preview_run / "preview.json"
    preview_doc = None
    if preview_doc_path.is_file():
        preview_doc = json.loads(preview_doc_path.read_text(encoding="utf-8"))

    tutorial_path = Path(task["tutorial_path"]) if task.get("tutorial_path") else None
    return assemble_makeup_preview(
        task_id,
        tutorial_path=tutorial_path,
        preview_run_dir=preview_run,
        preview_doc=preview_doc,
    )


@app.get("/api/v1/makeup/tasks/{task_id}/tutorial")
async def get_tutorial(task_id: str) -> dict:
    req_id = new_request_id()
    try:
        task = store.load(task_id)
    except FileNotFoundError:
        raise ApiError(404, "TASK_NOT_FOUND", "任务不存在", request_id=req_id)

    doc = load_tutorial_document(task, request_id=req_id)
    video_url = resolve_task_video_url(task_id, task)
    if video_url:
        doc = {**doc, "videoUrl": video_url}
    return doc


@app.post("/api/v1/makeup/tasks/{task_id}/adjustment")
async def save_adjustment(task_id: str, body: AdjustmentBody) -> dict[str, Any]:
    req_id = new_request_id()
    try:
        task = store.load(task_id)
    except FileNotFoundError:
        raise ApiError(404, "TASK_NOT_FOUND", "任务不存在", request_id=req_id)

    ensure_task_ready_for_adjustment(task, request_id=req_id)
    _require_occupancy(task_id, "adjustment", request_id=req_id)
    payload = body.model_dump(exclude_none=True)
    try:
        return run_adjustment_job(task_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise ApiError(
            500,
            "ADJUSTMENT_FAILED",
            str(exc) or "微调优化失败",
            request_id=req_id,
        ) from exc
    finally:
        occupancy.release(task_id, "adjustment")


@app.post("/api/v1/makeup/tasks/{task_id}/step-diagrams", status_code=202)
async def start_step_diagrams(task_id: str, background_tasks: BackgroundTasks) -> dict:
    req_id = new_request_id()
    try:
        task = store.load(task_id)
    except FileNotFoundError:
        raise ApiError(404, "TASK_NOT_FOUND", "任务不存在", request_id=req_id)

    ensure_task_ready_for_diagrams(task, request_id=req_id)
    diagram_status = task.get("step_diagrams_status") or "idle"
    if diagram_status == "processing" or task_id in _diagram_running:
        return {"taskId": task_id, "status": "processing"}
    # completed 且至少有一张图：幂等返回；全部失败 / failed 允许重试
    if diagram_status == "completed":
        media_dir = Path(task["media_dir"]) if task.get("media_dir") else None
        has_diagram = False
        if media_dir and media_dir.is_dir():
            has_diagram = any(media_dir.glob("diagram_*.jpg"))
        if has_diagram:
            return {"taskId": task_id, "status": "completed"}

    _require_occupancy(task_id, "step_diagrams", request_id=req_id)
    store.set_step_diagrams_processing(task_id)
    _diagram_running.add(task_id)

    def _run() -> None:
        try:
            run_step_diagrams_job(task_id)
        except Exception as exc:  # noqa: BLE001
            store.mark_step_diagrams_failed(task_id, reason=str(exc) or "示例图生成失败")
        finally:
            _diagram_running.discard(task_id)
            occupancy.release(task_id, "step_diagrams")

    background_tasks.add_task(_run)
    return {"taskId": task_id, "status": "processing"}


@app.get("/api/v1/makeup/tasks/{task_id}/step-diagrams")
async def get_step_diagrams(task_id: str) -> dict:
    req_id = new_request_id()
    try:
        task = store.load(task_id)
    except FileNotFoundError:
        raise ApiError(404, "TASK_NOT_FOUND", "任务不存在", request_id=req_id)

    ensure_task_ready_for_diagrams(task, request_id=req_id)
    tutorial = load_tutorial_document(task, request_id=req_id)
    return assemble_step_diagrams(task_id, task, tutorial)


@app.get("/api/v1/makeup/server/status")
async def server_status() -> dict:
    return occupancy.snapshot()


@app.post("/api/v1/makeup/dev/skip-to-preview")
async def dev_skip_to_preview() -> dict:
    req_id = new_request_id()
    if not ENABLE_DEV_SHORTCUTS:
        raise ApiError(
            404,
            "DEV_SHORTCUTS_DISABLED",
            "开发捷径未开启。请设置 ENABLE_DEV_SHORTCUTS=1 并重启 API，或勿将 APP_ENV 设为 production",
            request_id=req_id,
        )
    return bootstrap_from_pinned_file(store, request_id=req_id)


@app.get("/media/{task_id}/{filename}")
async def serve_media(task_id: str, filename: str) -> FileResponse:
    req_id = new_request_id()
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ApiError(400, "INVALID_PATH", "非法路径", request_id=req_id)
    try:
        task = store.load(task_id)
    except FileNotFoundError:
        raise ApiError(404, "TASK_NOT_FOUND", "任务不存在", request_id=req_id)

    media_dir = task.get("media_dir")
    if media_dir:
        path = Path(media_dir) / filename
        if path.is_file():
            return FileResponse(path)

    upload_dir = store.task_dir(task_id) / "upload"
    upload_path = upload_dir / filename
    if upload_path.is_file():
        return FileResponse(upload_path)

    if task.get("preview_run_dir"):
        preview_path = Path(task["preview_run_dir"]) / filename
        if preview_path.is_file():
            return FileResponse(preview_path)

    raise ApiError(404, "MEDIA_NOT_FOUND", "资源不存在", request_id=req_id)


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "features": {
            "devSkipToPreview": ENABLE_DEV_SHORTCUTS,
            "tutorialEndpoint": True,
            "stepDiagramsEndpoint": True,
        },
    }
