"""Pure deterministic derivation of governed Phase H H3 evidence.

This module performs no file, network, clock, or runtime-authority access.
Callers supply the frozen schema and every evidence record explicitly.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from math import isfinite
from typing import Any

from jsonschema import Draft7Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from scripts.validate_phase_h_v3_contracts import validate_recent_performance_semantics


class H3DerivationError(ValueError):
    """Fail-closed deterministic error for invalid H3 source evidence."""


_OBSERVATION_FIELDS = frozenset({
    "canonical_target_id", "market", "security_code", "trade_date", "close", "volume",
    "source_family", "source_contract_id", "retrieved_at", "citation_ids",
})
_IDENTITY_FIELDS = ("canonical_target_id", "market", "security_code")
_PRESERVED_FAILURE_STATES = {"source_failed", "binding_failed", "unsupported", "not_applicable"}


def _fail(code: str) -> None:
    raise H3DerivationError(code)


def _date(value: Any, code: str) -> str:
    if not isinstance(value, str):
        _fail(code)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise H3DerivationError(code) from exc
    if parsed.isoformat() != value:
        _fail(code)
    return value


def _timestamp(value: Any) -> str:
    if not isinstance(value, str):
        _fail("invalid_retrieved_at")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise H3DerivationError("invalid_retrieved_at") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail("retrieved_at_timezone_required")
    return value


def _citations(value: Any, code: str) -> list[str]:
    if not isinstance(value, list) or not value:
        _fail(code)
    if any(not isinstance(item, str) or not item.strip() for item in value):
        _fail(code)
    if len(set(value)) != len(value):
        _fail(code)
    return sorted(value)


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return isfinite(value)
    except OverflowError:
        return False


def _normalize_record(value: Any, identity: tuple[str, str, str], *, code: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _OBSERVATION_FIELDS:
        _fail(code)
    record = dict(value)
    if tuple(record.get(field) for field in _IDENTITY_FIELDS) != identity:
        _fail("target_identity_mismatch")
    if not isinstance(record["market"], str) or record["market"] not in {"TWSE", "TPEX"}:
        _fail("target_identity_invalid")
    record["trade_date"] = _date(record["trade_date"], "invalid_trade_date")
    close = record["close"]
    if not _finite_number(close) or close < 0:
        _fail("invalid_close")
    volume = record["volume"]
    if volume is not None and (isinstance(volume, bool) or not isinstance(volume, int) or volume < 0):
        _fail("invalid_volume")
    for field in ("source_family", "source_contract_id"):
        if not isinstance(record[field], str) or not record[field].strip():
            _fail("invalid_source_provenance")
    record["retrieved_at"] = _timestamp(record["retrieved_at"])
    record["citation_ids"] = _citations(record["citation_ids"], "invalid_citation_ids")
    return record


def _same_semantic_record(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return all(left[field] == right[field] for field in _OBSERVATION_FIELDS)


def _normalize_average(
    value: Any,
    identity: tuple[str, str, str],
) -> tuple[float | int | None, list[str]]:
    """Accept an already-governed aggregate; this core does not choose its window."""
    if value is None:
        return None, []
    if not isinstance(value, Mapping) or set(value) != {
        "target", "historical_average_basis", "value", "source_family",
        "source_contract_id", "retrieved_at", "citation_ids",
    }:
        _fail("invalid_historical_average_evidence")
    target = value["target"]
    if not isinstance(target, Mapping) or set(target) != set(_IDENTITY_FIELDS):
        _fail("historical_average_target_mismatch")
    if tuple(target.get(field) for field in _IDENTITY_FIELDS) != identity:
        _fail("historical_average_target_mismatch")
    if value["historical_average_basis"] != "completed_official_sessions":
        _fail("invalid_historical_average_basis")
    amount = value["value"]
    if not _finite_number(amount) or amount < 0:
        _fail("invalid_historical_average_volume")
    for field in ("source_family", "source_contract_id"):
        if not isinstance(value[field], str) or not value[field].strip():
            _fail("invalid_historical_average_provenance")
    _timestamp(value["retrieved_at"])
    return amount, _citations(value["citation_ids"], "invalid_historical_average_citations")


def build_recent_performance_evidence(
    *,
    target: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]],
    governed_end_observation: Mapping[str, Any] | None,
    requested_observations: int,
    baseline_lookbacks: Sequence[int],
    current_volume_basis: str,
    schema: Mapping[str, Any],
    historical_average_evidence: Mapping[str, Any] | None = None,
    governed_outcome: str | None = None,
    caveats: Sequence[str] = (),
) -> dict[str, Any]:
    """Build one schema and semantic-valid H3 artifact from explicit inputs.

    ``historical_average_evidence`` is an already-governed aggregate with its
    source provenance. Its averaging window is selected by the caller under a
    separate authority; this function does not invent or select a window.
    """
    if not isinstance(target, Mapping) or set(target) != set(_IDENTITY_FIELDS):
        _fail("target_identity_invalid")
    identity = tuple(target.get(field) for field in _IDENTITY_FIELDS)
    if not all(isinstance(part, str) and part.strip() for part in identity) or identity[1] not in {"TWSE", "TPEX"}:
        _fail("target_identity_invalid")
    target_value = dict(zip(_IDENTITY_FIELDS, identity))
    if isinstance(requested_observations, bool) or not isinstance(requested_observations, int) or not 1 <= requested_observations <= 20:
        _fail("invalid_requested_observations")
    if not isinstance(baseline_lookbacks, Sequence) or isinstance(baseline_lookbacks, (str, bytes)) or not baseline_lookbacks:
        _fail("baseline_lookbacks_required")
    if any(isinstance(item, bool) or not isinstance(item, int) or not 1 <= item <= requested_observations for item in baseline_lookbacks):
        _fail("invalid_baseline_lookback")
    if len(set(baseline_lookbacks)) != len(baseline_lookbacks):
        _fail("duplicate_baseline_lookback")
    if requested_observations not in baseline_lookbacks:
        _fail("requested_baseline_missing")
    if not isinstance(current_volume_basis, str) or current_volume_basis not in {"intraday_cumulative", "completed_session"}:
        _fail("invalid_current_volume_basis")
    if governed_outcome is not None and (not isinstance(governed_outcome, str) or governed_outcome not in _PRESERVED_FAILURE_STATES):
        _fail("invalid_governed_outcome")
    if not isinstance(caveats, Sequence) or isinstance(caveats, (str, bytes)) or any(not isinstance(item, str) for item in caveats):
        _fail("invalid_caveats")
    if governed_outcome in {"source_failed", "binding_failed"} and not caveats:
        _fail("failure_provenance_required")
    if not isinstance(schema, Mapping):
        _fail("schema_input_invalid")
    if not isinstance(observations, Sequence) or isinstance(observations, (str, bytes)):
        _fail("observations_must_be_a_sequence")

    by_date: dict[str, dict[str, Any]] = {}
    for source_record in observations:
        row = _normalize_record(source_record, identity, code="invalid_observation")
        existing = by_date.get(row["trade_date"])
        if existing is not None and not _same_semantic_record(existing, row):
            _fail("conflicting_duplicate_trade_date")
        by_date.setdefault(row["trade_date"], row)
    ordered = [by_date[key] for key in sorted(by_date)]

    end = None
    if governed_end_observation is not None:
        end = _normalize_record(governed_end_observation, identity, code="invalid_governed_end_observation")
        if end["trade_date"] in by_date:
            _fail("governed_end_must_be_separate")
    retained = ordered[-requested_observations:]
    if end is not None and retained and end["trade_date"] <= retained[-1]["trade_date"]:
        _fail("governed_end_chronology_invalid")

    historical_average, average_citations = _normalize_average(historical_average_evidence, identity)
    if current_volume_basis == "intraday_cumulative":
        comparison_alignment = "partial_session_vs_completed_sessions"
    elif historical_average is not None:
        comparison_alignment = "aligned"
    else:
        comparison_alignment = "unavailable"

    actual_close_count = len(retained) + (1 if end is not None else 0)
    baselines: list[dict[str, Any]] = []
    for lookback in sorted(baseline_lookbacks):
        required = lookback + 1
        can_calculate = governed_outcome is None and end is not None and len(retained) >= lookback
        if can_calculate:
            start = retained[-lookback]
            if start["close"] == 0:
                _fail("baseline_start_close_invalid")
            amount = (end["close"] - start["close"]) / abs(start["close"]) * 100
            if not _finite_number(amount):
                _fail("invalid_derived_return")
            baseline = {
                "lookback_trading_days": lookback,
                "status": "available",
                "start_observation_date": start["trade_date"],
                "end_observation_date": end["trade_date"],
                "required_distinct_close_count": required,
                "actual_distinct_close_count": required,
                "recent_return_pct": amount,
                "return_basis": "raw_unadjusted_close_to_close",
            }
        else:
            baseline_status = "unsupported" if governed_outcome == "unsupported" else (
                "unavailable" if governed_outcome is not None or not retained else "insufficient_coverage"
            )
            baseline = {
                "lookback_trading_days": lookback,
                "status": baseline_status,
                "start_observation_date": None,
                "end_observation_date": end["trade_date"] if end else None,
                "required_distinct_close_count": required,
                "actual_distinct_close_count": min(actual_close_count, required),
                "recent_return_pct": None,
                "return_basis": "raw_unadjusted_close_to_close",
            }
        baselines.append(baseline)

    available = sorted(item["lookback_trading_days"] for item in baselines if item["status"] == "available")
    unavailable = sorted(item["lookback_trading_days"] for item in baselines if item["status"] != "available")
    valid_count = len(retained)
    missing_count = requested_observations - valid_count
    if governed_outcome is not None:
        coverage_status = governed_outcome
    elif not retained:
        coverage_status = "unavailable"
    elif available and (missing_count or unavailable):
        coverage_status = "partial"
    elif available:
        coverage_status = "complete"
    else:
        coverage_status = "insufficient"

    range_closes = [row["close"] for row in retained]
    if end is not None:
        range_closes.append(end["close"])
    recent_range = None if not range_closes else {
        "range_basis": "completed_session_closing_price",
        "recent_close_high": max(range_closes),
        "recent_close_low": min(range_closes),
    }
    citations = sorted({
        citation
        for row in [*retained, *([end] if end else [])]
        for citation in row["citation_ids"]
    } | set(average_citations))
    result = {
        "schema_version": "recent_performance_evidence.v1",
        "target": target_value,
        "coverage_status": coverage_status,
        "requested_observations": requested_observations,
        "valid_observation_count": valid_count,
        "missing_observation_count": missing_count,
        "first_observation_date": retained[0]["trade_date"] if retained else None,
        "last_observation_date": retained[-1]["trade_date"] if retained else None,
        "governed_end_observation": end,
        "observations": retained,
        "baselines": baselines,
        "available_baselines": available,
        "unavailable_baselines": unavailable,
        "recent_close_range": recent_range,
        "volume_context": {
            "current_volume_basis": current_volume_basis,
            "historical_average_basis": "completed_official_sessions",
            "comparison_alignment": comparison_alignment,
            "historical_average_volume": historical_average,
        },
        "caveats": list(caveats),
        "citation_ids": citations,
    }

    try:
        Draft7Validator.check_schema(schema)
        errors = list(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(result))
    except SchemaError as exc:
        raise H3DerivationError("schema_input_invalid") from exc
    if errors:
        raise H3DerivationError("schema_invalid_output") from errors[0]
    try:
        validate_recent_performance_semantics(result)
    except (TypeError, ValueError) as exc:
        raise H3DerivationError("semantic_invalid_output") from exc
    return result
