"""Governed, pre-authorization I3 TWSE source-date resolution and binding."""
from __future__ import annotations

import copy
from datetime import date, datetime, timedelta
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from scripts.m8r_05b_01.canonical import plan_hash_and_id
from scripts.m8r_05b_01.planner import plan_identity_scope
from scripts.m8r_eod_expected_trade_date import determine_expected_eod_session_status

TAIPEI = ZoneInfo("Asia/Taipei")
TWSE_CALENDAR_URL = "https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule"


def resolve_i3_twse_source_trade_date(
    *, evaluation_time: str | datetime, official_calendar: Mapping[str, Any],
    closure_events: list[dict[str, Any]], calendar_authority_ref: str,
    closure_authority_ref: str, closure_authority_complete: bool,
) -> dict[str, str]:
    """Resolve latest completed TWSE T86 date using supplied governed data.

    The caller must supply a complete official calendar window and a closure
    authority attesting that its result covers the interval. No network, clock,
    calendar fallback, or previous-date probing occurs here.
    """
    if not isinstance(calendar_authority_ref, str) or not calendar_authority_ref.strip():
        raise ValueError("i3_calendar_authority_missing")
    if not isinstance(closure_authority_ref, str) or not closure_authority_ref.strip():
        raise ValueError("i3_closure_authority_missing")
    if closure_authority_complete is not True or not isinstance(closure_events, list):
        raise ValueError("i3_closure_coverage_unresolved")
    if not isinstance(official_calendar, Mapping) or not isinstance(official_calendar.get("dates"), list):
        raise ValueError("i3_official_calendar_required")
    source = official_calendar.get("source")
    if (official_calendar.get("schema_version") != "twse_trading_calendar.v1"
            or official_calendar.get("market") != "TWSE"
            or not isinstance(source, Mapping)
            or source.get("source_url") != TWSE_CALENDAR_URL
            or source.get("runtime_fetch") is not False):
        raise ValueError("i3_official_calendar_authority_invalid")
    if any(not isinstance(item, dict) for item in closure_events):
        raise ValueError("i3_closure_events_invalid")
    parsed = datetime.fromisoformat(evaluation_time.replace("Z", "+00:00")) if isinstance(evaluation_time, str) else evaluation_time
    if not isinstance(parsed, datetime) or parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("i3_evaluation_time_timezone_required")
    parsed = parsed.astimezone(TAIPEI)
    local_date = parsed.date()
    calendar_dates = {
        item.get("date") for item in official_calendar["dates"]
        if isinstance(item, Mapping) and isinstance(item.get("date"), str)
    }
    if len(calendar_dates) != len(official_calendar["dates"]):
        raise ValueError("i3_official_calendar_duplicate_or_invalid_dates")
    if any(type(item.get("is_trading_day")) is not bool for item in official_calendar["dates"]):
        raise ValueError("i3_official_calendar_status_invalid")
    earliest = local_date - timedelta(days=366)
    required_dates = {(earliest + timedelta(days=offset)).isoformat() for offset in range(367)}
    if not required_dates.issubset(calendar_dates):
        raise ValueError("i3_official_calendar_coverage_incomplete")
    resolved = determine_expected_eod_session_status(
        reference_time_utc=parsed, market="TWSE", official_calendar=dict(official_calendar),
        closure_status=closure_events, market_close_time="20:00", publication_grace_period=0,
    )
    source_date = resolved.get("expected_latest_completed_trade_date")
    if (resolved.get("fallback_policy_used") is not False
            or resolved.get("calendar_source") != "official_calendar_artifact"
            or resolved.get("closure_source") == "unresolved"
            or not isinstance(source_date, str)):
        raise ValueError("i3_source_date_unresolved")
    date.fromisoformat(source_date)
    return {
        "market": "TWSE", "evaluation_time": parsed.isoformat(),
        "resolved_source_trade_date": source_date,
        "calendar_authority_ref": calendar_authority_ref,
        "closure_authority_ref": closure_authority_ref,
    }


def bind_i3_source_trade_date(plan: Mapping[str, Any], binding: Mapping[str, str]) -> dict[str, Any]:
    """Bind a previously resolved date into plan identity before authorization."""
    if not isinstance(binding, Mapping) or binding.get("market") != "TWSE":
        raise ValueError("i3_source_date_binding_invalid")
    date.fromisoformat(binding.get("resolved_source_trade_date", ""))
    result = copy.deepcopy(dict(plan))
    if result.get("plan_status") not in {"plan_ready", "plan_ready_with_warnings", "plan_only_not_executable"}:
        raise ValueError("i3_plan_not_authorizable")
    if not any(op.get("capability_id") == "cash_institutional_flow_context" and op.get("market") == "TWSE"
               for op in result.get("operations", [])):
        raise ValueError("i3_operation_missing")
    result["resolved_source_trade_date"] = binding["resolved_source_trade_date"]
    result["source_date_binding"] = dict(binding)
    scope = plan_identity_scope(result)
    result["plan_hash"], result["plan_id"] = plan_hash_and_id(scope)
    return result


def resolve_and_bind_i3_twse_plan(
    plan: Mapping[str, Any], *, evaluation_time: str | datetime,
    official_calendar: Mapping[str, Any], closure_events: list[dict[str, Any]],
    calendar_authority_ref: str, closure_authority_ref: str,
    closure_authority_complete: bool,
) -> dict[str, Any]:
    """Canonical pre-authorization resolver -> immutable plan binding path."""
    binding = resolve_i3_twse_source_trade_date(
        evaluation_time=evaluation_time, official_calendar=official_calendar,
        closure_events=closure_events, calendar_authority_ref=calendar_authority_ref,
        closure_authority_ref=closure_authority_ref,
        closure_authority_complete=closure_authority_complete,
    )
    return bind_i3_source_trade_date(plan, binding)
