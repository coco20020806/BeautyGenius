"""Tests for ETA estimation."""

from api_server.eta import (
    compute_remaining_seconds,
    estimate_eta_total,
    formula_eta_total,
    micro_weight,
)


def test_formula_eta_increases_with_duration() -> None:
    short = formula_eta_total(parse_mode="fast", skip_transfer=True, duration_sec=60, file_size_bytes=1_000_000)
    long = formula_eta_total(parse_mode="fast", skip_transfer=True, duration_sec=600, file_size_bytes=1_000_000)
    assert long > short


def test_estimate_eta_minimum() -> None:
    assert estimate_eta_total(parse_mode="fast", skip_transfer=True, duration_sec=10, file_size_bytes=0) >= 30


def test_remaining_decreases_with_weight() -> None:
    eta = 300
    started = "2020-01-01T00:00:00+00:00"
    r1 = compute_remaining_seconds(
        eta_total_seconds=eta,
        completed_weight=0.2,
        processing_started_at=started,
    )
    r2 = compute_remaining_seconds(
        eta_total_seconds=eta,
        completed_weight=0.8,
        processing_started_at=started,
    )
    assert r2 < r1


def test_micro_weight_monotonic_parse() -> None:
    prev = 0.0
    for stage in range(1, 11):
        w = micro_weight(f"parse:{stage}", skip_transfer=False)
        assert w >= prev
        prev = w
