"""M8A market-day currentness resolver."""
from __future__ import annotations
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from scripts.m8a_ncdr_dgpa_closure_cap import is_taipei_market_closure_event
SCHEMA_VERSION="m8a_market_day_resolution.v1"; TAIPEI=ZoneInfo("Asia/Taipei")
def _d(x): return x if isinstance(x,date) and not isinstance(x,datetime) else date.fromisoformat(str(x))
def _dt(x):
    if isinstance(x, datetime): dt=x
    else: dt=datetime.fromisoformat(str(x))
    if dt.tzinfo is None: dt=dt.replace(tzinfo=TAIPEI)
    return dt.astimezone(TAIPEI)
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
def _is_actual_trading_day(day, calendar_artifact, closure_events, exchange_special_closures):
    return _skip_reason(day, calendar_artifact, closure_events, exchange_special_closures) is None
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
def resolve_market_day_currentness(*, evaluation_time_asia_taipei:str|datetime|None=None, reported_trade_date:str|None=None, calendar_artifact:dict|None=None, closure_events:list|None=None, closure_query_succeeded:bool|None=None, exchange_special_status:str|None=None, exchange_special_closures:list|None=None, target_date:str|None=None, eod_completion_time:str="15:30"):
    eval_dt=_dt(evaluation_time_asia_taipei or datetime.now(TAIPEI)); target=_d(target_date or eval_dt.date().isoformat())
    scheduled, scheduled_open=_scheduled_status(target, calendar_artifact)
    taipei=_is_emergency_closed(target, closure_events)
    if taipei: emergency="emergency_closure_confirmed"
    elif closure_events is None and not closure_query_succeeded: emergency="emergency_closure_unknown"
    else: emergency="no_emergency_closure_found"
    if exchange_special_status in {"closed_by_exchange_special_announcement","open_by_exchange_special_announcement"}: exchange=exchange_special_status
    elif taipei: exchange="closed_by_taipei_work_suspension_rule"
    elif _is_special_closed(target, exchange_special_closures): exchange="closed_by_exchange_special_announcement"
    elif scheduled_open: exchange="scheduled_open"
    elif scheduled in {"weekend","scheduled_holiday"}: exchange="scheduled_closed"
    else: exchange="unresolved"
    actual="emergency_closed" if taipei or exchange=="closed_by_exchange_special_announcement" else ("actual_trading_day" if exchange in {"scheduled_open","open_by_exchange_special_announcement"} else ("scheduled_closed" if exchange=="scheduled_closed" else "unresolved"))
    complete_time=time.fromisoformat(eod_completion_time)
    if actual=="actual_trading_day" and eval_dt.date()==target and eval_dt.timetz().replace(tzinfo=None) < complete_time:
        trace=previous_actual_trading_day_resolution(target, calendar_artifact, closure_events, exchange_special_closures); prev=trace["date"]; expected=prev.isoformat() if prev else None
    elif actual=="actual_trading_day":
        trace={"date": target, "skipped_dates": [], "crossed_emergency_closure": False, "reason": "current_actual_trading_day_after_eod_completion"}; expected=target.isoformat()
    else:
        trace=previous_actual_trading_day_resolution(target, calendar_artifact, closure_events, exchange_special_closures); prev=trace["date"]; expected=prev.isoformat() if prev else None
        target_reason=_skip_reason(target, calendar_artifact, closure_events, exchange_special_closures)
        if target_reason:
            trace["skipped_dates"] = [{"date": target.isoformat(), "reason": target_reason}] + trace.get("skipped_dates", [])
            trace["crossed_emergency_closure"] = trace.get("crossed_emergency_closure") or target_reason == "emergency_closed"
    if not reported_trade_date or not expected: current="unresolved_date_mismatch"
    elif reported_trade_date==expected: current="matches_expected_latest_trade_date_after_emergency_closure" if (actual=="emergency_closed" or trace.get("crossed_emergency_closure")) else "current_official_eod"
    else:
        prev_expected=previous_actual_trading_day(date.fromisoformat(expected), calendar_artifact, closure_events, exchange_special_closures)
        current="delayed_one_trading_day" if prev_expected and reported_trade_date==prev_expected.isoformat() else ("stale_official_eod" if reported_trade_date < expected else "unresolved_date_mismatch")
    evidence=[{"source_id":"NCDR_DGPA_CLOSURE_CAP","area_name":e.get("area_name"),"target_date":e.get("target_date"),"decision_status":e.get("decision_status"),"closure_scope":e.get("closure_scope"),"event_id":e.get("entry_id"),"published_at":e.get("published_at")} for e in (closure_events or []) if e.get("source_id")=="NCDR_DGPA_CLOSURE_CAP" and e.get("area_name")=="臺北市"]
    return {"schema_version":SCHEMA_VERSION,"evaluation_time_asia_taipei":eval_dt.isoformat(),"target_date":target.isoformat(),"scheduled_calendar_status":scheduled,"emergency_closure_status":emergency,"exchange_market_status":exchange,"actual_market_day_status":actual,"expected_latest_completed_trade_date":expected,"expected_latest_completed_trade_date_resolution_reason": trace.get("reason"), "expected_latest_completed_trade_date_resolution_trace": trace.get("skipped_dates", []), "reported_trade_date":reported_trade_date,"currentness_status":current,"evidence":evidence,"caveats":[]}
