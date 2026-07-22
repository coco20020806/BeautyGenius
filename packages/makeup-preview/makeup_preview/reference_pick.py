"""Pick KOL reference frame from parse run (replication after + fallbacks)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from makeup_preview.config import PREFERRED_PRIMARIES


@dataclass
class ReferencePick:
    path: Path
    meta: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    tutorial_before_path: Path | None = None
    tutorial_before_meta: dict[str, Any] | None = None
    strict_block_reason: str | None = None


class StrictReplicationError(Exception):
    """pair/after validation failed under --strict-replication."""


def _load_analysis(parse_run_dir: Path) -> dict[str, Any]:
    p = parse_run_dir / "analysis.json"
    if not p.is_file():
        raise FileNotFoundError(f"缺少 analysis.json: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _kf_file_exists(parse_run_dir: Path, filename: str) -> bool:
    return (parse_run_dir / "keyframes" / filename).is_file()


def _validation_pass(kf: dict[str, Any]) -> bool:
    v = kf.get("validation") or {}
    if "pass" in v:
        return bool(v["pass"])
    return True


def _collect_end_faces(
    steps: list[dict[str, Any]],
    parse_run_dir: Path,
    *,
    require_validation: bool,
    step_filter: str | None,
) -> list[tuple[dict[str, Any], dict[str, Any], float]]:
    items: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    for step in steps:
        name = step.get("step_name") or ""
        if step_filter and name != step_filter:
            continue
        for kf in step.get("keyframes") or []:
            if kf.get("role") != "step_end_face":
                continue
            fn = kf.get("filename") or ""
            if not fn or not _kf_file_exists(parse_run_dir, fn):
                continue
            if require_validation and not _validation_pass(kf):
                continue
            ts = float(kf.get("timestamp_sec") or 0)
            primary_rank = (
                len(PREFERRED_PRIMARIES) - PREFERRED_PRIMARIES.index(name)
                if name in PREFERRED_PRIMARIES
                else 0
            )
            score = ts + primary_rank * 1e6
            items.append((step, kf, score))
    return items


def _collect_makeup_detail(
    steps: list[dict[str, Any]], parse_run_dir: Path, step_filter: str | None
) -> list[tuple[dict[str, Any], dict[str, Any], float]]:
    items: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    for step in steps:
        name = step.get("step_name") or ""
        if step_filter and name != step_filter:
            continue
        for kf in step.get("keyframes") or []:
            if kf.get("role") != "makeup_detail":
                continue
            fn = kf.get("filename") or ""
            if fn and _kf_file_exists(parse_run_dir, fn):
                ts = float(kf.get("timestamp_sec") or 0)
                items.append((step, kf, ts))
    return items


def _pick_replication_after(
    parse_run_dir: Path,
    analysis: dict[str, Any],
    *,
    strict_replication: bool,
) -> ReferencePick | None:
    refs = analysis.get("makeup_replication_refs")
    if not refs:
        return None
    after = refs.get("after") or {}
    fn = after.get("filename") or ""
    if not fn or not _kf_file_exists(parse_run_dir, fn):
        return None

    warnings: list[str] = []
    pair = refs.get("pair_validation") or {}
    pair_pass = pair.get("pass")
    after_pass = _validation_pass(after)
    if pair_pass is not True:
        warnings.append("replication_pair_not_validated")
    if not after_pass:
        warnings.append("replication_after_validation_failed")

    if strict_replication and (pair_pass is not True or not after_pass):
        reason = pair.get("reason") or after.get("validation", {}).get("reason") or (
            "复刻参考对未通过验证"
        )
        raise StrictReplicationError(reason)

    path = parse_run_dir / "keyframes" / fn
    meta: dict[str, Any] = {
        "source": "parse_run",
        "parse_run_dir": str(parse_run_dir.resolve()),
        "parse_contract_version": analysis.get("contract_version"),
        "reference_tier": "replication_after",
        "keyframe_role": after.get("role", "replication_after"),
        "filename": fn,
        "after_source": after.get("source"),
        "replication_pair_pass": pair_pass,
    }
    before = refs.get("before") or {}
    bfn = before.get("filename") or ""
    before_path = None
    before_meta = None
    if bfn and _kf_file_exists(parse_run_dir, bfn):
        before_path = parse_run_dir / "keyframes" / bfn
        before_meta = {
            "role": before.get("role", "replication_before"),
            "filename": bfn,
            "source": before.get("source"),
        }

    return ReferencePick(
        path=path,
        meta=meta,
        warnings=warnings,
        tutorial_before_path=before_path,
        tutorial_before_meta=before_meta,
    )


def _pick_step_end_fallback(
    parse_run_dir: Path,
    analysis: dict[str, Any],
    *,
    reference_step: str | None,
) -> ReferencePick | None:
    steps = analysis.get("steps") or []
    warnings: list[str] = []
    for require_val in (True, False):
        candidates = _collect_end_faces(
            steps,
            parse_run_dir,
            require_validation=require_val,
            step_filter=reference_step,
        )
        if candidates:
            if not require_val:
                warnings.append("reference_end_face_without_validation_pass")
            step, kf, _ = max(candidates, key=lambda x: x[2])
            path = parse_run_dir / "keyframes" / kf["filename"]
            meta = {
                "source": "parse_run",
                "parse_run_dir": str(parse_run_dir.resolve()),
                "parse_contract_version": analysis.get("contract_version"),
                "reference_tier": "step_end_face",
                "step_name": step.get("step_name"),
                "keyframe_role": kf.get("role"),
                "filename": kf.get("filename"),
            }
            return ReferencePick(path=path, meta=meta, warnings=warnings)

    details = _collect_makeup_detail(steps, parse_run_dir, reference_step)
    if details:
        warnings.append("partial_reference")
        step, kf, _ = max(details, key=lambda x: x[2])
        path = parse_run_dir / "keyframes" / kf["filename"]
        meta = {
            "source": "parse_run",
            "parse_run_dir": str(parse_run_dir.resolve()),
            "parse_contract_version": analysis.get("contract_version"),
            "reference_tier": "makeup_detail",
            "step_name": step.get("step_name"),
            "keyframe_role": kf.get("role"),
            "filename": kf.get("filename"),
        }
        return ReferencePick(path=path, meta=meta, warnings=warnings)
    return None


def resolve_transfer_reference(
    parse_run_dir: Path,
    *,
    reference_step: str | None = None,
    strict_replication: bool = False,
) -> ReferencePick:
    parse_run_dir = parse_run_dir.resolve()
    analysis = _load_analysis(parse_run_dir)
    warnings_extra: list[str] = []

    if reference_step:
        pick = _pick_step_end_fallback(
            parse_run_dir, analysis, reference_step=reference_step
        )
        if pick:
            return pick
        raise FileNotFoundError(
            f"步骤 {reference_step!r} 中未找到可用 step_end_face: {parse_run_dir}"
        )

    repl = _pick_replication_after(
        parse_run_dir, analysis, strict_replication=strict_replication
    )
    if repl:
        return repl

    contract = analysis.get("contract_version")
    if contract == "v2.1":
        meta = _load_json_if_exists(parse_run_dir / "meta.json") or {}
        if meta.get("replication_refs"):
            warnings_extra.append("replication_after_missing_fallback")
        if _load_json_if_exists(parse_run_dir / "replication_hints.json"):
            warnings_extra.append("replication_hints_present")

    pick = _pick_step_end_fallback(parse_run_dir, analysis, reference_step=None)
    if pick:
        pick.warnings.extend(warnings_extra)
        return pick

    raise FileNotFoundError(f"parse run 中未找到可用参考关键帧: {parse_run_dir}")


def pick_reference_from_parse_run(
    parse_run_dir: Path,
    *,
    reference_step: str | None = None,
    strict_replication: bool = False,
) -> ReferencePick:
    return resolve_transfer_reference(
        parse_run_dir,
        reference_step=reference_step,
        strict_replication=strict_replication,
    )
