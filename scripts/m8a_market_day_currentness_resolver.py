"""M8A market-day currentness resolver."""
from __future__ import annotations
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from scripts.m8r_eod_expected_trade_date import determine_expected_eod_session_status, parse_taipei_datetime, get_taipei_closure_scope
from scripts.m8a_ncdr_dgpa_closure_cap import is_taipei_market_closure_event

SCHEMA_VERSION = "m8a_market_day_resolution.v1"
TAIPEI = ZoneInfo("Asia/Taipei")

def _d(x):
    return x if isinstance(x, date) and not isinstance(x, datetime) else date.fromisoformat(str(x))

# Original helpers restored for backward compatibility
def _calendar_entry(day, calendar_artifact):
    if calendar_artifact:
        for e in calendar_artifact.get("dates",[]):
            if e.get("date")==day.isoformat(): return e
    return None

def _scheduled_status(day, calendar_artifact):
    entry=_calendar_entry(day, calendar_artifact)
    if entry is not None:
        return ("scheduled_trading_day" if entry.get("is_trading_day") else "scheduled_holiday", bool(entry.get("is_trading_day")))
    return ("weekend", False) if day.weekday()>=5 else ("scheduled_trading_day", True)

def _is_emergency_closed(day, closure_events):
    return bool(closure_events) and any(is_taipei_market_closure_event(e, day.isoformat()) for e in closure_events)

def _is_special_closed(day, exchange_special_closures):
    return day.isoformat() in set(exchange_special_closures or [])

def _skip_reason(day, calendar_artifact, closure_events, exchange_special_closures):
    scheduled, scheduled_open=_scheduled_status(day, calendar_artifact)
    if not scheduled_open:
        return "weekend" if scheduled == "weekend" else "scheduled_holiday"
    if _is_emergency_closed(day, closure_events): return "emergency_closed"
    if _is_special_closed(day, exchange_special_closures): return "exchange_special_closed"
    return None

def previous_actual_trading_day_resolution(day, calendar_artifact=None, closure_events=None, exchange_special_closures=None):
    cur=day-timedelta(days=1); skipped=[]
    for _ in range(370):
        reason=_skip_reason(cur, calendar_artifact, closure_events, exchange_special_closures)
        if reason is None:
            return {"date": cur, "skipped_dates": skipped, "crossed_emergency_closure": any(x["reason"]=="emergency_closed" for x in skipped), "reason": "previous_actual_trading_day"}
        skipped.append({"date": cur.isoformat(), "reason": reason})
        cur-=timedelta(days=1)
    return {"date": None, "skipped_dates": skipped, "crossed_emergency_closure": any(x["reason"]=="emergency_closed" for x in skipped), "reason": "unresolved"}

def previous_actual_trading_day(day, calendar_artifact=None, closure_events=None, exchange_special_closures=None):
    return previous_actual_trading_day_resolution(day, calendar_artifact, closure_events, exchange_special_closures)["date"]

def resolve_market_day_currentness(
    *,
    evaluation_time_asia_taipei: str | datetime | None = None,
    reported_trade_date: str | None = None,
    calendar_artifact: dict | None = None,
    closure_events: list | None = None,
    closure_query_succeeded: bool | None = None,
    exchange_special_status: str | None = None,
    exchange_special_closures: list | None = None,
    target_date: str | None = None,
    eod_completion_time: str = "15:30",
):
    # Parse evaluation time
    eval_dt = parse_taipei_datetime(evaluation_time_asia_taipei or datetime.now(TAIPEI))
    
    if target_date:
        t_date = _d(target_date)
        eval_dt = eval_dt.replace(year=t_date.year, month=t_date.month, day=t_date.day)

    cls_status = closure_events
    if closure_query_succeeded is False:
        cls_status = None

    # Call the new expected trade date evaluator
    res = determine_expected_eod_session_status(
        reference_time_utc=eval_dt,
        market="TWSE",
        official_calendar=calendar_artifact,
        closure_status=cls_status,
        market_close_time=eod_completion_time,
        publication_grace_period=60,
        actual_trade_date=reported_trade_date,
        exchange_session_override=exchange_special_closures
    )

    expected = res["expected_latest_completed_trade_date"]
    
    # Heuristics for backward-compatible fields in resolver
    scheduled = "scheduled_trading_day"
    if calendar_artifact:
        for entry in calendar_artifact.get("dates", []):
            if entry.get("date") == res["reference_local_date"]:
                scheduled = "scheduled_trading_day" if entry.get("is_trading_day") else "scheduled_holiday"
                break
    else:
        scheduled = "weekend" if eval_dt.date().weekday() >= 5 else "scheduled_trading_day"

    emergency = "no_emergency_closure_found"
    if res["closure_source"] == "NCDR_DGPA_CLOSURE_CAP":
        emergency = "emergency_closure_confirmed"
    elif res["closure_source"] == "unresolved":
        emergency = "emergency_closure_unknown"

    actual_m = "actual_trading_day"
    if res["session_status"] == "market_closed_no_session":
        actual_m = "emergency_closed"
    elif res["session_status"] in {"weekend", "official_holiday"}:
        actual_m = "scheduled_closed"
    elif res["session_status"] == "calendar_status_unresolved":
        actual_m = "unresolved"

    evidence = []
    if closure_events:
        evidence = [
            {
                "source_id": "NCDR_DGPA_CLOSURE_CAP",
                "area_name": e.get("area_name"),
                "target_date": e.get("target_date"),
                "decision_status": e.get("decision_status"),
                "closure_scope": e.get("closure_scope"),
                "event_id": e.get("entry_id"),
                "published_at": e.get("published_at")
            }
            for e in closure_events
            if e.get("source_id") == "NCDR_DGPA_CLOSURE_CAP" and e.get("area_name") in {"臺北市", "台北市"}
        ]

    # Reconstruct trace information
    skipped_dates = []
    if expected:
        cur = eval_dt.date()
        exp_d = date.fromisoformat(expected)
        chk = cur
        if res["session_status"] in {"weekend", "official_holiday", "market_closed_no_session"}:
            reason = "weekend" if cur.weekday() >= 5 else "scheduled_holiday"
            if res["session_status"] == "market_closed_no_session":
                reason = "emergency_closed"
            skipped_dates.append({"date": cur.isoformat(), "reason": reason})
        
        chk -= timedelta(days=1)
        while chk > exp_d:
            reason = "weekend" if chk.weekday() >= 5 else "scheduled_holiday"
            # check closure for that date
            c_scope = get_taipei_closure_scope(closure_events, chk.isoformat())
            if c_scope in {"full_day", "morning"}:
                reason = "emergency_closed"
            skipped_dates.append({"date": chk.isoformat(), "reason": reason})
            chk -= timedelta(days=1)

    # Re-map status compatibility using the actual and expected dates
    status_compat = "unresolved_date_mismatch"
    if reported_trade_date and expected:
        if reported_trade_date == expected:
            if res["session_status"] == "market_closed_no_session" or any(x["reason"] == "emergency_closed" for x in skipped_dates) or res["closure_source"] == "NCDR_DGPA_CLOSURE_CAP":
                status_compat = "matches_expected_latest_trade_date_after_emergency_closure"
            else:
                status_compat = "current_official_eod"
        else:
            if reported_trade_date < expected:
                try:
                    prev_expected = previous_actual_trading_day(date.fromisoformat(expected), calendar_artifact, closure_events, exchange_special_closures)
                    if prev_expected and reported_trade_date == prev_expected.isoformat():
                        status_compat = "delayed_one_trading_day"
                    else:
                        status_compat = "stale_official_eod"
                except Exception:
                    status_compat = "stale_official_eod"
            else:
                status_compat = "unresolved_date_mismatch"

    exchange = "scheduled_open"
    if res["session_status"] == "market_closed_no_session":
        if res["closure_source"] == "NCDR_DGPA_CLOSURE_CAP":
            exchange = "closed_by_taipei_work_suspension_rule"
        else:
            exchange = "closed_by_exchange_special_announcement"
    elif res["session_status"] in {"weekend", "official_holiday"}:
        exchange = "scheduled_closed"
    elif res["session_status"] == "calendar_status_unresolved":
        exchange = "unresolved"

    return {
        "schema_version": SCHEMA_VERSION,
        "evaluation_time_asia_taipei": eval_dt.isoformat(),
        "target_date": res["reference_local_date"],
        "scheduled_calendar_status": scheduled,
        "emergency_closure_status": emergency,
        "exchange_market_status": exchange,
        "actual_market_day_status": actual_m,
        "expected_latest_completed_trade_date": expected,
        "expected_latest_completed_trade_date_resolution_reason": "previous_actual_trading_day" if res["session_status"] in {"weekend", "official_holiday", "market_closed_no_session"} else "current_actual_trading_day_after_eod_completion",
        "expected_latest_completed_trade_date_resolution_trace": skipped_dates,
        "reported_trade_date": reported_trade_date,
        "currentness_status": status_compat,
        "evidence": evidence,
        "caveats": res["caveats"]
    }
