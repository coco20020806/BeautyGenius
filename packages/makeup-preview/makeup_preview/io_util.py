"""Run directory and file helpers."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image


def to_file_uri(path: Path) -> str:
    return f"file://{path.resolve().as_posix()}"


def make_run_dir(output_root: Path) -> Path:
    runs = output_root / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = runs / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def copy_image_as_jpg(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        rgb = im.convert("RGB")
        rgb.save(dest, format="JPEG", quality=92)


def maybe_copy(src: Path, dest: Path) -> None:
    if src.resolve() == dest.resolve():
        return
    copy_image_as_jpg(src, dest)


def prepare_for_api(path: Path, run_dir: Path, label: str, max_long: int) -> Path:
    """Resize in-run if needed; return path to use for API."""
    with Image.open(path) as im:
        w, h = im.size
        long_side = max(w, h)
        if long_side <= max_long:
            return path
        scale = max_long / long_side
        nw, nh = int(w * scale), int(h * scale)
        out = run_dir / f"{label}_api.jpg"
        im.convert("RGB").resize((nw, nh), Image.Resampling.LANCZOS).save(
            out, format="JPEG", quality=90
        )
        return out
