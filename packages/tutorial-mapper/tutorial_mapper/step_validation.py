"""Tutorial step semantic validation (see skills/tutorial-mapper/step-validation.md)."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

VALIDATION_VERSION = "1"
SAME_CLIP_DELTA_SEC = 2.0
OVERLAP_RATIO_THRESHOLD = 0.30
INSTRUCTION_JACCARD_THRESHOLD = 0.85

PRIMARY_ENUM = frozenset(
    {
        "妆前",
        "底妆",
        "遮瑕",
        "定妆",
        "眉毛",
        "眼睛",
        "眼线",
        "睫毛",
        "修容",
        "腮红",
        "高光",
        "唇妆",
    }
)

_PUNCT = re.compile(r"[\s\.,，。!！?？、；;：:\"'\"''（）()\[\]【】\-—…·]+")


def _normalize_instruction(text: str) -> str:
    t = (text or "").strip().lower()
    t = _PUNCT.sub("", t)
    return t


def _bigram_jaccard(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0

    def bigrams(s: str) -> set[str]:
        if len(s) < 2:
            return {s} if s else set()
        return {s[i : i + 2] for i in range(len(s) - 1)}

    sa, sb = bigrams(a), bigrams(b)
    if not sa and not sb:
        return 1.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def _clip_bounds(step: dict[str, Any]) -> tuple[float, float]:
    clip = step.get("video_clip") or {}
    start = float(clip.get("start", 0))
    end = float(clip.get("end", start))
    return start, end


def _overlap_ratio(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    len_a = max(0.0, end_a - start_a)
    len_b = max(0.0, end_b - start_b)
    if len_a <= 0 or len_b <= 0:
        return 0.0
    overlap = max(0.0, min(end_a, end_b) - max(start_a, start_b))
    return overlap / min(len_a, len_b)


def _instruction_similar(a: str, b: str) -> bool:
    na, nb = _normalize_instruction(a), _normalize_instruction(b)
    if na == nb and na:
        return True
    return _bigram_jaccard(na, nb) >= INSTRUCTION_JACCARD_THRESHOLD


def _issue(
    code: str,
    severity: str,
    message: str,
    *,
    taxonomy_primary: str = "",
    step_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "taxonomy_primary": taxonomy_primary,
        "step_ids": step_ids or [],
        "message": message,
    }


def validate_tutorial_steps(tutorial: dict[str, Any]) -> dict[str, Any]:
    """Return tutorial_step_validation block for enrichment_meta."""
    duration = float(tutorial.get("duration") or 0)
    steps = [s for s in (tutorial.get("steps") or []) if isinstance(s, dict)]
    issues: list[dict[str, Any]] = []

    seen_ids: dict[str, int] = {}
    by_primary: dict[str, list[str]] = defaultdict(list)

    for step in steps:
        sid = (step.get("step_id") or "").strip()
        primary = (step.get("taxonomy_primary") or "").strip()
        if sid:
            if sid in seen_ids:
                issues.append(
                    _issue(
                        "duplicate_step_id",
                        "error",
                        f"重复的 step_id: {sid}",
                        step_ids=[sid],
                    )
                )
            seen_ids[sid] = seen_ids.get(sid, 0) + 1
            if primary:
                by_primary[primary].append(sid)

        if not primary:
            issues.append(
                _issue(
                    "unknown_taxonomy_primary",
                    "warning",
                    f"步骤 {sid or '?'} 缺少 taxonomy_primary",
                    step_ids=[sid] if sid else [],
                )
            )
        elif primary not in PRIMARY_ENUM:
            issues.append(
                _issue(
                    "unknown_taxonomy_primary",
                    "warning",
                    f"未知主类: {primary}",
                    taxonomy_primary=primary,
                    step_ids=[sid] if sid else [],
                )
            )

        start, end = _clip_bounds(step)
        if start >= end:
            issues.append(
                _issue(
                    "invalid_video_clip",
                    "error",
                    f"步骤 {sid}: start >= end",
                    taxonomy_primary=primary,
                    step_ids=[sid] if sid else [],
                )
            )
        elif duration > 0 and (start < 0 or end > duration + 0.01):
            issues.append(
                _issue(
                    "invalid_video_clip",
                    "error",
                    f"步骤 {sid}: clip 超出 duration",
                    taxonomy_primary=primary,
                    step_ids=[sid] if sid else [],
                )
            )

    title_owners: dict[str, list[str]] = defaultdict(list)
    for step in steps:
        sid = (step.get("step_id") or "").strip()
        title = (step.get("display_title") or "").strip()
        if title and sid:
            title_owners[title].append(sid)
    for title, ids in title_owners.items():
        if len(ids) >= 2:
            issues.append(
                _issue(
                    "duplicate_display_title",
                    "warning",
                    f"display_title 重复: {title}",
                    step_ids=ids,
                )
            )

    by_primary_out: dict[str, Any] = {
        p: {"step_count": len(ids), "step_ids": ids} for p, ids in by_primary.items()
    }

    steps_by_id = {
        (s.get("step_id") or ""): s for s in steps if (s.get("step_id") or "")
    }
    for primary, ids in by_primary.items():
        if len(ids) < 2:
            continue
        primary_steps = [steps_by_id[i] for i in ids if i in steps_by_id]
        for i in range(len(primary_steps)):
            for j in range(i + 1, len(primary_steps)):
                sa, sb = primary_steps[i], primary_steps[j]
                id_a = sa.get("step_id", "")
                id_b = sb.get("step_id", "")
                start_a, end_a = _clip_bounds(sa)
                start_b, end_b = _clip_bounds(sb)
                instr_a = sa.get("instruction") or ""
                instr_b = sb.get("instruction") or ""

                same_clip = (
                    abs(start_a - start_b) <= SAME_CLIP_DELTA_SEC
                    and abs(end_a - end_b) <= SAME_CLIP_DELTA_SEC
                )
                overlap = _overlap_ratio(start_a, end_a, start_b, end_b)
                high_overlap = overlap > OVERLAP_RATIO_THRESHOLD
                sim_instr = _instruction_similar(instr_a, instr_b)

                if same_clip:
                    issues.append(
                        _issue(
                            "duplicate_step_same_clip",
                            "error",
                            f"{id_a} 与 {id_b} 片段时间几乎相同",
                            taxonomy_primary=primary,
                            step_ids=[id_a, id_b],
                        )
                    )
                elif high_overlap and sim_instr:
                    issues.append(
                        _issue(
                            "duplicate_step_overlap_and_instruction",
                            "error",
                            f"{id_a} 与 {id_b} 时间重叠且 instruction 高度相似",
                            taxonomy_primary=primary,
                            step_ids=[id_a, id_b],
                        )
                    )
                else:
                    if high_overlap:
                        issues.append(
                            _issue(
                                "duplicate_step_overlap",
                                "warning",
                                f"{id_a} 与 {id_b} 片段时间重叠比例 {overlap:.0%}",
                                taxonomy_primary=primary,
                                step_ids=[id_a, id_b],
                            )
                        )
                    if sim_instr and instr_a.strip() and instr_b.strip():
                        issues.append(
                            _issue(
                                "duplicate_step_same_instruction",
                                "warning",
                                f"{id_a} 与 {id_b} instruction 高度相似",
                                taxonomy_primary=primary,
                                step_ids=[id_a, id_b],
                            )
                        )

    has_error = any(i.get("severity") == "error" for i in issues)
    return {
        "pass": not has_error,
        "version": VALIDATION_VERSION,
        "by_primary": by_primary_out,
        "issues": issues,
    }


def count_step_validation_issues(block: dict[str, Any]) -> tuple[int, int, int]:
    """Return (total, error_count, warning_count)."""
    issues = block.get("issues") or []
    errors = sum(1 for i in issues if i.get("severity") == "error")
    warnings = sum(1 for i in issues if i.get("severity") == "warning")
    return len(issues), errors, warnings


def format_step_validation_summary(block: dict[str, Any]) -> str:
    total, errors, warnings = count_step_validation_issues(block)
    passed = bool(block.get("pass"))
    return (
        f"tutorial_step_validation: pass={str(passed).lower()} "
        f"issues={total} errors={errors} warnings={warnings}"
    )
