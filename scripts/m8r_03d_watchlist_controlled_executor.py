from __future__ import annotations
import json, os
from pathlib import Path, PurePosixPath
from typing import Any
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan, validate_authorization, utc_now, sha256_json, plan_has_blocking_issues
from scripts.m8r_03d_watchlist_source_integration import normalize_twse_mis_watchlist_observation, normalize_twse_openapi_watchlist_observation, normalize_tpex_openapi_watchlist_observation
from scripts.m8r_03c_watchlist_bundle_builder import build_watchlist_snapshot_bundle, build_watchlist_performance_bundle
from scripts.m8a_twse_official_eod_adapter import execute_twse_official_eod_adapter
from scripts.m8a_tpex_official_eod_adapter import execute_tpex_official_eod_adapter
from scripts.m5k_common import execute_live_observation
from scripts.m8r_filesystem_safety import atomic_write_text, safe_destination, validate_authorized_root, classify_artifact_relative_path, FilesystemSafetyError
RESULT_SCHEMA_VERSION='m8r_03d_watchlist_execution_result.v1'
AUTHORIZATION_CONSUMPTION_ROOT=Path('artifacts/m8r_03d_authorization_consumption')
FORBIDDEN_ARTIFACT_TOKENS=('raw_payload"','cookies','session_id','access_token','refresh_token','msgArray')
MARKET_ALIASES={'TWSE':{'TWSE','listed','twse','tse'},'TPEX':{'TPEX','tpex','tpex_otc','otc'}}
class M8R03DExecutionError(RuntimeError): pass

def _safe_root(root):
    raw = str(root).replace('\\', '/')
    parts = set(p.lower() for p in raw.split('/') if p not in ('', '.'))
    if '..' in parts or any(x in parts for x in ('.env','secrets','credentials')):
        raise ValueError('unsafe_artifact_root')
    return validate_authorized_root(root)
def _write_json(root:Path, path:Path, data:Any):
    text=json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)
    low=text.lower()
    if any(t.lower() in low for t in FORBIDDEN_ARTIFACT_TOKENS): raise ValueError('forbidden_artifact_content')
    atomic_write_text(root, path.relative_to(root), text+'\n')

def preflight(request:dict, *, bundle_type:str, generated_at_utc:str|None=None, security_master=None):
    plan=build_execution_plan(request,bundle_type=bundle_type,generated_at_utc=generated_at_utc,security_master=security_master)
    return {'mode':'preflight','request_hash':plan['request_hash'],'plan':plan,'network_calls_performed':False,'observation_count':0,'status':'blocked_preflight' if plan_has_blocking_issues(plan) else 'success'}

def execute_watchlist(request:dict, *, mode:str, bundle_type:str, authorization:dict|None=None, fixture_source_data:dict|None=None, artifact_root:str='artifacts/m8r_03d', run_id:str|None=None, generated_at_utc:str|None=None, executors:dict|None=None, security_master=None)->dict:
    started=generated_at_utc or utc_now(); run_id=run_id or 'm8r03d-'+started.replace(':','').replace('-','')
    artifact_root_path=_safe_root(artifact_root)
    safe_destination(artifact_root_path, run_id, create_parent=False)
    plan=build_execution_plan(request,bundle_type=bundle_type,generated_at_utc=started,security_master=security_master)
    if mode not in {'preflight','fixture','execute'}: raise ValueError('invalid_mode')
    if mode=='preflight' or plan_has_blocking_issues(plan):
        status='blocked_preflight' if plan_has_blocking_issues(plan) else 'success'
        return _result(run_id,mode,started,utc_now(),request,plan,authorization if mode=='execute' else None,[],None,status,plan.get('issues',[]),artifact_root_path,source_execution_summary={'planned_source_call_groups':plan.get('source_call_groups',[]),'group_results':[],'network_calls_performed':False,'network_default_enabled':False,'polling':False,'scheduler':False},write=False)
    if mode=='execute':
        if not authorization: return _result(run_id,mode,started,utc_now(),request,plan,None,[],None,'authorization_failed',[{'code':'authorization_required'}],artifact_root_path,write=False)
        av=validate_authorization(authorization,request=request,plan=plan,bundle_type=bundle_type,now_utc=started,require_network=True)
        if not av['valid']: return _result(run_id,mode,started,utc_now(),request,plan,authorization,[],None,'authorization_failed',av['issues'],artifact_root_path,write=True)
        claim=_claim_authorization(authorization, plan, artifact_root, started)
        if not claim['valid']: return _result(run_id,mode,started,utc_now(),request,plan,authorization,[],None,'authorization_failed',claim['issues'],artifact_root_path,write=True)
        source_data, group_results = _execute_source_groups(plan,request,executors or {})
    else:
        source_data=fixture_source_data or {}; group_results=_fixture_group_results(plan, source_data, started)
    observations=[]; target_results=[]; normalize_issues=[]
    for t in plan['targets']:
        tid=t['target_id']
        if t['identity_status']!='resolved':
            target_results.append({'target_id':tid,'status':'skipped','reason_code':'identity_unresolved'}); continue
        srcs=(source_data.get('targets') or {}).get(tid,{})
        if bundle_type=='snapshot' and srcs.get('TWSE_MIS'):
            obs=_normalize_checked('TWSE_MIS',srcs['TWSE_MIS'],t,started)
            if obs: observations.append(obs); target_results.append({'target_id':tid,'source_family':'TWSE_MIS','status':'normalized'})
            else: normalize_issues.append({'code':'source_identity_mismatch','target_id':tid,'source_family':'TWSE_MIS'})
        fam=t['eod_source_plan'].get('source_family'); rows=srcs.get(fam)
        if rows:
            if not isinstance(rows,list): rows=[rows]
            kept=0
            for row in rows:
                obs=_normalize_checked(fam,row,t,started)
                if obs: observations.append(obs); kept+=1
                else: normalize_issues.append({'code':'source_identity_mismatch','target_id':tid,'source_family':fam})
            target_results.append({'target_id':tid,'source_family':fam,'status':'normalized' if kept else 'failed','row_count':kept})
        elif not srcs.get('TWSE_MIS'):
            target_results.append({'target_id':tid,'status':'source_unavailable','reason_code':'missing_fixture_or_source_result'})
    try:
        bundle=build_watchlist_snapshot_bundle(request=request,observations=observations,generated_at_utc=started) if bundle_type=='snapshot' else build_watchlist_performance_bundle(request=request,observations=observations,generated_at_utc=started)
        partial=any(c['coverage_state']!='usable' for c in bundle['coverage']['targets'])
        any_group_failed=any(g.get('status')=='failed' for g in group_results)
        status='success_with_partial_coverage' if partial or any_group_failed or normalize_issues else 'success'; issues=normalize_issues
        if not observations and any_group_failed: status='source_execution_failed'
    except Exception as exc:
        bundle=None; status='bundle_validation_failed'; issues=normalize_issues+[{'code':'bundle_validation_failed','detail':str(exc)[:160]}]
    return _result(run_id,mode,started,utc_now(),request,plan,authorization if mode=='execute' else None,observations,bundle,status,issues,artifact_root_path,target_results=target_results,source_execution_summary={'planned_source_call_groups':plan.get('source_call_groups',[]),'group_results':group_results,'network_calls_performed':mode=='execute','network_default_enabled':False,'polling':False,'scheduler':False},write=True)

def _claim_authorization(auth, plan, artifact_root, now):
    root=AUTHORIZATION_CONSUMPTION_ROOT
    key=sha256_json({'authorization_id':auth['authorization_id'],'one_shot_nonce':auth['one_shot_nonce'],'request_hash':plan['request_hash']})
    path=root/(key+'.json')
    receipt={'schema_version':'m8r_03d_authorization_consumption_receipt.v1','authorization_id':auth['authorization_id'],'one_shot_nonce_hash':sha256_json(auth['one_shot_nonce']),'request_hash':plan['request_hash'],'plan_id':plan['plan_id'],'claimed_at_utc':now,'status':'claimed'}
    
    if path.exists():
        return {'valid':False,'issues':[{'code':'authorization_replayed'}]}
        
    try:
        atomic_write_text(root, f"{key}.json", json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + '\n', allow_overwrite=False)
        return {'valid':True,'receipt_path':str(path),'issues':[]}
    except FilesystemSafetyError as exc:
        if exc.code == 'atomic_replace_failed':
            return {'valid':False,'issues':[{'code':'authorization_replayed'}]}
        return {'valid':False,'issues':[{'code':'authorization_consumption_failed','detail':str(exc)[:120]}]}
    except Exception as exc:
        return {'valid':False,'issues':[{'code':'authorization_consumption_failed','detail':str(exc)[:120]}]}

def _fixture_group_results(plan, source_data, started):
    out=[]
    for g in plan.get('source_call_groups',[]):
        count=0
        for tid in g['target_ids']:
            rows=(source_data.get('targets') or {}).get(tid,{}).get(g['source_family'])
            count += len(rows) if isinstance(rows,list) else (1 if rows else 0)
        out.append({'source_family':g['source_family'],'target_ids':g['target_ids'],'started_at_utc':started,'completed_at_utc':started,'status':'success' if count else 'failed','observation_count':count,'reason_code':None if count else 'fixture_source_unavailable'})
    return out

def _execute_source_groups(plan, request, executors):
    data={'targets':{}}; results=[]
    for g in plan.get('source_call_groups',[]):
        fam=g['source_family']; start=utc_now(); count=0; status='success'; reason=None
        try:
            if fam in executors:
                res=executors[fam](g['target_ids'], plan=plan, request=request, source_call_group=g)
            elif fam=='TWSE_MIS': res=_live_twse_mis(plan, request, g)
            elif fam=='TWSE_OPENAPI': res=_live_eod(plan, g, execute_twse_official_eod_adapter, 'TWSE:')
            elif fam=='TPEX_OPENAPI': res=_live_eod(plan, g, execute_tpex_official_eod_adapter, 'TPEX:')
            else: raise ValueError('unsupported_source_family')
            for tid, srcs in (res.get('targets') or {}).items():
                for sf, rows in srcs.items():
                    data['targets'].setdefault(tid,{})[sf]=rows
                    count += len(rows) if isinstance(rows,list) else (1 if rows else 0)
        except Exception as exc:
            status='failed'; reason=str(exc).splitlines()[0][:80]
        results.append({'source_family':fam,'target_ids':g['target_ids'],'started_at_utc':start,'completed_at_utc':utc_now(),'status':status,'observation_count':count,'reason_code':reason})
    return data, results

def _live_twse_mis(plan, request, g):
    byid={t['target_id']:t for t in plan['targets']}
    wl={'schema_version':'m5n_watchlist.v1','watchlist_id':request['persistent_watchlist_reference']['watchlist_id'],'items':[{'symbol':byid[tid]['security_code'],'market':'twse' if byid[tid]['market']=='TWSE' else 'tpex_otc','instrument_type':byid[tid]['instrument_type'],'enabled':True} for tid in g['target_ids']]}
    live=execute_live_observation(wl,write_latest=False); out={'targets':{}}
    for obs in live.get('observations',[]):
        tid=('TPEX:' if obs.get('market') in MARKET_ALIASES['TPEX'] else 'TWSE:')+str(obs.get('symbol'))
        out['targets'].setdefault(tid,{})['TWSE_MIS']=obs
    return out

def _live_eod(plan, g, fn, pref):
    byid={t['target_id']:t for t in plan['targets']}; syms=[byid[tid]['security_code'] for tid in g['target_ids']]
    res=fn(syms); out={'targets':{}}
    for obs in res.get('observations',[]): out['targets'].setdefault(pref+obs.get('symbol'),{})[g['source_family']]=obs
    return out

def _normalize_checked(fam, row, target, retrieved_at):
    symbol=str(row.get('symbol') or row.get('c') or row.get('safe_fields',{}).get('symbol') or '')
    market=row.get('market') or row.get('exchange') or row.get('ex')
    expected_market=target.get('market')
    if symbol != str(target.get('security_code')): return None
    if market is not None and str(market) not in MARKET_ALIASES.get(expected_market,set()): return None
    if fam=='TWSE_MIS': return normalize_twse_mis_watchlist_observation(row,target,retrieved_at_utc=retrieved_at)
    if fam=='TWSE_OPENAPI': return normalize_twse_openapi_watchlist_observation(row,target)
    return normalize_tpex_openapi_watchlist_observation(row,target)

def _result(run_id,mode,started,completed,request,plan,auth,observations,bundle,status,issues,artifact_root_path,target_results=None,source_execution_summary=None,write=True):
    artifact_root_path = artifact_root_path if isinstance(artifact_root_path, Path) else _safe_root(artifact_root_path)
    root=safe_destination(artifact_root_path, run_id, create_parent=True).path
    paths={}; final_status=status; final_issues=list(issues or [])
    if write:
        try:
            _write_json(artifact_root_path,root/'validated_request.json',request); paths['validated_request']=str(root/'validated_request.json')
            _write_json(artifact_root_path,root/'execution_plan.json',plan); paths['execution_plan']=str(root/'execution_plan.json')
            if auth: _write_json(artifact_root_path,root/'authorization.json',auth); paths['authorization']=str(root/'authorization.json')
            _write_json(artifact_root_path,root/'normalized_observations.json',observations); paths['normalized_observations']=str(root/'normalized_observations.json')
            if bundle:
                name='watchlist_snapshot_bundle.json' if bundle['schema_version'].endswith('snapshot_bundle.v1') else 'watchlist_performance_bundle.json'
                _write_json(artifact_root_path,root/name,bundle); paths['bundle']=str(root/name)
        except Exception as exc:
            paths={}; final_status='bundle_validation_failed' if status in {'success','success_with_partial_coverage'} else status
            final_issues.append({'code':'artifact_write_failed','detail':str(exc)[:120]})
    summary=source_execution_summary or {'planned_source_call_groups':plan.get('source_call_groups',[]),'group_results':[],'network_default_enabled':False,'polling':False,'scheduler':False}
    result={'schema_version':RESULT_SCHEMA_VERSION,'run_id':run_id,'authorization_id':(auth or {}).get('authorization_id'),'request_id':request.get('request_id'),'request_hash':plan.get('request_hash'),'plan_id':plan.get('plan_id'),'mode':mode,'started_at_utc':started,'completed_at_utc':completed,'source_execution_summary':summary,'target_results':target_results or [],'observation_count':len(observations),'bundle_artifact':paths.get('bundle'),'status':final_status,'issues':final_issues,'artifact_paths':paths}
    if write and paths:
        try: _write_json(artifact_root_path,root/'execution_result.json',result)
        except Exception as exc: result['status']='bundle_validation_failed'; result['issues'].append({'code':'artifact_write_failed','detail':str(exc)[:120]})
    return result
