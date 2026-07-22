from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api_server.config import SKIP_TRANSFER, TASKS_ROOT

# Smoke-tuned constants; adjust after local runs.
_ETA_BASE: dict[tuple[str, bool], float] = {
    ("fast", True): 90.0,
    ("fast", False): 180.0,
    ("full", True): 150.0,
    ("full", False): 300.0,
}
_ETA_K_DURATION: dict[tuple[str, bool], float] = {
    ("fast", True): 0.8,
    ("fast", False): 1.2,
    ("full", True): 1.0,
    ("full", False): 1.5,
}
_K_SIZE_MB = 2.0

STATS_PATH = TASKS_ROOT / "_eta_stats.jsonl"
MAX_STATS_LINES = 200

# Micro-step cumulative weights (must be non-decreasing, last = 1.0)
_PARSE_WEIGHTS: dict[int, float] = {
    1: 0.03,
    2: 0.06,
    3: 0.10,
    4: 0.22,
    5: 0.35,
    6: 0.42,
    7: 0.48,
    8: 0.52,
    9: 0.54,
    10: 0.55,
}
_MAP_WEIGHTS: dict[int, float] = {
    1: 0.57,
    2: 0.60,
    3: 0.63,
    4: 0.66,
    5: 0.68,
    6: 0.70,
}
_PREVIEW_WEIGHTS: dict[str, float] = {
    "pick": 0.72,
    "target": 0.78,
    "transfer": 0.93,
    "write": 0.95,
}
_PREVIEW_SKIP_TRANSFER_WEIGHTS: dict[str, float] = {
    "pick": 0.72,
    "target": 0.78,
    "transfer": 0.82,
    "write": 0.95,
}
_HINT_WEIGHT = 1.0


def micro_weight(step_id: str, *, skip_transfer: bool) -> float:
    if step_id.startswith("parse:"):
        stage = int(step_id.split(":", 1)[1])
        return _PARSE_WEIGHTS.get(stage, 0.55)
    if step_id.startswith("map:"):
        stage = int(step_id.split(":", 1)[1])
        return _MAP_WEIGHTS.get(stage, 0.70)
    if step_id.startswith("preview:"):
        key = step_id.split(":", 1)[1]
        table = _PREVIEW_SKIP_TRANSFER_WEIGHTS if skip_transfer else _PREVIEW_WEIGHTS
        return table.get(key, 0.95)
    if step_id == "hint:done":
        return _HINT_WEIGHT
    return 0.0


def formula_eta_total(
    *,
    parse_mode: str,
    skip_transfer: bool,
    duration_sec: float,
    file_size_bytes: int,
) -> float:
    mode = parse_mode if parse_mode in {"fast", "full"} else "fast"
    key = (mode, skip_transfer)
    base = _ETA_BASE.get(key, 120.0)
    k_dur = _ETA_K_DURATION.get(key, 1.0)
    file_mb = max(0.0, file_size_bytes / (1024 * 1024))
    return base + duration_sec * k_dur + file_mb * _K_SIZE_MB


def _load_stats() -> list[dict[str, Any]]:
    if not STATS_PATH.is_file():
        return []
    lines = STATS_PATH.read_text(encoding="utf-8").strip().splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-MAX_STATS_LINES:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def median_historical_seconds(
    *,
    parse_mode: str,
    skip_transfer: bool,
    duration_sec: float,
) -> float | None:
    rows = _load_stats()
    if not rows:
        return None
    lo = duration_sec * 0.7
    hi = duration_sec * 1.3
    matches = [
        r["actual_seconds"]
        for r in rows
        if r.get("parse_mode") == parse_mode
        and bool(r.get("skip_transfer")) == skip_transfer
        and lo <= float(r.get("duration_sec", 0)) <= hi
    ]
    if len(matches) < 2:
        return None
    return float(statistics.median(matches))


def estimate_eta_total(
    *,
    parse_mode: str,
    skip_transfer: bool,
    duration_sec: float,
    file_size_bytes: int,
) -> int:
    formula = formula_eta_total(
        parse_mode=parse_mode,
        skip_transfer=skip_transfer,
        duration_sec=duration_sec,
        file_size_bytes=file_size_bytes,
    )
    median = median_historical_seconds(
        parse_mode=parse_mode,
        skip_transfer=skip_transfer,
        duration_sec=duration_sec,
    )
    if median is not None:
        blended = 0.6 * median + 0.4 * formula
    else:
        blended = formula
    return max(30, int(round(blended)))


def compute_remaining_seconds(
    *,
    eta_total_seconds: float,
    completed_weight: float,
    processing_started_at: str | None,
) -> int:
    if completed_weight >= 1.0:
        return 0
    w = min(max(completed_weight, 0.0), 0.99)
    budget_remaining = eta_total_seconds * (1.0 - w)
    extrapolated = budget_remaining
    if processing_started_at and w > 0.05:
        try:
            started = datetime.fromisoformat(processing_started_at.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - started).total_seconds()
            rate = elapsed / w
            extrapolated = rate * (1.0 - w)
        except ValueError:
            extrapolated = budget_remaining
    remaining = min(budget_remaining, extrapolated)
    if completed_weight < 1.0:
        remaining = max(5.0, remaining)
    return int(round(remaining))


def record_completed_stats(
    *,
    parse_mode: str,
    skip_transfer: bool,
    duration_sec: float,
    actual_seconds: float,
) -> None:
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "parse_mode": parse_mode,
        "skip_transfer": skip_transfer,
        "duration_sec": duration_sec,
        "actual_seconds": actual_seconds,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    with STATS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if STATS_PATH.is_file():
        lines = STATS_PATH.read_text(encoding="utf-8").strip().splitlines()
        if len(lines) > MAX_STATS_LINES:
            STATS_PATH.write_text("\n".join(lines[-MAX_STATS_LINES:]) + "\n", encoding="utf-8")
