from __future__ import annotations
import hashlib, json
from copy import deepcopy
from datetime import datetime, date
from typing import Any
from scripts import m8r_03c_conversation_contract_validator as V
from scripts.m8r_03c_conversation_contract_validator import (assert_no_forbidden_keys, validate_watchlist_snapshot_request, validate_watchlist_performance_request, validate_watchlist_snapshot_bundle, validate_watchlist_performance_bundle)
from scripts.m8r_03c_watchlist_metrics import calculate_metrics

SOURCE_ROLE_MATRIX={
    'TWSE_MIS': {'role':'current','timing_classes':{'liveish_intraday_snapshot'},'context_types':{'liveish_observation'}},
    'TAIFEX_MIS': {'role':'current','timing_classes':{'liveish_intraday_snapshot'},'context_types':{'liveish_observation'}},
    'TWSE_OPENAPI': {'role':'eod_reference','timing_classes':{'official_eod'},'context_types':{'official_eod_reference'}},
    'TPEX_OPENAPI': {'role':'eod_reference','timing_classes':{'official_eod'},'context_types':{'official_eod_reference'}},
    'TAIFEX_OPENAPI': {'role':'eod_reference','timing_classes':{'official_eod','official_statistics_eod'},'context_types':{'official_eod_reference','official_statistical_reference'}},
    'BENCHMARK_FIXTURE': {'role':'benchmark_eod','timing_classes':{'official_eod','fixture_eod'},'context_types':{'benchmark_eod_reference','official_eod_reference'}},
}
CURRENT_ROLES={'current'}; EOD_ROLES={'eod_reference'}; BENCHMARK_ROLES={'benchmark_eod'}

def _canon(v): return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',',':'))
def _bid(req, typ, gen): return f'm8r03c-{typ}-'+hashlib.sha256(_canon({'request_id':req['request_id'],'generated_at_utc':gen,'type':typ}).encode()).hexdigest()[:16]
def _period(req): return req['conversation_intent']['time_scope']

def _parse_date_or_none(value: Any, path: str) -> str | None:
    if value is None: return None
    if not isinstance(value, str): V._err('field_type_invalid', path, 'expected ISO date or null')
    try: parsed=date.fromisoformat(value)
    except ValueError: V._err('explicit_range_invalid', path, 'invalid ISO YYYY-MM-DD date')
    if parsed.isoformat()!=value: V._err('explicit_range_invalid', path, 'date must be YYYY-MM-DD')
    return value

def _parse_datetime_or_none(value: Any, path: str, *, required: bool) -> str | None:
    if value is None:
        if required: V._err('field_type_invalid', path, 'timezone-aware ISO datetime required')
        return None
    if not isinstance(value, str) or not value.strip(): V._err('field_type_invalid', path, 'timezone-aware ISO datetime required')
    text=value.replace('Z','+00:00')
    try: parsed=datetime.fromisoformat(text)
    except ValueError: V._err('explicit_range_invalid', path, 'invalid ISO datetime')
    if parsed.tzinfo is None or parsed.utcoffset() is None: V._err('explicit_range_invalid', path, 'timezone-aware ISO datetime required')
    return value

def _source_role(o: dict[str, Any]) -> str:
    spec=SOURCE_ROLE_MATRIX.get(o.get('source_family'))
    if not spec: V._err('enum_value_invalid','$.observation.source_family','invalid source family')
    if o.get('timing_class') not in spec['timing_classes'] or o.get('context_type') not in spec['context_types']:
        V._err('observation_source_semantics_invalid','$.observation','source_family/timing_class/context_type mismatch')
    return spec['role']

def validate_watchlist_input_observation(v: dict) -> dict:
    assert_no_forbidden_keys(v); o=deepcopy(V._obj(v,'$.observation'))
    allowed={'schema_version','target_id','requested_identity','resolved_identity','source_family','timing_class','context_type','source_timestamp','trade_date','retrieved_at_utc','currentness','facts','issues','benchmark_id'}
    V._strict(o,'$.observation',allowed)
    if o.get('schema_version')!='m8r_watchlist_input_observation.v1': V._err('schema_version_invalid','$.observation.schema_version','invalid')
    for f in ('target_id','source_family','timing_class','context_type','retrieved_at_utc'): V._str(o.get(f),'$.observation.'+f)
    for f in ('requested_identity','resolved_identity','currentness','facts'):
        if not isinstance(o.get(f),dict): V._err('field_type_invalid','$.observation.'+f,'object')
    if not isinstance(o.get('issues'),list): V._err('field_type_invalid','$.observation.issues','list')
    o['trade_date']=_parse_date_or_none(o.get('trade_date'),'$.observation.trade_date')
    _parse_datetime_or_none(o.get('retrieved_at_utc'),'$.observation.retrieved_at_utc', required=True)
    _parse_datetime_or_none(o.get('source_timestamp'),'$.observation.source_timestamp', required=False)
    o['source_role']=_source_role(o)
    if o['source_role']=='benchmark_eod': V._str(o.get('benchmark_id'),'$.observation.benchmark_id')
    return o

def _obs_by_target(observations):
    out={}
    for obs in observations:
        o=validate_watchlist_input_observation(obs); out.setdefault(o['target_id'],[]).append(o)
    return out

def _latest(cands):
    return sorted(cands, key=lambda o:(str(o.get('source_timestamp') or o.get('trade_date') or ''), str(o.get('retrieved_at_utc'))), reverse=True)[0] if cands else None

def _src_summary(obs):
    fams=sorted({o['source_family'] for o in obs}); return {f:{'observation_count':sum(1 for o in obs if o['source_family']==f)} for f in fams}

def _missing(target_id, cap, reason, required=True):
    return {'target_id':target_id,'capability_id':cap,'reason_code':reason,'required_for_answer':required,'impact':'coverage degraded','fallback_used':None,'recommended_follow_up':'supply normalized non-network observation'}

def _dedupe_rows(rows: list[dict[str, Any]], *, key_id: str, path_prefix: str) -> list[dict[str, Any]]:
    seen={}
    for r in sorted(rows, key=lambda o:str(o.get('trade_date') or '')):
        d=r.get('trade_date')
        if not d: V._err('explicit_range_invalid',f'{path_prefix}.{key_id}.trade_date','performance EOD observation requires trade_date')
        if d in seen and _canon(seen[d].get('facts')) != _canon(r.get('facts')): V._err('source_fact_boundary_invalid',f'{path_prefix}.{key_id}.{d}','contradictory duplicate')
        seen[d]=r
    return [seen[d] for d in sorted(seen)]

def _benchmark_rows(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped={}
    for o in observations:
        if o['source_role'] in BENCHMARK_ROLES:
            grouped.setdefault(o.get('benchmark_id'),[]).append(o)
    if len(grouped)>1: V._err('evidence_priority_mismatch','$.observations.benchmark_id','multiple benchmark IDs require explicit target mapping')
    if not grouped: return []
    bid=next(iter(grouped))
    return _dedupe_rows(grouped[bid], key_id=bid, path_prefix='$.observations.benchmark')

def build_watchlist_snapshot_bundle(*, request: dict, observations: list[dict], generated_at_utc: str) -> dict:
    req=validate_watchlist_snapshot_request(request)
    if req['clarification_required']: V._err('clarification_invariant_failed','$.clarification_required','cannot build')
    ids=req['persistent_watchlist_reference']['enabled_target_ids']; by=_obs_by_target(observations); targets=[]; coverage=[]; facts=[]; missing=[]; assumptions=[]; allobs=[]
    for tid in ids:
        obs=by.get(tid,[]); allobs+=obs
        cur=_latest([o for o in obs if o['source_role'] in CURRENT_ROLES])
        eod=_latest([o for o in obs if o['source_role'] in EOD_ROLES])
        ident=(cur or eod or {}).get('resolved_identity') or {}
        current_evidence={k:cur[k] for k in ('source_family','timing_class','source_timestamp','retrieved_at_utc','currentness','facts') if cur and k in cur} if cur else {}
        eod_reference={k:eod[k] for k in ('source_family','timing_class','trade_date','retrieved_at_utc','currentness','facts') if eod and k in eod} if eod else {}
        present=[]; miss=[]; reason=None
        if ident: present.append('resolved_identity')
        else: miss.append('resolved_identity')
        if cur and (cur['facts'].get('latest_price') is not None or cur['facts'].get('no_trade_state')): present.append('current_evidence')
        else: miss.append('current_evidence'); missing.append(_missing(tid,'current_mis_observation','MIS observation unavailable'))
        currentness_status=(cur or {}).get('currentness',{}).get('status')
        if cur and cur.get('currentness') and currentness_status not in {'stale','unresolved'}: present.append('currentness')
        else:
            miss.append('currentness')
            if cur:
                reason_code='stale_observation' if currentness_status=='stale' else 'currentness_unresolved'
                missing.append(_missing(tid,'currentness_validation',reason_code,False))
        if eod: present.append('eod_reference')
        else: miss.append('eod_reference'); missing.append(_missing(tid,'official_eod_reference','EOD reference unavailable',False))
        if not obs or not ident: state='unavailable'; reason='identity_unresolved' if not ident else 'no_usable_source_observation'
        elif miss: state='partial'
        else: state='usable'
        cov={'target_id':tid,'coverage_state':state,'present_field_groups':present,'missing_field_groups':miss,'reason_code':reason}
        targets.append({'target_id':tid,'requested_identity':(cur or eod or {}).get('requested_identity') or {},'resolved_identity':ident,'current_evidence':current_evidence,'eod_reference':eod_reference,'coverage':cov,'issues':sum([o.get('issues',[]) for o in obs],[])})
        coverage.append(cov)
        if cur: facts.append({'target_id':tid,'fact_type':'current_evidence','values':cur['facts'],'source_family':cur['source_family'],'timing_class':cur['timing_class']})
        if eod: facts.append({'target_id':tid,'fact_type':'eod_reference','values':eod['facts'],'source_family':eod['source_family'],'timing_class':eod['timing_class']})
    bundle={'schema_version':'m8r_watchlist_snapshot_bundle.v1','bundle_id':_bid(req,'snapshot',generated_at_utc),'request_id':req['request_id'],'generated_at_utc':generated_at_utc,'conversation_context':{'original_user_text':req['original_user_text'],'scope_modes':req['conversation_intent']['scope_modes']},'targets':targets,'facts':facts,'derived_metrics':[],'resolution_assumptions':assumptions,'missing_evidence':sorted(missing,key=lambda m:(m['target_id'],m['capability_id'],m['reason_code'])),'coverage':{'requested_target_ids':ids,'targets':coverage},'source_summary':_src_summary(allobs),'issues':[]}
    return validate_watchlist_snapshot_bundle(bundle)

def build_watchlist_performance_bundle(*, request: dict, observations: list[dict], generated_at_utc: str) -> dict:
    req=validate_watchlist_performance_request(request); ids=req['persistent_watchlist_reference']['enabled_target_ids']; by={}; allobs=[]
    for obs in observations:
        o=validate_watchlist_input_observation(obs); allobs.append(o)
        if o['source_role'] in BENCHMARK_ROLES: continue
        if o['source_role'] not in EOD_ROLES: V._err('observation_source_semantics_invalid','$.observations','performance accepts EOD observations only')
        by.setdefault(o['target_id'],[]).append(o)
    bench=_benchmark_rows(allobs)
    targets=[]; coverage=[]; facts=[]; metrics=[]; missing=[]
    for tid in ids:
        rows=_dedupe_rows(by.get(tid,[]), key_id=tid, path_prefix='$.observations') if by.get(tid) else []
        identity_present=bool(rows and rows[-1].get('resolved_identity'))
        present=['resolved_identity'] if identity_present else []
        if rows: present.append('eod_series')
        miss=[] if rows else ['eod_series']
        if rows and not identity_present: miss.append('resolved_identity')
        if rows and not identity_present:
            state='unavailable'; reason='identity_unresolved'; missing.append(_missing(tid,'identity_resolution','identity_unresolved',True))
        elif rows and len(rows)>=21:
            state='usable'; reason=None
        elif rows:
            state='partial'; reason=None
        else:
            state='unavailable'; reason='no_usable_source_observation'
        period=_period(req); m=calculate_metrics(rows,target_id=tid,as_of=rows[-1]['trade_date'] if rows else generated_at_utc,period=period,benchmark_rows=bench or None)
        for rec in m:
            if rec['calculation_status']=='input_unavailable': missing.append(_missing(tid,rec['metric_id'],'insufficient_history',False))
        metrics.extend(m)
        cov={'target_id':tid,'coverage_state':state,'present_field_groups':present,'missing_field_groups':miss + ([] if len(rows)>=21 else ['20_day_history']),'reason_code':reason}
        coverage.append(cov); targets.append({'target_id':tid,'requested_identity':rows[-1].get('requested_identity') if rows else {},'resolved_identity':rows[-1].get('resolved_identity') if rows else {},'eod_series':rows,'coverage':cov,'issues':[]})
        facts.extend({'target_id':tid,'fact_type':'eod_row','values':r['facts'],'source_family':r['source_family'],'timing_class':r['timing_class'],'trade_date':r.get('trade_date')} for r in rows)
    bundle={'schema_version':'m8r_watchlist_performance_bundle.v1','bundle_id':_bid(req,'performance',generated_at_utc),'request_id':req['request_id'],'generated_at_utc':generated_at_utc,'conversation_context':{'original_user_text':req['original_user_text'],'scope_modes':req['conversation_intent']['scope_modes']},'targets':targets,'facts':facts,'derived_metrics':metrics,'resolution_assumptions':['price metrics use source-provided unadjusted closes unless fixture states otherwise','relative_return_1d_vs_benchmark uses one explicit supplied benchmark_id only'],'missing_evidence':sorted(missing,key=lambda m:(m['target_id'],m['capability_id'],m['reason_code'])),'coverage':{'requested_target_ids':ids,'targets':coverage},'source_summary':_src_summary(allobs),'issues':[]}
    return validate_watchlist_performance_bundle(bundle)
