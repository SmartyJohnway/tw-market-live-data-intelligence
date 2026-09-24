"""Fixture-only tests for bounded TWSE STOCK_DAY month traversal."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from server.services.phase_h_h3_twse_stock_day_adapter import (
    SOURCE_CONTRACT_ID,
    SOURCE_FAMILY,
    TWSEStockDayResult,
)
from server.services.phase_h_h3_twse_stock_day_walker import collect_twse_stock_day_lookback
from server.services.phase_h_recent_performance import build_recent_performance_evidence


ROOT = Path(__file__).resolve().parents[2]
TARGET = {"canonical_target_id": "TWSE:1423", "market": "TWSE", "security_code": "1423"}
RETRIEVED = "2026-09-24T15:00:00+08:00"
END_DATE = "2025-03-10"


def _observation(trade_date: str, close: float | int = 20.0, **changes: Any) -> dict[str, Any]:
    row = {
        **TARGET,
        "trade_date": trade_date,
        "close": close,
        "volume": 1000,
        "source_family": SOURCE_FAMILY,
        "source_contract_id": SOURCE_CONTRACT_ID,
        "retrieved_at": RETRIEVED,
        "citation_ids": [f"fixture:{trade_date}"],
    }
    row.update(changes)
    return row


def _end(trade_date: str = END_DATE) -> dict[str, Any]:
    return _observation(trade_date, 30.0, source_family="GOVERNED_END_FIXTURE", source_contract_id="END_FIXTURE_V1")


def _unusable(trade_date: str) -> dict[str, str]:
    return {"trade_date": trade_date, "reason": "close_unavailable"}


def _month_result(
    month: str,
    observations: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
    *,
    unusable: tuple[dict[str, str], ...] | list[dict[str, str]] = (),
    status: str | None = None,
    error_code: str | None = None,
) -> TWSEStockDayResult:
    body = f"fixture:{month}:{len(observations)}:{len(unusable)}".encode()
    return TWSEStockDayResult(
        status=status or ("available" if observations else "no_evidence_in_covered_scope"),
        requested_month=month,
        http_status=200 if status not in {"source_failed", "binding_failed"} else 503,
        response_byte_count=len(body),
        response_sha256=sha256(body).hexdigest(),
        observations=tuple(observations),
        unusable_observation_count=len(unusable),
        unusable_observations=tuple(unusable),
        error_code=error_code,
    )


def _run(
    month_results: dict[str, TWSEStockDayResult],
    *,
    end: dict[str, Any] | None = None,
    lookback: int = 1,
    budget: int = 3,
    calls: list[str] | None = None,
):
    calls = calls if calls is not None else []

    def fetch_month(**kwargs):
        month = kwargs["requested_month"]
        calls.append(month)
        return month_results[month]

    result = collect_twse_stock_day_lookback(
        target=TARGET,
        instrument_family="company_share",
        instrument_type="common_share",
        governed_end_observation=end or _end(),
        lookback_trading_days=lookback,
        retrieved_at=RETRIEVED,
        timeout_seconds=3.0,
        max_response_bytes=32_000,
        month_request_budget=budget,
        fetch_month=fetch_month,
    )
    return result, calls


def _project(result, end, lookback: int, *, outcome: str | None = None) -> dict[str, Any]:
    return build_recent_performance_evidence(
        target=TARGET,
        observations=result.observations,
        governed_end_observation=end,
        requested_observations=lookback,
        baseline_lookbacks=[lookback],
        current_volume_basis="completed_session",
        schema=json.loads((ROOT / "schemas/recent_performance_evidence.v1.schema.json").read_text(encoding="utf-8")),
        governed_outcome=outcome,
        caveats=[result.error_code or result.stop_reason] if outcome in {"source_failed", "binding_failed"} else [],
    )


def test_one_day_uses_one_end_month_and_excludes_end_and_post_end_rows() -> None:
    end = _end()
    rows = [
        _observation("2025-03-07", 21.0),
        _observation("2025-03-10", 30.0),
        _observation("2025-03-11", 31.0),
        _observation("2025-03-12", 32.0),
    ]
    result, calls = _run({"2025-03": _month_result("2025-03", rows)}, end=end)

    assert result.status == "available"
    assert calls == ["2025-03"]
    assert result.observations == (_observation("2025-03-07", 21.0),)
    assert result.post_end_rows_excluded == 3
    assert result.valid_lookback_count == 1
    assert result.missing_lookback_count == 0
    projected = _project(result, end, 1)
    assert projected["coverage_status"] == "complete"
    assert projected["baselines"][0]["required_distinct_close_count"] == 2


def test_unusable_close_metadata_is_bounded_strictly_before_governed_end() -> None:
    end = _end("2025-03-10")
    month = _month_result(
        "2025-03",
        [_observation("2025-03-07", 21.0)],
        unusable=[
            _unusable("2025-03-06"),
            _unusable("2025-03-10"),
            _unusable("2025-03-12"),
        ],
    )

    result, calls = _run({"2025-03": month}, end=end, lookback=1)

    assert result.status == "available"
    assert calls == ["2025-03"]
    assert [row["trade_date"] for row in result.observations] == ["2025-03-07"]
    assert result.unusable_observation_count == 1
    assert result.unusable_observations == (
        {"trade_date": "2025-03-06", "reason": "close_unavailable", "source_month": "2025-03"},
    )
    assert result.post_end_rows_excluded == 2


def test_five_day_same_month_satisfaction_is_minimal_and_h3_complete() -> None:
    end = _end("2025-03-10")
    days = ["2025-03-03", "2025-03-04", "2025-03-05", "2025-03-06", "2025-03-07"]
    rows = [_observation(day, 20 + index) for index, day in enumerate(days)]
    result, calls = _run({"2025-03": _month_result("2025-03", rows)}, end=end, lookback=5)

    assert result.status == "available"
    assert calls == ["2025-03"]
    assert [row["trade_date"] for row in result.observations] == days
    projected = _project(result, end, 5)
    assert projected["coverage_status"] == "complete"
    assert projected["available_baselines"] == [5]
    assert projected["baselines"][0]["required_distinct_close_count"] == 6


def test_twenty_day_stops_at_previous_month_as_soon_as_twenty_exist() -> None:
    end = _end("2025-03-14")
    march_days = ["2025-03-03", "2025-03-04", "2025-03-05", "2025-03-06", "2025-03-07", "2025-03-10", "2025-03-11", "2025-03-12"]
    feb_days = ["2025-02-11", "2025-02-12", "2025-02-13", "2025-02-14", "2025-02-17", "2025-02-18", "2025-02-19", "2025-02-20", "2025-02-21", "2025-02-24", "2025-02-25", "2025-02-26"]
    result, calls = _run(
        {
            "2025-03": _month_result("2025-03", [_observation(day, 10 + index) for index, day in enumerate(march_days)] + [_observation("2025-03-14", 30), _observation("2025-03-17", 31)]),
            "2025-02": _month_result("2025-02", [_observation(day, 20 + index) for index, day in enumerate(feb_days)]),
            "2025-01": _month_result("2025-01"),
        },
        end=end,
        lookback=20,
    )

    assert result.status == "available"
    assert calls == ["2025-03", "2025-02"]
    assert result.request_count == 2
    assert len(result.observations) == 20
    assert result.post_end_rows_excluded == 2
    projected = _project(result, end, 20)
    assert projected["coverage_status"] == "complete"
    assert projected["baselines"][0]["required_distinct_close_count"] == 21


def test_three_month_walk_preserves_unavailable_close_provenance_and_reaches_twenty() -> None:
    end = _end("2025-03-10")
    march_days = ["2025-03-03", "2025-03-04", "2025-03-05", "2025-03-07"]
    feb_days = ["2025-02-03", "2025-02-04", "2025-02-05", "2025-02-06", "2025-02-07", "2025-02-10", "2025-02-11", "2025-02-12", "2025-02-13"]
    jan_days = ["2025-01-20", "2025-01-21", "2025-01-22", "2025-01-23", "2025-01-24", "2025-01-27", "2025-01-28"]
    months = {
        "2025-03": _month_result("2025-03", [_observation(day) for day in march_days] + [_observation("2025-03-10"), _observation("2025-03-12")]),
        "2025-02": _month_result("2025-02", [_observation(day) for day in feb_days], unusable=[_unusable("2025-02-14"), _unusable("2025-02-18")]),
        "2025-01": _month_result("2025-01", [_observation(day) for day in jan_days]),
    }
    result, calls = _run(months, end=end, lookback=20)

    assert calls == ["2025-03", "2025-02", "2025-01"]
    assert result.status == "available"
    assert result.request_count == 3
    assert result.request_count <= 3
    assert result.unusable_observation_count == 2
    assert result.unusable_observations == (
        {"trade_date": "2025-02-14", "reason": "close_unavailable", "source_month": "2025-02"},
        {"trade_date": "2025-02-18", "reason": "close_unavailable", "source_month": "2025-02"},
    )
    assert result.post_end_rows_excluded == 2
    assert len(result.observations) == 20
    assert all(row["trade_date"] < end["trade_date"] for row in result.observations)
    assert _project(result, end, 20)["coverage_status"] == "complete"


def test_twenty_day_budget_exhaustion_is_insufficient_and_does_not_request_third_month() -> None:
    months = {
        "2025-03": _month_result("2025-03", [_observation(day) for day in ["2025-03-03", "2025-03-04", "2025-03-05"]]),
        "2025-02": _month_result("2025-02", [_observation(day) for day in ["2025-02-03", "2025-02-04", "2025-02-05", "2025-02-06"]]),
        "2025-01": _month_result("2025-01", [_observation("2025-01-03")]),
    }
    result, calls = _run(months, lookback=20, budget=2)

    assert result.status == "insufficient"
    assert calls == ["2025-03", "2025-02"]
    assert result.request_count == 2
    assert result.valid_lookback_count == 7
    assert result.missing_lookback_count == 13
    projected = _project(result, _end(), 20)
    assert projected["coverage_status"] == "insufficient"
    assert projected["baselines"][0]["status"] == "insufficient_coverage"


def test_zero_usable_closes_after_valid_months_is_unavailable_with_source_metadata() -> None:
    months = {
        "2025-03": _month_result("2025-03", unusable=[_unusable("2025-03-03"), _unusable("2025-03-04")]),
        "2025-02": _month_result("2025-02", unusable=[_unusable("2025-02-03")]),
        "2025-01": _month_result("2025-01"),
    }
    result, calls = _run(months, lookback=5, budget=2)

    assert result.status == "unavailable"
    assert calls == ["2025-03", "2025-02"]
    assert result.observations == ()
    assert result.unusable_observation_count == 3
    assert all(row["reason"] == "close_unavailable" and row["source_month"] for row in result.unusable_observations)
    assert _project(result, _end(), 5)["coverage_status"] == "unavailable"


def test_source_failure_on_second_month_stops_without_fetching_third_and_projects_truthfully() -> None:
    end = _end()
    months = {
        "2025-03": _month_result("2025-03", [_observation("2025-03-03"), _observation("2025-03-04")]),
        "2025-02": _month_result("2025-02", status="source_failed", error_code="http_status_unaccepted"),
        "2025-01": _month_result("2025-01", [_observation("2025-01-03")]),
    }
    result, calls = _run(months, end=end, lookback=5)

    assert result.status == "source_failed"
    assert calls == ["2025-03", "2025-02"]
    assert result.valid_lookback_count == 2
    projected = _project(result, end, 5, outcome="source_failed")
    assert projected["coverage_status"] == "source_failed"


def test_binding_failure_on_second_month_stops_immediately() -> None:
    months = {
        "2025-03": _month_result("2025-03", [_observation("2025-03-03")]),
        "2025-02": _month_result("2025-02", status="binding_failed", error_code="report_heading_target_or_month_mismatch"),
        "2025-01": _month_result("2025-01", [_observation("2025-01-03")]),
    }
    result, calls = _run(months, lookback=4)
    assert result.status == "binding_failed"
    assert calls == ["2025-03", "2025-02"]
    assert result.month_attempts[-1]["status"] == "binding_failed"


def test_year_boundary_walks_from_january_to_prior_december() -> None:
    end = _end("2025-01-03")
    months = {
        "2025-01": _month_result("2025-01", [_observation("2025-01-06")]),
        "2024-12": _month_result("2024-12", [_observation("2024-12-31")]),
    }
    result, calls = _run(months, end=end, lookback=1)
    assert result.status == "available"
    assert calls == ["2025-01", "2024-12"]
    assert [row["trade_date"] for row in result.observations] == ["2024-12-31"]


def test_conflicting_duplicate_date_in_collected_rows_fails_closed() -> None:
    duplicate_date = "2025-02-28"
    months = {
        "2025-03": _month_result("2025-03", [
            _observation("2025-03-03", close=20),
            _observation("2025-03-03", close=21),
        ]),
    }
    result, calls = _run(months, lookback=1)
    assert result.status == "source_failed"
    assert result.error_code == "conflicting_duplicate_trade_date"
    assert calls == ["2025-03"]


@pytest.mark.parametrize("lookback,budget", [(0, 1), (21, 1), (1, 0), (1, 4)])
def test_lookback_and_month_budget_are_hard_bounded_before_fetch(lookback: int, budget: int) -> None:
    calls: list[str] = []

    def fetch_month(**kwargs):
        calls.append(kwargs["requested_month"])
        raise AssertionError("must not call fetcher for invalid bounds")

    result = collect_twse_stock_day_lookback(
        target=TARGET,
        instrument_family="company_share",
        instrument_type="common_share",
        governed_end_observation=_end(),
        lookback_trading_days=lookback,
        retrieved_at=RETRIEVED,
        timeout_seconds=1,
        max_response_bytes=100,
        month_request_budget=budget,
        fetch_month=fetch_month,
    )
    assert result.status == "source_failed"
    assert calls == []


def test_governed_end_identity_or_shape_failure_prevents_source_calls() -> None:
    calls: list[str] = []

    def fetch_month(**kwargs):
        calls.append(kwargs["requested_month"])
        raise AssertionError("must not fetch with invalid end binding")

    end = _end()
    end["security_code"] = "2330"
    result = collect_twse_stock_day_lookback(
        target=TARGET,
        instrument_family="company_share",
        instrument_type="common_share",
        governed_end_observation=end,
        lookback_trading_days=1,
        retrieved_at=RETRIEVED,
        timeout_seconds=1,
        max_response_bytes=100,
        month_request_budget=1,
        fetch_month=fetch_month,
    )
    assert result.status == "binding_failed"
    assert result.error_code == "invalid_governed_end_observation"
    assert calls == []
