"""Tests for transfer prompt loading from skill markdown."""

from __future__ import annotations

from pathlib import Path

import pytest

from makeup_preview.prompt_loader import load_scope_appendix, load_transfer_prompt, parse_prompt_text_version

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / "skills" / "kol-makeup-preview"


@pytest.fixture
def skill_dir() -> Path:
    assert SKILL_DIR.is_dir(), f"missing skill dir: {SKILL_DIR}"
    return SKILL_DIR


def test_parse_prompt_text_version_from_repo_md(skill_dir: Path) -> None:
    md = (skill_dir / "transfer-prompt.md").read_text(encoding="utf-8")
    assert parse_prompt_text_version(md) == "wan-long-2"


def test_load_v2_long_prompt(skill_dir: Path) -> None:
    result = load_transfer_prompt(skill_dir, layout="v2")
    assert not result.used_fallback
    assert result.prompt_text_version == "wan-long-2"
    assert len(result.text) > 500
    assert "图3" in result.text
    assert "禁止" in result.text
    assert "不得换脸" in result.text


def test_load_v1_long_prompt(skill_dir: Path) -> None:
    result = load_transfer_prompt(skill_dir, layout="v1")
    assert not result.used_fallback
    assert "图2" in result.text
    assert "禁止" in result.text


def test_fallback_when_md_missing(tmp_path: Path) -> None:
    empty_skill = tmp_path / "skill"
    empty_skill.mkdir()
    result = load_transfer_prompt(empty_skill, layout="v2")
    assert result.used_fallback
    assert len(result.text) < 300


def test_fallback_when_block_missing(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "transfer-prompt.md").write_text(
        "prompt_text_version: wan-long-1\n\n```prompt-v1\nonly v1\n```\n",
        encoding="utf-8",
    )
    result = load_transfer_prompt(skill, layout="v2")
    assert result.used_fallback


def test_load_scope_appendix_v2(skill_dir: Path) -> None:
    result = load_scope_appendix(skill_dir, layout="v2")
    assert "{{PRIMARY_LIST_ZH}}" in result.text
    assert not result.used_fallback
