"""Load transfer prompts from kol-makeup-preview/transfer-prompt.md."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from makeup_preview.config import (
    PROMPT_TEXT_VERSION_DEFAULT,
    TRANSFER_PROMPT_V1,
    TRANSFER_PROMPT_V2,
)

logger = logging.getLogger(__name__)

Layout = Literal["v1", "v2"]
_BLOCK_LANG = {"v1": "prompt-v1", "v2": "prompt-v2"}
_FALLBACK = {"v1": TRANSFER_PROMPT_V1, "v2": TRANSFER_PROMPT_V2}

_TEXT_VERSION_RE = re.compile(
    r"prompt_text_version:\s*([a-zA-Z0-9_-]+)",
)
_FENCE_RE = re.compile(
    r"```(prompt-v1|prompt-v2)\s*\n(.*?)```",
    re.DOTALL,
)


@dataclass(frozen=True)
class TransferPromptLoadResult:
    text: str
    prompt_text_version: str
    used_fallback: bool


def parse_prompt_text_version(md: str) -> str:
    m = _TEXT_VERSION_RE.search(md)
    if m:
        return m.group(1).strip()
    return PROMPT_TEXT_VERSION_DEFAULT


def _extract_block(md: str, layout: Layout) -> str | None:
    lang = _BLOCK_LANG[layout]
    for match in _FENCE_RE.finditer(md):
        if match.group(1) == lang:
            body = match.group(2).strip()
            if body:
                return body
    return None


def load_transfer_prompt(skill_dir: Path, *, layout: Layout) -> TransferPromptLoadResult:
    """Load prompt text for v1 (two-image) or v2 (three-image) layout."""
    path = skill_dir / "transfer-prompt.md"
    if not path.is_file():
        logger.warning("transfer-prompt.md missing at %s; using static fallback", path)
        return TransferPromptLoadResult(
            text=_FALLBACK[layout],
            prompt_text_version=PROMPT_TEXT_VERSION_DEFAULT,
            used_fallback=True,
        )

    md = path.read_text(encoding="utf-8")
    text_version = parse_prompt_text_version(md)
    block = _extract_block(md, layout)
    if block is None:
        logger.warning("No ```%s block in %s; using static fallback", _BLOCK_LANG[layout], path)
        return TransferPromptLoadResult(
            text=_FALLBACK[layout],
            prompt_text_version=text_version,
            used_fallback=True,
        )

    return TransferPromptLoadResult(
        text=block,
        prompt_text_version=text_version,
        used_fallback=False,
    )
