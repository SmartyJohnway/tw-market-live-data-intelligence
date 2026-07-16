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
    status=source_obs.get('currentness',{}).get('status') if isinstance(source_obs.get('currentness'),dict) else None
    status=status or ({'live_candidate':'fresh','delayed':'acceptable','stale':'stale','unknown':'unresolved'}.get(source_obs.get('freshness_status')) or ('stale' if source_obs.get('reference_only') else 'fresh'))
    cur={'status':status,'reason':source_obs.get('delay_status') or source_obs.get('price_semantics') or 'twse_mis_normalized'}
    return _base(plan_target,'TWSE_MIS','liveish_intraday_snapshot','liveish_observation',retrieved_at_utc or source_obs.get('retrieved_at_utc') or source_obs.get('retrieved_at'),source_obs.get('source_timestamp'),None,cur,{k:v for k,v in facts.items() if k in SAFE_CURRENT},list(source_obs.get('caveats') or source_obs.get('issues') or []))

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
