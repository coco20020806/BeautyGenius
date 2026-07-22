"""Run directory helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def make_run_dir(output_root: Path) -> Path:
    runs = output_root / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = runs / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir
