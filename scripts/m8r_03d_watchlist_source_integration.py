from __future__ import annotations
from typing import Any
from scripts.m8r_03c_watchlist_bundle_builder import validate_watchlist_input_observation
SAFE_CURRENT={'latest_price','change','change_percent','open','high','low','volume','no_trade_state','close'}
SAFE_EOD={'open','high','low','close','volume','trade_date','latest_price'}
FORBIDDEN={'raw_payload','raw','headers','cookies','cookie','session_id','session_ids','authorization','body','msgArray'}

from datetime import datetime, timezone, timedelta

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
    trade_date: str | None = None
) -> dict:
    if not reference_clock_str:
        return {"status": "unresolved", "reason": "missing_reference_clock"}
    try:
        ref_dt = parse_iso_datetime(reference_clock_str)
    except Exception:
        return {"status": "unresolved", "reason": "invalid_reference_clock"}
        
    eff_dt = None
    if timing_class == "liveish_intraday_snapshot":
        ts_str = source_timestamp_str or retrieved_at_str
        if not ts_str:
            return {"status": "unresolved", "reason": "missing_evidence_timestamp"}
        try:
            eff_dt = parse_iso_datetime(ts_str)
        except Exception:
            return {"status": "unresolved", "reason": "invalid_evidence_timestamp"}
    elif timing_class == "official_eod":
        if not trade_date:
            return {"status": "unresolved", "reason": "missing_trade_date"}
        try:
            eff_dt = parse_iso_datetime(f"{trade_date}T05:30:00Z")
        except Exception:
            return {"status": "unresolved", "reason": "invalid_trade_date"}
    else:
        ts_str = source_timestamp_str or retrieved_at_str
        if not ts_str:
            return {"status": "unresolved", "reason": "missing_evidence_timestamp"}
        try:
            eff_dt = parse_iso_datetime(ts_str)
        except Exception:
            return {"status": "unresolved", "reason": "invalid_evidence_timestamp"}

    age_seconds = (ref_dt - eff_dt).total_seconds()
    latency_seconds = None
    if retrieved_at_str and source_timestamp_str:
        try:
            ret_dt = parse_iso_datetime(retrieved_at_str)
            src_dt = parse_iso_datetime(source_timestamp_str)
            latency_seconds = (ret_dt - src_dt).total_seconds()
        except Exception:
            pass

    if age_seconds < 0:
        status = "unresolved"
        reason = "evidence_timestamp_in_future"
    else:
        if timing_class == "liveish_intraday_snapshot":
            if age_seconds > max_age_seconds:
                status = "stale"
                reason = f"evidence_age_exceeds_max_limit:{int(age_seconds)}s"
            else:
                status = "fresh"
                reason = "evidence_within_freshness_limit"
        elif timing_class == "official_eod":
            if age_seconds > 259200.0:
                status = "stale"
                reason = "eod_older_than_three_days"
            else:
                status = "official_completed_eod"
                reason = "latest completed EOD reference"
        else:
            status = "fresh"
            reason = "default_freshness_status"

    result = {"status": status, "reason": reason, "age_seconds": age_seconds}
    if latency_seconds is not None:
        result["transport_latency_seconds"] = latency_seconds
    return result

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

def normalize_twse_openapi_watchlist_observation(source_obs:dict, plan_target:dict, *, reference_clock_utc:str|None=None)->dict:
    return _normalize_eod(source_obs,plan_target,'TWSE_OPENAPI',reference_clock_utc)

def normalize_tpex_openapi_watchlist_observation(source_obs:dict, plan_target:dict, *, reference_clock_utc:str|None=None)->dict:
    return _normalize_eod(source_obs,plan_target,'TPEX_OPENAPI',reference_clock_utc)

def _normalize_eod(source_obs,plan_target,fam,reference_clock_utc=None):
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
    
    cur = evaluate_evidence_currentness(
        reference_clock_str=reference_clock_utc,
        source_timestamp_str=source_obs.get('source_timestamp'),
        retrieved_at_str=actual_retrieved,
        timing_class="official_eod",
        trade_date=trade_date
    )
    
    return _base(plan_target,fam,'official_eod','official_eod_reference',actual_retrieved,None,facts.get('trade_date'),cur,facts,list(source_obs.get('caveats') or []))
