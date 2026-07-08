"""M7E pure market clock/session-state helpers.

This module is intentionally pure: it performs no network requests, no runtime
integration, and no filesystem writes. It classifies only supplied records and
observations.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

M7E_MARKET_CLOCK_SESSION_STATE_SCHEMA_VERSION = "m7e_market_clock_session_state.v1"
HOLIDAY_CLASSIFICATION_SCHEMA_VERSION = "m7e_twse_holiday_schedule_classification.v1"
_ALLOWED_LANGUAGE = [
    "latest observed context",
    "latest retrieved observation",
    "reference-only context",
    "during regular-session candidate",
    "not verified as live",
    "session-state unknown",
    "weekday heuristic only",
    "holiday schedule records supplied",
]
_BLOCKED_LANGUAGE = [
    "currently rising",
    "currently falling",
    "market is now moving",
    "live trading signal",
    "buy signal",
    "sell signal",
    "recommendation",
    "target price",
    "support",
    "resistance",
    "capital flow",
    "sector rotation",
    "full-market breadth",
]
_TS_FIELDS = ["retrieved_at_utc", "retrieved_at", "observation_time_utc", "generated_at_utc", "created_at_utc"]


def parse_twse_roc_date(value: str) -> date:
    if not isinstance(value, str) or len(value) != 7 or not value.isdigit():
        raise ValueError("TWSE ROC date must be exactly 7 digits in YYYMMDD form")
    roc_year = int(value[:3])
    if roc_year <= 0:
        raise ValueError("ROC year must be positive")
    return date(roc_year + 1911, int(value[3:5]), int(value[5:7]))


def classify_twse_holiday_schedule_records(records: list[dict[str, object]]) -> dict[str, object]:
    out: dict[str, Any] = {
        "schema_version": HOLIDAY_CLASSIFICATION_SCHEMA_VERSION,
        "source": "TWSE_OpenAPI_holidaySchedule",
        "date_format": "ROC_YYYMMDD",
        "rule": "weekends_plus_endpoint_dates_excluding_names_containing_trading_day",
        "endpoint_non_trading_dates": [],
        "explicit_endpoint_trading_dates": [],
        "record_count": len(records or []),
        "invalid_records": [],
        "caveats": [
            "Classifier uses supplied records only; no network fetch is performed.",
            "Names containing exact substring 交易日 are explicit trading-day labels, not holiday closures.",
            "Weekend non-trading rule remains independent of endpoint labels.",
        ],
    }
    for idx, record in enumerate(records or []):
        name = record.get("Name") if isinstance(record, dict) else None
        raw_date = record.get("Date") if isinstance(record, dict) else None
        weekday = record.get("Weekday") if isinstance(record, dict) else None
        try:
            if not isinstance(name, str):
                raise ValueError("Name must be a string")
            if not isinstance(raw_date, str):
                raise ValueError("Date must be a ROC_YYYMMDD string")
            parsed = parse_twse_roc_date(raw_date)
        except Exception as exc:
            out["invalid_records"].append({"index": idx, "Name": name, "Date": raw_date, "Weekday": weekday, "reason": str(exc)})
            continue
        item = {"Name": name, "Date": raw_date, "gregorian_date": parsed.isoformat(), "Weekday": weekday}
        if "交易日" in name:
            item["reason"] = "name_contains_exact_trading_day_substring"
            out["explicit_endpoint_trading_dates"].append(item)
        else:
            item["reason"] = "name_does_not_contain_exact_trading_day_substring"
            out["endpoint_non_trading_dates"].append(item)
    return out


def build_empty_market_clock_session_state() -> dict[str, object]:
    return {
        "schema_version": M7E_MARKET_CLOCK_SESSION_STATE_SCHEMA_VERSION,
        "context_id": "M7E_MARKET_CLOCK_SESSION_STATE",
        "context_status": "schema_defined_not_computed",
        "runtime_populated": False,
        "safe_for_ai_context": False,
        "builder_output_safe_for_ai_context": False,
        "market": "TW",
        "timezone": "Asia/Taipei",
        "bounded_watchlist_only": True,
        "not_full_market_breadth": True,
        "not_trading_signal": True,
        "not_recommendation": True,
        "not_market_prediction": True,
        "not_capital_flow": True,
        "session_state": None,
        "session_phase": None,
        "trade_date": None,
        "calendar_policy": "weekends_plus_supplied_twse_holiday_schedule_records",
        "calendar_confidence": "unknown_or_degraded",
        "holiday_status": "unknown",
        "is_weekend": None,
        "is_trading_day_candidate": None,
        "latest_observation_time": None,
        "latest_observation_age_seconds": None,
        "freshness_state": "unknown",
        "currentness_label": "degraded_unknown",
        "semantic_caveats": [],
        "allowed_language": list(_ALLOWED_LANGUAGE),
        "blocked_language": list(_BLOCKED_LANGUAGE),
        "source_provenance": [],
        "quality_gates": {"raw_payload_exposed": False, "raw_rich_facts_exposed": False, "raw_full_ladder_exposed": False},
    }


def _parse_dt(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("timestamp must be datetime or ISO string")
    if dt.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return dt.astimezone(timezone.utc)


def _freshness(now: datetime, obs: dict[str, object] | None) -> tuple[str, str | None, int | None]:
    if not obs:
        return "no_observation", None, None
    raw = next((obs.get(k) for k in _TS_FIELDS if obs.get(k)), None)
    if raw is None:
        return "no_observation", None, None
    try:
        ts = _parse_dt(raw)  # type: ignore[arg-type]
    except Exception:
        return "invalid_timestamp", None, None
    age = int((now - ts).total_seconds())
    if age < -60:
        return "future_timestamp", ts.isoformat(), age
    if age <= 180:
        return "fresh", ts.isoformat(), age
    if age <= 900:
        return "recent", ts.isoformat(), age
    return "stale", ts.isoformat(), age


def build_market_clock_session_state(*, now_utc: datetime | str, latest_observation: dict[str, object] | None = None, holiday_schedule_records: list[dict[str, object]] | None = None, timezone_name: str = "Asia/Taipei") -> dict[str, object]:
    now = _parse_dt(now_utc)
    local = now.astimezone(ZoneInfo(timezone_name))
    result = build_empty_market_clock_session_state()
    result.update({"context_status": "computed_candidate_not_runtime_integrated", "timezone": timezone_name, "trade_date": local.date().isoformat(), "source_provenance": ["now_utc_input", "latest_observation_timestamp_only"]})
    is_weekend = local.weekday() >= 5
    result["is_weekend"] = is_weekend
    classification = classify_twse_holiday_schedule_records(holiday_schedule_records) if holiday_schedule_records is not None else None
    non = {r["gregorian_date"] for r in classification["endpoint_non_trading_dates"]} if classification else set()
    explicit = {r["gregorian_date"] for r in classification["explicit_endpoint_trading_dates"]} if classification else set()
    d = local.date().isoformat()
    if is_weekend:
        holiday_status, state, phase, trading = "weekend", "weekend_closed", "non_trading_day", False
    elif d in non:
        holiday_status, state, phase, trading = "endpoint_non_trading_date", "holiday_closed", "non_trading_day", False
    else:
        holiday_status = "explicit_endpoint_trading_label" if d in explicit else ("not_in_endpoint_holiday_records" if classification else "records_missing")
        trading = True
        t = local.time()
        if t >= datetime.strptime("09:00", "%H:%M").time() and t < datetime.strptime("13:30", "%H:%M").time():
            state, phase = "regular_open", "regular_session"
        elif t >= datetime.strptime("08:00", "%H:%M").time() and t < datetime.strptime("09:00", "%H:%M").time():
            state, phase = "preopen", "before_regular_session"
        elif t >= datetime.strptime("13:30", "%H:%M").time() and t < datetime.strptime("14:30", "%H:%M").time():
            state, phase = "postclose", "after_regular_session"
        else:
            state, phase = "closed", "after_regular_session"
    freshness, ts, age = _freshness(now, latest_observation)
    if freshness in {"no_observation", "invalid_timestamp", "future_timestamp", "unknown"}:
        currentness = "degraded_unknown"
    elif state == "regular_open" and trading and freshness == "fresh":
        currentness = "live_candidate"
    elif state == "regular_open" and trading and freshness == "recent":
        currentness = "recent_but_unverified"
    elif state in {"weekend_closed", "holiday_closed", "preopen"}:
        currentness = "not_current"
    else:
        currentness = "reference_only"
    caveats = ["Builder output is not safe for direct AI context until controlled promotion is implemented."]
    if classification:
        conf = "official_holiday_schedule_records_supplied"
        caveats.append("TWSE holiday schedule records were supplied and classified locally without network fetch.")
        result["source_provenance"].append("supplied_twse_holiday_schedule_records")
    else:
        conf = "weekday_heuristic_only"
        caveats.append("Holiday records missing; weekday heuristic only and official holiday correctness is unknown.")
    result.update({"session_state": state, "session_phase": phase, "calendar_confidence": conf, "holiday_status": holiday_status, "is_trading_day_candidate": trading, "latest_observation_time": ts, "latest_observation_age_seconds": age, "freshness_state": freshness, "currentness_label": currentness, "semantic_caveats": caveats})
    return result
