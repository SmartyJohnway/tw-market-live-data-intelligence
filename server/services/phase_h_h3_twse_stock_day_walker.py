"""Dormant, bounded month walker for prior TWSE STOCK_DAY observations.

The caller supplies the governed end observation. This module only collects
up to N valid observations strictly before that end, with at most three
single-month adapter calls. It does not read a clock, persist history, or
choose a current/end price.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import math
from typing import Any, Callable, Literal, Mapping

from server.services.phase_h_h3_twse_stock_day_adapter import (
    SOURCE_CONTRACT_ID,
    SOURCE_FAMILY,
    TWSEStockDayResult,
    fetch_twse_stock_day_month,
)


_IDENTITY_FIELDS = ("canonical_target_id", "market", "security_code")
_OBSERVATION_FIELDS = frozenset({
    *_IDENTITY_FIELDS,
    "trade_date",
    "close",
    "volume",
    "source_family",
    "source_contract_id",
    "retrieved_at",
    "citation_ids",
})


@dataclass(frozen=True)
class TWSEStockDayWalkResult:
    """Bounded metadata and the selected prior observations; never raw HTML."""

    status: Literal["available", "insufficient", "unavailable", "source_failed", "binding_failed"]
    requested_months: tuple[str, ...] = ()
    request_count: int = 0
    month_attempts: tuple[dict[str, Any], ...] = ()
    observations: tuple[dict[str, Any], ...] = ()
    unusable_observation_count: int = 0
    unusable_observations: tuple[dict[str, str], ...] = ()
    post_end_rows_excluded: int = 0
    requested_lookback: int = 0
    valid_lookback_count: int = 0
    missing_lookback_count: int = 0
    stop_reason: str = "invalid_input"
    error_code: str | None = None


MonthFetcher = Callable[..., TWSEStockDayResult]


def _result(status: str, lookback: int, *, error_code: str | None = None) -> TWSEStockDayWalkResult:
    return TWSEStockDayWalkResult(
        status=status,  # type: ignore[arg-type]
        requested_lookback=lookback if isinstance(lookback, int) and not isinstance(lookback, bool) else 0,
        missing_lookback_count=lookback if isinstance(lookback, int) and not isinstance(lookback, bool) else 0,
        stop_reason="invalid_input",
        error_code=error_code,
    )


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return stamp.tzinfo is not None and stamp.utcoffset() is not None


def _identity(target: Any, instrument_family: Any, instrument_type: Any) -> tuple[str, str, str] | None:
    if not isinstance(target, Mapping) or set(target) != set(_IDENTITY_FIELDS):
        return None
    parts = tuple(target.get(field) for field in _IDENTITY_FIELDS)
    if not all(isinstance(part, str) and part.strip() for part in parts):
        return None
    canonical, market, code = parts
    if (
        market != "TWSE"
        or canonical != f"TWSE:{code}"
        or not (code.isascii() and code.isdigit() and 1 <= len(code) <= 6)
        or instrument_family != "company_share"
        or instrument_type != "common_share"
    ):
        return None
    return canonical, market, code


def _valid_observation(value: Any, identity: tuple[str, str, str], *, fetched: bool) -> bool:
    if not isinstance(value, Mapping) or set(value) != _OBSERVATION_FIELDS:
        return False
    if tuple(value.get(field) for field in _IDENTITY_FIELDS) != identity:
        return False
    trade_date = value.get("trade_date")
    if not isinstance(trade_date, str):
        return False
    try:
        parsed_date = date.fromisoformat(trade_date)
    except ValueError:
        return False
    if parsed_date.isoformat() != trade_date:
        return False
    close = value.get("close")
    if isinstance(close, bool) or not isinstance(close, (int, float)):
        return False
    try:
        if not math.isfinite(close) or close < 0:
            return False
    except (OverflowError, TypeError):
        return False
    volume = value.get("volume")
    if volume is not None and (isinstance(volume, bool) or not isinstance(volume, int) or volume < 0):
        return False
    for field in ("source_family", "source_contract_id"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            return False
    if fetched and (
        value.get("source_family") != SOURCE_FAMILY
        or value.get("source_contract_id") != SOURCE_CONTRACT_ID
    ):
        return False
    if not _valid_timestamp(value.get("retrieved_at")):
        return False
    citations = value.get("citation_ids")
    if (
        not isinstance(citations, list)
        or not citations
        or any(not isinstance(item, str) or not item.strip() for item in citations)
        or len(set(citations)) != len(citations)
    ):
        return False
    return True


def _previous_month(month: str) -> str:
    year, number = (int(part) for part in month.split("-"))
    if number == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{number - 1:02d}"


def _get(result: Any, name: str, default: Any = None) -> Any:
    if isinstance(result, Mapping):
        return result.get(name, default)
    return getattr(result, name, default)


def collect_twse_stock_day_lookback(
    *,
    target: Mapping[str, str],
    instrument_family: str,
    instrument_type: str,
    governed_end_observation: Mapping[str, Any],
    lookback_trading_days: int,
    retrieved_at: str,
    timeout_seconds: float,
    max_response_bytes: int,
    month_request_budget: int,
    fetch_month: MonthFetcher | None = None,
) -> TWSEStockDayWalkResult:
    """Collect the N most recent valid prior closes with a hard three-month cap.

    ``fetch_month`` defaults to the accepted one-month adapter for explicit
    callers. Bounds, end observation, and retrieval timestamp have no defaults.
    """
    requested = lookback_trading_days if isinstance(lookback_trading_days, int) and not isinstance(lookback_trading_days, bool) else 0
    identity = _identity(target, instrument_family, instrument_type)
    if identity is None:
        return _result("binding_failed", requested, error_code="invalid_target_binding")
    if (
        not isinstance(lookback_trading_days, int)
        or isinstance(lookback_trading_days, bool)
        or not 1 <= lookback_trading_days <= 20
    ):
        return _result("source_failed", requested, error_code="invalid_lookback")
    if (
        not isinstance(month_request_budget, int)
        or isinstance(month_request_budget, bool)
        or not 1 <= month_request_budget <= 3
    ):
        return _result("source_failed", requested, error_code="invalid_month_request_budget")
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
        return _result("source_failed", requested, error_code="invalid_timeout")
    if isinstance(max_response_bytes, bool) or not isinstance(max_response_bytes, int) or max_response_bytes <= 0:
        return _result("source_failed", requested, error_code="invalid_response_limit")
    if not _valid_timestamp(retrieved_at):
        return _result("source_failed", requested, error_code="invalid_retrieved_at")
    if not _valid_observation(governed_end_observation, identity, fetched=False):
        return _result("binding_failed", requested, error_code="invalid_governed_end_observation")

    end_date = governed_end_observation["trade_date"]
    month = end_date[:7]
    month_fetcher = fetch_month or fetch_twse_stock_day_month
    by_date: dict[str, dict[str, Any]] = {}
    unusable_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    attempts: list[dict[str, Any]] = []
    requested_months: list[str] = []
    post_end_excluded = 0

    def finish(status: str, reason: str, *, error_code: str | None = None) -> TWSEStockDayWalkResult:
        chosen = [by_date[key] for key in sorted(by_date)[-lookback_trading_days:]]
        return TWSEStockDayWalkResult(
            status=status,  # type: ignore[arg-type]
            requested_months=tuple(requested_months),
            request_count=len(requested_months),
            month_attempts=tuple(attempts),
            observations=tuple(chosen),
            unusable_observation_count=len(unusable_by_key),
            unusable_observations=tuple(unusable_by_key[key] for key in sorted(unusable_by_key)),
            post_end_rows_excluded=post_end_excluded,
            requested_lookback=lookback_trading_days,
            valid_lookback_count=len(chosen),
            missing_lookback_count=lookback_trading_days - len(chosen),
            stop_reason=reason,
            error_code=error_code,
        )

    while len(requested_months) < month_request_budget:
        requested_months.append(month)
        try:
            source_result = month_fetcher(
                target=dict(target),
                instrument_family=instrument_family,
                instrument_type=instrument_type,
                requested_month=month,
                retrieved_at=retrieved_at,
                timeout_seconds=timeout_seconds,
                max_response_bytes=max_response_bytes,
            )
        except Exception:
            attempts.append({
                "month": month,
                "status": "source_failed",
                "http_status": None,
                "response_byte_count": 0,
                "response_sha256": None,
                "usable_observation_count": 0,
                "unusable_observation_count": 0,
                "error_code": "month_fetch_failed",
            })
            return finish("source_failed", "month_source_failed", error_code="month_fetch_failed")

        source_status = _get(source_result, "status")
        source_month = _get(source_result, "requested_month")
        source_observations = _get(source_result, "observations", ())
        source_unusable = _get(source_result, "unusable_observations", ())
        source_unusable_count = _get(source_result, "unusable_observation_count", 0)
        if (
            source_status not in {"available", "no_evidence_in_covered_scope", "source_failed", "binding_failed"}
            or source_month != month
            or not isinstance(source_observations, (tuple, list))
            or not isinstance(source_unusable, (tuple, list))
            or isinstance(source_unusable_count, bool)
            or not isinstance(source_unusable_count, int)
            or source_unusable_count != len(source_unusable)
        ):
            attempts.append({
                "month": month,
                "status": "source_failed",
                "http_status": _get(source_result, "http_status"),
                "response_byte_count": _get(source_result, "response_byte_count", 0),
                "response_sha256": _get(source_result, "response_sha256"),
                "usable_observation_count": 0,
                "unusable_observation_count": 0,
                "error_code": "invalid_month_result",
            })
            return finish("source_failed", "invalid_month_result", error_code="invalid_month_result")

        attempt = {
            "month": month,
            "status": source_status,
            "http_status": _get(source_result, "http_status"),
            "response_byte_count": _get(source_result, "response_byte_count", 0),
            "response_sha256": _get(source_result, "response_sha256"),
            "usable_observation_count": len(source_observations),
            "unusable_observation_count": source_unusable_count,
        }
        source_error = _get(source_result, "error_code")
        if source_error is not None:
            attempt["error_code"] = source_error
        attempts.append(attempt)

        if source_status in {"source_failed", "binding_failed"}:
            return finish(source_status, f"month_{source_status}", error_code=source_error)
        if source_status == "no_evidence_in_covered_scope" and source_observations:
            attempts[-1] = {**attempts[-1], "status": "source_failed", "error_code": "invalid_empty_month_result"}
            return finish("source_failed", "invalid_empty_month_result", error_code="invalid_empty_month_result")
        if source_status == "available" and not source_observations:
            attempts[-1] = {**attempts[-1], "status": "source_failed", "error_code": "invalid_available_month_result"}
            return finish("source_failed", "invalid_available_month_result", error_code="invalid_available_month_result")

        month_unusable_seen: set[tuple[str, str]] = set()
        for source_observation in source_observations:
            if not _valid_observation(source_observation, identity, fetched=True):
                target_match = (
                    isinstance(source_observation, Mapping)
                    and tuple(source_observation.get(field) for field in _IDENTITY_FIELDS) == identity
                )
                code = "invalid_month_observation" if target_match else "month_observation_binding_mismatch"
                failure_status = "source_failed" if target_match else "binding_failed"
                attempts[-1] = {**attempts[-1], "status": failure_status, "error_code": code}
                return finish(failure_status, f"month_{failure_status}", error_code=code)
            row = dict(source_observation)
            trade_date = row["trade_date"]
            if trade_date[:7] != month:
                attempts[-1] = {**attempts[-1], "status": "source_failed", "error_code": "month_row_date_mismatch"}
                return finish("source_failed", "month_source_failed", error_code="month_row_date_mismatch")
            if trade_date >= end_date:
                post_end_excluded += 1
                continue
            previous = by_date.get(trade_date)
            if previous is not None and previous != row:
                attempts[-1] = {**attempts[-1], "status": "source_failed", "error_code": "conflicting_duplicate_trade_date"}
                return finish("source_failed", "duplicate_observation_conflict", error_code="conflicting_duplicate_trade_date")
            by_date.setdefault(trade_date, row)

        for unusable in source_unusable:
            if (
                not isinstance(unusable, Mapping)
                or set(unusable) != {"trade_date", "reason"}
                or unusable.get("reason") != "close_unavailable"
                or not isinstance(unusable.get("trade_date"), str)
            ):
                attempts[-1] = {**attempts[-1], "status": "source_failed", "error_code": "invalid_unusable_observation_metadata"}
                return finish("source_failed", "month_source_failed", error_code="invalid_unusable_observation_metadata")
            try:
                unusable_date = date.fromisoformat(unusable["trade_date"])
            except ValueError:
                attempts[-1] = {**attempts[-1], "status": "source_failed", "error_code": "invalid_unusable_observation_date"}
                return finish("source_failed", "month_source_failed", error_code="invalid_unusable_observation_date")
            if unusable_date.isoformat() != unusable["trade_date"] or unusable["trade_date"][:7] != month:
                attempts[-1] = {**attempts[-1], "status": "source_failed", "error_code": "invalid_unusable_observation_date"}
                return finish("source_failed", "month_source_failed", error_code="invalid_unusable_observation_date")
            unusable_key = (unusable["trade_date"], unusable["reason"])
            if unusable_key in month_unusable_seen:
                attempts[-1] = {**attempts[-1], "status": "source_failed", "error_code": "duplicate_unusable_observation"}
                return finish("source_failed", "month_source_failed", error_code="duplicate_unusable_observation")
            month_unusable_seen.add(unusable_key)
            if unusable["trade_date"] >= end_date:
                post_end_excluded += 1
                continue
            if unusable["trade_date"] in by_date:
                attempts[-1] = {**attempts[-1], "status": "source_failed", "error_code": "conflicting_duplicate_trade_date"}
                return finish("source_failed", "duplicate_observation_conflict", error_code="conflicting_duplicate_trade_date")
            metadata_key = (unusable["trade_date"], unusable["reason"], month)
            unusable_by_key.setdefault(metadata_key, {
                "trade_date": unusable["trade_date"],
                "reason": unusable["reason"],
                "source_month": month,
            })
        if len(month_unusable_seen) != len(source_unusable):
            attempts[-1] = {**attempts[-1], "status": "source_failed", "error_code": "duplicate_unusable_observation"}
            return finish("source_failed", "month_source_failed", error_code="duplicate_unusable_observation")

        if len(by_date) >= lookback_trading_days:
            return finish("available", "lookback_satisfied")
        month = _previous_month(month)

    if by_date:
        return finish("insufficient", "month_budget_exhausted_insufficient")
    return finish("unavailable", "month_budget_exhausted_unavailable")
