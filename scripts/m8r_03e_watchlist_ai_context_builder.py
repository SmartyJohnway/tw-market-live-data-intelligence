from __future__ import annotations
import json
from typing import Any
from scripts.m8r_03e_context_validator import *
DEFAULT_POLICY={'max_citations_per_target':40,'max_missing_evidence_entries':80,'max_caveat_entries':80,'max_lifecycle_event_summaries_per_target':3,'max_serialized_bytes':250000}
MATERIAL_CURRENT=['latest_price','change','change_percent','open','high','low','volume','no_trade_state']
IDENTITY_MAP={'canonical_target_id':'target_id','security_code':'security_code','security_name_zh':'security_name','security_name_en':'resolved_identity/security_name_en','market':'market','instrument_type':'instrument_type','classification_status':'classification_status','snapshot_id':'snapshot_id','record_id':'record_id','record_hash':'record_hash'}
PERF_MAP={'metric_id':'metric_id','calculation_status':'calculation_status','requested_lookback_trading_days':'input_period/lookback_trading_days','end_date':'as_of','unadjusted_price_return':'value'}
CLASSIFICATION_MAP={'classification_status':'classification_status','instrument_type':'instrument_type','market':'market'}
LIFECYCLE_MAP={'lifecycle_state':'lifecycle_state','lifecycle_resolution_status':'lifecycle_resolution_status','as_of_date':'execution_eligibility/as_of_date','basis_event_ids':'execution_eligibility/basis_event_ids','execution_policy':'execution_policy','lifecycle_caveats':'resolution_caveats'}
EXECUTION_ELIGIBILITY_MAP={'status':'execution_eligibility/status','reason_codes':'execution_eligibility/reason_codes','execution_policy':'execution_policy'}

def _get(d,*keys,default=None):
    cur=d
    for k in keys:
        if not isinstance(cur,dict): return default
        cur=cur.get(k)
    return default if cur is None else cur

def _cid(seed): return 'cite-'+sha256_json(seed)[:20]
def _mid(seed): return 'missing-'+sha256_json(seed)[:20]
def _source_ptr(*parts): return '/' + '/'.join(str(p).replace('~','~0').replace('/','~1') for p in parts)
def _citation(pkg,target_id,path,fact_type,value,source_type,source_id,source_path,source_family=None,observed_at=None,retrieved_at=None,currentness_status=None,evidence_status='supported',caveats=None):
    c={'schema_version':CITATION_SCHEMA_VERSION,'citation_id':_cid({'target_id':target_id,'path':path,'source_type':source_type,'source_id':source_id,'source_path':source_path}),'target_id':target_id,'fact_path':path,'fact_type':fact_type,'value_hash':sha256_json(value),'source_artifact_type':source_type,'source_artifact_id':source_id or 'unknown','source_path':source_path,'source_family':source_family,'observed_at':observed_at,'retrieved_at_utc':retrieved_at,'currentness_status':currentness_status,'evidence_status':evidence_status,'caveats':caveats or []}
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

def _source_group_missing(plan, result, tid):
    failed=[]
    for g in (result.get('source_execution_summary') or {}).get('group_results',[]):
        if g.get('status')=='failed' and tid in (g.get('target_ids') or []): failed.append(g)
    return failed

def _metric_target(m, tid): return m.get('target_id')==tid or any(d.get('target_id')==tid for d in (m.get('source_dependencies') or []))
def _metric_index(metrics, metric):
    for i,m in enumerate(metrics):
        if m is metric: return i
    return 0

def _remove_citations_for_paths(pkg, target, prefixes):
    rm={c['citation_id'] for c in pkg['citation_index'] if c.get('target_id')==target['target_id'] and any(c.get('fact_path','').startswith(p) for p in prefixes)}
    if rm:
        pkg['citation_index']=[c for c in pkg['citation_index'] if c['citation_id'] not in rm]
        target['citations']=[c for c in target['citations'] if c not in rm]
        return len(rm)
    return 0



def _section_state(t, sec):
    return 'supported' if t.get(sec) else 'unavailable'

def _recompute_after_budget(pkg):
    for t in pkg['targets']:
        t['coverage']['evidence_states']['current_observation']=_section_state(t,'current_observation')
        t['coverage']['evidence_states']['eod_reference']=_section_state(t,'eod_reference')
        t['coverage']['evidence_states']['performance']=_section_state(t,'performance') if t['coverage']['evidence_states'].get('performance')!='not_applicable' else ('supported' if t.get('performance') else 'not_applicable')
        if t['coverage']['evidence_states']['identity']=='unavailable': t['coverage']['coverage_state']='unavailable'
        elif any(t['coverage']['evidence_states'].get(k)=='unavailable' for k in ('current_observation','eod_reference') if k in t['coverage']['evidence_states']): t['coverage']['coverage_state']='partial'
        elif t['coverage']['evidence_states'].get('performance')=='unavailable': t['coverage']['coverage_state']='partial'
        else: t['coverage']['coverage_state']='usable'
    failed=[g for g in pkg['source_lineage']['source_group_summaries'] if g.get('status')=='failed']
    complete=sum(1 for t in pkg['targets'] if t['coverage']['coverage_state']=='usable')
    blocked=sum(1 for t in pkg['targets'] if t['coverage']['evidence_states']['identity']=='unavailable')
    status='partial' if failed or complete<len(pkg['targets']) else 'complete'
    if pkg['source_lineage'].get('execution_result_status')=='blocked_preflight': status='blocked'
    elif pkg['source_lineage'].get('execution_result_status')=='source_execution_failed': status='failed'
    pkg['coverage_summary']={'target_count_requested':len(pkg['targets']),'target_count_resolved':sum(1 for t in pkg['targets'] if t['coverage']['evidence_states']['identity']!='unavailable'),'target_count_with_current_observation':sum(1 for t in pkg['targets'] if t['current_observation']),'target_count_with_eod_reference':sum(1 for t in pkg['targets'] if t['eod_reference']),'target_count_with_performance':sum(1 for t in pkg['targets'] if t['performance']),'complete_target_count':complete,'partial_target_count':sum(1 for t in pkg['targets'] if t['coverage']['coverage_state']=='partial'),'blocked_target_count':blocked,'failed_source_groups':[g.get('source_family') for g in failed],'coverage_status':status}

def _apply_budget(pkg, policy):
    omitted=pkg['context_budget']['omitted_counts']
    # Per-target citation pressure: remove lower-priority projected sections, never identity.
    for t in pkg['targets']:
        limit=policy.get('max_citations_per_target')
        if limit is not None and len(t['citations'])>limit:
            for sec in ('performance','eod_reference','current_observation'):
                if len(t['citations'])<=limit: break
                if t.get(sec):
                    omitted['citations']+=_remove_citations_for_paths(pkg,t,[f"/targets/{t['target_position']}/{sec}/"])
                    t[sec]={}; t['missing_evidence'].append(_missing(t['target_id'], {'current_observation':'current_observation','eod_reference':'official_eod_reference','performance':'performance'}[sec], 'context_budget_omitted', None, False, 'requires_new_source', {'budget_limit':'max_citations_per_target'})); pkg['missing_evidence'].append(t['missing_evidence'][-1]); t['caveats'].append('context_budget_omitted_'+sec)
            if len(t['citations'])>limit: pkg['context_budget']['truncated']=True
    for key,limit in [('missing_evidence',policy.get('max_missing_evidence_entries')),('caveats',policy.get('max_caveat_entries'))]:
        if limit is not None and len(pkg[key])>limit:
            omitted[key]=len(pkg[key])-limit; pkg[key]=pkg[key][:limit]; pkg['context_budget']['truncated']=True
    # Serialized-byte pressure: deterministic low-priority removal until within budget.
    max_bytes=policy.get('max_serialized_bytes')
    if max_bytes:
        for sec in ('performance','eod_reference','current_observation'):
            if len(canonical_json(pkg).encode())<=max_bytes: break
            for t in pkg['targets']:
                if t.get(sec):
                    omitted['citations']+=_remove_citations_for_paths(pkg,t,[f"/targets/{t['target_position']}/{sec}/"])
                    t[sec]={}; t['missing_evidence'].append(_missing(t['target_id'], {'current_observation':'current_observation','eod_reference':'official_eod_reference','performance':'performance'}[sec], 'context_budget_omitted', None, False, 'requires_new_source', {'budget_limit':'max_serialized_bytes'})); pkg['missing_evidence'].append(t['missing_evidence'][-1]); t['caveats'].append('context_budget_omitted_'+sec); pkg['context_budget']['truncated']=True
                if len(canonical_json(pkg).encode())<=max_bytes: break
    if policy.get('max_caveat_entries') == 0 and not pkg['context_budget']['truncated']:
        pkg['context_budget']['truncated']=True
    if pkg['context_budget']['truncated'] and 'context_truncated' not in pkg['caveats']: pkg['caveats'].append('context_truncated')
    _recompute_after_budget(pkg)
    pkg['context_budget']['final_serialized_bytes']=len(canonical_json(pkg).encode())
    max_bytes=policy.get('max_serialized_bytes')
    if max_bytes and pkg['context_budget']['final_serialized_bytes']>max_bytes:
        pkg['context_budget']['budget_satisfied']=False
        pkg['context_budget']['minimum_required_context_exceeds_budget']=True

def build_watchlist_ai_context_package(*, validated_request:dict, execution_plan:dict, execution_result:dict, watchlist_bundle:dict, generated_at_utc:str, context_policy:dict|None=None) -> dict:
    upstream_validation=validate_m8r_03e_upstream_artifacts(validated_request=validated_request, execution_plan=execution_plan, execution_result=execution_result, watchlist_bundle=watchlist_bundle)
    if not upstream_validation['valid']: raise ValueError('upstream_artifact_validation_failed:'+canonical_json(upstream_validation['issues']))
    policy={**DEFAULT_POLICY,**(context_policy or {})}; bundle_type=upstream_validation['bundle_type']
    pkg={'schema_version':PACKAGE_SCHEMA_VERSION,'context_package_id':'','generated_at_utc':generated_at_utc,'request':_project_request(validated_request,bundle_type),'conversation_scope':{'analysis_mode':bundle_type if bundle_type in {'snapshot','performance'} else 'comparison','allowed_topics':['identity','current observation','completed EOD reference','bounded historical performance','coverage','missing evidence','caveats'],'disallowed_topics':['personalized investment advice','trade recommendation','future return prediction','unsupported causal claims','order execution']},'source_lineage':{'execution_result_status':execution_result.get('status'),'execution_mode':execution_result.get('mode'),'network_calls_performed':bool(_get(execution_result,'source_execution_summary','network_calls_performed',default=False)),'source_group_summaries':_get(execution_result,'source_execution_summary','group_results',default=[]),'bundle_id':watchlist_bundle.get('bundle_id'),'plan_id':execution_plan.get('plan_id'),'lineage_status':'partial','lineage_missing_fields':['execution_result_bundle_id','execution_result_bundle_hash']},'targets':[],'cross_target_context':{'target_order':execution_plan.get('target_order') or []},'coverage_summary':{},'missing_evidence':[],'caveats':[],'prohibitions':[{'code':'do_not_infer_active_from_missing_lifecycle_event','scope':'global','target_id':None,'reason':'lifecycle must come from verified upstream identity evidence'},{'code':'do_not_treat_retrieval_time_as_market_time','scope':'global','target_id':None,'reason':'retrieval timestamp alone never proves market currentness'}],'citation_index':[],'context_budget':{'policy':policy,'omitted_counts':{'citations':0,'missing_evidence':0,'caveats':0},'truncated':False,'final_serialized_bytes':0,'budget_satisfied':True,'minimum_required_context_exceeds_budget':False},'package_hash':None}
    plan_by={t['target_id']:(i,t) for i,t in enumerate(execution_plan.get('targets',[]))}; bundle_by={t['target_id']:(i,t) for i,t in enumerate(watchlist_bundle.get('targets',[]))}; metrics_all=watchlist_bundle.get('derived_metrics',[])
    for pos,tid in enumerate(pkg['request']['enabled_target_order']):
        plan_i,pt=plan_by.get(tid,(pos,{})); bundle_i,bt=bundle_by.get(tid,(pos,{})); cov=bt.get('coverage') or {'coverage_state':'unavailable','present_field_groups':[],'missing_field_groups':[]}
        target={'target_id':tid,'target_position':pos,'identity':_identity_from_plan_target(pt),'classification':{'classification_status':pt.get('classification_status'),'instrument_type':pt.get('instrument_type'),'market':pt.get('market')},'lifecycle':{'lifecycle_state':pt.get('lifecycle_state'),'lifecycle_resolution_status':pt.get('lifecycle_resolution_status'),'as_of_date':_get(pt,'execution_eligibility','as_of_date'),'basis_event_ids':_get(pt,'execution_eligibility','basis_event_ids',default=[]),'execution_policy':pt.get('execution_policy'),'lifecycle_caveats':pt.get('resolution_caveats') or []},'execution_eligibility':pt.get('execution_eligibility') or {'execution_policy':pt.get('execution_policy')},'current_observation':{},'eod_reference':{},'performance':{},'coverage':{'evidence_states':{'identity':'supported' if pt.get('identity_status')=='resolved' else 'unavailable','lifecycle':'supported' if pt.get('lifecycle_resolution_status')=='resolved' else 'supported_with_caveat' if pt.get('lifecycle_resolution_status') else 'unavailable','current_observation':_status_from_cov(cov,'current_evidence'),'eod_reference':_status_from_cov(cov,'eod_reference'),'performance':'not_applicable'},'coverage_state':cov.get('coverage_state'),'missing_field_groups':cov.get('missing_field_groups',[])},'missing_evidence':[],'caveats':list(pt.get('resolution_caveats') or [])+list(bt.get('issues') or []),'allowed_interpretations':['identify governed target','discuss cited supplied evidence and caveats'],'prohibited_inferences':['do not infer adjusted returns','do not infer future returns','do not infer causality from price evidence'],'citations':[]}
        for f,src in IDENTITY_MAP.items():
            if target['identity'].get(f) is not None:
                target['citations'].append(_citation(pkg,tid,_source_ptr('targets',pos,'identity',f),'identity_'+f,target['identity'][f],'execution_plan',execution_plan.get('plan_id'),'/targets/%s/%s'%(plan_i,src),None,None,None,None,'supported'))
        for f,src in CLASSIFICATION_MAP.items():
            if target['classification'].get(f) is not None:
                target['citations'].append(_citation(pkg,tid,_source_ptr('targets',pos,'classification',f),'classification_'+f,target['classification'][f],'execution_plan',execution_plan.get('plan_id'),'/targets/%s/%s'%(plan_i,src),None,None,None,None,'supported'))
        for f,src in LIFECYCLE_MAP.items():
            if target['lifecycle'].get(f) not in (None, [], {}):
                target['citations'].append(_citation(pkg,tid,_source_ptr('targets',pos,'lifecycle',f),'lifecycle_'+f,target['lifecycle'][f],'execution_plan',execution_plan.get('plan_id'),'/targets/%s/%s'%(plan_i,src),None,None,None,None,'supported'))
        for f,src in EXECUTION_ELIGIBILITY_MAP.items():
            if target['execution_eligibility'].get(f) not in (None, [], {}):
                target['citations'].append(_citation(pkg,tid,_source_ptr('targets',pos,'execution_eligibility',f),'execution_eligibility_'+f,target['execution_eligibility'][f],'execution_plan',execution_plan.get('plan_id'),'/targets/%s/%s'%(plan_i,src),None,None,None,None,'supported'))
        cur=bt.get('current_evidence') or {}
        if cur:
            facts=cur.get('facts') or {}; target['current_observation']={k:facts[k] for k in MATERIAL_CURRENT if k in facts and facts.get(k) is not None}; target['current_observation'].update({k:cur.get(k) for k in ('source_timestamp','retrieved_at_utc','source_family') if cur.get(k) is not None}); target['current_observation']['currentness_status']=_get(cur,'currentness','status',default='unresolved')
            if not cur.get('source_timestamp') and target['current_observation']: target['missing_evidence'].append(_missing(tid,'current_observation','currentness_unresolved',cur.get('source_family'),False,detail={'retrieved_at_utc':cur.get('retrieved_at_utc')})); target['caveats'].append('currentness_unresolved')
            if _get(cur,'currentness','status')=='stale': target['missing_evidence'].append(_missing(tid,'current_observation','stale_observation',cur.get('source_family'),False)); target['caveats'].append('stale_observation')
            for k,v in target['current_observation'].items():
                src_path='/targets/%s/current_evidence/%s'%(bundle_i, 'currentness/status' if k=='currentness_status' else k if k in {'source_timestamp','retrieved_at_utc','source_family'} else 'facts/'+k)
                target['citations'].append(_citation(pkg,tid,_source_ptr('targets',pos,'current_observation',k),'current_'+k,v,'watchlist_bundle',watchlist_bundle.get('bundle_id'),src_path,cur.get('source_family'),cur.get('source_timestamp'),cur.get('retrieved_at_utc'),target['current_observation'].get('currentness_status'),'stale' if target['current_observation'].get('currentness_status')=='stale' else 'supported'))
        eod=bt.get('eod_reference') or {}
        if eod:
            facts=eod.get('facts') or {}; target['eod_reference']={k:facts[k] for k in ['open','high','low','close','volume'] if k in facts and facts.get(k) is not None}; target['eod_reference'].update({'official_trade_date':eod.get('trade_date'),'source_family':eod.get('source_family')})
            for k,v in target['eod_reference'].items():
                src_key='trade_date' if k=='official_trade_date' else k if k=='source_family' else 'facts/'+k
                target['citations'].append(_citation(pkg,tid,_source_ptr('targets',pos,'eod_reference',k),'eod_'+k,v,'watchlist_bundle',watchlist_bundle.get('bundle_id'),'/targets/%s/eod_reference/%s'%(bundle_i,src_key),eod.get('source_family'),eod.get('trade_date'),eod.get('retrieved_at_utc'),None,'supported'))
        metrics=[m for m in metrics_all if _metric_target(m,tid)]
        if metrics:
            m=metrics[0]; mi=_metric_index(metrics_all,m); target['performance']={'metric_id':m.get('metric_id'),'calculation_status':m.get('calculation_status'),'requested_lookback_trading_days':_get(m,'input_period','lookback_trading_days'),'end_date':m.get('as_of'),'unadjusted_price_return':m.get('value')}; target['coverage']['evidence_states']['performance']='supported' if m.get('calculation_status')=='calculated' else 'unavailable'; target['caveats'].append('unadjusted_price_return'); target['prohibited_inferences'].append('do not claim adjusted or total return')
            pkg['prohibitions'].append({'code':'do_not_claim_adjusted_return','scope':'target','target_id':tid,'reason':'performance uses upstream unadjusted completed EOD closes'})
            for k,src in PERF_MAP.items():
                v=target['performance'].get(k)
                if v is not None: target['citations'].append(_citation(pkg,tid,_source_ptr('targets',pos,'performance',k),'performance_'+k,v,'watchlist_bundle',watchlist_bundle.get('bundle_id'),'/derived_metrics/%s/%s'%(mi,src),None,None,None,None,'supported' if m.get('calculation_status')=='calculated' else 'unavailable'))
        for miss in watchlist_bundle.get('missing_evidence',[]):
            if miss.get('target_id')==tid:
                cap=miss.get('capability_id','unknown'); cat={'current_mis_observation':'current_observation','official_eod_reference':'official_eod_reference','currentness_validation':'currentness_validation','identity_resolution':'identity'}.get(cap, cap if cap in {'identity','current_observation','currentness_validation','official_eod_reference','performance','history','unknown'} else 'unknown')
                target['missing_evidence'].append(_missing(tid,cat,miss.get('reason_code','evidence_not_requested'),None,bool(miss.get('required_for_answer')),detail=miss))
        for g in _source_group_missing(execution_plan,execution_result,tid): target['missing_evidence'].append(_missing(tid,'current_observation','source_execution_failed',g.get('source_family'),False,detail=g))
        if pt.get('identity_status')!='resolved': target['missing_evidence'].append(_missing(tid,'identity',pt.get('identity_status') or 'identity_unresolved',None,True,'not_recoverable_in_scope',{'plan_issues':pt.get('blocking_issues',[])})); pkg['prohibitions'].append({'code':'do_not_claim_live_price','scope':'target','target_id':tid,'reason':'target identity/execution eligibility is not resolved'})
        if not target['current_observation']: pkg['prohibitions'].append({'code':'do_not_claim_live_price','scope':'target','target_id':tid,'reason':'current observation unavailable'})
        pkg['missing_evidence'].extend(target['missing_evidence']); pkg['caveats'].extend(str(c) for c in target['caveats']); pkg['targets'].append(target)
    _recompute_after_budget(pkg)
    if pkg['coverage_summary']['coverage_status']!='complete': pkg['caveats'].append(pkg['coverage_summary']['coverage_status']+'_coverage')
    _apply_budget(pkg,policy)
    pkg['context_package_id']='m8r03e-context-'+sha256_json({k:pkg[k] for k in pkg if k not in {'context_package_id','package_hash'}})[:16]
    pkg['package_hash']=artifact_hash_without(pkg,'package_hash')
    validation=validate_watchlist_ai_context_package(pkg, upstream_artifacts={'execution_plan':execution_plan,'watchlist_bundle':watchlist_bundle,'execution_result':execution_result,'validated_request':validated_request})
    if not validation['valid']: raise ValueError('context_package_validation_failed:'+canonical_json(validation['issues']))
    return pkg

def build_context_manifest(*, context_package:dict, conversation_handoff:dict, upstream_artifacts:dict, generated_at_utc:str)->dict:
    up={'request_id':context_package.get('request',{}).get('request_id'),'request_hash':sha256_json(upstream_artifacts.get('validated_request',{})),'execution_plan_id':upstream_artifacts.get('execution_plan',{}).get('plan_id'),'execution_plan_hash':sha256_json(upstream_artifacts.get('execution_plan',{})),'execution_result_id':upstream_artifacts.get('execution_result',{}).get('run_id'),'execution_result_hash':sha256_json(upstream_artifacts.get('execution_result',{})),'bundle_id':upstream_artifacts.get('watchlist_bundle',{}).get('bundle_id'),'bundle_hash':sha256_json(upstream_artifacts.get('watchlist_bundle',{})),'security_master_snapshot_ids':sorted({t.get('identity',{}).get('snapshot_id') for t in context_package.get('targets',[]) if t.get('identity',{}).get('snapshot_id')})}
    m={'schema_version':MANIFEST_SCHEMA_VERSION,'context_package_id':context_package['context_package_id'],'handoff_id':conversation_handoff['handoff_id'],'generated_at_utc':generated_at_utc,'builder_version':BUILDER_VERSION,'context_package_sha256':sha256_json(context_package),'conversation_handoff_sha256':sha256_json(conversation_handoff),'schema_bundle_sha256':schema_bundle_sha256(),'upstream':up,'counts':{'target_count':len(context_package.get('targets',[])),'fact_count':len(material_fact_paths(context_package)),'citation_count':len(context_package.get('citation_index',[])),'missing_evidence_count':len(context_package.get('missing_evidence',[])),'caveat_count':len(context_package.get('caveats',[])),'prohibition_count':len(context_package.get('prohibitions',[]))},'validation_status':'passed','validation_issues':[]}
    return m

def render_watchlist_ai_context_preview(package:dict)->str:
    validation=validate_watchlist_ai_context_package(package)
    if not validation['valid'] and any(i['code'] in {'uncited_material_fact','missing_identity_citation','target_orphan_citation'} for i in validation['issues']): raise ValueError('preview_material_citation_validation_failed')
    lines=['# Watchlist AI Context Preview','','## Request summary',f"- Request ID: {package['request']['request_id']}",f"- Bundle type: {package['request']['bundle_type']}",'','## Coverage',f"- Status: {package['coverage_summary']['coverage_status']}",f"- Targets: {package['coverage_summary']['target_count_requested']}",'','## Targets in request order']
    cby={c['fact_path']:c['citation_id'] for c in package.get('citation_index',[])}
    def cite(path):
        if path not in cby: raise ValueError('preview_missing_citation:'+path)
        return cby[path]
    for t in package.get('targets',[]):
        pos=t['target_position']; lines += [f"### {pos}. {t['target_id']}",'','#### Identity and lifecycle']
        if t['identity'].get('security_name_zh') is not None: lines.append(f"- Name: {t['identity'].get('security_name_zh')} [{cite(f'/targets/{pos}/identity/security_name_zh')}]")
        lines += [f"- Lifecycle: {t['lifecycle'].get('lifecycle_state')} [{cite(f'/targets/{pos}/lifecycle/lifecycle_state')}]",'','#### Current observation']
        if t['current_observation']:
            for k,v in t['current_observation'].items(): lines.append(f"- {k}: {v} [{cite(f'/targets/{pos}/current_observation/{k}')}]")
        else: lines.append('- Unavailable')
        lines += ['','#### Completed EOD reference']
        if t['eod_reference']:
            for k,v in t['eod_reference'].items(): lines.append(f"- {k}: {v} [{cite(f'/targets/{pos}/eod_reference/{k}')}]")
        else: lines.append('- Unavailable')
        lines += ['','#### Performance']
        if t['performance']:
            for k,v in t['performance'].items(): lines.append(f"- {k}: {v} [{cite(f'/targets/{pos}/performance/{k}')}]")
        else: lines.append('- Not applicable or unavailable')
        lines += ['','#### Missing evidence']+([f"- {m['category']}: {m['reason_code']}" for m in t['missing_evidence']] or ['- None'])
        lines += ['','#### Caveats']+[f"- {c}" for c in t['caveats']] + ['','#### Prohibited interpretations']+[f"- {p}" for p in t['prohibited_inferences']]
    lines += ['','## Source lineage',f"- Execution status: {package['source_lineage'].get('execution_result_status')}",f"- Network calls performed: {package['source_lineage'].get('network_calls_performed')}"]
    return '\n'.join(str(x) for x in lines)+'\n'
