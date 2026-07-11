"""M8A market-day currentness resolver."""
from __future__ import annotations
from datetime import date, datetime, timedelta
from scripts.m8a_ncdr_dgpa_closure_cap import is_taipei_market_closure_event
SCHEMA_VERSION="m8a_market_day_resolution.v1"
def _d(x): return x if isinstance(x,date) and not isinstance(x,datetime) else date.fromisoformat(str(x))
def _prev_weekday(day):
    d=day-timedelta(days=1)
    while d.weekday()>=5: d-=timedelta(days=1)
    return d
def resolve_market_day_currentness(*, evaluation_time_asia_taipei:str, reported_trade_date:str|None, calendar_artifact:dict|None=None, closure_events:list|None=None, exchange_special_status:str|None=None, target_date:str|None=None):
    target=_d(target_date or evaluation_time_asia_taipei[:10]); weekend=target.weekday()>=5
    scheduled="weekend" if weekend else "scheduled_trading_day"; scheduled_open=not weekend
    if calendar_artifact:
        for e in calendar_artifact.get("dates",[]):
            if e.get("date")==target.isoformat(): scheduled="scheduled_trading_day" if e.get("is_trading_day") else "scheduled_holiday"; scheduled_open=bool(e.get("is_trading_day")); break
    closures=closure_events or []; taipei=any(is_taipei_market_closure_event(e,target.isoformat()) for e in closures)
    emergency="emergency_closure_confirmed" if taipei else ("no_emergency_closure_found" if closures is not None else "emergency_closure_unknown")
    if exchange_special_status in {"closed_by_exchange_special_announcement","open_by_exchange_special_announcement"}: exchange=exchange_special_status
    elif taipei: exchange="closed_by_taipei_work_suspension_rule"
    elif scheduled_open: exchange="scheduled_open"
    elif scheduled in {"weekend","scheduled_holiday"}: exchange="scheduled_closed"
    else: exchange="unresolved"
    actual="emergency_closed" if taipei or exchange=="closed_by_exchange_special_announcement" else ("actual_trading_day" if exchange in {"scheduled_open","open_by_exchange_special_announcement"} else ("scheduled_closed" if exchange=="scheduled_closed" else "unresolved"))
    expected=(_prev_weekday(target) if actual in {"emergency_closed","scheduled_closed"} else target).isoformat()
    if not reported_trade_date: current="unresolved_date_mismatch"
    elif reported_trade_date==expected: current="matches_expected_latest_trade_date_after_emergency_closure" if actual=="emergency_closed" else "current_official_eod"
    elif reported_trade_date==_prev_weekday(date.fromisoformat(expected)).isoformat(): current="delayed_one_trading_day"
    else: current="stale_official_eod" if reported_trade_date < expected else "unresolved_date_mismatch"
    evidence=[{"source_id":"NCDR_DGPA_CLOSURE_CAP","area_name":e.get("area_name"),"target_date":e.get("target_date"),"decision_status":e.get("decision_status"),"closure_scope":e.get("closure_scope"),"event_id":e.get("entry_id"),"published_at":e.get("published_at")} for e in closures if e.get("source_id")=="NCDR_DGPA_CLOSURE_CAP"]
    return {"schema_version":SCHEMA_VERSION,"evaluation_time_asia_taipei":evaluation_time_asia_taipei,"target_date":target.isoformat(),"scheduled_calendar_status":scheduled,"emergency_closure_status":emergency,"exchange_market_status":exchange,"actual_market_day_status":actual,"expected_latest_completed_trade_date":expected,"reported_trade_date":reported_trade_date,"currentness_status":current,"evidence":evidence,"caveats":[]}
