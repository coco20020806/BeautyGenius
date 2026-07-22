"""Orchestrate KOL makeup preview job."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from makeup_preview.baselines import baseline_metadata, resolve_baseline_path
from makeup_preview.config import CONTRACT_VERSION, PreviewConfig, PreviewJobResult, resolve_image_size
from makeup_preview.face_gate import FaceValidationError, run_l0_l1
from makeup_preview.face_qa import run_face_qa
from makeup_preview.io_util import make_run_dir, maybe_copy, prepare_for_api, ensure_preview_matches_target
from makeup_preview.preview_align import harmonize_preview_pair
from makeup_preview.reference_pick import pick_reference_from_parse_run
from makeup_preview.scope_loader import resolve_transfer_scope
from makeup_preview.transfer import run_transfer

BaselineGender = Literal["female", "male"]


class UserPhotoRejected(Exception):
    def __init__(self, qa_doc: dict[str, Any]):
        self.qa_doc = qa_doc
        super().__init__(qa_doc.get("reason") or "用户照片未通过质检")


def _validate_inputs(
    *,
    parse_run_dir: Path | None,
    reference_image: Path | None,
    user_photo: Path | None,
    use_baseline: bool,
    validate_only: bool,
) -> None:
    if user_photo and use_baseline:
        raise ValueError("不能同时指定 user_photo 与 use_baseline")
    if not validate_only and not parse_run_dir and not reference_image:
        raise ValueError("需要 --parse-run 或 --reference-image（validate-only 除外）")
    if not user_photo and not use_baseline and not validate_only:
        raise ValueError("需要 --user-photo 或 --use-baseline")
    if validate_only and not user_photo:
        raise ValueError("validate-only 需要 --user-photo")


def run_preview_job(
    *,
    parse_run_dir: Path | None,
    reference_image: Path | None,
    user_photo: Path | None,
    use_baseline: bool,
    baseline: BaselineGender = "female",
    reference_step: str | None,
    output_root: Path,
    config: PreviewConfig,
    validate_only: bool = False,
    skip_transfer: bool = False,
    strict_replication: bool = False,
) -> PreviewJobResult:
    _validate_inputs(
        parse_run_dir=parse_run_dir,
        reference_image=reference_image,
        user_photo=user_photo,
        use_baseline=use_baseline,
        validate_only=validate_only,
    )

    t0 = time.perf_counter()
    run_dir = make_run_dir(output_root)
    warnings: list[str] = []
    reference_meta: dict[str, Any] | None = None
    ref_src_path: Path | None = None
    pick = None

    if validate_only and user_photo:
        qa_doc = _validate_user_photo(user_photo, config, run_dir)
        if not qa_doc["pass"]:
            raise UserPhotoRejected(qa_doc)
        preview = {
            "contract_version": CONTRACT_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "validate_only",
            "validation": qa_doc,
        }
        preview_path = run_dir / "preview.json"
        preview_path.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
        meta = _write_meta(config, run_dir, t0, transfer_ms=None)
        return PreviewJobResult(
            run_dir=run_dir,
            preview_path=preview_path,
            preview=preview,
            meta=meta,
            validation_pass=True,
        )

    if reference_image:
        ref_src_path = reference_image.resolve()
        if not ref_src_path.is_file():
            raise FileNotFoundError(ref_src_path)
        reference_meta = {
            "source": "manual",
            "path": str(ref_src_path),
            "reference_tier": "manual",
        }
    elif parse_run_dir:
        pick = pick_reference_from_parse_run(
            parse_run_dir,
            reference_step=reference_step,
            strict_replication=strict_replication,
        )
        ref_src_path = pick.path
        reference_meta = pick.meta
        warnings.extend(pick.warnings)
        if pick.tutorial_before_path and pick.tutorial_before_path.is_file():
            maybe_copy(pick.tutorial_before_path, run_dir / "tutorial_before.jpg")

    tutorial_replication: dict[str, Any] | None = None
    if pick and pick.tutorial_before_meta:
        tutorial_replication = {
            "before": pick.tutorial_before_meta,
            "tutorial_before_file": "tutorial_before.jpg",
        }

    target_meta: dict[str, Any]
    target_src: Path
    validation_doc: dict[str, Any] | None = None

    if user_photo:
        target_src = user_photo.resolve()
        qa_doc = _validate_user_photo(target_src, config, run_dir)
        if not qa_doc["pass"]:
            raise UserPhotoRejected(qa_doc)
        target_meta = {"type": "user_photo", "path": "target.jpg"}
        validation_doc = qa_doc
    else:
        target_src = resolve_baseline_path(config.skill_dir, baseline)
        target_meta = {
            "path": "target.jpg",
            **baseline_metadata(baseline),
        }

    ref_run = run_dir / "reference.jpg"
    before_run = run_dir / "tutorial_before.jpg"
    tgt_run = run_dir / "target.jpg"
    if ref_src_path:
        maybe_copy(ref_src_path, ref_run)
    maybe_copy(target_src, tgt_run)

    ref_api = prepare_for_api(ref_run, run_dir, "reference", 2048) if ref_run.is_file() else None
    tgt_api = prepare_for_api(tgt_run, run_dir, "target", 2048)
    before_api: Path | None = None
    if before_run.is_file():
        before_api = prepare_for_api(before_run, run_dir, "tutorial_before", 2048)
    elif not skip_transfer:
        warnings.append("transfer_without_tutorial_before")

    outputs: list[dict[str, Any]] = []
    transfer_ms: float | None = None
    requested_size: str | None = None
    preview_alignment: dict[str, Any] | None = None
    prompt_version = "v2" if before_run.is_file() else "v1"
    prompt_text_version: str | None = None
    target_pixel_size: list[int] | None = None
    transfer_scope = resolve_transfer_scope(
        parse_run_dir,
        transfer_scope_override=config.transfer_scope_override,
    )
    warnings.extend(transfer_scope.warnings)
    prompt_mode: str = transfer_scope.prompt_mode
    transfer_scope_doc: dict[str, Any] | None = None

    if not skip_transfer and ref_api and ref_api.is_file():
        from PIL import Image

        with Image.open(tgt_run) as im:
            tw, th = im.size
        target_pixel_size = [tw, th]
        requested_size = resolve_image_size(tw, th, default=config.image_size)
        t1 = time.perf_counter()
        names, prompt_version, requested_size, prompt_text_version, prompt_fallback, prompt_mode, transfer_scope_doc = run_transfer(
            ref_api,
            tgt_api,
            config,
            run_dir,
            tutorial_before_path=before_api,
            transfer_scope=transfer_scope,
            image_size=requested_size,
            output_canvas_path=tgt_run,
        )
        transfer_ms = (time.perf_counter() - t1) * 1000
        if prompt_fallback:
            warnings.append("transfer_prompt_fallback_static")
        outputs = [{"filename": n, "selected": i == 0} for i, n in enumerate(names)]
        if names:
            preview_path = run_dir / names[0]
            preview_alignment = harmonize_preview_pair(tgt_run, preview_path, config)
            out_w, out_h = ensure_preview_matches_target(preview_path, tgt_run)
            preview_alignment["preview_size_after"] = [out_w, out_h]

    preview: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference": reference_meta,
        "target": target_meta,
        "validation": validation_doc,
        "transfer": {
            "model": config.image_model,
            "prompt_version": prompt_version,
            "prompt_text_version": prompt_text_version,
            "prompt_mode": prompt_mode,
        },
        "outputs": outputs,
        "warnings": warnings,
    }
    if requested_size:
        preview["transfer"]["requested_size"] = requested_size
    if target_pixel_size is not None:
        preview["transfer"]["target_pixel_size"] = target_pixel_size
    if transfer_scope_doc is not None:
        preview["transfer"]["scope"] = transfer_scope_doc
    elif transfer_scope.source != "default_full" or transfer_scope.present_primaries:
        from makeup_preview.scope_loader import scope_to_preview_dict

        preview["transfer"]["scope"] = scope_to_preview_dict(transfer_scope)
    if preview_alignment is not None:
        preview["alignment"] = preview_alignment
        align_warnings = preview_alignment.get("warnings") or []
        if align_warnings:
            warnings.extend(align_warnings)
            preview["warnings"] = warnings
    if tutorial_replication:
        preview["tutorial_replication"] = tutorial_replication
    if skip_transfer:
        preview["transfer"]["skipped"] = True

    preview_path = run_dir / "preview.json"
    preview_path.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = _write_meta(config, run_dir, t0, transfer_ms=transfer_ms)

    return PreviewJobResult(
        run_dir=run_dir,
        preview_path=preview_path,
        preview=preview,
        meta=meta,
        validation_pass=True if user_photo else None,
    )


def _validate_user_photo(path: Path, config: PreviewConfig, run_dir: Path) -> dict[str, Any]:
    qa_path = run_dir / "user-photo-qa.json"
    l1: dict[str, Any] | None = None
    codes: list[str] = []
    failed_layer: str | None = None
    try:
        l1 = run_l0_l1(path, config)
    except FaceValidationError as e:
        codes = e.codes
        l1 = e.l1
        failed_layer = "l1"
        doc = {
            "contract_version": CONTRACT_VERSION,
            "pass": False,
            "failed_layer": failed_layer,
            "codes": codes,
            "l1": l1,
            "l2": None,
            "reason": "照片不符合平视正脸要求（" + ", ".join(codes) + "）",
        }
        qa_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        return doc

    l2 = run_face_qa(path, config, run_dir)
    passed = bool(l2.get("pass"))
    if not passed:
        failed_layer = "l2"
    doc = {
        "contract_version": CONTRACT_VERSION,
        "pass": passed,
        "failed_layer": failed_layer,
        "codes": codes,
        "l1": l1,
        "l2": l2,
        "reason": l2.get("reason") or "",
    }
    qa_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc


def _write_meta(
    config: PreviewConfig, run_dir: Path, t0: float, transfer_ms: float | None
) -> dict[str, Any]:
    meta = {
        "skill_dir": str(config.skill_dir.resolve()),
        "time_used_ms": round((time.perf_counter() - t0) * 1000, 1),
        "transfer_time_used_ms": round(transfer_ms, 1) if transfer_ms is not None else None,
    }
    (run_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta
