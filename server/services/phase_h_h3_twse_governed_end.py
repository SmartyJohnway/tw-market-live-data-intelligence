"""Select a bounded, official TWSE completed-session end observation.

This dormant resolver captures no clock itself. The caller supplies one
timezone-aware execution timestamp; fetched monthly results are retained only
in the returned in-process value for reuse by the bounded walker.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import math
from typing import Any, Callable, Literal, Mapping
from zoneinfo import ZoneInfo

from server.services.phase_h_h3_twse_stock_day_adapter import (
    SOURCE_CONTRACT_ID,
    SOURCE_FAMILY,
    TWSEStockDayResult,
    fetch_twse_stock_day_month,
)


MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_MONTH_REQUESTS = 3
_TAIPEI = ZoneInfo("Asia/Taipei")
_IDENTITY_FIELDS = ("canonical_target_id", "market", "security_code")
MonthFetcher = Callable[..., TWSEStockDayResult]


@dataclass(frozen=True)
class TWSEGovernedEndResolution:
    status: Literal["available", "unavailable", "source_failed", "binding_failed"]
    governed_end_observation: dict[str, Any] | None
    retrieved_at: str
    as_of_taipei_date: str
    requested_months: tuple[str, ...]
    network_request_count: int
    month_results: tuple[TWSEStockDayResult, ...]
    walker_month_request_budget: int
    stop_reason: str
    error_code: str | None = None


def _previous_month(value: str) -> str:
    year, month = (int(part) for part in value.split("-"))
    return f"{year - 1:04d}-12" if month == 1 else f"{year:04d}-{month - 1:02d}"


def _target_identity(target: Any, instrument_family: Any, instrument_type: Any) -> tuple[str, str, str] | None:
    if not isinstance(target, Mapping) or set(target) != set(_IDENTITY_FIELDS):
        return None
    identity = tuple(target.get(key) for key in _IDENTITY_FIELDS)
    canonical, market, code = identity
    if (
        not all(isinstance(item, str) and item.strip() for item in identity)
        or market != "TWSE"
        or canonical != f"TWSE:{code}"
        or not (code.isascii() and code.isdigit() and 1 <= len(code) <= 6)
        or instrument_family != "company_share"
        or instrument_type != "common_share"
    ):
        return None
    return canonical, market, code


def _observation_is_valid(
    value: Any, identity: tuple[str, str, str], as_of: date, month: str, retrieved_at: str
) -> bool:
    if not isinstance(value, Mapping) or tuple(value.get(key) for key in _IDENTITY_FIELDS) != identity:
        return False
    if (
        value.get("source_family") != SOURCE_FAMILY
        or value.get("source_contract_id") != SOURCE_CONTRACT_ID
    ):
        return False
    trade_date = value.get("trade_date")
    try:
        parsed_date = date.fromisoformat(trade_date) if isinstance(trade_date, str) else None
    except ValueError:
        return False
    if parsed_date is None or parsed_date.isoformat() != trade_date or trade_date[:7] != month:
        return False
    close = value.get("close")
    if isinstance(close, bool) or not isinstance(close, (int, float)):
        return False
    if not math.isfinite(close) or close < 0:
        return False
    volume = value.get("volume")
    if volume is not None and (isinstance(volume, bool) or not isinstance(volume, int) or volume < 0):
        return False
    retrieved = value.get("retrieved_at")
    if not isinstance(retrieved, str):
        return False
    try:
        timestamp = datetime.fromisoformat(retrieved.replace("Z", "+00:00"))
    except ValueError:
        return False
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return False
    if retrieved != retrieved_at:
        return False
    citations = value.get("citation_ids")
    return (
        isinstance(citations, list)
        and bool(citations)
        and all(isinstance(item, str) and item.strip() for item in citations)
        and len(set(citations)) == len(citations)
    )


def resolve_twse_governed_end(
    *,
    target: Mapping[str, str],
    instrument_family: str,
    instrument_type: str,
    execution_timestamp: datetime,
    timeout_seconds: float,
    fetch_month: MonthFetcher | None = None,
) -> TWSEGovernedEndResolution:
    """Resolve the latest valid monthly close not later than Taipei as-of date.

    ``execution_timestamp`` is the sole time input. Each attempted month is
    fetched at most once, with the accepted verified-TLS compatibility policy.
    """
    identity = _target_identity(target, instrument_family, instrument_type)
    if identity is None:
        return TWSEGovernedEndResolution(
            "binding_failed", None, "", "", (), 0, (), 3, "target_binding_failed", "invalid_target_binding"
        )
    if (
        not isinstance(execution_timestamp, datetime)
        or execution_timestamp.tzinfo is None
        or execution_timestamp.utcoffset() is None
    ):
        return TWSEGovernedEndResolution(
            "source_failed", None, "", "", (), 0, (), 3, "invalid_execution_timestamp", "timezone_aware_timestamp_required"
        )
    try:
        timeout_is_finite = math.isfinite(timeout_seconds)
    except (OverflowError, TypeError):
        timeout_is_finite = False
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not timeout_is_finite
        or timeout_seconds <= 0
    ):
        return TWSEGovernedEndResolution(
            "source_failed", None, "", "", (), 0, (), 3, "invalid_timeout", "invalid_timeout"
        )
    utc_stamp = execution_timestamp.astimezone(timezone.utc)
    retrieved_at = utc_stamp.isoformat(timespec="seconds").replace("+00:00", "Z")
    as_of = execution_timestamp.astimezone(_TAIPEI).date()
    as_of_text = as_of.isoformat()
    month = as_of_text[:7]
    fetcher = fetch_month or fetch_twse_stock_day_month
    months: list[str] = []
    results: list[TWSEStockDayResult] = []

    def finish(
        status: Literal["available", "unavailable", "source_failed", "binding_failed"],
        end: dict[str, Any] | None,
        reason: str,
        error: str | None = None,
    ) -> TWSEGovernedEndResolution:
        count = len(months)
        return TWSEGovernedEndResolution(
            status=status,
            governed_end_observation=end,
            retrieved_at=retrieved_at,
            as_of_taipei_date=as_of_text,
            requested_months=tuple(months),
            network_request_count=count,
            month_results=tuple(results),
            walker_month_request_budget=4 - count,
            stop_reason=reason,
            error_code=error,
        )

    for _ in range(MAX_MONTH_REQUESTS):
        months.append(month)
        try:
            result = fetcher(
                target=dict(target),
                instrument_family=instrument_family,
                instrument_type=instrument_type,
                requested_month=month,
                retrieved_at=retrieved_at,
                timeout_seconds=timeout_seconds,
                max_response_bytes=MAX_RESPONSE_BYTES,
                ssl_policy="compatibility",
            )
        except Exception:
            return finish("source_failed", None, "month_source_exception", "month_fetch_failed")
        if not isinstance(result, TWSEStockDayResult) or result.requested_month != month:
            return finish("source_failed", None, "month_result_contract_invalid", "invalid_month_result")
        results.append(result)
        if result.status == "source_failed":
            return finish("source_failed", None, "month_source_failed", result.error_code or "month_source_failed")
        if result.status == "binding_failed":
            return finish("binding_failed", None, "month_binding_failed", result.error_code or "month_binding_failed")
        if result.status not in {"available", "no_evidence_in_covered_scope"}:
            return finish("source_failed", None, "month_result_status_invalid", "invalid_month_status")
        if not isinstance(result.observations, tuple):
            return finish("source_failed", None, "month_observations_invalid", "invalid_observations")
        if (result.status == "available") != bool(result.observations):
            return finish("source_failed", None, "month_result_status_inconsistent", "inconsistent_month_result")
        candidates = []
        for observation in result.observations:
            if not _observation_is_valid(observation, identity, as_of, month, retrieved_at):
                return finish("binding_failed", None, "month_observation_binding_invalid", "invalid_end_candidate")
            if date.fromisoformat(observation["trade_date"]) <= as_of:
                candidates.append(observation)
        if candidates:
            selected = max(candidates, key=lambda item: item["trade_date"])
            return finish("available", dict(selected), "latest_valid_close_in_first_available_month")
        month = _previous_month(month)
    return finish("unavailable", None, "no_governed_end_within_three_month_budget")
