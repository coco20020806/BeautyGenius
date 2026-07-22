"""Average-face baseline assets (skill root PNGs)."""

from __future__ import annotations

from pathlib import Path

from makeup_preview.config import BaselineGender

ASSETS = {
    "female": "female_average_face.png",
    "male": "male_average_face.png",
}


def resolve_baseline_path(skill_dir: Path, gender: BaselineGender) -> Path:
    name = ASSETS[gender]
    path = skill_dir / name
    if not path.is_file():
        raise FileNotFoundError(f"平均脸底图不存在: {path}")
    return path


def baseline_metadata(gender: BaselineGender) -> dict[str, str]:
    return {
        "type": "average_baseline",
        "baseline": gender,
        "skill_asset": ASSETS[gender],
    }
