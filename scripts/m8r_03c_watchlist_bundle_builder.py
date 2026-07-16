from __future__ import annotations
import hashlib, json
from copy import deepcopy
from typing import Any
from scripts import m8r_03c_conversation_contract_validator as V
from scripts.m8r_03c_conversation_contract_validator import (M8R03CValidationError, assert_no_forbidden_keys, validate_watchlist_snapshot_request, validate_watchlist_performance_request, validate_watchlist_snapshot_bundle, validate_watchlist_performance_bundle, SOURCE_FAMILIES, CURRENT_SOURCES, EOD_SOURCES)
from scripts.m8r_03c_watchlist_metrics import calculate_metrics, METRIC_ORDER

def _canon(v): return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',',':'))
def _bid(req, typ, gen): return f'm8r03c-{typ}-'+hashlib.sha256(_canon({'request_id':req['request_id'],'generated_at_utc':gen,'type':typ}).encode()).hexdigest()[:16]
def _period(req): return req['conversation_intent']['time_scope']

def validate_watchlist_input_observation(v: dict) -> dict:
    assert_no_forbidden_keys(v); o=deepcopy(V._obj(v,'$.observation'))
    allowed={'schema_version','target_id','requested_identity','resolved_identity','source_family','timing_class','context_type','source_timestamp','trade_date','retrieved_at_utc','currentness','facts','issues','benchmark_id'}
    V._strict(o,'$.observation',allowed)
    if o.get('schema_version')!='m8r_watchlist_input_observation.v1': V._err('schema_version_invalid','$.observation.schema_version','invalid')
    for f in ('target_id','source_family','timing_class','context_type','retrieved_at_utc'): V._str(o.get(f),'$.observation.'+f)
    if o['source_family'] not in SOURCE_FAMILIES: V._err('enum_value_invalid','$.observation.source_family','invalid')
    for f in ('requested_identity','resolved_identity','currentness','facts'):
        if not isinstance(o.get(f),dict): V._err('field_type_invalid','$.observation.'+f,'object')
    if not isinstance(o.get('issues'),list): V._err('field_type_invalid','$.observation.issues','list')
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

def build_watchlist_snapshot_bundle(*, request: dict, observations: list[dict], generated_at_utc: str) -> dict:
    req=validate_watchlist_snapshot_request(request)
    if req['clarification_required']: V._err('clarification_invariant_failed','$.clarification_required','cannot build')
    ids=req['persistent_watchlist_reference']['enabled_target_ids']; by=_obs_by_target(observations); targets=[]; coverage=[]; facts=[]; missing=[]; assumptions=[]; allobs=[]
    for tid in ids:
        obs=by.get(tid,[]); allobs+=obs
        cur=_latest([o for o in obs if o['source_family'] in CURRENT_SOURCES or o['context_type']=='liveish_observation'])
        eod=_latest([o for o in obs if o['source_family'] in EOD_SOURCES or o['context_type']=='official_eod_reference'])
        ident=(cur or eod or {}).get('resolved_identity') or {}
        current_evidence={k:cur[k] for k in ('source_family','timing_class','source_timestamp','retrieved_at_utc','currentness','facts') if cur and k in cur} if cur else {}
        eod_reference={k:eod[k] for k in ('source_family','timing_class','trade_date','retrieved_at_utc','currentness','facts') if eod and k in eod} if eod else {}
        present=[]; miss=[]; reason=None
        if ident: present.append('resolved_identity')
        else: miss.append('resolved_identity')
        if cur and (cur['facts'].get('latest_price') is not None or cur['facts'].get('no_trade_state')): present.append('current_evidence')
        else: miss.append('current_evidence'); missing.append(_missing(tid,'current_mis_observation','MIS observation unavailable'))
        if cur and cur.get('currentness') and cur['currentness'].get('status') not in {'stale','unresolved'}: present.append('currentness')
        else: miss.append('currentness');
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
    bundle={'schema_version':'m8r_watchlist_snapshot_bundle.v1','bundle_id':_bid(req,'snapshot',generated_at_utc),'request_id':req['request_id'],'generated_at_utc':generated_at_utc,'conversation_context':{'original_user_text':req['original_user_text'],'scope_modes':req['conversation_intent']['scope_modes']},'targets':targets,'facts':facts,'derived_metrics':[],'resolution_assumptions':assumptions,'missing_evidence':sorted(missing,key=lambda m:(m['target_id'],m['capability_id'])),'coverage':{'requested_target_ids':ids,'targets':coverage},'source_summary':_src_summary(allobs),'issues':[]}
    return validate_watchlist_snapshot_bundle(bundle)

def build_watchlist_performance_bundle(*, request: dict, observations: list[dict], generated_at_utc: str) -> dict:
    req=validate_watchlist_performance_request(request); ids=req['persistent_watchlist_reference']['enabled_target_ids']; by={}; bench=[]; allobs=[]
    for obs in observations:
        o=validate_watchlist_input_observation(obs); allobs.append(o)
        if o.get('benchmark_id') or o['target_id'].startswith('BENCHMARK'): bench.append(o)
        else: by.setdefault(o['target_id'],[]).append(o)
    targets=[]; coverage=[]; facts=[]; metrics=[]; missing=[]
    for tid in ids:
        rows=sorted(by.get(tid,[]), key=lambda o:str(o.get('trade_date') or ''))
        seen={}
        for r in rows:
            d=r.get('trade_date')
            if not d: continue
            if d in seen and _canon(seen[d].get('facts')) != _canon(r.get('facts')): V._err('source_fact_boundary_invalid',f'$.observations.{tid}.{d}','contradictory duplicate')
            seen[d]=r
        rows=[seen[d] for d in sorted(seen)]
        present=['resolved_identity'] if rows and rows[-1].get('resolved_identity') else []
        if rows: present.append('eod_series')
        miss=[] if rows else ['eod_series']
        state='usable' if rows and len(rows)>=21 else ('partial' if rows else 'unavailable')
        reason=None if state!='unavailable' else 'no_usable_source_observation'
        period=_period(req); m=calculate_metrics(rows,target_id=tid,as_of=rows[-1]['trade_date'] if rows else generated_at_utc,period=period,benchmark_rows=bench or None)
        for rec in m:
            if rec['calculation_status']=='input_unavailable':
                missing.append(_missing(tid,rec['metric_id'],'insufficient_history',False))
        metrics.extend(m)
        cov={'target_id':tid,'coverage_state':state,'present_field_groups':present,'missing_field_groups':miss + ([] if len(rows)>=21 else ['20_day_history']),'reason_code':reason}
        coverage.append(cov); targets.append({'target_id':tid,'requested_identity':rows[-1].get('requested_identity') if rows else {},'resolved_identity':rows[-1].get('resolved_identity') if rows else {},'eod_series':rows,'coverage':cov,'issues':[]})
        facts.extend({'target_id':tid,'fact_type':'eod_row','values':r['facts'],'source_family':r['source_family'],'timing_class':r['timing_class'],'trade_date':r.get('trade_date')} for r in rows)
    bundle={'schema_version':'m8r_watchlist_performance_bundle.v1','bundle_id':_bid(req,'performance',generated_at_utc),'request_id':req['request_id'],'generated_at_utc':generated_at_utc,'conversation_context':{'original_user_text':req['original_user_text'],'scope_modes':req['conversation_intent']['scope_modes']},'targets':targets,'facts':facts,'derived_metrics':metrics,'resolution_assumptions':['price metrics use source-provided unadjusted closes unless fixture states otherwise','benchmark metrics only calculated when supplied'],'missing_evidence':sorted(missing,key=lambda m:(m['target_id'],m['capability_id'])),'coverage':{'requested_target_ids':ids,'targets':coverage},'source_summary':_src_summary(allobs),'issues':[]}
    return validate_watchlist_performance_bundle(bundle)
