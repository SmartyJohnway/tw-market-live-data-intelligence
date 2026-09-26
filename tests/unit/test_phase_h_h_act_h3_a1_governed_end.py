from __future__ import annotations

from datetime import datetime, timezone

import pytest

from server.services.phase_h_h3_twse_stock_day_adapter import (
    SOURCE_CONTRACT_ID,
    SOURCE_FAMILY,
    TWSEStockDayResult,
)
from server.services.phase_h_h3_twse_governed_end import resolve_twse_governed_end
from server.services.phase_h_h3_twse_stock_day_walker import collect_twse_stock_day_lookback


TARGET = {"canonical_target_id": "TWSE:1423", "market": "TWSE", "security_code": "1423"}
STAMP = datetime(2025, 3, 10, 2, 0, tzinfo=timezone.utc)


def observation(day: str, *, retrieved_at: str = "2025-03-10T02:00:00Z") -> dict:
    return {
        **TARGET,
        "trade_date": day,
        "close": 36.65,
        "volume": 100,
        "source_family": SOURCE_FAMILY,
        "source_contract_id": SOURCE_CONTRACT_ID,
        "retrieved_at": retrieved_at,
        "citation_ids": [f"fixture:{day}"],
    }


def month_result(month: str, observations=(), status=None, error_code=None) -> TWSEStockDayResult:
    rows = tuple(observations)
    return TWSEStockDayResult(
        status=status or ("available" if rows else "no_evidence_in_covered_scope"),
        requested_month=month,
        retrieved_at="2025-03-10T02:00:00Z",
        observations=rows,
        error_code=error_code,
    )


def resolve(results, *, stamp=STAMP):
    calls = []

    def fetch_month(**kwargs):
        calls.append(kwargs["requested_month"])
        return results[kwargs["requested_month"]]

    value = resolve_twse_governed_end(
        target=TARGET,
        instrument_family="company_share",
        instrument_type="common_share",
        execution_timestamp=stamp,
        timeout_seconds=15,
        fetch_month=fetch_month,
    )
    return value, calls


def test_current_month_end_selection_excludes_future_row_and_binds_single_clock() -> None:
    result, calls = resolve({"2025-03": month_result("2025-03", [
        observation("2025-03-10"), observation("2025-03-11"),
    ])})
    assert result.status == "available"
    assert result.governed_end_observation["trade_date"] == "2025-03-10"
    assert result.governed_end_observation["close"] == 36.65
    assert result.requested_months == ("2025-03",)
    assert calls == ["2025-03"]
    assert result.network_request_count == 1
    assert result.walker_month_request_budget == 3
    assert result.retrieved_at == "2025-03-10T02:00:00Z"
    assert result.as_of_taipei_date == "2025-03-10"


def test_empty_current_month_uses_previous_month_for_end() -> None:
    result, calls = resolve({
        "2025-03": month_result("2025-03"),
        "2025-02": month_result("2025-02", [observation("2025-02-28")]),
    })
    assert result.status == "available"
    assert result.requested_months == ("2025-03", "2025-02")
    assert result.governed_end_observation["trade_date"] == "2025-02-28"
    assert result.walker_month_request_budget == 2
    assert calls == ["2025-03", "2025-02"]


def test_source_call_uses_fixed_verified_compatibility_bounds() -> None:
    captured = []

    def fetch_month(**kwargs):
        captured.append(kwargs)
        return month_result(kwargs["requested_month"], [observation("2025-03-10")])

    result = resolve_twse_governed_end(
        target=TARGET,
        instrument_family="company_share",
        instrument_type="common_share",
        execution_timestamp=STAMP,
        timeout_seconds=12.5,
        fetch_month=fetch_month,
    )
    assert result.status == "available"
    assert len(captured) == 1
    assert captured[0]["ssl_policy"] == "compatibility"
    assert captured[0]["timeout_seconds"] == 12.5
    assert captured[0]["max_response_bytes"] == 2 * 1024 * 1024
    assert captured[0]["retrieved_at"] == result.retrieved_at


@pytest.mark.parametrize("failure", ["source_failed", "binding_failed"])
def test_source_or_binding_failure_stops_without_older_month(failure: str) -> None:
    result, calls = resolve({"2025-03": month_result("2025-03", status=failure, error_code="fixture_failure")})
    assert result.status == failure
    assert result.requested_months == ("2025-03",)
    assert result.network_request_count == 1
    assert calls == ["2025-03"]


@pytest.mark.parametrize("failure", ["source_failed", "binding_failed"])
def test_second_month_failure_stops_before_third_month(failure: str) -> None:
    result, calls = resolve({
        "2025-03": month_result("2025-03"),
        "2025-02": month_result("2025-02", status=failure, error_code="fixture_failure"),
    })
    assert result.status == failure
    assert result.requested_months == ("2025-03", "2025-02")
    assert result.network_request_count == 2
    assert calls == ["2025-03", "2025-02"]


def test_three_successful_empty_months_are_unavailable() -> None:
    result, calls = resolve({month: month_result(month) for month in ("2025-03", "2025-02", "2025-01")})
    assert result.status == "unavailable"
    assert result.requested_months == ("2025-03", "2025-02", "2025-01")
    assert result.network_request_count == 3
    assert result.walker_month_request_budget == 1
    assert calls == ["2025-03", "2025-02", "2025-01"]


def test_taipei_date_controls_month_at_utc_boundary() -> None:
    stamp = datetime(2026, 9, 24, 16, 30, tzinfo=timezone.utc)
    result, calls = resolve({"2026-09": month_result("2026-09", [observation("2026-09-25")])}, stamp=stamp)
    assert result.as_of_taipei_date == "2026-09-25"
    assert result.retrieved_at == "2026-09-24T16:30:00Z"
    assert result.requested_months == ("2026-09",)
    assert calls == ["2026-09"]


def test_month_walk_rolls_back_across_year_boundary() -> None:
    stamp = datetime(2025, 1, 15, 2, 0, tzinfo=timezone.utc)
    result, calls = resolve({
        "2025-01": month_result("2025-01"),
        "2024-12": month_result("2024-12", [observation("2024-12-31", retrieved_at="2025-01-15T02:00:00Z")]),
    }, stamp=stamp)
    assert result.status == "available"
    assert result.requested_months == ("2025-01", "2024-12")
    assert result.governed_end_observation["trade_date"] == "2024-12-31"
    assert calls == ["2025-01", "2024-12"]


def test_invalid_target_and_naive_timestamp_fail_before_fetch() -> None:
    calls = []

    def fetch_month(**kwargs):
        calls.append(kwargs)
        return month_result(kwargs["requested_month"])

    wrong = resolve_twse_governed_end(
        target={**TARGET, "canonical_target_id": "TPEX:1423"},
        instrument_family="company_share", instrument_type="common_share",
        execution_timestamp=STAMP, timeout_seconds=15, fetch_month=fetch_month,
    )
    naive = resolve_twse_governed_end(
        target=TARGET, instrument_family="company_share", instrument_type="common_share",
        execution_timestamp=datetime(2025, 3, 10), timeout_seconds=15, fetch_month=fetch_month,
    )
    assert wrong.status == "binding_failed"
    assert naive.status == "source_failed"
    assert calls == []


@pytest.mark.parametrize(
    ("months", "end_month", "budget"),
    [
        (("2025-03",), "2025-03", 3),
        (("2025-03", "2025-02"), "2025-02", 2),
        (("2025-03", "2025-02", "2025-01"), "2025-01", 1),
    ],
)
def test_resolver_results_are_reused_by_walker_with_shared_three_month_budget(months, end_month, budget) -> None:
    source_rows = {}
    for month in months:
        source_rows[month] = month_result(month)
    # Earlier attempted months are empty; the last attempted month supplies
    # both the caller-governed end and one distinct prior completed close.
    end_day = {"2025-03": "2025-03-10", "2025-02": "2025-02-28", "2025-01": "2025-01-31"}[end_month]
    prior_day = {"2025-03": "2025-03-07", "2025-02": "2025-02-27", "2025-01": "2025-01-30"}[end_month]
    source_rows[end_month] = month_result(end_month, [observation(prior_day), observation(end_day)])

    resolution, resolver_calls = resolve(source_rows)
    assert resolution.status == "available"
    assert resolution.requested_months == months
    assert resolution.walker_month_request_budget == budget

    result_cache = {item.requested_month: item for item in resolution.month_results}
    network_calls = list(resolver_calls)

    def bounded_fetch_month(**kwargs):
        requested = kwargs["requested_month"]
        if requested in result_cache:
            return result_cache[requested]
        network_calls.append(requested)
        return month_result(requested)

    walk = collect_twse_stock_day_lookback(
        target=TARGET,
        instrument_family="company_share",
        instrument_type="common_share",
        governed_end_observation=resolution.governed_end_observation,
        lookback_trading_days=1,
        retrieved_at=resolution.retrieved_at,
        timeout_seconds=15,
        max_response_bytes=2 * 1024 * 1024,
        month_request_budget=budget,
        fetch_month=bounded_fetch_month,
    )
    assert walk.status == "available"
    assert len(network_calls) <= 3
    assert len(network_calls) == len(set(network_calls))
    assert walk.observations[0]["trade_date"] == prior_day


def test_malformed_month_result_fails_closed() -> None:
    class WrongMonth:
        requested_month = "2025-02"
        status = "available"

    result, calls = resolve({"2025-03": WrongMonth()})
    assert result.status == "source_failed"
    assert result.error_code == "invalid_month_result"
    assert calls == ["2025-03"]
