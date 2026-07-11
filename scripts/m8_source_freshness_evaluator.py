"""Pure M8-00-04 source freshness evaluator.

This module intentionally performs no filesystem, network, server, frontend, or
model access.  The public helper classifies one observation/source-policy pair
using only caller-provided dictionaries and an optional caller-provided clock.
"""

from datetime import datetime, timezone
from typing import Any

FRESHNESS_ASSESSMENT_SCHEMA_VERSION = "m8_source_freshness_assessment.v1"

FRESHNESS_ASSESSMENTS = {
    "fresh_intraday_snapshot",
    "stale_intraday_snapshot",
    "official_eod_reference",
    "official_statistics_eod",
    "regulatory_reference",
    "manual_snapshot",
    "validation_only",
    "credential_gated_metadata_only",
    "source_unavailable",
    "unknown",
}

_DEFAULT_INTRADAY_MAX_AGE_SECONDS = 900


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]


def _append_unique(items: list[Any], value: Any) -> None:
    if value not in items:
        items.append(value)


def _parse_utc(timestamp: Any) -> tuple[datetime | None, str | None]:
    if not isinstance(timestamp, str) or not timestamp.strip():
        return None, "timestamp missing or not a string"
    text = timestamp.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None, f"timestamp parse failure: {timestamp}"
    if parsed.tzinfo is None:
        return None, f"timestamp parse failure: timezone missing for {timestamp}"
    return parsed.astimezone(timezone.utc), None


def _base_assessment(observation: dict, source_policy: dict) -> dict:
    return {
        "schema_version": FRESHNESS_ASSESSMENT_SCHEMA_VERSION,
        "source_id": observation.get("source_id") or source_policy.get("source_id"),
        "source_family": observation.get("source_family") or source_policy.get("source_family"),
        "authority_level": source_policy.get("authority_level"),
        "timing_class": source_policy.get("timing_class"),
        "latency_class": source_policy.get("latency_class"),
        "freshness_assessment": "unknown",
        "freshness_reason": "timing class not evaluated yet",
        "stale_reason": None,
        "source_unavailable_reason": observation.get("source_unavailable_reason"),
        "source_timestamp": observation.get("source_timestamp"),
        "retrieved_at_utc": observation.get("retrieved_at_utc"),
        "market_date": observation.get("market_date"),
        "trading_date": observation.get("trading_date"),
        "session_state": observation.get("session_state"),
        "delay_seconds": None,
        "age_seconds": None,
        "not_realtime_guaranteed": False,
        "eod_only": False,
        "intraday_snapshot": False,
        "manual_snapshot": False,
        "validation_only": False,
        "credential_gated": False,
        "exchange_timestamp_absent": observation.get("source_timestamp") in (None, ""),
        "retrieved_time_only": False,
        "requires_caveats": False,
        "safe_for_ai_context": bool(source_policy.get("ai_context_allowed")),
        "ai_exposure_level": source_policy.get("ai_exposure_level"),
        "allowed_interpretation": _as_list(source_policy.get("allowed_interpretation")),
        "blocked_interpretation": _as_list(source_policy.get("blocked_interpretation")),
        "caveats": _as_list(source_policy.get("caveats")),
        "not_trading_signal": True,
        "not_recommendation": True,
        "trading_advice_allowed": False,
        "trading_signal_allowed": False,
        "recommendation_allowed": False,
    }


def _unknown(result: dict, reason: str) -> dict:
    result["freshness_assessment"] = "unknown"
    result["freshness_reason"] = reason
    result["not_realtime_guaranteed"] = True
    result["requires_caveats"] = True
    result["safe_for_ai_context"] = False
    _append_unique(result["caveats"], reason)
    return result


def build_source_freshness_assessment(
    observation: dict,
    source_policy: dict,
    *,
    now_utc: str | None = None,
) -> dict:
    """Classify one observation/source-policy pair into an M8 freshness label."""
    observation = dict(observation or {})
    source_policy = dict(source_policy or {})
    policy = dict(source_policy.get("freshness_evaluator_policy") or {})
    result = _base_assessment(observation, source_policy)

    value_statuses = set(_as_list(policy.get("unavailable_if_value_status_in")))
    if observation.get("source_unavailable") or observation.get("value_status") in value_statuses:
        result.update(
            freshness_assessment="source_unavailable",
            freshness_reason="source marked unavailable by observation or evaluator policy",
            not_realtime_guaranteed=True,
            requires_caveats=True,
            safe_for_ai_context=False,
        )
        return result

    timing_class = source_policy.get("timing_class")

    if timing_class == "liveish_intraday_snapshot":
        result["intraday_snapshot"] = True
        result["not_realtime_guaranteed"] = True
        _append_unique(result["caveats"], "retrieved_at_utc is local retrieval/load time unless source_timestamp proves exchange time")
        if result["exchange_timestamp_absent"]:
            result["retrieved_time_only"] = True
        retrieved_at = observation.get("retrieved_at_utc")
        if not retrieved_at:
            return _unknown(result, "retrieved_at_utc missing for liveish intraday snapshot")
        now_dt, now_error = _parse_utc(now_utc or datetime.now(timezone.utc).isoformat())
        retrieved_dt, retrieved_error = _parse_utc(retrieved_at)
        if now_error:
            return _unknown(result, now_error)
        if retrieved_error:
            return _unknown(result, retrieved_error)
        age_seconds = int((now_dt - retrieved_dt).total_seconds())
        result["age_seconds"] = age_seconds
        max_age = int(policy.get("max_intraday_age_seconds", _DEFAULT_INTRADAY_MAX_AGE_SECONDS))
        if age_seconds <= max_age:
            result.update(
                freshness_assessment="fresh_intraday_snapshot",
                freshness_reason=f"retrieved_at_utc age {age_seconds}s is within {max_age}s policy window",
                requires_caveats=result["retrieved_time_only"],
            )
        else:
            result.update(
                freshness_assessment="stale_intraday_snapshot",
                freshness_reason=f"retrieved_at_utc age {age_seconds}s exceeds {max_age}s policy window",
                stale_reason="stale source must not be described as current market",
                requires_caveats=True,
                safe_for_ai_context=False,
            )
            _append_unique(result["blocked_interpretation"], "stale source not safe to describe as current market")
        return result

    if timing_class == "official_eod":
        result.update(freshness_assessment="official_eod_reference", freshness_reason="official EOD timing class", eod_only=True, not_realtime_guaranteed=True, requires_caveats=True)
        _append_unique(result["caveats"], "EOD must not be described as current price or realtime")
        _append_unique(result["blocked_interpretation"], "not realtime")
        _append_unique(result["blocked_interpretation"], "not current price")
        return result

    if timing_class == "official_statistics_eod":
        result.update(freshness_assessment="official_statistics_eod", freshness_reason="official statistics EOD timing class", eod_only=True, not_realtime_guaranteed=True, requires_caveats=True)
        _append_unique(result["caveats"], "official statistics EOD must not be described as live derivatives signal")
        _append_unique(result["blocked_interpretation"], "not live derivatives signal")
        return result

    if timing_class == "regulatory_reference":
        result.update(freshness_assessment="regulatory_reference", freshness_reason="regulatory reference timing class", not_realtime_guaranteed=True, requires_caveats=True)
        return result

    if timing_class == "manual_snapshot":
        result.update(freshness_assessment="manual_snapshot", freshness_reason="manual operator evidence timing class", manual_snapshot=True, not_realtime_guaranteed=True, requires_caveats=True)
        _append_unique(result["caveats"], "not official source and cannot override official source")
        _append_unique(result["blocked_interpretation"], "not official source")
        _append_unique(result["blocked_interpretation"], "cannot override official source")
        return result

    if timing_class == "validation_only":
        result.update(freshness_assessment="validation_only", freshness_reason="validation-only timing class", validation_only=True, not_realtime_guaranteed=True, requires_caveats=True, safe_for_ai_context=False)
        _append_unique(result["caveats"], "validation-only source cannot be primary context")
        _append_unique(result["blocked_interpretation"], "cannot be primary context")
        return result

    if timing_class == "credential_gated_research":
        result.update(freshness_assessment="credential_gated_metadata_only", freshness_reason="credential-gated research timing class", credential_gated=True, not_realtime_guaranteed=True, requires_caveats=True, safe_for_ai_context=False)
        _append_unique(result["caveats"], "no credentials in repo; not runtime dependency")
        _append_unique(result["blocked_interpretation"], "not runtime dependency")
        return result

    if timing_class == "fundamental_reference":
        return _unknown(result, "fundamental_reference_not_yet_classified_by_m8_00_04")

    return _unknown(result, "unknown timing_class")
