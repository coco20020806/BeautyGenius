"""Sync user-photo L0–L2 validation at upload time."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from makeup_preview import PreviewConfig, UserPhotoRejected, run_preview_job

from api_server.config import PREVIEW_OUTPUT_ROOT, PREVIEW_SKILL
from api_server.pipeline import load_api_key


def validate_user_photo_for_upload(photo_path: Path) -> dict[str, Any]:
    """Run validate_only preview job. Raises UserPhotoRejected on failure.

    Returns a compact qa summary suitable for task.photo_qa.
    """
    api_key = load_api_key()
    config = PreviewConfig(api_key=api_key, skill_dir=PREVIEW_SKILL)
    result = run_preview_job(
        parse_run_dir=None,
        reference_image=None,
        user_photo=photo_path,
        use_baseline=False,
        reference_step=None,
        output_root=PREVIEW_OUTPUT_ROOT,
        config=config,
        validate_only=True,
    )
    qa = (result.preview or {}).get("validation") or {}
    return {
        "pass": bool(qa.get("pass", result.validation_pass)),
        "reason": qa.get("reason") or "",
        "failed_layer": qa.get("failed_layer"),
        "codes": qa.get("codes") or [],
        "l1": qa.get("l1"),
        "l2": qa.get("l2"),
        "run_dir": str(result.run_dir),
    }
