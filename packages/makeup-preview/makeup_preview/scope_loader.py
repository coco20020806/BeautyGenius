"""Resolve makeup transfer scope from parse run (transfer-scope.md v1)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

FULL_SCOPE_PRIMARY_COUNT = 6
PREP_PRIMARY = "妆前"

PromptMode = Literal["full", "scoped"]
ScopeSource = Literal["taxonomy-coverage", "tutorial.json", "default_full"]


@dataclass(frozen=True)
class TransferScope:
    prompt_mode: PromptMode
    source: ScopeSource
    present_primaries: tuple[str, ...]
    application_primaries: tuple[str, ...]
    allowed_region_labels: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if not x or x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def _primaries_from_tutorial(parse_run_dir: Path) -> list[str]:
    doc = _load_json(parse_run_dir / "tutorial.json")
    if not doc:
        return []
    steps = doc.get("steps") or []
    primaries: list[str] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        primary = step.get("taxonomy_primary")
        if isinstance(primary, str) and primary.strip():
            primaries.append(primary.strip())
        else:
            tax = step.get("taxonomy")
            if isinstance(tax, dict):
                p = tax.get("primary")
                if isinstance(p, str) and p.strip():
                    primaries.append(p.strip())
    return _unique_preserve_order(primaries)


def _application_primaries(present: list[str]) -> list[str]:
    return [p for p in present if p != PREP_PRIMARY]


def _decide_mode(
    application: list[str],
    *,
    transfer_scope_override: str | None,
) -> PromptMode:
    if transfer_scope_override == "full":
        return "full"
    if not application:
        return "full"
    if len(application) >= FULL_SCOPE_PRIMARY_COUNT:
        return "full"
    return "scoped"


def resolve_transfer_scope(
    parse_run_dir: Path | None,
    *,
    transfer_scope_override: str | None = None,
) -> TransferScope:
    """Build transfer scope; manual preview (no parse) → full + transfer_scope_fallback_full."""
    warnings: list[str] = []
    if parse_run_dir is None:
        warnings.append("transfer_scope_fallback_full")
        return TransferScope(
            prompt_mode="full",
            source="default_full",
            present_primaries=(),
            application_primaries=(),
            allowed_region_labels=(),
            warnings=tuple(warnings),
        )

    parse_run_dir = parse_run_dir.resolve()
    source: ScopeSource = "default_full"
    present: list[str] = []

    coverage = _load_json(parse_run_dir / "taxonomy-coverage.json")
    if coverage:
        raw = coverage.get("present_primaries")
        if isinstance(raw, list):
            present = _unique_preserve_order([str(x).strip() for x in raw if str(x).strip()])
        if present:
            source = "taxonomy-coverage"

    if not present:
        present = _primaries_from_tutorial(parse_run_dir)
        if present:
            source = "tutorial.json"
            warnings.append("transfer_scope_from_tutorial")

    application = _application_primaries(present)
    mode = _decide_mode(application, transfer_scope_override=transfer_scope_override)

    if not present and not application:
        warnings.append("transfer_scope_fallback_full")
        source = "default_full"

    labels = list(application)
    return TransferScope(
        prompt_mode=mode,
        source=source,
        present_primaries=tuple(present),
        application_primaries=tuple(application),
        allowed_region_labels=tuple(labels),
        warnings=tuple(warnings),
    )


def scope_to_preview_dict(scope: TransferScope) -> dict[str, Any]:
    return {
        "source": scope.source,
        "present_primaries": list(scope.present_primaries),
        "application_primaries": list(scope.application_primaries),
        "allowed_region_labels": list(scope.allowed_region_labels),
    }
