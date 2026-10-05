"""Governed, pre-authorization I3 TWSE source-date resolution and binding."""
from __future__ import annotations

import copy
from datetime import date, datetime, time, timedelta
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from scripts.m8r_05b_01.canonical import plan_hash_and_id
from scripts.m8r_05b_01.planner import plan_identity_scope
from scripts.m8r_eod_expected_trade_date import get_taipei_closure_scope

TAIPEI = ZoneInfo("Asia/Taipei")
TWSE_CALENDAR_URL = "https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule"


def resolve_i3_twse_source_trade_date(
    *, evaluation_time: str | datetime, official_calendar: Mapping[str, Any] | list[Mapping[str, Any]],
    closure_events: list[dict[str, Any]], calendar_authority_ref: str,
    closure_authority_ref: str, closure_authority_complete: bool,
) -> dict[str, str]:
    """Resolve latest completed TWSE T86 date using supplied governed data.

    Calendar coverage is required only for dates actually inspected. A caller
    may provide one annual artifact or a governed collection of annual
    artifacts. No network, weekday fallback, or source probing occurs here.
    """
    if not isinstance(calendar_authority_ref, str) or not calendar_authority_ref.strip():
        raise ValueError("i3_calendar_authority_missing")
    if not isinstance(closure_authority_ref, str) or not closure_authority_ref.strip():
        raise ValueError("i3_closure_authority_missing")
    if closure_authority_complete is not True or not isinstance(closure_events, list):
        raise ValueError("i3_closure_coverage_unresolved")
    artifacts = official_calendar if isinstance(official_calendar, list) else [official_calendar]
    if not artifacts or any(not isinstance(a, Mapping) for a in artifacts):
        raise ValueError("i3_official_calendar_required")
    if any(not isinstance(item, dict) for item in closure_events):
        raise ValueError("i3_closure_events_invalid")
    parsed = datetime.fromisoformat(evaluation_time.replace("Z", "+00:00")) if isinstance(evaluation_time, str) else evaluation_time
    if not isinstance(parsed, datetime) or parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("i3_evaluation_time_timezone_required")
    parsed = parsed.astimezone(TAIPEI)
    local_date = parsed.date()
    calendar_by_date: dict[date, bool] = {}
    for artifact in artifacts:
        source = artifact.get("source")
        year = artifact.get("year")
        if (artifact.get("schema_version") != "twse_trading_calendar.v1"
                or artifact.get("market") != "TWSE"
                or type(year) is not int or not 1900 <= year <= 2200
                or not isinstance(source, Mapping)
                or source.get("source_url") != TWSE_CALENDAR_URL
                or source.get("runtime_fetch") is not False
                or not isinstance(artifact.get("dates"), list)):
            raise ValueError("i3_official_calendar_authority_invalid")
        seen: set[date] = set()
        for item in artifact["dates"]:
            if not isinstance(item, Mapping) or not isinstance(item.get("date"), str):
                raise ValueError("i3_official_calendar_duplicate_or_invalid_dates")
            try:
                item_date = date.fromisoformat(item["date"])
            except ValueError as exc:
                raise ValueError("i3_official_calendar_duplicate_or_invalid_dates") from exc
            if item_date.isoformat() != item["date"] or item_date.year != year:
                raise ValueError("i3_official_calendar_year_membership_invalid")
            if item_date in seen:
                raise ValueError("i3_official_calendar_duplicate_or_invalid_dates")
            seen.add(item_date)
            if type(item.get("is_trading_day")) is not bool:
                raise ValueError("i3_official_calendar_status_invalid")
            previous = calendar_by_date.get(item_date)
            if previous is not None and previous != item["is_trading_day"]:
                raise ValueError("i3_official_calendar_conflicting_duplicate_date")
            if previous is not None:
                raise ValueError("i3_official_calendar_duplicate_or_invalid_dates")
            calendar_by_date[item_date] = item["is_trading_day"]

    # Resolve only dates traversed. Missing irrelevant dates elsewhere in an
    # annual artifact do not block this lookup.
    source_session_cutoff = time(20, 0)
    current_is_trading = calendar_by_date.get(local_date)
    if current_is_trading is None:
        raise ValueError("i3_official_calendar_coverage_incomplete")
    current_closure = get_taipei_closure_scope(closure_events, local_date.isoformat())
    current_closed = current_closure in {"full_day", "morning"}
    if current_is_trading and not current_closed and parsed.timetz().replace(tzinfo=None) >= source_session_cutoff:
        source_date = local_date.isoformat()
    else:
        cursor = local_date - timedelta(days=1)
        source_date = None
        for _ in range(367):
            is_trading = calendar_by_date.get(cursor)
            if is_trading is None:
                raise ValueError("i3_official_calendar_coverage_incomplete")
            closure = get_taipei_closure_scope(closure_events, cursor.isoformat())
            if is_trading and closure not in {"full_day", "morning"}:
                source_date = cursor.isoformat()
                break
            cursor -= timedelta(days=1)
        if source_date is None:
            raise ValueError("i3_source_date_unresolved")
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
