from __future__ import annotations
import json, re
from copy import deepcopy
from pathlib import Path
from typing import Any
from scripts.m8r_03e_context_validator import *
DEFAULT_POLICY={'max_citations_per_target':40,'max_missing_evidence_entries':80,'max_caveat_entries':80,'max_lifecycle_event_summaries_per_target':3,'max_serialized_bytes':250000}
MATERIAL_CURRENT=['latest_price','change','change_percent','open','high','low','volume','no_trade_state']
MATERIAL_EOD=['trade_date','open','high','low','close','volume']
MATERIAL_PERF=['requested_lookback_trading_days','start_date','end_date','start_close','end_close','unadjusted_price_return','valid_observation_count']

def _get(d,*keys,default=None):
    cur=d
    for k in keys:
        if not isinstance(cur,dict): return default
        cur=cur.get(k)
    return default if cur is None else cur

def _cid(seed): return 'cite-'+sha256_json(seed)[:20]
def _mid(seed): return 'missing-'+sha256_json(seed)[:20]
def _citation(pkg,target_id,path,fact_type,value,source_type,source_id,source_path,source_family=None,observed_at=None,retrieved_at=None,currentness_status=None,evidence_status='supported',caveats=None):
    c={'schema_version':CITATION_SCHEMA_VERSION,'citation_id':_cid({'target_id':target_id,'path':path,'source_id':source_id,'source_path':source_path}),'target_id':target_id,'fact_path':path,'fact_type':fact_type,'value_hash':sha256_json(value),'source_artifact_type':source_type,'source_artifact_id':source_id or 'unknown','source_path':source_path,'source_family':source_family,'observed_at':observed_at,'retrieved_at_utc':retrieved_at,'currentness_status':currentness_status,'evidence_status':evidence_status,'caveats':caveats or []}
    pkg['citation_index'].append(c); return c['citation_id']

def _identity_from_plan_target(t):
    return {'canonical_target_id':t.get('target_id'),'security_code':t.get('security_code'),'security_name_zh':t.get('security_name'),'security_name_en':_get(t,'resolved_identity','security_name_en'),'market':t.get('market'),'instrument_type':t.get('instrument_type'),'classification_status':t.get('classification_status'),'snapshot_id':t.get('snapshot_id'),'record_id':t.get('record_id'),'record_hash':t.get('record_hash')}

def _status_from_cov(cov, present_key):
    if cov.get('coverage_state')=='usable': return 'supported'
    if present_key in cov.get('present_field_groups',[]): return 'supported_with_caveat'
    if cov.get('coverage_state')=='unavailable': return 'unavailable'
    return 'partial'

def _missing(target_id, category, reason, source_family=None, blocking=False, recoverability='retry_with_new_authorization', detail=None, related=None):
    return {'schema_version':MISSING_SCHEMA_VERSION,'missing_evidence_id':_mid({'target_id':target_id,'category':category,'reason':reason,'source':source_family,'detail':detail}),'target_id':target_id,'category':category,'reason_code':reason,'source_family':source_family,'blocking':blocking,'recoverability':recoverability,'detail':detail or {},'related_citation_ids':related or []}

def _project_request(req,bundle_type):
    ci=req.get('conversation_intent') or {}; pwr=req.get('persistent_watchlist_reference') or {}
    return {'request_id':req.get('request_id'),'bundle_type':bundle_type,'conversation_intent':{'intent_type':ci.get('intent_type'),'scope_modes':ci.get('scope_modes',[]),'time_scope':ci.get('time_scope',{})},'time_scope':ci.get('time_scope',{}),'enabled_target_order':list(pwr.get('enabled_target_ids') or []),'requested_metrics_or_evidence_categories':req.get('requested_metrics') or req.get('requested_evidence_categories') or [bundle_type],'persistent_watchlist_reference':{k:pwr.get(k) for k in ('watchlist_id','watchlist_version','enabled_target_ids') if k in pwr},'target_scope':{'scope_type':'persistent_watchlist_reference' if pwr else 'temporary_conversation_target_set','persistent_watchlist_mutation':False}}

def build_watchlist_ai_context_package(*, validated_request:dict, execution_plan:dict, execution_result:dict, watchlist_bundle:dict, generated_at_utc:str, context_policy:dict|None=None)->dict:
    policy={**DEFAULT_POLICY,**(context_policy or {})}; bundle_type=execution_plan.get('bundle_type') or ('performance' if 'performance' in watchlist_bundle.get('schema_version','') else 'snapshot')
    pkg={'schema_version':PACKAGE_SCHEMA_VERSION,'context_package_id':'','generated_at_utc':generated_at_utc,'request':_project_request(validated_request,bundle_type),'conversation_scope':{'analysis_mode':bundle_type if bundle_type in {'snapshot','performance'} else 'comparison','allowed_topics':['identity','current observation','completed EOD reference','bounded historical performance','coverage','missing evidence','caveats'],'disallowed_topics':['personalized investment advice','trade recommendation','future return prediction','unsupported causal claims','order execution']},'source_lineage':{'execution_result_status':execution_result.get('status'),'execution_mode':execution_result.get('mode'),'network_calls_performed':bool(_get(execution_result,'source_execution_summary','network_calls_performed',default=False)),'source_group_summaries':_get(execution_result,'source_execution_summary','group_results',default=[]),'bundle_id':watchlist_bundle.get('bundle_id'),'plan_id':execution_plan.get('plan_id')},'targets':[],'cross_target_context':{'target_order':execution_plan.get('target_order') or []},'coverage_summary':{},'missing_evidence':[],'caveats':[],'prohibitions':[{'code':'do_not_infer_active_from_missing_lifecycle_event','scope':'global','target_id':None,'reason':'lifecycle must come from verified upstream identity evidence'},{'code':'do_not_treat_retrieval_time_as_market_time','scope':'global','target_id':None,'reason':'retrieval timestamp alone never proves market currentness'}],'citation_index':[],'context_budget':{'policy':policy,'omitted_counts':{'citations':0,'missing_evidence':0,'caveats':0},'truncated':False},'package_hash':None}
    plan_by={t['target_id']:t for t in execution_plan.get('targets',[])}; bundle_by={t['target_id']:t for t in watchlist_bundle.get('targets',[])}
    for pos,tid in enumerate(pkg['request']['enabled_target_order']):
        pt=plan_by.get(tid,{}) ; bt=bundle_by.get(tid,{}) ; cov=bt.get('coverage') or {'coverage_state':'unavailable','present_field_groups':[],'missing_field_groups':[]}
        target={'target_id':tid,'target_position':pos,'identity':_identity_from_plan_target(pt),'classification':{'classification_status':pt.get('classification_status'),'instrument_type':pt.get('instrument_type'),'market':pt.get('market')},'lifecycle':{'lifecycle_state':pt.get('lifecycle_state'),'lifecycle_resolution_status':pt.get('lifecycle_resolution_status'),'as_of_date':_get(pt,'execution_eligibility','as_of_date'),'basis_event_ids':_get(pt,'execution_eligibility','basis_event_ids',default=[]),'execution_policy':pt.get('execution_policy'),'lifecycle_caveats':pt.get('resolution_caveats') or []},'execution_eligibility':pt.get('execution_eligibility') or {'execution_policy':pt.get('execution_policy')},'current_observation':{},'eod_reference':{},'performance':{},'coverage':{'evidence_states':{'identity':'supported' if pt.get('identity_status')=='resolved' else 'unavailable','lifecycle':'supported' if pt.get('lifecycle_resolution_status')=='resolved' else 'supported_with_caveat' if pt.get('lifecycle_resolution_status') else 'unavailable','current_observation':_status_from_cov(cov,'current_evidence'),'eod_reference':_status_from_cov(cov,'eod_reference'),'performance':'not_applicable'},'coverage_state':cov.get('coverage_state'),'missing_field_groups':cov.get('missing_field_groups',[])},'missing_evidence':[],'caveats':list(pt.get('resolution_caveats') or [])+list(bt.get('issues') or []),'allowed_interpretations':['identify governed target','discuss cited supplied evidence and caveats'],'prohibited_inferences':['do not infer adjusted returns','do not infer future returns','do not infer causality from price evidence'],'citations':[]}
        for f in ['canonical_target_id','security_code','security_name_zh','market','instrument_type','classification_status','snapshot_id','record_id','record_hash']:
            if target['identity'].get(f) is not None:
                target['citations'].append(_citation(pkg,tid,f'/targets/{pos}/identity/{f}','identity_'+f,target['identity'][f],'verified_security_master_snapshot',target['identity'].get('snapshot_id') or execution_plan.get('plan_id'),f'/targets/{pos}/resolution_evidence/0',None,None,None,None,'supported'))
        cur=bt.get('current_evidence') or {}
        if cur:
            facts=cur.get('facts') or {}; target['current_observation']={k:facts[k] for k in MATERIAL_CURRENT if k in facts and facts.get(k) is not None}; target['current_observation'].update({k:cur.get(k) for k in ('source_timestamp','retrieved_at_utc','source_family') if cur.get(k) is not None}); target['current_observation']['currentness_status']=_get(cur,'currentness','status',default='unresolved')
            if not cur.get('source_timestamp') and target['current_observation']: target['missing_evidence'].append(_missing(tid,'current_observation','currentness_unresolved',cur.get('source_family'),False,detail={'retrieved_at_utc':cur.get('retrieved_at_utc')})); target['caveats'].append('currentness_unresolved')
            if _get(cur,'currentness','status')=='stale': target['missing_evidence'].append(_missing(tid,'current_observation','stale_observation',cur.get('source_family'),False)); target['caveats'].append('stale_observation')
            for k,v in target['current_observation'].items():
                if k in MATERIAL_CURRENT+['source_timestamp','retrieved_at_utc','currentness_status']:
                    target['citations'].append(_citation(pkg,tid,f'/targets/{pos}/current_observation/{k}','current_'+k,v,'watchlist_bundle',watchlist_bundle.get('bundle_id'),f'/targets/{pos}/current_evidence',cur.get('source_family'),cur.get('source_timestamp'),cur.get('retrieved_at_utc'),target['current_observation'].get('currentness_status'),'stale' if target['current_observation'].get('currentness_status')=='stale' else 'supported'))
        eod=bt.get('eod_reference') or {}
        if eod:
            facts=eod.get('facts') or {}; target['eod_reference']={k:facts[k] for k in ['open','high','low','close','volume'] if k in facts and facts.get(k) is not None}; target['eod_reference'].update({'official_trade_date':eod.get('trade_date'),'source_family':eod.get('source_family')})
            for k,v in target['eod_reference'].items(): target['citations'].append(_citation(pkg,tid,f'/targets/{pos}/eod_reference/{k}','eod_'+k,v,'watchlist_bundle',watchlist_bundle.get('bundle_id'),f'/targets/{pos}/eod_reference',eod.get('source_family'),eod.get('trade_date'),eod.get('retrieved_at_utc'),None,'supported'))
        metrics=[m for m in watchlist_bundle.get('derived_metrics',[]) if m.get('target_id')==tid or any(d.get('target_id')==tid for d in (m.get('source_dependencies') or []))]
        if metrics:
            m=metrics[0]; target['performance']={k:m.get(k) for k in MATERIAL_PERF if k in m}; target['performance'].update({'metric_id':m.get('metric_id'),'calculation_status':m.get('calculation_status'),'requested_lookback_trading_days':_get(m,'input_period','lookback_trading_days'),'end_date':m.get('as_of'),'unadjusted_price_return':m.get('value'),'valid_observation_count':len(m.get('source_dependencies') or [])}); target['coverage']['evidence_states']['performance']='supported' if m.get('calculation_status')=='calculated' else 'unavailable'; target['caveats'].append('unadjusted_price_return') ; target['prohibited_inferences'].append('do not claim adjusted or total return')
            pkg['prohibitions'].append({'code':'do_not_claim_adjusted_return','scope':'target','target_id':tid,'reason':'performance uses upstream unadjusted completed EOD closes'})
            for k,v in target['performance'].items():
                if v is not None: target['citations'].append(_citation(pkg,tid,f'/targets/{pos}/performance/{k}','performance_'+k,v,'watchlist_bundle',watchlist_bundle.get('bundle_id'),'/derived_metrics',None,None,None,None,'supported' if m.get('calculation_status')=='calculated' else 'unavailable'))
        for miss in watchlist_bundle.get('missing_evidence',[]):
            if miss.get('target_id')==tid:
                cap=miss.get('capability_id','unknown')
                cat={'current_mis_observation':'current_observation','official_eod_reference':'official_eod_reference','currentness_validation':'currentness_validation','identity_resolution':'identity'}.get(cap, cap if cap in {'identity','current_observation','currentness_validation','official_eod_reference','performance','history','unknown'} else 'unknown')
                target['missing_evidence'].append(_missing(tid,cat,miss.get('reason_code','evidence_not_requested'),None,bool(miss.get('required_for_answer')),detail=miss))
        if pt.get('identity_status')!='resolved': target['missing_evidence'].append(_missing(tid,'identity',pt.get('identity_status') or 'identity_unresolved',None,True,'not_recoverable_in_scope',{'plan_issues':pt.get('blocking_issues',[])})); pkg['prohibitions'].append({'code':'do_not_claim_live_price','scope':'target','target_id':tid,'reason':'target identity/execution eligibility is not resolved'})
        if not target['current_observation']: pkg['prohibitions'].append({'code':'do_not_claim_live_price','scope':'target','target_id':tid,'reason':'current observation unavailable'})
        pkg['missing_evidence'].extend(target['missing_evidence']); pkg['caveats'].extend(str(c) for c in target['caveats']); pkg['targets'].append(target)
    failed=[g for g in pkg['source_lineage']['source_group_summaries'] if g.get('status')=='failed']
    complete=sum(1 for t in pkg['targets'] if t['coverage']['coverage_state']=='usable'); blocked=sum(1 for t in pkg['targets'] if t['coverage']['evidence_states']['identity']=='unavailable')
    status='blocked' if execution_result.get('status')=='blocked_preflight' else 'failed' if execution_result.get('status')=='source_execution_failed' else 'partial' if failed or complete<len(pkg['targets']) else 'complete'
    pkg['coverage_summary']={'target_count_requested':len(pkg['targets']),'target_count_resolved':sum(1 for t in pkg['targets'] if t['coverage']['evidence_states']['identity']!='unavailable'),'target_count_with_current_observation':sum(1 for t in pkg['targets'] if t['current_observation']),'target_count_with_eod_reference':sum(1 for t in pkg['targets'] if t['eod_reference']),'target_count_with_performance':sum(1 for t in pkg['targets'] if t['performance']),'complete_target_count':complete,'partial_target_count':sum(1 for t in pkg['targets'] if t['coverage']['coverage_state']=='partial'),'blocked_target_count':blocked,'failed_source_groups':[g.get('source_family') for g in failed],'coverage_status':status}
    if status!='complete': pkg['caveats'].append(status+'_coverage')
    # deterministic truncation of nonblocking global lists only; targets retained
    for key,limit in [('missing_evidence',policy['max_missing_evidence_entries']),('caveats',policy['max_caveat_entries'])]:
        if len(pkg[key])>limit:
            pkg['context_budget']['omitted_counts'][key]=len(pkg[key])-limit; pkg[key]=pkg[key][:limit]; pkg['context_budget']['truncated']=True
    if policy.get('max_caveat_entries') == 0 and not pkg['context_budget']['truncated']:
        pkg['context_budget']['truncated']=True
    if pkg['context_budget']['truncated']: pkg['caveats'].append('context_truncated')
    pkg['context_package_id']='m8r03e-context-'+sha256_json({k:pkg[k] for k in pkg if k not in {'context_package_id','package_hash'}})[:16]
    pkg['package_hash']=artifact_hash_without(pkg,'package_hash')
    return pkg

def build_context_manifest(*, context_package:dict, conversation_handoff:dict, upstream_artifacts:dict, generated_at_utc:str)->dict:
    up={'request_id':context_package.get('request',{}).get('request_id'),'request_hash':sha256_json(upstream_artifacts.get('validated_request',{})),'execution_plan_id':upstream_artifacts.get('execution_plan',{}).get('plan_id'),'execution_plan_hash':sha256_json(upstream_artifacts.get('execution_plan',{})),'execution_result_id':upstream_artifacts.get('execution_result',{}).get('run_id'),'execution_result_hash':sha256_json(upstream_artifacts.get('execution_result',{})),'bundle_id':upstream_artifacts.get('watchlist_bundle',{}).get('bundle_id'),'bundle_hash':sha256_json(upstream_artifacts.get('watchlist_bundle',{})),'security_master_snapshot_ids':sorted({t.get('identity',{}).get('snapshot_id') for t in context_package.get('targets',[]) if t.get('identity',{}).get('snapshot_id')})}
    m={'schema_version':MANIFEST_SCHEMA_VERSION,'context_package_id':context_package['context_package_id'],'handoff_id':conversation_handoff['handoff_id'],'generated_at_utc':generated_at_utc,'builder_version':BUILDER_VERSION,'context_package_sha256':sha256_json(context_package),'conversation_handoff_sha256':sha256_json(conversation_handoff),'schema_bundle_sha256':schema_bundle_sha256(),'upstream':up,'counts':{'target_count':len(context_package.get('targets',[])),'fact_count':len(context_package.get('citation_index',[])),'citation_count':len(context_package.get('citation_index',[])),'missing_evidence_count':len(context_package.get('missing_evidence',[])),'caveat_count':len(context_package.get('caveats',[])),'prohibition_count':len(context_package.get('prohibitions',[]))},'validation_status':'passed','validation_issues':[]}
    return m

def render_watchlist_ai_context_preview(package:dict)->str:
    lines=['# Watchlist AI Context Preview','','## Request summary',f"- Request ID: {package['request']['request_id']}",f"- Bundle type: {package['request']['bundle_type']}",'','## Coverage',f"- Status: {package['coverage_summary']['coverage_status']}",f"- Targets: {package['coverage_summary']['target_count_requested']}",'','## Targets in request order']
    cby={c['fact_path']:c['citation_id'] for c in package.get('citation_index',[])}
    for t in package.get('targets',[]):
        lines += [f"### {t['target_position']}. {t['target_id']}",'','#### Identity and lifecycle',f"- Name: {t['identity'].get('security_name_zh')} [{cby.get('/targets/%s/identity/security_name_zh'%t['target_position'],'no-citation')}]",f"- Lifecycle: {t['lifecycle'].get('lifecycle_state')}",'','#### Current observation']
        if t['current_observation']:
            for k,v in t['current_observation'].items(): lines.append(f"- {k}: {v} [{cby.get('/targets/%s/current_observation/%s'%(t['target_position'],k),'no-citation')}]")
        else: lines.append('- Unavailable')
        lines += ['','#### Completed EOD reference']
        if t['eod_reference']:
            for k,v in t['eod_reference'].items(): lines.append(f"- {k}: {v} [{cby.get('/targets/%s/eod_reference/%s'%(t['target_position'],k),'no-citation')}]")
        else: lines.append('- Unavailable')
        lines += ['','#### Performance']
        if t['performance']:
            for k,v in t['performance'].items(): lines.append(f"- {k}: {v} [{cby.get('/targets/%s/performance/%s'%(t['target_position'],k),'no-citation')}]")
        else: lines.append('- Not applicable or unavailable')
        lines += ['','#### Missing evidence']+[f"- {m['category']}: {m['reason_code']}" for m in t['missing_evidence']] or ['- None']
        lines += ['','#### Caveats']+[f"- {c}" for c in t['caveats']] + ['','#### Prohibited interpretations']+[f"- {p}" for p in t['prohibited_inferences']]
    lines += ['','## Source lineage',f"- Execution status: {package['source_lineage'].get('execution_result_status')}",f"- Network calls performed: {package['source_lineage'].get('network_calls_performed')}"]
    return '\n'.join(str(x) for x in lines)+'\n'
