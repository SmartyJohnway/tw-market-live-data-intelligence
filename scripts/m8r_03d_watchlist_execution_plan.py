from __future__ import annotations
import hashlib,json,re
from datetime import datetime,timezone
from typing import Any
from scripts.m8r_03c_conversation_contract_validator import validate_watchlist_snapshot_request, validate_watchlist_performance_request

AUTH_SCHEMA_VERSION='m8r_03d_watchlist_execution_authorization.v1'
PLAN_SCHEMA_VERSION='m8r_03d_watchlist_execution_plan.v1'
MAX_WATCHLIST_TARGETS=10
ALLOWED_SOURCE_FAMILIES={'TWSE_MIS','TWSE_OPENAPI','TPEX_OPENAPI'}

def utc_now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def canonical_json(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha256_json(v): return hashlib.sha256(canonical_json(v).encode()).hexdigest()
def canonical_request_hash(request:dict)->str: return sha256_json(request)
def _parse_utc(s):
    if not isinstance(s,str): raise ValueError('invalid_utc_timestamp')
    d=datetime.fromisoformat(s[:-1]+'+00:00' if s.endswith('Z') else s)
    if d.tzinfo is None or d.utcoffset()!=timezone.utc.utcoffset(d): raise ValueError('invalid_utc_timestamp')
    return d

def validate_authorization(auth:dict, *, request:dict, plan:dict, bundle_type:str, now_utc:str|None=None, require_network:bool=True)->dict:
    issues=[]; h=canonical_request_hash(request); fams={g['source_family'] for g in plan.get('source_call_groups',[]) if g.get('source_family')}
    if not isinstance(auth,dict) or auth.get('schema_version')!=AUTH_SCHEMA_VERSION: issues.append({'code':'invalid_authorization_schema'})
    if auth.get('authorized_request_hash')!=h: issues.append({'code':'request_hash_mismatch'})
    if bundle_type not in set(auth.get('authorized_bundle_types') or []): issues.append({'code':'unauthorized_bundle_type'})
    targets=plan.get('target_order') or []
    allowed_targets=set(auth.get('authorized_target_ids') or [])
    if allowed_targets and not set(targets).issubset(allowed_targets): issues.append({'code':'unauthorized_target'})
    if len(targets)>int(auth.get('max_target_count') or -1): issues.append({'code':'target_limit_exceeded'})
    if not fams.issubset(set(auth.get('authorized_source_families') or [])): issues.append({'code':'unauthorized_source_family'})
    for k,want in {'network_execution_allowed':True,'one_shot_only':True,'polling_allowed':False,'scheduler_allowed':False,'persistent_storage_allowed':False,'raw_payload_retention_allowed':False}.items():
        if auth.get(k) is not want: issues.append({'code':'authorization_flag_rejected','field':k})
    if require_network and auth.get('network_execution_allowed') is not True: issues.append({'code':'network_not_authorized'})
    try:
        now=_parse_utc(now_utc) if now_utc else datetime.now(timezone.utc)
        if now>=_parse_utc(auth.get('expires_at_utc')): issues.append({'code':'authorization_expired'})
        _parse_utc(auth.get('issued_at_utc'))
    except Exception: issues.append({'code':'authorization_timestamp_invalid'})
    return {'valid':not issues,'issues':issues,'request_hash':h,'authorized_source_families':sorted(auth.get('authorized_source_families') or [])}

def _rid(tid:str)->dict:
    parts=tid.split(':'); requested={'target_id':tid}
    if len(parts)!=2 or parts[0] not in {'TWSE','TPEX'} or not re.fullmatch(r'[A-Z0-9._-]{1,20}',parts[1]):
        return {'target_id':tid,'requested_identity':requested,'resolved_identity':{},'identity_status':'unresolved','market':None,'instrument_type':None,'security_code':None,'security_name':None,'lifecycle_state':'unresolved','blocking_issues':[{'code':'identity_unresolved'}]}
    market,code=parts; typ='etf' if code.startswith('00') else 'equity'
    return {'target_id':tid,'requested_identity':requested,'resolved_identity':{'target_id':tid,'symbol':code,'market':market,'instrument_type':typ,'lifecycle_state':'active'},'identity_status':'resolved','market':market,'instrument_type':typ,'security_code':code,'security_name':None,'lifecycle_state':'active','blocking_issues':[]}

def build_execution_plan(request:dict, *, bundle_type:str, generated_at_utc:str|None=None)->dict:
    req=validate_watchlist_snapshot_request(request) if bundle_type=='snapshot' else validate_watchlist_performance_request(request)
    ids=list(req['persistent_watchlist_reference']['enabled_target_ids'])
    targets=[]; groups=[]; issues=[]
    if len(ids)>MAX_WATCHLIST_TARGETS: issues.append({'code':'target_limit_exceeded','max_target_count':MAX_WATCHLIST_TARGETS})
    for i,tid in enumerate(ids):
        r=_rid(tid); cur={}; eod={}; expected='unavailable'
        if r['identity_status']=='resolved':
            expected='usable'; market=r['market']; code=r['security_code']
            if bundle_type=='snapshot': cur={'source_family':'TWSE_MIS','route':('tse_' if market=='TWSE' else 'otc_')+code.lower()+'.tw','operation_class':'planned_network_fetch'}
            eodfam='TWSE_OPENAPI' if market=='TWSE' else 'TPEX_OPENAPI'; eod={'source_family':eodfam,'route':eodfam,'operation_class':'planned_network_fetch'}
            if cur: groups.append({'source_family':'TWSE_MIS','context_type':'liveish_observation','target_ids':[tid],'network_required':True})
            groups.append({'source_family':eodfam,'context_type':'official_eod_reference','target_ids':[tid],'network_required':True,'history_window':_history_window(req) if bundle_type=='performance' else {'latest_completed_eod_only':True}})
        targets.append({**r,'current_source_plan':cur,'eod_source_plan':eod,'expected_coverage':expected})
    # merge deterministic groups
    merged={}
    for g in groups:
        k=(g['source_family'],g['context_type'],canonical_json(g.get('history_window',{})))
        merged.setdefault(k,{**g,'target_ids':[]})['target_ids'].extend(g['target_ids'])
    groups=[{**v,'target_ids':sorted(v['target_ids'], key=ids.index)} for k,v in sorted(merged.items())]
    base={'schema_version':PLAN_SCHEMA_VERSION,'request_id':req['request_id'],'request_hash':canonical_request_hash(req),'bundle_type':bundle_type,'target_order':ids,'targets':targets,'source_call_groups':groups,'network_required':bool(groups),'authorization_required':True,'max_target_count':MAX_WATCHLIST_TARGETS,'issues':issues}
    base['plan_id']='m8r03d-plan-'+sha256_json({k:base[k] for k in ('request_id','request_hash','bundle_type','target_order','targets','source_call_groups')})[:16]
    base['created_at_utc']=generated_at_utc or utc_now(); return base

def _history_window(req):
    days=req['conversation_intent']['time_scope'].get('lookback_trading_days') or 20
    need={1:2,5:6,10:11,20:21}.get(days, min(21, days+1 if isinstance(days,int) else 21))
    return {'requested_lookback_trading_days':days,'minimum_valid_closes':need,'buffer_trading_days':5,'bounded':True}
