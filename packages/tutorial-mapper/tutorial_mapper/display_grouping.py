"""Deterministic display grouping + display_title (skills/tutorial-mapper/display-grouping.md)."""

from __future__ import annotations

from typing import Any


def _primary_of(step: dict[str, Any]) -> str:
    return (step.get("taxonomy_primary") or "").strip()


def _group_title(primary: str) -> str:
    return primary or "其他"


def _unique_title(candidate: str, used: set[str]) -> str:
    if candidate not in used:
        return candidate
    n = 2
    while True:
        alt = f"{candidate} · {n}"
        if alt not in used:
            return alt
        n += 1


def _titles_for_group(
    primary: str,
    group_steps: list[dict[str, Any]],
) -> list[str]:
    title_prefix = _group_title(primary)
    if len(group_steps) == 1:
        step = group_steps[0]
        alone = primary or (step.get("step_id") or "步骤")
        return [alone]

    used: set[str] = set()
    out: list[str] = []
    for i, step in enumerate(group_steps):
        subs = [
            str(s).strip()
            for s in (step.get("taxonomy_sub_steps") or [])
            if str(s).strip()
        ]
        chosen = ""
        if subs:
            for sub in subs:
                cand = f"{title_prefix} · {sub}"
                if cand not in used:
                    chosen = cand
                    break
            if not chosen:
                chosen = _unique_title(f"{title_prefix} · {subs[0]}", used)
        else:
            chosen = f"{title_prefix} · {i + 1}"
            if chosen in used:
                chosen = _unique_title(chosen, used)
        used.add(chosen)
        out.append(chosen)
    return out


def build_step_groups(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group consecutive steps with the same taxonomy_primary."""
    groups: list[dict[str, Any]] = []
    current_primary: str | None = None
    current_ids: list[str] = []

    def flush() -> None:
        nonlocal current_primary, current_ids
        if current_primary is None and not current_ids:
            return
        idx = len(groups) + 1
        groups.append(
            {
                "group_id": f"group_{idx:02d}",
                "title": _group_title(current_primary or ""),
                "index": idx,
                "step_ids": list(current_ids),
            }
        )
        current_primary = None
        current_ids = []

    for step in steps:
        if not isinstance(step, dict):
            continue
        primary = _primary_of(step)
        sid = (step.get("step_id") or "").strip() or f"step_{len(current_ids) + 1}"
        if current_primary is None:
            current_primary = primary
            current_ids = [sid]
            continue
        if primary == current_primary:
            current_ids.append(sid)
        else:
            flush()
            current_primary = primary
            current_ids = [sid]
    flush()
    return groups


def apply_display_grouping(tutorial: dict[str, Any]) -> dict[str, Any]:
    """Mutate tutorial in place: set step_groups, display_title, display_group_id."""
    steps = [s for s in (tutorial.get("steps") or []) if isinstance(s, dict)]
    groups = build_step_groups(steps)
    tutorial["step_groups"] = groups

    by_id = {(s.get("step_id") or ""): s for s in steps if (s.get("step_id") or "")}

    for group in groups:
        group_id = group["group_id"]
        ids = group.get("step_ids") or []
        group_steps = [by_id[i] for i in ids if i in by_id]
        if not group_steps:
            continue
        primary = _primary_of(group_steps[0])
        titles = _titles_for_group(primary, group_steps)
        for step, title in zip(group_steps, titles):
            step["display_title"] = title
            step["display_group_id"] = group_id

    # Steps missing from groups (should not happen) still get fallbacks
    for step in steps:
        if not step.get("display_title"):
            primary = _primary_of(step)
            step["display_title"] = primary or (step.get("step_id") or "步骤")
        if not step.get("display_group_id"):
            step["display_group_id"] = ""

    return tutorial
