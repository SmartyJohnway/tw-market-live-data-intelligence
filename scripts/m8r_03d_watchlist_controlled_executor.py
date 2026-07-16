from __future__ import annotations
import json, os
from pathlib import Path, PurePosixPath
from typing import Any
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan, validate_authorization, utc_now, AUTH_SCHEMA_VERSION
from scripts.m8r_03d_watchlist_source_integration import normalize_twse_mis_watchlist_observation, normalize_twse_openapi_watchlist_observation, normalize_tpex_openapi_watchlist_observation
from scripts.m8r_03c_watchlist_bundle_builder import build_watchlist_snapshot_bundle, build_watchlist_performance_bundle
from scripts.m8a_twse_official_eod_adapter import execute_twse_official_eod_adapter
from scripts.m8a_tpex_official_eod_adapter import execute_tpex_official_eod_adapter
from scripts.m5k_common import execute_live_observation
RESULT_SCHEMA_VERSION='m8r_03d_watchlist_execution_result.v1'
ALLOWED_STATUSES={'success','success_with_partial_coverage','blocked_preflight','authorization_failed','source_execution_failed','bundle_validation_failed'}
FORBIDDEN_ARTIFACT_TOKENS=('raw_payload\"','cookies','session_id','access_token','refresh_token','msgArray')
class M8R03DExecutionError(RuntimeError): pass

def _safe_root(root):
    p=PurePosixPath(root)
    if '..' in p.parts or any(x in p.parts for x in ('.env','secrets','credentials')): raise ValueError('unsafe_artifact_root')
    return Path(p)
def _write_json(path:Path,data:Any):
    text=json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)
    low=text.lower()
    if any(t.lower() in low for t in FORBIDDEN_ARTIFACT_TOKENS): raise ValueError('forbidden_artifact_content')
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text+'\n',encoding='utf-8')
def _load(p): return json.loads(Path(p).read_text(encoding='utf-8'))

def preflight(request:dict, *, bundle_type:str, generated_at_utc:str|None=None):
    plan=build_execution_plan(request,bundle_type=bundle_type,generated_at_utc=generated_at_utc)
    return {'mode':'preflight','request_hash':plan['request_hash'],'plan':plan,'network_calls_performed':False,'observation_count':0}

def execute_watchlist(request:dict, *, mode:str, bundle_type:str, authorization:dict|None=None, fixture_source_data:dict|None=None, artifact_root:str='artifacts/m8r_03d', run_id:str|None=None, generated_at_utc:str|None=None, executors:dict|None=None)->dict:
    started=generated_at_utc or utc_now(); run_id=run_id or 'm8r03d-'+started.replace(':','').replace('-','')
    plan=build_execution_plan(request,bundle_type=bundle_type,generated_at_utc=started)
    if mode=='preflight':
        return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'blocked_preflight' if plan.get('issues') else 'success',plan.get('issues',[]),artifact_root,write=False)
    if mode not in {'fixture','execute'}: raise ValueError('invalid_mode')
    if mode=='execute':
        if not authorization: return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'authorization_required'}],artifact_root,write=False)
        av=validate_authorization(authorization,request=request,plan=plan,bundle_type=bundle_type,now_utc=started,require_network=True)
        if not av['valid']: return _result(run_id,mode,started,utc_now(),request,plan,authorization,[],None,'authorization_failed',av['issues'],artifact_root,write=True)
        source_data=_execute_live(plan,request,executors or {})
    else:
        source_data=fixture_source_data or {}
    observations=[]; target_results=[]; by_target={t['target_id']:t for t in plan['targets']}
    try:
        for t in plan['targets']:
            tid=t['target_id']
            if t['identity_status']!='resolved':
                target_results.append({'target_id':tid,'status':'skipped','reason_code':'identity_unresolved'}); continue
            srcs=(source_data.get('targets') or {}).get(tid,{})
            if bundle_type=='snapshot' and srcs.get('TWSE_MIS'):
                observations.append(normalize_twse_mis_watchlist_observation(srcs['TWSE_MIS'],t,retrieved_at_utc=started)); target_results.append({'target_id':tid,'source_family':'TWSE_MIS','status':'normalized'})
            fam=t['eod_source_plan'].get('source_family')
            rows=srcs.get(fam)
            if rows:
                if not isinstance(rows,list): rows=[rows]
                for row in rows:
                    observations.append((normalize_twse_openapi_watchlist_observation if fam=='TWSE_OPENAPI' else normalize_tpex_openapi_watchlist_observation)(row,t))
                target_results.append({'target_id':tid,'source_family':fam,'status':'normalized','row_count':len(rows)})
            elif not srcs.get('TWSE_MIS'):
                target_results.append({'target_id':tid,'status':'source_unavailable','reason_code':'missing_fixture_or_source_result'})
        bundle=build_watchlist_snapshot_bundle(request=request,observations=observations,generated_at_utc=started) if bundle_type=='snapshot' else build_watchlist_performance_bundle(request=request,observations=observations,generated_at_utc=started)
        partial=any(c['coverage_state']!='usable' for c in bundle['coverage']['targets'])
        status='success_with_partial_coverage' if partial else 'success'; issues=[]
    except Exception as exc:
        bundle=None; status='bundle_validation_failed'; issues=[{'code':'bundle_validation_failed','detail':str(exc)[:160]}]
    return _result(run_id,mode,started,utc_now(),request,plan,authorization if mode=='execute' else None,observations,bundle,status,issues,artifact_root,target_results=target_results,write=True)

def _execute_live(plan,request,executors):
    data={'targets':{}}
    ids_by_market={t['market']:[t['security_code'] for t in plan['targets'] if t['market']==t['market'] and t['identity_status']=='resolved'] for t in plan['targets']}
    if any(g['source_family']=='TWSE_MIS' for g in plan['source_call_groups']):
        wl={'schema_version':'m5n_watchlist.v1','watchlist_id':request['persistent_watchlist_reference']['watchlist_id'],'items':[{'symbol':t['security_code'],'market':'twse' if t['market']=='TWSE' else 'tpex_otc','instrument_type':t['instrument_type'],'enabled':True} for t in plan['targets'] if t['identity_status']=='resolved']}
        live=(executors.get('TWSE_MIS') or (lambda w: execute_live_observation(w,write_latest=False)))(wl)
        for obs in live.get('observations',[]):
            tid=('TPEX:' if obs.get('market') in {'tpex_otc','TPEX'} else 'TWSE:')+str(obs.get('symbol'))
            data['targets'].setdefault(tid,{})['TWSE_MIS']=obs
    for fam,fn in [('TWSE_OPENAPI',executors.get('TWSE_OPENAPI') or execute_twse_official_eod_adapter),('TPEX_OPENAPI',executors.get('TPEX_OPENAPI') or execute_tpex_official_eod_adapter)]:
        syms=[t['security_code'] for t in plan['targets'] if t.get('eod_source_plan',{}).get('source_family')==fam]
        if syms:
            res=fn(syms)
            for obs in res.get('observations',[]):
                pref='TWSE:' if fam=='TWSE_OPENAPI' else 'TPEX:'; data['targets'].setdefault(pref+obs.get('symbol'),{})[fam]=obs
    return data

def _result(run_id,mode,started,completed,request,plan,auth,observations,bundle,status,issues,artifact_root,target_results=None,write=True):
    root=_safe_root(artifact_root)/run_id; paths={}
    if write:
        _write_json(root/'validated_request.json',request); paths['validated_request']=str(root/'validated_request.json')
        _write_json(root/'execution_plan.json',plan); paths['execution_plan']=str(root/'execution_plan.json')
        if auth: _write_json(root/'authorization.json',auth); paths['authorization']=str(root/'authorization.json')
        _write_json(root/'normalized_observations.json',observations); paths['normalized_observations']=str(root/'normalized_observations.json')
        if bundle:
            name='watchlist_snapshot_bundle.json' if bundle['schema_version'].endswith('snapshot_bundle.v1') else 'watchlist_performance_bundle.json'
            _write_json(root/name,bundle); paths['bundle']=str(root/name)
    result={'schema_version':RESULT_SCHEMA_VERSION,'run_id':run_id,'authorization_id':(auth or {}).get('authorization_id'),'request_id':request.get('request_id'),'request_hash':plan.get('request_hash'),'plan_id':plan.get('plan_id'),'mode':mode,'started_at_utc':started,'completed_at_utc':completed,'source_execution_summary':{'planned_source_call_groups':plan.get('source_call_groups',[]),'network_default_enabled':False,'polling':False,'scheduler':False},'target_results':target_results or [],'observation_count':len(observations),'bundle_artifact':paths.get('bundle'),'status':status,'issues':issues,'artifact_paths':paths}
    if write: _write_json(root/'execution_result.json',result)
    return result
