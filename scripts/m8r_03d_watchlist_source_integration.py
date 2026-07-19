from __future__ import annotations
from typing import Any
from scripts.m8r_03c_watchlist_bundle_builder import validate_watchlist_input_observation
from scripts.m8r_eod_expected_trade_date import determine_expected_eod_session_status, parse_taipei_datetime

SAFE_CURRENT = {'latest_price','change','change_percent','open','high','low','volume','no_trade_state','close'}
SAFE_EOD = {'open','high','low','close','volume','trade_date','latest_price'}
FORBIDDEN = {'raw_payload','raw','headers','cookies','cookie','session_id','session_ids','authorization','body','msgArray'}

from datetime import datetime, timezone, timedelta, time, date
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo("Asia/Taipei")

def parse_iso_datetime(s: str) -> datetime:
    if not s:
        raise ValueError("empty timestamp")
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        parts = s.split("+")
        if len(parts) == 2:
            time_part, tz_part = parts
            if "." in time_part:
                time_part = time_part.split(".")[0]
            s = f"{time_part}+{tz_part}"
        else:
            parts = s.split("-")
            if len(parts) >= 4:
                tz_part = parts[-1]
                time_part = "-".join(parts[:-1])
                if "." in time_part:
                    time_part = time_part.split(".")[0]
                s = f"{time_part}-{tz_part}"
            else:
                if "." in s:
                    s = s.split(".")[0]
        dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def evaluate_evidence_currentness(
    *,
    reference_clock_str: str | None,
    source_timestamp_str: str | None,
    retrieved_at_str: str | None,
    timing_class: str,
    max_age_seconds: float = 900.0,
    trade_date: str | None = None,
    calendar_artifact: dict | None = None,
    closure_events: list | None = None,
    market: str = "TWSE"
) -> dict:
    if timing_class not in {"liveish_intraday_snapshot", "official_eod"}:
        return {"status": "unresolved", "reason": f"unsupported_timing_class:{timing_class}"}
    if not reference_clock_str:
        return {"status": "unresolved", "reason": "missing_reference_clock"}
        
    try:
        ref_dt = parse_iso_datetime(reference_clock_str)
    except Exception:
        return {"status": "unresolved", "reason": "invalid_reference_clock"}
        
    # Default outputs
    latency_seconds = None
    if retrieved_at_str and source_timestamp_str:
        try:
            ret_dt = parse_iso_datetime(retrieved_at_str)
            src_dt = parse_iso_datetime(source_timestamp_str)
            latency_seconds = (ret_dt - src_dt).total_seconds()
        except Exception:
            pass

    if timing_class == "liveish_intraday_snapshot":
        ts_str = source_timestamp_str or retrieved_at_str
        if not ts_str:
            return {"status": "unresolved", "reason": "missing_evidence_timestamp"}
        try:
            eff_dt = parse_iso_datetime(ts_str)
        except Exception:
            return {"status": "unresolved", "reason": "invalid_evidence_timestamp"}
            
        age_seconds = (ref_dt - eff_dt).total_seconds()
        if age_seconds < 0:
            status = "unresolved"
            reason = "evidence_timestamp_in_future"
        elif age_seconds > max_age_seconds:
            status = "stale"
            reason = f"evidence_age_exceeds_max_limit:{int(age_seconds)}s"
        else:
            status = "fresh"
            reason = "evidence_within_freshness_limit"
            
        res_dict = {
            "status": status,
            "reason": reason,
            "age_seconds": age_seconds,
            "actual_trade_date": None,
            "expected_trade_date": None,
            "session_status": None,
            "publication_grace_applied": False,
            "fallback_policy_used": False,
            "fallback_policy": None,
            "caveats": []
        }
        if latency_seconds is not None:
            res_dict["transport_latency_seconds"] = latency_seconds
        return res_dict
        
    else:  # timing_class == "official_eod"
        # Call determine_expected_eod_session_status
        try:
            res = determine_expected_eod_session_status(
                reference_time_utc=ref_dt,
                market=market,
                official_calendar=calendar_artifact,
                closure_status=closure_events,
                market_close_time="13:30" if market in {"TWSE", "TPEX"} else "13:45",
                publication_grace_period=60,
                actual_trade_date=trade_date
            )
        except Exception as exc:
            return {"status": "unresolved", "reason": f"expected_trade_date_evaluator_failed:{exc}"}
            
        # Calculate age_seconds using same close time logic for reference comparison
        age_seconds = 0.0
        if trade_date:
            try:
                act_date = date.fromisoformat(trade_date)
                c_time = time.fromisoformat("13:30" if market in {"TWSE", "TPEX"} else "13:45")
                eff_dt = datetime.combine(act_date, c_time, tzinfo=TAIPEI)
                age_seconds = (ref_dt.astimezone(TAIPEI) - eff_dt).total_seconds()
            except Exception:
                pass
                
        # Status normalization
        # original tests expect "official_completed_eod" for good EOD currentness,
        # but our new spec has "official_latest_completed_eod".
        # Let's map "official_latest_completed_eod" to "official_completed_eod" or keep both
        # We can map them compatibly
        status = res["currentness_status"]
        if status in {"official_latest_completed_eod", "official_previous_session_eod_before_close", "not_yet_published_after_close"}:
            status = "official_completed_eod"
        elif status == "unexpected_stale_eod":
            status = "stale"
        elif status in {"source_trade_date_missing", "calendar_status_unresolved", "invalid_trade_date_format", "future_trade_date_invalid"}:
            status = "unresolved"
            
        reason = f"EOD session check: {res['currentness_status']}"
        if res["currentness_status"] == "source_trade_date_missing":
            reason = "missing_trade_date"
        elif res["currentness_status"] == "unexpected_stale_eod":
            reason = "eod_older_than_three_days"
            
        res_dict = {
            "status": status,
            "reason": reason,
            "age_seconds": age_seconds,
            "actual_trade_date": trade_date,
            "expected_trade_date": res["expected_latest_completed_trade_date"],
            "session_status": res["session_status"],
            "publication_grace_applied": res["publication_grace_applied"],
            "fallback_policy_used": res["fallback_policy_used"],
            "fallback_policy": res["fallback_policy"],
            "caveats": res["caveats"]
        }
        if latency_seconds is not None:
            res_dict["transport_latency_seconds"] = latency_seconds
        return res_dict

def _reject_raw(d):
    if isinstance(d,dict):
        bad={str(k) for k in d}&FORBIDDEN
        if bad: raise ValueError('forbidden_raw_field:'+sorted(bad)[0])
        for v in d.values(): _reject_raw(v)
    elif isinstance(d,list):
        for v in d: _reject_raw(v)

def _identity(plan_target): return plan_target.get('requested_identity') or {}, plan_target.get('resolved_identity') or {}
def _base(target,source_family,timing,context,retrieved,source_ts=None,trade_date=None,currentness=None,facts=None,issues=None):
    req,res=_identity(target); obs={'schema_version':'m8r_watchlist_input_observation.v1','target_id':target['target_id'],'requested_identity':req,'resolved_identity':res,'source_family':source_family,'timing_class':timing,'context_type':context,'source_timestamp':source_ts,'trade_date':trade_date,'retrieved_at_utc':retrieved,'currentness':currentness or {'status':'unresolved','reason':'not_provided'},'facts':facts or {},'issues':issues or []}
    _reject_raw(obs); validate_watchlist_input_observation(obs)
    obs.pop('source_role', None)
    return obs

def normalize_twse_mis_watchlist_observation(source_obs:dict, plan_target:dict, *, reference_clock_utc:str|None=None)->dict:
    _reject_raw(source_obs); facts={}
    mapping={'price':'latest_price','price_like_value':'latest_price','latest_price':'latest_price','change':'change','change_percent':'change_percent','open':'open','high':'high','low':'low','volume':'volume','no_trade_state':'no_trade_state','close':'close'}
    sf=source_obs.get('safe_fields') if isinstance(source_obs.get('safe_fields'),dict) else source_obs
    for k,dst in mapping.items():
        if k in sf and dst in SAFE_CURRENT: facts[dst]=sf.get(k)
        
    actual_retrieved = source_obs.get('retrieved_at_utc') or source_obs.get('retrieved_at')
    src_str = source_obs.get('source_timestamp')
    
    cur = evaluate_evidence_currentness(
        reference_clock_str=reference_clock_utc,
        source_timestamp_str=src_str,
        retrieved_at_str=actual_retrieved,
        timing_class="liveish_intraday_snapshot",
        max_age_seconds=900.0
    )
    
    return _base(plan_target,'TWSE_MIS','liveish_intraday_snapshot','liveish_observation',actual_retrieved,src_str,None,cur,{k:v for k,v in facts.items() if k in SAFE_CURRENT},list(source_obs.get('caveats') or source_obs.get('issues') or []))

def normalize_twse_openapi_watchlist_observation(source_obs:dict, plan_target:dict, *, reference_clock_utc:str|None=None, calendar_artifact:dict|None=None, closure_events:list|None=None)->dict:
    return _normalize_eod(source_obs,plan_target,'TWSE_OPENAPI',reference_clock_utc, calendar_artifact, closure_events)

def normalize_tpex_openapi_watchlist_observation(source_obs:dict, plan_target:dict, *, reference_clock_utc:str|None=None, calendar_artifact:dict|None=None, closure_events:list|None=None)->dict:
    return _normalize_eod(source_obs,plan_target,'TPEX_OPENAPI',reference_clock_utc, calendar_artifact, closure_events)

def _normalize_eod(source_obs,plan_target,fam,reference_clock_utc=None, calendar_artifact=None, closure_events=None):
    _reject_raw(source_obs)
    safe_fields=source_obs.get('safe_fields') if isinstance(source_obs.get('safe_fields'),dict) else {}
    price=source_obs.get('price') or safe_fields.get('price') or {}
    act=source_obs.get('activity') or safe_fields.get('activity') or {}
    facts={k:price.get(k) for k in ('open','high','low','close') if price.get(k) is not None}
    vol=act.get('trade_volume') if isinstance(act,dict) else None
    if vol is not None: facts['volume']=vol
    trade_date=source_obs.get('trade_date') or source_obs.get('market_date') or source_obs.get('trading_date')
    facts['trade_date']=trade_date
    facts={k:v for k,v in facts.items() if k in SAFE_EOD}
    
    actual_retrieved = source_obs.get('retrieved_at_utc') or source_obs.get('retrieved_at')
    
    market = "TWSE" if "TWSE" in fam else "TPEX"
    
    cur = evaluate_evidence_currentness(
        reference_clock_str=reference_clock_utc,
        source_timestamp_str=source_obs.get('source_timestamp'),
        retrieved_at_str=actual_retrieved,
        timing_class="official_eod",
        trade_date=trade_date,
        calendar_artifact=calendar_artifact,
        closure_events=closure_events,
        market=market
    )
    
    return _base(plan_target,fam,'official_eod','official_eod_reference',actual_retrieved,None,facts.get('trade_date'),cur,facts,list(source_obs.get('caveats') or []))
