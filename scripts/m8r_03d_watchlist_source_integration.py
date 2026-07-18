from __future__ import annotations
from typing import Any
from scripts.m8r_03c_watchlist_bundle_builder import validate_watchlist_input_observation
SAFE_CURRENT={'latest_price','change','change_percent','open','high','low','volume','no_trade_state','close'}
SAFE_EOD={'open','high','low','close','volume','trade_date','latest_price'}
FORBIDDEN={'raw_payload','raw','headers','cookies','cookie','session_id','session_ids','authorization','body','msgArray'}

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

def normalize_twse_mis_watchlist_observation(source_obs:dict, plan_target:dict, *, retrieved_at_utc:str|None=None)->dict:
    _reject_raw(source_obs); facts={}
    mapping={'price':'latest_price','price_like_value':'latest_price','latest_price':'latest_price','change':'change','change_percent':'change_percent','open':'open','high':'high','low':'low','volume':'volume','no_trade_state':'no_trade_state','close':'close'}
    sf=source_obs.get('safe_fields') if isinstance(source_obs.get('safe_fields'),dict) else source_obs
    for k,dst in mapping.items():
        if k in sf and dst in SAFE_CURRENT: facts[dst]=sf.get(k)
        
    # 真正的新鮮度評估器推導邏輯 (Production Currentness Evaluator)
    ret_str = retrieved_at_utc or source_obs.get('retrieved_at_utc') or source_obs.get('retrieved_at')
    src_str = source_obs.get('source_timestamp')
    
    if not ret_str:
        status = "missing_currentness"
    elif not src_str:
        status = "retrieved_at_only"
    else:
        try:
            from datetime import datetime
            def parse_dt(s):
                s = s.replace("Z", "")
                if "." in s:
                    s = s.split(".")[0]
                return datetime.fromisoformat(s)
            ret_dt = parse_dt(ret_str)
            src_dt = parse_dt(src_str)
            diff = (ret_dt - src_dt).total_seconds()
            
            # 若 retrieved 與 source 時間差大於 5400 秒 (1.5小時)，判定為 stale
            if diff > 5400:
                status = "stale"
            elif diff < 0:
                status = "unresolved"
            else:
                status = "fresh"
        except Exception:
            status = "unresolved"
            
    cur={'status':status,'reason':'twse_mis_calculated_freshness'}
    return _base(plan_target,'TWSE_MIS','liveish_intraday_snapshot','liveish_observation',ret_str,src_str,None,cur,{k:v for k,v in facts.items() if k in SAFE_CURRENT},list(source_obs.get('caveats') or source_obs.get('issues') or []))

def normalize_twse_openapi_watchlist_observation(source_obs:dict, plan_target:dict)->dict:
    return _normalize_eod(source_obs,plan_target,'TWSE_OPENAPI')
def normalize_tpex_openapi_watchlist_observation(source_obs:dict, plan_target:dict)->dict:
    return _normalize_eod(source_obs,plan_target,'TPEX_OPENAPI')
def _normalize_eod(source_obs,plan_target,fam):
    _reject_raw(source_obs)
    safe_fields=source_obs.get('safe_fields') if isinstance(source_obs.get('safe_fields'),dict) else {}
    price=source_obs.get('price') or safe_fields.get('price') or {}
    act=source_obs.get('activity') or safe_fields.get('activity') or {}
    facts={k:price.get(k) for k in ('open','high','low','close') if price.get(k) is not None}
    vol=act.get('trade_volume') if isinstance(act,dict) else None
    if vol is not None: facts['volume']=vol
    facts['trade_date']=source_obs.get('trade_date') or source_obs.get('market_date') or source_obs.get('trading_date')
    facts={k:v for k,v in facts.items() if k in SAFE_EOD}
    return _base(plan_target,fam,'official_eod','official_eod_reference',source_obs.get('retrieved_at_utc'),None,facts.get('trade_date'),{'status':'official_completed_eod','reason':'latest completed EOD reference'},facts,list(source_obs.get('caveats') or []))
