from __future__ import annotations
import hashlib,json,re
from datetime import datetime,timezone
from typing import Any
from scripts.m8r_03c_conversation_contract_validator import validate_watchlist_snapshot_request, validate_watchlist_performance_request, assert_no_forbidden_keys
from scripts.m8a_official_eod_instrument_classifier import build_security_master_lookup, normalize_market as _sm_market, normalize_instrument_type
from scripts.m8r_03d_f1_security_master_snapshot_adapter import ValidatedVerifiedSecurityMasterSnapshot, load_verified_security_master_snapshot, resolve_verified_security_identity, VerifiedSecurityMasterSnapshotError

AUTH_SCHEMA_VERSION='m8r_03d_watchlist_execution_authorization.v1'
PLAN_SCHEMA_VERSION='m8r_03d_watchlist_execution_plan.v1'
MAX_WATCHLIST_TARGETS=10
ALLOWED_SOURCE_FAMILIES={'TWSE_MIS','TWSE_OPENAPI','TPEX_OPENAPI'}
AUTH_ALLOWED_FIELDS={'schema_version','authorization_id','issued_at_utc','expires_at_utc','authorized_request_hash','authorized_bundle_types','authorized_source_families','authorized_target_ids','max_target_count','network_execution_allowed','one_shot_only','one_shot_nonce','polling_allowed','scheduler_allowed','persistent_storage_allowed','raw_payload_retention_allowed','operator_approval'}
BUNDLE_TYPES={'snapshot','performance'}
BLOCKING_PLAN_CODES={'target_limit_exceeded','market_mismatch','unsupported_instrument','invalid_request','authorization_planning_inconsistency'}

def utc_now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def canonical_json(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha256_json(v): return hashlib.sha256(canonical_json(v).encode()).hexdigest()
def canonical_request_hash(request:dict)->str: return sha256_json(request)
def _parse_utc(s):
    if not isinstance(s,str): raise ValueError('invalid_utc_timestamp')
    d=datetime.fromisoformat(s[:-1]+'+00:00' if s.endswith('Z') else s)
    if d.tzinfo is None or d.utcoffset()!=timezone.utc.utcoffset(d): raise ValueError('invalid_utc_timestamp')
    return d

def _issue(code, **extra):
    return {'code': code, **extra}

def _non_empty_unique_str_list(value, field, allowed=None):
    if not isinstance(value, list) or not value:
        return None, [_issue('authorization_field_invalid', field=field)]
    if not all(isinstance(x, str) and x.strip() for x in value):
        return None, [_issue('authorization_field_invalid', field=field)]
    if len(value) != len(set(value)):
        return None, [_issue('authorization_duplicate_value', field=field)]
    if allowed is not None and not set(value).issubset(allowed):
        return None, [_issue('authorization_enum_invalid', field=field)]
    return value, []

def validate_authorization(auth:dict, *, request:dict, plan:dict, bundle_type:str, now_utc:str|None=None, require_network:bool=True)->dict:
    issues=[]; h=canonical_request_hash(request); fams={g['source_family'] for g in plan.get('source_call_groups',[]) if g.get('source_family')}
    try: assert_no_forbidden_keys(auth)
    except Exception as exc: issues.append(_issue('authorization_forbidden_key', detail=str(exc)[:120]))
    if not isinstance(auth,dict):
        return {'valid':False,'issues':[_issue('invalid_authorization_schema')],'request_hash':h,'authorized_source_families':[]}
    unknown=sorted(set(auth)-AUTH_ALLOWED_FIELDS)
    if unknown: issues.append(_issue('authorization_unknown_field', field=unknown[0]))
    if auth.get('schema_version')!=AUTH_SCHEMA_VERSION: issues.append(_issue('invalid_authorization_schema'))
    for field in ('authorization_id','one_shot_nonce'):
        if not isinstance(auth.get(field),str) or not auth.get(field).strip(): issues.append(_issue('authorization_field_invalid', field=field))
    if not isinstance(auth.get('authorized_request_hash'),str) or not re.fullmatch(r'[0-9a-f]{64}', auth.get('authorized_request_hash') or ''): issues.append(_issue('authorization_field_invalid', field='authorized_request_hash'))
    elif auth.get('authorized_request_hash')!=h: issues.append(_issue('request_hash_mismatch'))
    bundles, e = _non_empty_unique_str_list(auth.get('authorized_bundle_types'), 'authorized_bundle_types', BUNDLE_TYPES); issues.extend(e)
    sources, e = _non_empty_unique_str_list(auth.get('authorized_source_families'), 'authorized_source_families', ALLOWED_SOURCE_FAMILIES); issues.extend(e)
    targets_allowed, e = _non_empty_unique_str_list(auth.get('authorized_target_ids'), 'authorized_target_ids'); issues.extend(e)
    if bundles and bundle_type not in set(bundles): issues.append(_issue('unauthorized_bundle_type'))
    targets=plan.get('target_order') or []
    if targets_allowed and not set(targets).issubset(set(targets_allowed)): issues.append(_issue('unauthorized_target'))
    if not isinstance(auth.get('max_target_count'), int) or auth.get('max_target_count') <= 0: issues.append(_issue('authorization_field_invalid', field='max_target_count'))
    elif len(targets)>auth.get('max_target_count'): issues.append(_issue('target_limit_exceeded'))
    if sources and not fams.issubset(set(sources)): issues.append(_issue('unauthorized_source_family'))
    for k,want in {'network_execution_allowed':True,'one_shot_only':True,'polling_allowed':False,'scheduler_allowed':False,'persistent_storage_allowed':False,'raw_payload_retention_allowed':False}.items():
        if auth.get(k) is not want: issues.append(_issue('authorization_flag_rejected', field=k))
    if not isinstance(auth.get('operator_approval'), dict): issues.append(_issue('authorization_field_invalid', field='operator_approval'))
    else:
        try: assert_no_forbidden_keys(auth.get('operator_approval'))
        except Exception as exc: issues.append(_issue('authorization_forbidden_key', field='operator_approval', detail=str(exc)[:120]))
    try:
        issued=_parse_utc(auth.get('issued_at_utc')); expires=_parse_utc(auth.get('expires_at_utc'))
        now=_parse_utc(now_utc) if now_utc else datetime.now(timezone.utc)
        if expires <= issued: issues.append(_issue('authorization_expiry_invalid'))
        if now>=expires: issues.append(_issue('authorization_expired'))
    except Exception: issues.append(_issue('authorization_timestamp_invalid'))
    if require_network and auth.get('network_execution_allowed') is not True: issues.append(_issue('network_not_authorized'))
    if any(i.get('blocking') for i in plan.get('issues', [])): issues.append(_issue('authorization_planning_inconsistency'))
    return {'valid':not issues,'issues':issues,'request_hash':h,'authorized_source_families':sorted(auth.get('authorized_source_families') or [])}

def _market_to_canonical(prefix):
    return {'TWSE':'listed','TPEX':'tpex_otc'}.get(prefix)
def _canonical_to_prefix(canonical):
    return {'listed':'TWSE','tpex_otc':'TPEX'}.get(canonical)
def _lookup_entry(lookup, canonical_market, code):
    return lookup.get((canonical_market, code)) or lookup.get(f'{canonical_market}:{code}') or lookup.get(code)
def _resolve_verified_security(tid: str, snapshot_lookup, *, allow_fixture_snapshot: bool=False) -> dict:
    parts=tid.split(':'); requested={'target_id':tid}
    market_context=parts[0] if len(parts)==2 else None
    rr=resolve_verified_security_identity(tid, snapshot_lookup, market_context=market_context, allow_fixture_snapshot=allow_fixture_snapshot, execute_mode=True)
    sel=rr.get('selected') or {}
    if rr.get('resolution_status')!='resolved':
        code = {'ambiguous':'identity_conflict','quarantined':'lifecycle_unsupported' if 'fixture_observation_only_rejected' in rr.get('reason_codes',[]) else 'identity_conflict','not_found':'identity_unresolved'}.get(rr.get('resolution_status'),'identity_unresolved')
        return {'target_id':tid,'security_code':parts[1] if len(parts)==2 else None,'security_name':None,'canonical_market':_market_to_canonical(market_context),'instrument_type':None,'listing_status':None,'lifecycle_state':'unresolved','lifecycle_resolution_status':'unavailable','resolution_status':code,'resolution_evidence':[{'source':'verified_security_master_snapshot','resolution':rr}],'requested_identity':requested}
    ident=sel.get('identity') or {}; cls=sel.get('classification') or {}; life=sel.get('lifecycle') or {}; elig=sel.get('execution_eligibility') or {}
    canonical=_market_to_canonical(cls.get('market')); typ=cls.get('instrument_type')
    status='resolved'; caveats=list(sel.get('caveats') or [])
    if canonical != _market_to_canonical(market_context): status='market_mismatch'
    elif elig.get('status')=='blocked': status='lifecycle_unsupported' if 'lifecycle_blocks_current_execution' in elig.get('reason_codes',[]) or 'fixture_observation_only' in elig.get('reason_codes',[]) else 'unsupported_instrument' if 'unsupported_instrument_type' in elig.get('reason_codes',[]) else 'identity_conflict'
    elif elig.get('status')=='allowed_with_caveat': caveats += elig.get('reason_codes',[])
    execution_policy='execution_allowed' if elig.get('status')=='allowed' else 'execution_allowed_with_caveat' if elig.get('status')=='allowed_with_caveat' else 'execution_blocked'
    return {'target_id':tid,'security_code':ident.get('security_code'),'security_name':ident.get('security_name_zh') or ident.get('security_name_en'),'canonical_market':canonical,'instrument_type':typ,'listing_status':life.get('state'),'lifecycle_state':life.get('state'),'lifecycle_resolution_status':life.get('resolution_status'),'execution_policy':execution_policy,'resolution_caveats':caveats,'resolution_status':status,'snapshot_id':sel.get('snapshot_id'),'record_id':sel.get('record_id'),'record_hash':sel.get('record_hash'),'classification_status':cls.get('classification_status'),'classification_execution_policy':sel.get('classification_execution_policy'),'execution_eligibility':elig,'resolution_evidence':[{'source':'verified_security_master_snapshot','snapshot_id':sel.get('snapshot_id'),'record_id':sel.get('record_id'),'record_hash':sel.get('record_hash'),'resolution_reason':sel.get('resolution_reason')}], 'requested_identity':requested}

def _resolve_security(tid: str, security_master=None, *, allow_fixture_snapshot: bool=False) -> dict:
    if isinstance(security_master, ValidatedVerifiedSecurityMasterSnapshot):
        return _resolve_verified_security(tid, security_master.lookup, allow_fixture_snapshot=allow_fixture_snapshot)
    if isinstance(security_master, dict) and (security_master.get('schema_version')=='tw_verified_security_master_snapshot.v1' or (security_master.get('snapshot') and security_master.get('by_canonical') is not None)):
        raise VerifiedSecurityMasterSnapshotError('unvalidated_verified_snapshot_injection_rejected')
    parts=tid.split(':'); requested={'target_id':tid}; evidence=[]
    if len(parts)!=2 or parts[0] not in {'TWSE','TPEX'} or not re.fullmatch(r'[A-Z0-9._-]{1,20}',parts[1]):
        return {'target_id':tid,'security_code':None,'security_name':None,'canonical_market':None,'instrument_type':None,'listing_status':None,'lifecycle_state':'unresolved','resolution_status':'identity_unresolved','resolution_evidence':[{'code':'invalid_target_id'}],'requested_identity':requested}
    prefix, code=parts; requested_market=_market_to_canonical(prefix)
    lookup=security_master if security_master is not None else build_security_master_lookup()
    found=[]
    for market in ('listed','tpex_otc'):
        entry=_lookup_entry(lookup, market, code) if isinstance(lookup, dict) else None
        if isinstance(entry, str): entry={'instrument_type':entry}
        if isinstance(entry, dict): found.append((market, entry))
    if not found:
        return {'target_id':tid,'security_code':code,'security_name':None,'canonical_market':None,'instrument_type':None,'listing_status':None,'lifecycle_state':'unknown','lifecycle_resolution_status':'unavailable','resolution_status':'identity_unresolved','resolution_evidence':[{'code':'security_master_miss','requested_market':requested_market}],'requested_identity':requested}
    exact=[(m,e) for m,e in found if m==requested_market]
    if not exact:
        canonical_market, entry = found[0]
    elif len(found)>1 and not exact[0][1].get('cross_market_duplicate_policy') == 'exact_requested_market_ok':
        return {'target_id':tid,'security_code':code,'security_name':None,'canonical_market':requested_market,'instrument_type':None,'listing_status':None,'lifecycle_state':'unknown','lifecycle_resolution_status':'unavailable','resolution_status':'identity_conflict','resolution_evidence':[{'code':'cross_market_duplicate','markets':[m for m,_ in found]}],'requested_identity':requested}
    else:
        canonical_market, entry = exact[0]
    typ=normalize_instrument_type(entry.get('instrument_type')) or entry.get('instrument_type')
    lifecycle_supplied='lifecycle_state' in entry or 'listing_status' in entry
    lifecycle=entry.get('lifecycle_state') or entry.get('listing_status') if lifecycle_supplied else 'unknown'
    listing=entry.get('listing_status')
    lifecycle_status='resolved' if lifecycle_supplied else 'unavailable'
    execution_policy='execution_allowed'
    caveats=[]
    status='resolved'
    if canonical_market != requested_market: status='market_mismatch'
    elif typ not in {'equity','etf'}: status='unsupported_instrument'
    elif lifecycle_supplied and lifecycle not in {'active','listed','trading'}: status='lifecycle_unsupported'
    elif not lifecycle_supplied:
        execution_policy='execution_allowed_with_caveat'; caveats.append('lifecycle_evidence_unavailable_not_assumed_active')
    return {'target_id':tid,'security_code':code,'security_name':entry.get('security_name') or entry.get('name'),'canonical_market':canonical_market,'instrument_type':typ,'listing_status':listing,'lifecycle_state':lifecycle,'lifecycle_resolution_status':lifecycle_status,'execution_policy':execution_policy,'resolution_caveats':caveats,'resolution_status':status,'resolution_evidence':[{'source':entry.get('source'),'provenance':entry.get('provenance'),'coverage_mode':entry.get('coverage_mode')}], 'requested_identity':requested}

def _target_from_resolution(res: dict) -> dict:
    status=res['resolution_status']; canonical=res.get('canonical_market'); prefix=_canonical_to_prefix(canonical) if canonical else None
    issues=[]
    if status!='resolved': issues.append(_issue(status, blocking=status in {'market_mismatch','unsupported_instrument','lifecycle_unsupported','identity_conflict'}, target_id=res['target_id']))
    for caveat in res.get('resolution_caveats') or []: issues.append(_issue(caveat, blocking=False, target_id=res['target_id']))
    resolved={'target_id':res['target_id'],'symbol':res.get('security_code'),'market':prefix,'canonical_market':canonical,'instrument_type':res.get('instrument_type'),'security_name':res.get('security_name'),'listing_status':res.get('listing_status'),'lifecycle_state':res.get('lifecycle_state'),'lifecycle_resolution_status':res.get('lifecycle_resolution_status'),'execution_policy':res.get('execution_policy'),'resolution_caveats':res.get('resolution_caveats') or [],'snapshot_id':res.get('snapshot_id'),'record_id':res.get('record_id'),'record_hash':res.get('record_hash'),'classification_status':res.get('classification_status'),'execution_eligibility':res.get('execution_eligibility')} if status=='resolved' else {}
    return {'target_id':res['target_id'],'requested_identity':res.get('requested_identity') or {'target_id':res['target_id']},'resolved_identity':resolved,'identity_status':'resolved' if status=='resolved' else status,'market':prefix,'canonical_market':canonical,'instrument_type':res.get('instrument_type'),'security_code':res.get('security_code'),'security_name':res.get('security_name'),'listing_status':res.get('listing_status'),'lifecycle_state':res.get('lifecycle_state'),'lifecycle_resolution_status':res.get('lifecycle_resolution_status'),'execution_policy':res.get('execution_policy'),'resolution_caveats':res.get('resolution_caveats') or [],'resolution_status':status,'snapshot_id':res.get('snapshot_id'),'record_id':res.get('record_id'),'record_hash':res.get('record_hash'),'classification_status':res.get('classification_status'),'classification_execution_policy':res.get('classification_execution_policy'),'execution_eligibility':res.get('execution_eligibility'),'resolution_evidence':res.get('resolution_evidence') or [],'blocking_issues':issues}

def build_execution_plan(request:dict, *, bundle_type:str, generated_at_utc:str|None=None, security_master=None, verified_snapshot_path:str|None=None, verified_snapshot_manifest_path:str|None=None, allow_fixture_snapshot:bool=False)->dict:
    req=validate_watchlist_snapshot_request(request) if bundle_type=='snapshot' else validate_watchlist_performance_request(request)
    if verified_snapshot_path or verified_snapshot_manifest_path:
        if not (verified_snapshot_path and verified_snapshot_manifest_path): raise VerifiedSecurityMasterSnapshotError('snapshot_and_manifest_required')
        security_master=load_verified_security_master_snapshot(verified_snapshot_path, verified_snapshot_manifest_path, allow_fixture_snapshot=allow_fixture_snapshot)
    ids=list(req['persistent_watchlist_reference']['enabled_target_ids'])
    targets=[]; groups=[]; issues=[]
    if len(ids)>MAX_WATCHLIST_TARGETS: issues.append({'code':'target_limit_exceeded','max_target_count':MAX_WATCHLIST_TARGETS,'blocking':True})
    for i,tid in enumerate(ids):
        r=_target_from_resolution(_resolve_security(tid, security_master, allow_fixture_snapshot=allow_fixture_snapshot)); cur={}; eod={}; expected='unavailable'
        if r['identity_status']=='resolved':
            expected='usable'; market=r['market']; code=r['security_code']
            if bundle_type=='snapshot': cur={'source_family':'TWSE_MIS','route':('tse_' if market=='TWSE' else 'otc_')+code.lower()+'.tw','operation_class':'planned_network_fetch'}
            eodfam='TWSE_OPENAPI' if market=='TWSE' else 'TPEX_OPENAPI'; eod={'source_family':eodfam,'route':eodfam,'operation_class':'planned_network_fetch'}
            if cur: groups.append({'source_family':'TWSE_MIS','context_type':'liveish_observation','target_ids':[tid],'network_required':True})
            groups.append({'source_family':eodfam,'context_type':'official_eod_reference','target_ids':[tid],'network_required':True,'history_window':_history_window(req) if bundle_type=='performance' else {'latest_completed_eod_only':True}})
        targets.append({**r,'current_source_plan':cur,'eod_source_plan':eod,'expected_coverage':expected}); issues.extend(r.get('blocking_issues', []))
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

def plan_has_blocking_issues(plan: dict) -> bool:
    return any(i.get('blocking') or i.get('code') in BLOCKING_PLAN_CODES for i in plan.get('issues', []))
