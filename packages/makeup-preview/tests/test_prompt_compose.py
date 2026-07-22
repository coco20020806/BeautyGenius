"""Tests for scoped prompt composition."""

from __future__ import annotations

from pathlib import Path

import pytest

from makeup_preview.prompt_compose import compose_transfer_prompt
from makeup_preview.scope_loader import TransferScope

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / "skills" / "kol-makeup-preview"


@pytest.fixture
def skill_dir() -> Path:
    assert SKILL_DIR.is_dir()
    return SKILL_DIR


def test_scoped_lip_appends_constraint(skill_dir: Path) -> None:
    scope = TransferScope(
        prompt_mode="scoped",
        source="taxonomy-coverage",
        present_primaries=("唇妆",),
        application_primaries=("唇妆",),
        allowed_region_labels=("唇妆",),
    )
    result = compose_transfer_prompt(skill_dir, layout="v2", transfer_scope=scope)
    assert result.prompt_mode == "scoped"
    assert "教程范围约束" in result.text
    assert "唇妆" in result.text
    assert "图3" in result.text


def test_full_no_appendix(skill_dir: Path) -> None:
    scope = TransferScope(
        prompt_mode="full",
        source="default_full",
        present_primaries=(),
        application_primaries=(),
        allowed_region_labels=(),
        warnings=("transfer_scope_fallback_full",),
    )
    result = compose_transfer_prompt(skill_dir, layout="v2", transfer_scope=scope)
    assert result.prompt_mode == "full"
    assert "教程范围约束" not in result.text
