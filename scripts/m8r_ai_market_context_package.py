from __future__ import annotations

import json, os, tempfile, hashlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.m8r_bounded_market_context_request import canonical_json, load_source_registry
from scripts.m8r_one_shot_market_context_orchestrator import RESULT_SCHEMA_VERSION, RECEIPT_SCHEMA_VERSION, LOCAL_CLASSES

SCHEMA_VERSION = "ai_market_context.v1"
FORBIDDEN_KEYS = {"raw_payload","response_body","html","cookies","cookie","authorization","api_key","access_token","refresh_token","secret","password","full_market_rows","full_market_data"}
ALLOWED_SOURCES = {"TWSE_MIS","TWSE_OPENAPI","TPEX_OPENAPI","TAIFEX_MIS","TAIFEX_OPENAPI","LOCAL_CONTEXT","LOCAL_SOURCE_HEALTH","LOCAL_MARKET_CLOCK"}
STATUS_ORDER = {"ready":0,"ready_with_caveats":1,"partial":2,"blocked":3}
BASE_FORBIDDEN = ["not_full_market","not_trading_signal","not_prediction","not_recommendation","not_broker_instruction","not_guaranteed_realtime","not_live_production_ready_without_m8r02a","not_safe_to_infer_missing_values"]
PROD = {"package_schema_ready": True, "offline_packaging_ready": True, "production_orchestrator_contract_ready": True, "production_executor_adapters_ready": False, "production_live_execution_ready": False, "m8r_02a_required": True, "live_validation_completed": False}

class AIMarketContextPackageError(ValueError): pass

def utc_now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def assert_no_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            if str(k).lower() in FORBIDDEN_KEYS:
                raise AIMarketContextPackageError(f"forbidden_raw_key:{path}.{k}")
            assert_no_forbidden_keys(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value): assert_no_forbidden_keys(v, f"{path}[{i}]")

def _sorted(items): return sorted(items, key=lambda x: canonical_json(x))
def _list(v): return v if isinstance(v, list) else ([] if v is None else [v])
def _targets(orchestration):
    plan = orchestration.get('preflight',{}).get('plan') or orchestration.get('plan') or {}
    receipt = orchestration.get('execution_receipt') or {}
    # M8R-02 results commonly omit the plan; infer bounded targets from operation results when needed.
    ts = plan.get('targets') or []
    if not ts:
        seen={}
        for r in orchestration.get('operation_results') or []:
            tid=r.get('target_id'); obs=r.get('source_observation') or {}
            if tid and tid not in seen:
                parts=str(tid).split(':')
                seen[tid]={"target_id":tid,"market":obs.get('market') or (parts[0] if len(parts)>0 else None),"instrument_type":obs.get('instrument_type') or (parts[1] if len(parts)>1 else None),"symbol":obs.get('symbol') or (parts[2] if len(parts)>2 else None),"requested_context_types":[] ,"derivative_identity":obs.get('safe_fields',{}).get('contract_identity') or {}}
        ts=list(seen.values())
    return ts

def _plan_meta(orchestration):
    r=orchestration.get('execution_receipt') or {}; a=orchestration.get('approval_state') or {}
    return {"request_id": orchestration.get('request_id') or a.get('request_id'), "plan_id": r.get('plan_id'), "plan_hash": r.get('plan_hash'), "approval_id": r.get('approval_id'), "receipt_id": r.get('receipt_id'), "orchestration_result_schema": orchestration.get('schema_version'), "execution_started_at_utc": r.get('execution_started_at_utc'), "execution_finished_at_utc": r.get('execution_finished_at_utc'), "approval_consumed": bool(r.get('approval_consumed')), "approved_output_scope": r.get('approved_output_scope') or {}, "bounded_retention": r.get('bounded_retention') is True, "raw_payload_retained": r.get('raw_payload_retained') is True, "full_market_retained_output": r.get('full_market_retained_output') is True}

def build_source_context_views(orchestration):
    out=[]
    for r in orchestration.get('operation_results') or []:
        if r.get('status')!='succeeded' or r.get('operation_class') in LOCAL_CLASSES: continue
        obs=deepcopy(r.get('source_observation') or {})
        if not obs: continue
        ctx={"source_context_id":"amc-src-"+hashlib.sha256(canonical_json({"op":r.get('operation_id'),"target":r.get('target_id'),"source":r.get('source_family'),"context":r.get('context_type')}).encode()).hexdigest()[:16],"target_id":r.get('target_id'),"operation_id":r.get('operation_id'),"source_id":obs.get('source_id') or r.get('source_family'),"source_family":obs.get('source_family') or r.get('source_family'),"market":obs.get('market'),"symbol":obs.get('symbol'),"instrument_type":obs.get('instrument_type'),"context_type":obs.get('context_type') or r.get('context_type'),"authority_level":obs.get('authority_level'),"timing_class":obs.get('timing_class'),"source_timestamp":obs.get('source_timestamp') or (obs.get('safe_fields') or {}).get('source_time',{}).get('source_timestamp'),"retrieved_at_utc":obs.get('retrieved_at_utc'),"currentness":r.get('currentness') or obs.get('currentness') or (obs.get('safe_fields') or {}).get('currentness') or {"status":obs.get('overall_ai_currentness')},"safe_fields":deepcopy(obs.get('safe_fields') or {}),"caveats":sorted(set(_list(obs.get('caveats'))+_list(r.get('issues'))))}
        out.append(ctx)
    return _sorted(out)

def build_local_views(orchestration):
    health=[]; sessions=[]
    for r in orchestration.get('operation_results') or []:
        obs=r.get('source_observation') or {}; sf=obs.get('safe_fields') or {}
        if obs.get('source_id')=='LOCAL_SOURCE_HEALTH':
            health.append({"target_id":r.get('target_id'),"operation_id":r.get('operation_id'),"referenced_source_family":sf.get('referenced_source_family'),"artifact_availability":sf.get('artifact_availability'),"record_timestamp":obs.get('retrieved_at_utc'),"staleness_caveat":sf.get('staleness_caveat'),"local_only":True})
        if obs.get('source_id')=='LOCAL_MARKET_CLOCK':
            sessions.append({"target_id":r.get('target_id'),"operation_id":r.get('operation_id'),"target_market":sf.get('target_market') or obs.get('market'),"market_session_state":sf.get('market_session_state'),"calendar_evidence":sf.get('calendar_evidence'),"session_caveat":sf.get('calendar_caveat') or '; '.join(_list(obs.get('caveats'))),"resolution_status":"unresolved" if sf.get('market_session_state') in (None,'unresolved') else "resolved"})
    return _sorted(sessions), _sorted(health)

def _currentness_status(c):
    if isinstance(c, dict):
        return c.get('overall_status') or c.get('status') or c.get('freshness_assessment') or c.get('overall_ai_currentness') or 'unknown'
    return 'unknown'

def build_currentness_summary(source_contexts):
    counts={"unknown_count":0,"stale_count":0,"current_count":0}; by_sf={}; by_t={}
    for c in source_contexts:
        st=str(_currentness_status(c.get('currentness')))
        bucket='unknown'
        if 'stale' in st: bucket='stale'
        elif any(x in st for x in ('current','fresh','active_session_fresh')) and 'unresolved' not in st: bucket='current'
        counts[bucket+'_count']+=1
        by_sf.setdefault(c.get('source_family'),[]).append(st); by_t.setdefault(c.get('target_id'),[]).append(st)
    present=[k for k,v in counts.items() if v]
    overall='not_applicable' if not source_contexts else ('mixed' if len(present)>1 else present[0].replace('_count',''))
    return {"overall_status": overall, "by_source_family": {k:sorted(set(v)) for k,v in by_sf.items()}, "by_target": {k:sorted(set(v)) for k,v in by_t.items()}, **counts}

def _missing(orchestration):
    return _sorted([{ "target_id":m.get('target_id'),"context_type":m.get('context_type'),"planned_source_family":m.get('planned_source_family'),"reason_code":m.get('reason_code'),"operation_status":m.get('operation_status'),"usable_fallback":None,"forbidden_interpretations":sorted(set(_list(m.get('forbidden_interpretations'))+["not_safe_to_infer_missing_values"]))} for m in orchestration.get('missing_context') or []])

def build_forbidden_interpretations(pkg):
    codes=set(BASE_FORBIDDEN)
    if pkg.get('package_status') in {'partial','blocked'}: codes.add('not_complete_when_partial')
    if pkg.get('currentness_summary',{}).get('overall_status') in {'mixed','unknown','stale'}: codes.add('not_all_sources_current')
    for c in pkg.get('source_contexts',[]):
        if c.get('timing_class')=='official_eod': codes.add('official_eod_not_live')
        if c.get('timing_class')=='liveish_intraday_snapshot': codes.add('liveish_not_official_realtime')
    if pkg.get('source_health_context'): codes.add('local_health_not_live_probe')
    if any(s.get('resolution_status')=='unresolved' for s in pkg.get('market_session_context',[])): codes.add('unresolved_session_not_open_or_closed')
    return sorted(codes)

def build_caveats(pkg, unsafe_reason=None):
    cav=[]
    def add(code,severity='warning',scope='package',**kw): cav.append({"code":code,"severity":severity,"scope":scope,"message":code.replace('_',' '), **{k:v for k,v in kw.items() if v is not None}})
    add('production_executor_adapter_not_ready'); add('production_live_execution_not_ready')
    if unsafe_reason: add(unsafe_reason,'blocking')
    if pkg.get('missing_context'): add('missing_context'); add('partial_context')
    if pkg.get('currentness_summary',{}).get('unknown_count'): add('currentness_unknown')
    if pkg.get('currentness_summary',{}).get('stale_count'): add('source_stale')
    for s in pkg.get('market_session_context',[]):
        if s.get('resolution_status')=='unresolved': add('market_session_unresolved', target_id=s.get('target_id'))
    for h in pkg.get('source_health_context',[]): add('source_health_not_live_probe', source_family=h.get('referenced_source_family'))
    for c in pkg.get('source_contexts',[]):
        if c.get('timing_class')=='official_eod': add('official_eod_not_intraday', source_family=c.get('source_family'))
        if c.get('timing_class')=='liveish_intraday_snapshot': add('liveish_not_exchange_official_realtime', source_family=c.get('source_family'))
        if 'stale' in str(_currentness_status(c.get('currentness'))): add('source_stale','warning','source',target_id=c.get('target_id'),source_family=c.get('source_family'))
    if any((t.get('market')=='TAIFEX') for t in pkg.get('targets',[])): add('taifex_exact_contract_required')
    if (pkg.get('provenance') or {}).get('m8_context_core_status')=='build_failed': add('m8_context_core_unavailable')
    return _sorted({canonical_json(x):x for x in cav}.values())

def build_target_views(orchestration, source_contexts, missing):
    refs={}; avail={}
    for c in source_contexts: refs.setdefault(c['target_id'],[]).append(c['source_context_id']); avail.setdefault(c['target_id'],set()).add(c['context_type'])
    miss={}
    for m in missing: miss.setdefault(m['target_id'],set()).add(m['context_type'])
    out=[]
    for t in _targets(orchestration):
        tid=t.get('target_id') or ':'.join(str(t.get(k,'')) for k in ('market','instrument_type','symbol'))
        status='partial' if miss.get(tid) else ('ready_with_caveats' if refs.get(tid) else 'blocked')
        out.append({"target_id":tid,"market":t.get('market'),"symbol":t.get('symbol'),"instrument_type":t.get('instrument_type'),"derivative_identity":deepcopy(t.get('derivative_identity') or {}),"requested_context_types":sorted(set(t.get('requested_context_types') or list(avail.get(tid,set())|miss.get(tid,set())))),"available_context_types":sorted(avail.get(tid,set())),"missing_context_types":sorted(miss.get(tid,set())),"target_status":status,"source_context_refs":sorted(refs.get(tid,[])),"caveats":[],"forbidden_interpretations":[]})
    return _sorted(out)

def derive_ai_market_context_status(orchestration, pkg, unsafe=False):
    up=orchestration.get('execution_status') or (orchestration.get('execution_receipt') or {}).get('package_status')
    if unsafe or up=='blocked' or (not pkg.get('source_contexts') and not pkg.get('source_health_context') and not pkg.get('market_session_context')): return 'blocked'
    st='ready'
    if up=='partial' or pkg.get('missing_context') or (orchestration.get('m8_context_core_status') or {}).get('status')=='build_failed': st='partial'
    elif pkg.get('caveats'): st='ready_with_caveats'
    if up in STATUS_ORDER and STATUS_ORDER[st] < STATUS_ORDER[up]: st=up
    return st

def build_ai_market_context_hash_scope(pkg):
    return {k:pkg.get(k) for k in ["schema_version","package_status","scope","provenance","targets","source_contexts","market_session_context","source_health_context","missing_context","currentness_summary","caveats","forbidden_interpretations","production_readiness"]}

def compute_ai_market_context_hash(scope): return hashlib.sha256(canonical_json(scope).encode()).hexdigest()

def build_conversation_views(pkg):
    compact={"package_id":pkg['package_id'],"package_status":pkg['package_status'],"targets":[{"target_id":t['target_id'],"status":t['target_status']} for t in pkg['targets']],"latest_usable_observations":[{"target_id":c['target_id'],"source_context_id":c['source_context_id'],"source_family":c['source_family'],"source_timestamp":c['source_timestamp'],"retrieved_at_utc":c['retrieved_at_utc'],"currentness":c['currentness']} for c in pkg['source_contexts']],"currentness":pkg['currentness_summary'],"highest_severity_caveats":[c for c in pkg['caveats'] if c['severity'] in {'blocking','warning'}][:10],"missing_context_count":len(pkg['missing_context'])}
    standard={"package_id":pkg['package_id'],"targets":pkg['targets'],"source_provenance":pkg['source_contexts'],"currentness":pkg['currentness_summary'],"missing_context":pkg['missing_context'],"caveats":pkg['caveats'],"forbidden_interpretations":pkg['forbidden_interpretations']}
    diagnostic={"package_id":pkg['package_id'],"provenance":pkg['provenance'],"operation_outcomes":pkg.get('_operation_outcomes',[]),"source_mappings":[{"target_id":c['target_id'],"operation_id":c['operation_id'],"source_context_id":c['source_context_id']} for c in pkg['source_contexts']],"identity_evidence":[{"target_id":t['target_id'],"derivative_identity":t.get('derivative_identity')} for t in pkg['targets']],"all_caveat_codes":[c['code'] for c in pkg['caveats']]}
    return {"compact":compact,"standard":standard,"diagnostic":diagnostic}

def build_ai_market_context_package(orchestration_result: dict[str, Any], *, generated_at_utc: str | None=None, package_policy: dict[str, Any] | None=None) -> dict[str, Any]:
    assert_no_forbidden_keys(orchestration_result)
    receipt=orchestration_result.get('execution_receipt') or {}; unsafe = not (receipt.get('bounded_retention') is True and receipt.get('raw_payload_retained') is False and receipt.get('full_market_retained_output') is False)
    sc=build_source_context_views(orchestration_result); sessions, health=build_local_views(orchestration_result); missing=_missing(orchestration_result)
    pkg={"schema_version":SCHEMA_VERSION,"package_id":"","generated_at_utc":generated_at_utc or utc_now(),"package_status":"blocked","scope":{},"provenance":_plan_meta(orchestration_result),"targets":[],"source_contexts":sc,"market_session_context":sessions,"source_health_context":health,"missing_context":missing,"currentness_summary":build_currentness_summary(sc),"caveats":[],"forbidden_interpretations":[],"conversation_views":{},"production_readiness":dict(PROD),"integrity":{}}
    pkg['provenance']['m8_context_core_status']=(orchestration_result.get('m8_context_core_status') or {}).get('status')
    pkg['targets']=build_target_views(orchestration_result, sc, missing)
    pkg['scope']={"approved_target_count":receipt.get('approved_target_count',len(pkg['targets'])),"approved_operation_count":receipt.get('approved_operation_count',len(orchestration_result.get('operation_results') or [])),"successful_context_count":len(sc),"missing_context_count":len(missing),"markets":sorted({t.get('market') for t in pkg['targets'] if t.get('market')}),"instrument_types":sorted({t.get('instrument_type') for t in pkg['targets'] if t.get('instrument_type')}),"source_families":sorted({c.get('source_family') for c in sc if c.get('source_family')}),"requested_context_types":sorted({x for t in pkg['targets'] for x in t.get('requested_context_types',[])}),"successful_context_types":sorted({c.get('context_type') for c in sc if c.get('context_type')}),"missing_context_types":sorted({m.get('context_type') for m in missing if m.get('context_type')}),"network_operations_attempted":receipt.get('network_operations_attempted',0),"local_operations_attempted":receipt.get('local_operations_attempted',0),"full_market_scope":False,"bounded_target_scope":True}
    pkg['package_status']=derive_ai_market_context_status(orchestration_result, pkg, unsafe)
    pkg['caveats']=build_caveats(pkg, 'unsafe_upstream_retention_contract' if unsafe else None)
    pkg['package_status']=derive_ai_market_context_status(orchestration_result, pkg, unsafe)
    pkg['forbidden_interpretations']=build_forbidden_interpretations(pkg)
    hs=build_ai_market_context_hash_scope(pkg); h=compute_ai_market_context_hash(hs)
    pkg['package_id']='amc-'+h[:16]; pkg['integrity']={"package_hash":h,"hash_scope_schema":"ai_market_context_hash_scope.v1"}
    pkg['_operation_outcomes']=[{"operation_id":r.get('operation_id'),"target_id":r.get('target_id'),"status":r.get('status'),"source_family":r.get('source_family'),"context_type":r.get('context_type')} for r in orchestration_result.get('operation_results') or []]
    pkg['conversation_views']=build_conversation_views(pkg); pkg.pop('_operation_outcomes',None)
    validate_ai_market_context_package(pkg)
    return pkg

def validate_ai_market_context_package(pkg):
    assert_no_forbidden_keys(pkg)
    if pkg.get('schema_version')!=SCHEMA_VERSION: raise AIMarketContextPackageError('invalid_schema_version')
    h=compute_ai_market_context_hash(build_ai_market_context_hash_scope(pkg))
    if pkg.get('integrity',{}).get('package_hash')!=h or pkg.get('package_id')!='amc-'+h[:16]: raise AIMarketContextPackageError('package_hash_mismatch')
    if not pkg.get('provenance',{}).get('receipt_id') and pkg.get('package_status')!='blocked': raise AIMarketContextPackageError('missing_receipt_id')
    if pkg.get('package_status') != 'blocked' and (pkg.get('provenance',{}).get('raw_payload_retained') or pkg.get('provenance',{}).get('full_market_retained_output') or not pkg.get('provenance',{}).get('bounded_retention')): raise AIMarketContextPackageError('unsafe_retention')
    tids=[t['target_id'] for t in pkg.get('targets',[])]; sids=[s['source_context_id'] for s in pkg.get('source_contexts',[])]
    if len(tids)!=len(set(tids)) or len(sids)!=len(set(sids)): raise AIMarketContextPackageError('duplicate_ids')
    for s in pkg.get('source_contexts',[]):
        if s.get('target_id') not in tids: raise AIMarketContextPackageError('dangling_source_target_ref')
        if s.get('source_family') not in ALLOWED_SOURCES: raise AIMarketContextPackageError('unsafe_source_family')
    for t in pkg.get('targets',[]):
        for ref in t.get('source_context_refs',[]):
            if ref not in sids: raise AIMarketContextPackageError('dangling_source_context_ref')
        if t.get('market')=='TAIFEX':
            ident=t.get('derivative_identity') or {}; need=['expiry','contract_type','session'] + (['underlying','strike','call_put'] if t.get('instrument_type')=='option' else [])
            if any(not ident.get(k) for k in need): raise AIMarketContextPackageError('derivative_identity_incomplete')
    if pkg.get('scope',{}).get('successful_context_count') != len(pkg.get('source_contexts',[])): raise AIMarketContextPackageError('wrong_successful_context_count')
    if pkg.get('scope',{}).get('missing_context_count') != len(pkg.get('missing_context',[])): raise AIMarketContextPackageError('wrong_missing_context_count')
    if pkg.get('missing_context') and pkg.get('package_status')=='ready': raise AIMarketContextPackageError('status_inconsistency')
    if pkg.get('production_readiness',{}).get('production_live_execution_ready') or pkg.get('production_readiness',{}).get('production_executor_adapters_ready'): raise AIMarketContextPackageError('unsafe_production_readiness')
    return {"status":"valid"}

def write_ai_market_context_artifacts(package, *, artifact_root: str, receipt_id: str | None=None):
    validate_ai_market_context_package(package)
    if artifact_root.startswith('/') or '..' in Path(artifact_root).parts or artifact_root.startswith('frontend/public') or artifact_root.startswith('research/generated'):
        raise OSError('unapproved_artifact_root')
    rid=receipt_id or package['provenance']['receipt_id']; run_dir=Path(artifact_root)/rid
    run_dir.mkdir(parents=True, exist_ok=False)
    payloads={"ai_market_context_v1.json":package,"ai_market_context_compact.json":package['conversation_views']['compact'],"ai_market_context_standard.json":package['conversation_views']['standard'],"ai_market_context_diagnostic.json":package['conversation_views']['diagnostic']}
    written=[]
    for name,payload in payloads.items():
        assert_no_forbidden_keys(payload)
        fd,tmp=tempfile.mkstemp(prefix=name, dir=run_dir)
        with os.fdopen(fd,'w',encoding='utf-8') as fh: json.dump(payload,fh,ensure_ascii=False,sort_keys=True,indent=2)
        os.replace(tmp, run_dir/name); written.append(str(run_dir/name))
    return written
