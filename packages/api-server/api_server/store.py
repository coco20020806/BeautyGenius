from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api_server.config import TASKS_ROOT
from api_server.eta import micro_weight, record_completed_stats
from api_server.progress import initial_stages, progress_payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_task_id() -> str:
    return f"task_{uuid.uuid4().hex[:16]}"


class TaskStore:
    def __init__(self, root: Path = TASKS_ROOT) -> None:
        self.root = root
        self._lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)

    def task_dir(self, task_id: str) -> Path:
        return self.root / task_id

    def task_path(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "task.json"

    def load(self, task_id: str) -> dict[str, Any]:
        path = self.task_path(task_id)
        if not path.is_file():
            raise FileNotFoundError(task_id)
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def save(self, task: dict[str, Any]) -> None:
        task_id = task["taskId"]
        task_dir = self.task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        task["updated_at"] = _utc_now()
        path = self.task_path(task_id)
        with self._lock:
            path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")

    def _prior_doc(self, task: dict[str, Any]) -> dict[str, Any]:
        return dict(task.get("progress_doc") or {})

    def create_uploaded(
        self,
        *,
        file_name: str,
        file_size: int,
        video_path: str,
        task_id: str | None = None,
        parse_mode: str = "fast",
        skip_transfer: bool = False,
    ) -> dict[str, Any]:
        task_id = task_id or new_task_id()
        mode = parse_mode if parse_mode in {"fast", "full"} else "fast"
        task = {
            "taskId": task_id,
            "status": "uploaded",
            "fileName": file_name,
            "fileSize": file_size,
            "video_path": video_path,
            "parse_mode": mode,
            "skip_transfer": bool(skip_transfer),
            "video_duration_sec": None,
            "photo_path": None,
            "photo_skipped": None,
            "baseline": "female",
            "parse_run_dir": None,
            "preview_run_dir": None,
            "tutorial_path": None,
            "optimized_tutorial_path": None,
            "optimization_run_dir": None,
            "adjustment": None,
            "optimization_summary": None,
            "analysis_status": None,
            "progress_doc": progress_payload(task_id, active_index=0, progress=0, status="processing"),
            "failureReason": None,
            "media_dir": None,
            "step_diagrams_status": "idle",
            "step_diagrams_run_dir": None,
            "step_diagrams_failure": None,
            "step_diagrams_progress": None,
            "photo_id": None,
            "pipeline_started_at": None,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
        }
        self.save(task)
        return task

    def set_photo_ready(
        self,
        task_id: str,
        *,
        photo_path: str | None,
        skipped: bool,
        photo_id: str | None,
        photo_qa: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task = self.load(task_id)
        if task["status"] not in {"uploaded", "photo_ready"}:
            raise ValueError("invalid_state")
        task["status"] = "photo_ready"
        task["photo_path"] = photo_path
        task["photo_skipped"] = skipped
        task["photo_id"] = photo_id
        if skipped:
            task["photo_qa"] = None
        elif photo_qa is not None:
            task["photo_qa"] = photo_qa
        self.save(task)
        return task

    def mark_processing(self, task_id: str) -> dict[str, Any]:
        task = self.load(task_id)
        if task["status"] == "processing":
            return task
        if task["status"] != "photo_ready":
            raise ValueError("invalid_state")
        task["status"] = "processing"
        task["analysis_status"] = "processing"
        started = _utc_now()
        prior = self._prior_doc(task)
        prior["processingStartedAt"] = started
        prior["logLines"] = []
        task["pipeline_started_at"] = started
        task["progress_doc"] = progress_payload(
            task_id,
            active_index=0,
            progress=5,
            status="processing",
            detail_message="[job] 开始解析…",
            log_lines=["[job] 开始解析…"],
            processing_started_at=started,
            prior_doc=prior,
        )
        self.save(task)
        return task

    def set_eta_context(
        self,
        task_id: str,
        *,
        video_duration_sec: float,
        eta_total_seconds: int,
    ) -> None:
        task = self.load(task_id)
        task["video_duration_sec"] = video_duration_sec
        prior = self._prior_doc(task)
        active_index = 0
        for idx, stage in enumerate(prior.get("stages") or initial_stages()):
            if stage.get("status") == "active":
                active_index = idx
                break
        task["progress_doc"] = progress_payload(
            task_id,
            active_index=active_index,
            progress=int(prior.get("progress", 5)),
            status="processing",
            eta_total_seconds=eta_total_seconds,
            completed_weight=float(prior.get("completedWeight", 0.0)),
            processing_started_at=prior.get("processingStartedAt"),
            detail_message=prior.get("detailMessage"),
            log_lines=prior.get("logLines"),
            prior_doc=prior,
        )
        self.save(task)

    def update_pipeline_step(
        self,
        task_id: str,
        *,
        active_index: int,
        progress: int,
        micro_step_id: str,
        log_line: str,
        skip_transfer: bool,
    ) -> None:
        task = self.load(task_id)
        prior = self._prior_doc(task)
        weight = max(float(prior.get("completedWeight", 0.0)), micro_weight(micro_step_id, skip_transfer=skip_transfer))
        lines = list(prior.get("logLines") or [])
        lines.append(log_line)
        task["progress_doc"] = progress_payload(
            task_id,
            active_index=active_index,
            progress=progress,
            status="processing",
            detail_message=log_line,
            log_lines=lines,
            eta_total_seconds=prior.get("etaTotalSeconds"),
            completed_weight=weight,
            processing_started_at=prior.get("processingStartedAt"),
            prior_doc=prior,
        )
        self.save(task)

    def update_progress(self, task_id: str, *, active_index: int, progress: int) -> None:
        task = self.load(task_id)
        prior = self._prior_doc(task)
        task["progress_doc"] = progress_payload(
            task_id,
            active_index=active_index,
            progress=progress,
            status="processing",
            detail_message=prior.get("detailMessage"),
            log_lines=prior.get("logLines"),
            eta_total_seconds=prior.get("etaTotalSeconds"),
            completed_weight=prior.get("completedWeight", 0.0),
            processing_started_at=prior.get("processingStartedAt"),
            prior_doc=prior,
        )
        self.save(task)

    def append_log_only(self, task_id: str, line: str, *, micro_step_id: str | None = None, skip_transfer: bool = False) -> None:
        task = self.load(task_id)
        prior = self._prior_doc(task)
        lines = list(prior.get("logLines") or [])
        lines.append(line)
        weight = float(prior.get("completedWeight", 0.0))
        if micro_step_id:
            weight = max(weight, micro_weight(micro_step_id, skip_transfer=skip_transfer))
        active_index = 0
        for idx, stage in enumerate(prior.get("stages") or initial_stages()):
            if stage.get("status") == "active":
                active_index = idx
                break
        task["progress_doc"] = progress_payload(
            task_id,
            active_index=active_index,
            progress=int(prior.get("progress", 0)),
            status="processing",
            detail_message=line,
            log_lines=lines,
            eta_total_seconds=prior.get("etaTotalSeconds"),
            completed_weight=weight,
            processing_started_at=prior.get("processingStartedAt"),
            prior_doc=prior,
        )
        self.save(task)

    def mark_completed(
        self,
        task_id: str,
        *,
        parse_run_dir: str,
        preview_run_dir: str,
        tutorial_path: str | None,
        media_dir: str,
    ) -> dict[str, Any]:
        task = self.load(task_id)
        prior = self._prior_doc(task)
        lines = list(prior.get("logLines") or [])
        lines.append("[job] 完成")
        task["status"] = "completed"
        task["analysis_status"] = "completed"
        task["parse_run_dir"] = parse_run_dir
        task["preview_run_dir"] = preview_run_dir
        task["tutorial_path"] = tutorial_path
        task["media_dir"] = media_dir
        task["progress_doc"] = progress_payload(
            task_id,
            active_index=3,
            progress=100,
            status="completed",
            detail_message="[job] 完成",
            log_lines=lines,
            completed_weight=1.0,
            eta_total_seconds=prior.get("etaTotalSeconds"),
            processing_started_at=prior.get("processingStartedAt"),
            prior_doc=prior,
        )
        self.save(task)

        started = task.get("pipeline_started_at") or prior.get("processingStartedAt")
        if started:
            try:
                t0 = datetime.fromisoformat(started.replace("Z", "+00:00"))
                actual = (datetime.now(timezone.utc) - t0).total_seconds()
                from api_server.config import SKIP_TRANSFER

                skip_xfer = bool(task.get("skip_transfer")) or SKIP_TRANSFER
                record_completed_stats(
                    parse_mode=task.get("parse_mode") or "fast",
                    skip_transfer=skip_xfer,
                    duration_sec=float(task.get("video_duration_sec") or 0),
                    actual_seconds=actual,
                )
            except ValueError:
                pass
        return task

    def mark_failed(self, task_id: str, *, reason: str, code: str = "PIPELINE_FAILED") -> dict[str, Any]:
        task = self.load(task_id)
        prior = self._prior_doc(task)
        lines = list(prior.get("logLines") or [])
        lines.append(f"[job] 失败: {reason}")
        task["status"] = "failed"
        task["analysis_status"] = "failed"
        task["failureReason"] = reason
        task["failureCode"] = code
        active_index = 0
        for index, stage in enumerate(prior.get("stages") or initial_stages()):
            if stage.get("status") == "active":
                active_index = index
                break
        task["progress_doc"] = progress_payload(
            task_id,
            active_index=active_index,
            progress=int(prior.get("progress", 0)),
            status="failed",
            failure_reason=reason,
            detail_message=lines[-1],
            log_lines=lines,
            eta_total_seconds=prior.get("etaTotalSeconds"),
            completed_weight=prior.get("completedWeight", 0.0),
            processing_started_at=prior.get("processingStartedAt"),
            prior_doc=prior,
        )
        self.save(task)
        return task

    def set_step_diagrams_processing(self, task_id: str) -> dict[str, Any]:
        task = self.load(task_id)
        task["step_diagrams_status"] = "processing"
        task["step_diagrams_failure"] = None
        task["step_diagrams_progress"] = {"done": 0, "total": 0, "currentStepId": None}
        self.save(task)
        return task

    def update_step_diagrams_progress(
        self,
        task_id: str,
        *,
        done: int,
        total: int,
        current_step_id: str | None,
    ) -> None:
        task = self.load(task_id)
        task["step_diagrams_progress"] = {
            "done": done,
            "total": total,
            "currentStepId": current_step_id,
        }
        self.save(task)

    def mark_step_diagrams_completed(self, task_id: str, *, run_dir: str) -> dict[str, Any]:
        task = self.load(task_id)
        task["step_diagrams_status"] = "completed"
        task["step_diagrams_run_dir"] = run_dir
        task["step_diagrams_failure"] = None
        prog = task.get("step_diagrams_progress") or {}
        total = int(prog.get("total") or 0)
        task["step_diagrams_progress"] = {
            "done": total,
            "total": total,
            "currentStepId": None,
        }
        self.save(task)
        return task

    def mark_step_diagrams_failed(self, task_id: str, *, reason: str) -> dict[str, Any]:
        task = self.load(task_id)
        task["step_diagrams_status"] = "failed"
        task["step_diagrams_failure"] = reason
        self.save(task)
        return task

    def reset_step_diagrams(self, task_id: str) -> dict[str, Any]:
        task = self.load(task_id)
        task["step_diagrams_status"] = "idle"
        task["step_diagrams_run_dir"] = None
        task["step_diagrams_failure"] = None
        task["step_diagrams_progress"] = None
        self.save(task)
        return task

    def save_adjustment(
        self,
        task_id: str,
        *,
        adjustment: dict[str, Any],
        optimized_tutorial_path: str,
        optimization_run_dir: str,
        summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task = self.load(task_id)
        task["adjustment"] = adjustment
        task["optimized_tutorial_path"] = optimized_tutorial_path
        task["optimization_run_dir"] = optimization_run_dir
        task["optimization_summary"] = summary
        task["step_diagrams_status"] = "idle"
        task["step_diagrams_run_dir"] = None
        task["step_diagrams_failure"] = None
        task["step_diagrams_progress"] = None
        self.save(task)
        return task

    def get_analysis_progress(self, task_id: str) -> dict[str, Any]:
        task = self.load(task_id)
        if task.get("progress_doc"):
            return task["progress_doc"]
        status = task.get("analysis_status") or "processing"
        if task["status"] == "photo_ready":
            status = "processing"
        return progress_payload(task_id, active_index=0, progress=0, status=status)


store = TaskStore()
