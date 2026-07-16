from __future__ import annotations
from scripts.m8r_03e_context_validator import HANDOFF_SCHEMA_VERSION, artifact_hash_without, sha256_json

def build_watchlist_conversation_handoff(*, context_package:dict, generated_at_utc:str)->dict:
    cov=context_package.get('coverage_summary',{}); has_cur=cov.get('target_count_with_current_observation',0)>0; has_eod=cov.get('target_count_with_eod_reference',0)>0; has_perf=cov.get('target_count_with_performance',0)>0
    ans=[]
    if has_cur: ans.append({'category':'latest_supplied_observations','question':'What are the latest supplied observations?','requires_citations':True})
    if has_eod: ans.append({'category':'completed_eod_reference','question':'What official completed EOD reference is available?','requires_citations':True})
    if has_perf: ans.append({'category':'bounded_unadjusted_performance','question':'What was the bounded unadjusted price performance?','requires_citations':True})
    ans.append({'category':'coverage_and_caveats','question':'Which targets lack evidence or have caveats?','requires_citations':False})
    part=[]
    if cov.get('coverage_status')!='complete': part.append({'category':'partial_coverage','question':'Which target evidence is incomplete?','reason':'coverage is not complete'})
    unsupported=[{'category':'causality','question':'Why did the stock move?'},{'category':'prediction','question':'What will happen tomorrow?'},{'category':'recommendation','question':'Should the user buy or sell?'},{'category':'adjusted_return','question':'What is the dividend-adjusted return?'},{'category':'news','question':'What is the company latest news?'},{'category':'valuation','question':'What is the fundamental valuation?'}]
    disclosures=['data currentness status','source failures' if cov.get('failed_source_groups') else None,'partial target coverage' if cov.get('coverage_status')!='complete' else None,'unadjusted performance semantics' if has_perf else None,'lifecycle uncertainty','fixture/non-live status' if context_package.get('source_lineage',{}).get('execution_mode')=='fixture' else None]
    h={'schema_version':HANDOFF_SCHEMA_VERSION,'handoff_id':'','generated_at_utc':generated_at_utc,'context_package_id':context_package['context_package_id'],'conversation_intent':context_package['request'].get('conversation_intent',{}),'target_order':context_package['request'].get('enabled_target_order',[]),'answerable_questions':ans,'partially_answerable_questions':part,'unsupported_questions':unsupported,'required_disclosures':[d for d in disclosures if d],'follow_up_evidence_options':[{'category':'current_observation','option':'retry with new explicit authorization'} if cov.get('target_count_with_current_observation',0)<cov.get('target_count_requested',0) else None, {'category':'history','option':'supply additional official EOD rows'} if has_perf and context_package.get('missing_evidence') else None], 'response_constraints':{'must_cite_material_facts':True,'must_not_provide_investment_advice':True,'must_not_predict_future_returns':True,'must_not_execute_orders':True},'citation_requirements':{'material_market_facts_require_citation':True,'identity_facts_require_citation':True,'unsupported_facts_must_be_disclosed':True},'handoff_hash':None}
    h['follow_up_evidence_options']=[x for x in h['follow_up_evidence_options'] if x]
    h['handoff_id']='m8r03e-handoff-'+sha256_json({k:h[k] for k in h if k not in {'handoff_id','handoff_hash'}})[:16]
    h['handoff_hash']=artifact_hash_without(h,'handoff_hash')
    return h
