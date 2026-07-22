"""Tests for transfer scope resolution."""

from __future__ import annotations

import json
from pathlib import Path

from makeup_preview.scope_loader import (
    FULL_SCOPE_PRIMARY_COUNT,
    resolve_transfer_scope,
)


def test_no_parse_run_full_with_warning() -> None:
    scope = resolve_transfer_scope(None)
    assert scope.prompt_mode == "full"
    assert scope.source == "default_full"
    assert "transfer_scope_fallback_full" in scope.warnings


def test_lip_only_scoped(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "taxonomy-coverage.json").write_text(
        json.dumps({"present_primaries": ["唇妆"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    scope = resolve_transfer_scope(run)
    assert scope.prompt_mode == "scoped"
    assert scope.application_primaries == ("唇妆",)
    assert scope.source == "taxonomy-coverage"


def test_prep_plus_lip_excludes_prep(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "taxonomy-coverage.json").write_text(
        json.dumps({"present_primaries": ["妆前", "唇妆"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    scope = resolve_transfer_scope(run)
    assert scope.application_primaries == ("唇妆",)
    assert scope.prompt_mode == "scoped"


def test_many_primaries_full(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    primaries = [f"p{i}" for i in range(FULL_SCOPE_PRIMARY_COUNT)]
    (run / "taxonomy-coverage.json").write_text(
        json.dumps({"present_primaries": primaries}, ensure_ascii=False),
        encoding="utf-8",
    )
    scope = resolve_transfer_scope(run)
    assert scope.prompt_mode == "full"


def test_tutorial_fallback(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "tutorial.json").write_text(
        json.dumps(
            {
                "steps": [
                    {"step_id": "a", "taxonomy_primary": "唇妆"},
                    {"step_id": "b", "taxonomy_primary": "唇妆"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    scope = resolve_transfer_scope(run)
    assert scope.present_primaries == ("唇妆",)
    assert scope.source == "tutorial.json"
    assert "transfer_scope_from_tutorial" in scope.warnings


def test_override_full(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "taxonomy-coverage.json").write_text(
        json.dumps({"present_primaries": ["唇妆"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    scope = resolve_transfer_scope(run, transfer_scope_override="full")
    assert scope.prompt_mode == "full"
