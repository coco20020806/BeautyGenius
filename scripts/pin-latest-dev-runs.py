#!/usr/bin/env python3
"""Pin latest video-parse and makeup-preview run dirs for dev skip-to-preview."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PARSE_OUTPUT_ROOT = REPO_ROOT / "outputs" / "runs"
PREVIEW_RUNS_ROOT = REPO_ROOT / "outputs" / "makeup-preview" / "runs"
PINNED_PATH = REPO_ROOT / "configs" / "dev-pinned-runs.json"


def _latest_run(parent: Path, *, marker_names: tuple[str, ...]) -> Path | None:
    if not parent.is_dir():
        return None
    candidates: list[Path] = []
    for child in parent.iterdir():
        if not child.is_dir():
            continue
        if any((child / name).is_file() for name in marker_names):
            candidates.append(child)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _rel_posix(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def main() -> int:
    parse_run = _latest_run(PARSE_OUTPUT_ROOT, marker_names=("analysis.json",))
    preview_run = _latest_run(
        PREVIEW_RUNS_ROOT,
        marker_names=("preview.json", "preview_01.jpg"),
    )

    missing: list[str] = []
    if parse_run is None:
        missing.append(f"video parse run（需 {PARSE_OUTPUT_ROOT}/<ts>/analysis.json）")
    if preview_run is None:
        missing.append(
            f"makeup preview run（需 {PREVIEW_RUNS_ROOT}/<ts>/preview.json 或 preview_01.jpg）"
        )
    if missing:
        sys.stderr.write("未找到可固定的本地 run：\n")
        for item in missing:
            sys.stderr.write(f"  - {item}\n")
        sys.stderr.write("请先运行 beauty-video-parse 与 makeup-preview，再执行本脚本。\n")
        return 1

    doc = {
        "parse_run_dir": _rel_posix(parse_run),
        "preview_run_dir": _rel_posix(preview_run),
        "pinned_at": datetime.now(timezone.utc).isoformat(),
    }
    PINNED_PATH.parent.mkdir(parents=True, exist_ok=True)
    PINNED_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(PINNED_PATH)
    print(json.dumps(doc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
