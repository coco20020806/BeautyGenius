"""Taxonomy primary → product part / step_id slug mapping."""

from __future__ import annotations

# beauty-video-parse 12 主类 → 跟练 part
PRIMARY_TO_PART: dict[str, str] = {
    "妆前": "prep",
    "底妆": "base",
    "遮瑕": "concealer",
    "定妆": "set",
    "眉毛": "brow",
    "眼睛": "eye",
    "眼线": "eye",
    "睫毛": "eye",
    "修容": "contour",
    "高光": "highlight",
    "腮红": "cheek",
    "唇妆": "lip",
}

# part → step_id 前缀（blush_01 风格）
PART_TO_STEP_SLUG: dict[str, str] = {
    "prep": "prep",
    "base": "base",
    "concealer": "concealer",
    "set": "set",
    "brow": "brow",
    "eye": "eye",
    "contour": "contour",
    "highlight": "highlight",
    "cheek": "blush",
    "lip": "lip",
    "other": "other",
}

PARTS = frozenset(PART_TO_STEP_SLUG.keys())
DIFFICULTIES = frozenset({"easy", "medium", "hard", "unknown"})


def primary_to_part(primary: str) -> str:
    return PRIMARY_TO_PART.get((primary or "").strip(), "other")


def part_step_slug(part: str) -> str:
    return PART_TO_STEP_SLUG.get(part, "other")
