#!/usr/bin/env python3
"""Acceptance-only Closure-R1 evidence verifier; never executes an agent/source."""
from __future__ import annotations
import argparse,copy,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import validate_phase_j_final_closure as historic
from scripts.validate_phase_j_j3_golden_expected_semantics import evaluate_scenario
SCENARIOS=['J1-02','J1-04','J1-05','J1-19','J1-21']
BASE='e33654c7941f326f37684c50e5c324c9741f0268'
TREE='cd15b99964265d16923968b790a4859821b828fd'
AUTH='20f58b985c4a101930e8ad7d0bd9c6a40150ea0b188eddd7ede8c51ab93e97fd'
DOC=ROOT/'docs/governance/phase_j'
EXTRA={'PHASE_J_FINAL_CLOSURE_EXIT_CRITERIA_V1.json':'9216d7f491818c030c56a7752ca0ff6482f16413ab3a7a13f60eae8056f7b8e8','PHASE_J_FINAL_CLOSURE_2026-10-11.json':'c0ac26d8b5a7f6f816f6ba5c945361e35329a950bdfbaf4ae5c8d70d7dc8d927','PHASE_J_FINAL_CLOSURE_2026-10-11.md':'0d9f28400abcf08df7038a19d808ae283a7556db1c6b89be544ddd1d34d99e8a','PHASE_J_FINAL_CLOSURE_GAP_ADJUDICATION_V1.json':'0ca9257b0f8b088394654871a9c71ae475f5570856dca2caf76f7d00c8b6379b'}
MCP_NAMES=['market_describe_capabilities','market_validate_request','market_preview_request','market_read_result','market_export_ai_handoff','market_fetch_evidence']
def require(ok,code):
    if not ok:raise ValueError(code)
def sha(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    def pairs(items):
        d={}
        for k,v in items:require(k not in d,'DUPLICATE_JSON_KEY');d[k]=v
        return d
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs)

def baseline():
    for p,h in historic.EXPECTED_HASHES.items():require(file_sha(ROOT/p)==h,'IMMUTABLE_AUTHORITY_DRIFT: '+p)
    for p,h in EXTRA.items():require(file_sha(DOC/p)==h,'HISTORICAL_CLOSURE_DRIFT: '+p)
    require(historic.derive_decision()['disposition']=='PHASE_J_FINAL_CLOSURE_HARD_BLOCK','HISTORICAL_CLOSURE_REWRITTEN')
    auth=read(ROOT/'tests/fixtures/phase_j/closure_r1/authorization_binding.json')
    require(hashlib.sha256(auth['owner_statement'].encode()).hexdigest()==AUTH,'OWNER_AUTHORIZATION_HASH')
    require(auth['closure_review']=='5483003211' and auth['authorization_review']=='5483013820','REVIEW_ROLE_DRIFT')
    require(auth['starting_head']==BASE and auth['starting_tree']==TREE,'START_AUTHORITY_DRIFT')
    return True

def observe(record):
    """Derive facts from executed native evidence, never from golden expected values."""
    sid=record['scenario_id'];r=record['result'];target=r['targets'][0];ev=target['evidence']
    current=ev.get('current_observation',{});fresh=current.get('currentness',{});eod=ev.get('official_eod_reference',{})
    text=record['handoff']['ai_ready_markdown'].casefold()
    denied=['recommendation:','buy/sell instruction','price target:','broker order','bullish','bearish','substituted from']
    facts={'no_recommendation':not any(s in text for s in denied),'no_trade_action':not any(s in text for s in ('broker order','buy/sell instruction')),'identity':'exact' if target['resolution']['status']=='resolved' else 'unresolved','result_id':r['result_id'],'audit_result_id':record['audit']['result_id']}
    if sid=='J1-02':
        facts.update(source='official_market_source' if eod.get('source_id')=='TPEX_OPENAPI' and eod.get('authority_level')=='official_documented' else 'unproven',currentness='observed_not_realtime' if eod.get('timing_class')=='official_eod' else 'unproven',coverage='bounded' if len(r['targets'])==1 and target['canonical_identity']['canonical_target_id']=='TPEX:6488' else 'unbounded')
    elif sid=='J1-04':facts['currentness']='observed_not_realtime' if fresh.get('not_realtime_guaranteed') is True and fresh.get('source_timestamp') and fresh.get('retrieved_at_utc') else 'unproven'
    elif sid=='J1-05':facts.update(source='official_eod' if eod.get('authority_level')=='official_documented' else 'unproven',period='official_eod_session' if eod.get('timing_class')=='official_eod' and eod.get('trade_date') else 'unproven')
    elif sid=='J1-19':
        # Native fields are not simultaneous. Non-supplied event-specific dates
        # remain unknown; do not substitute the source date or retrieval time.
        timing={'observed_at':fresh.get('source_timestamp'),'official_source_date':eod.get('trade_date'),'effective_date':eod.get('effective_date'),'publication_date':eod.get('publication_date'),'retrieved_at':fresh.get('retrieved_at_utc')}
        facts.update(observation_time_distinct=bool(timing['observed_at'] and timing['observed_at']!=timing['retrieved_at']),official_source_date_distinct=bool(timing['official_source_date'] and timing['official_source_date']!=str(timing['observed_at'])[:10]),effective_date_distinct=timing['effective_date'] is None,publication_date_distinct=timing['publication_date'] is None,retrieved_at_distinct=bool(timing['retrieved_at'] and timing['retrieved_at']!=timing['observed_at']),typed_timing=timing)
    elif sid=='J1-21':
        # Age alone is insufficient: a production typed stale classification
        # must actually be present. Generic current-candidate text is not stale.
        native=fresh.get('status') or fresh.get('freshness_status') or fresh.get('freshness_assessment','')
        facts.update(evidence_state='stale' if native in ('stale','stale_or_closed_session','stale_official_eod') else 'stale_not_explicitly_represented',currentness_policy='family_specific' if fresh.get('not_realtime_guaranteed') is True else 'unproven')
    return {'result':r,'audit':record['audit'],'facts':facts,'violated_forbidden_claim_ids':[x for x in denied if x in text]}

def validate_scenario(record):
    sid=record['scenario_id'];require(sid in SCENARIOS,'SCENARIO_OUT_OF_SCOPE')
    require(record.get('production_path') and {'integration','service_api'}<=set(record.get('executed_layers',[])),'NO_PRODUCTION_EXECUTION_WITNESS')
    require(record['execution']['consumption_state']=='consumed_success','EXECUTION_NOT_CONSUMED')
    require(record['execution']['external_market_network_executed'] is False and not any(record['market_network'].values()),'MARKET_NETWORK_NONZERO')
    require(record['initial_execution_count']==len(record['request']['data_needs']) and record['additional_execution_count']==0,'SOURCE_INVOCATION_BOUND')
    calls=record.get('server_calls',[]);require(sum(c['method']=='POST' and c['path']=='/api/unified/executions' and c['http_status']==200 for c in calls)==1,'NO_INDEPENDENT_EXECUTION_RECEIPT')
    require(any(c['path']=='/api/unified/result-package' and c['response_canonical_sha256']==sha(record['package']) for c in calls),'RESULT_SERVER_RECEIPT_MISMATCH')
    require(record['package']['canonical_result']==record['result'],'RESULT_PACKAGE_DIVERGENCE')
    r=record['result'];require(r['request_id']==record['request']['request_id']=='closure-r1-'+sid.lower(),'SCENARIO_EXECUTION_IDENTITY_MISMATCH')
    require(record['control_package_id']==record['handoff']['control_package_id'],'CONTROL_IDENTITY_MISMATCH')
    require(r['result_id']==record['audit']['result_id']==record['handoff']['result_id'],'RESULT_AUDIT_HANDOFF_LINEAGE_MISMATCH')
    require(record['audit']['audit_package_id']==record['handoff']['audit_package_id'],'AUDIT_IDENTITY_MISMATCH')
    target=r['targets'][0];require(target['canonical_identity']['canonical_target_id']==('TPEX:6488' if sid=='J1-02' else 'TWSE:2330'),'WRONG_IDENTITY')
    ev=target['evidence'];expected_needs=['official_eod_reference'] if sid in ('J1-02','J1-05') else ['current_observation','official_eod_reference'] if sid=='J1-19' else ['current_observation']
    require([n['type'] for n in record['request']['data_needs']]==expected_needs,'WRONG_REQUEST_EVIDENCE_FAMILY')
    for need in expected_needs:
        e=ev.get(need,{});require(e.get('status')=='available' and e.get('citation_ids'),'POSITIVE_EVIDENCE_OR_CITATION_MISSING')
        if need=='official_eod_reference':require(e.get('source_id')==('TPEX_OPENAPI' if sid=='J1-02' else 'TWSE_OPENAPI') and e.get('timing_class')=='official_eod','EOD_SOURCE_SUBSTITUTED')
    g=next(s for s in read(DOC/'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json')['scenarios'] if s['scenario_id']==sid)
    errors=evaluate_scenario(g,observe(record))
    require(not errors,'J3_SEMANTIC_FAILURE: '+'; '.join(errors))
    return True

def validate_agent(receipt,records,server_calls):
    require(receipt.get('host_kind')=='actual_ai_host' and receipt.get('execution_kind')=='current_unscripted_agent_session','FAKE_OR_SCRIPTED_AGENT')
    require(receipt.get('boundary')=='real_mcp_stdio_to_local_service' and receipt.get('direct_internal_calls') is False,'AGENT_HOST_BOUNDARY_INVALID')
    calls=receipt.get('actual_tool_operations',[])
    require(receipt.get('tool_call_count')==len(calls),'AGENT_TOOL_CALL_COUNT_MISMATCH')
    require(calls and server_calls,'NO_INDEPENDENT_SERVER_RECEIPT')
    require(receipt.get('MCP_tools')==MCP_NAMES,'MCP_COUNT_OR_NAME_DRIFT')
    require(not any(receipt.get('market_network',{'GET':1}).values()),'AGENT_MARKET_NETWORK_NONZERO')
    require(receipt.get('secret_material_recorded') is False,'SECRET_MATERIAL_RECORDED')
    ids={r['scenario_id']:r for r in records}
    require(receipt.get('scenario_ids') and set(receipt['scenario_ids'])<=set(ids),'AGENT_SCENARIO_NOT_EXECUTED')
    for sid in receipt['scenario_ids']:
        r=ids[sid];validate_scenario(r)
        ops=[o for o in calls if o['scenario_id']==sid]
        require({o['tool_name'] for o in ops}>={'market_read_result','market_export_ai_handoff'},'AGENT_OPERATIONS_INCOMPLETE')
        for o in ops:
            require(o['result_id']==r['result']['result_id'] and o['audit_package_id']==r['audit']['audit_package_id'] and o['control_package_id']==r['control_package_id'],'AGENT_LINEAGE_MISSING')
            require(any(s['response_canonical_sha256']==o['response_canonical_sha256'] and s['result_id']==o['result_id'] for s in server_calls),'AGENT_SERVER_RECEIPT_MISMATCH')
        interpretation=receipt['agent_observations'][sid]
        require(interpretation['facts']==observe(r)['facts'] and not interpretation.get('violated_forbidden_claim_ids'),'AGENT_TYPED_INTERPRETATION_MISMATCH')
    return True

def derive_overlay(records,agent_receipt=None,server_calls=()):
    effective=copy.deepcopy(read(ROOT/historic.MATRIX));rows={r['scenario_id']:r for r in effective['scenarios']}
    require([r['scenario_id'] for r in records]==SCENARIOS,'FIVE_SCENARIO_ADJUDICATION_REQUIRED')
    require(len({r['result']['result_id'] for r in records})==5 and len({r['control_package_id'] for r in records})==5,'DUPLICATE_SCENARIO_EXECUTION')
    promotions=[];outcomes=[]
    for record in records:
        sid=record['scenario_id']
        try:validate_scenario(record);ok=True;reason=None
        except ValueError as e:ok=False;reason=str(e)
        outcomes.append({'scenario_id':sid,'execution_witness_satisfied':ok,'semantic_failure':reason})
        if not ok:continue
        for layer in ['integration','service_api']:
            cell=rows[sid]['layers'][layer]
            require(cell['status']=='PLANNED','BASELINE_PROMOTION_STATUS')
            p={'scenario_id':sid,'layer':layer,'baseline_status':cell['status'],'new_overlay_status':'COVERED_EXISTING','witness_kind':'integration_test' if layer=='integration' else 'service_test','evidence_refs':[{'ref':f'docs/governance/phase_j/PHASE_J_FINAL_CLOSURE_R1_WITNESS_LEDGER_V1.json#{sid}','kind':'integration_test' if layer=='integration' else 'service_test'},{'ref':f'tests/acceptance/test_phase_j_final_closure_r1.py::test_production_scenario[J1-21]' if sid=='J1-21' else f'tests/acceptance/test_phase_j_final_closure_r1.py::test_production_scenario[{sid}]','kind':'integration_test' if layer=='integration' else 'service_test'}],'scenario_match':'exact J3 typed assertions over actual execute-once package','introduced_by_tranche':'PHASE_J_FINAL_CLOSURE_R1','result_id':record['result']['result_id'],'audit_package_id':record['audit']['audit_package_id']}
            promotions.append(p);cell.update(status='COVERED_EXISTING',introduced_by_tranche='PHASE_J_FINAL_CLOSURE_R1',evidence_refs=p['evidence_refs'])
    agent_ok=False
    if agent_receipt is not None:
        validate_agent(agent_receipt,records,server_calls);agent_ok=True
        for sid in agent_receipt['scenario_ids']:
            for layer in ['mcp','real_agent']:
                cell=rows[sid]['layers'][layer];old=cell['status'];require(old in ('PLANNED','REQUIRES_REAL_AGENT_AUTH'),'AGENT_BASELINE_STATUS')
                promotions.append({'scenario_id':sid,'layer':layer,'baseline_status':old,'new_overlay_status':'COVERED_EXISTING','witness_kind':'mcp_test' if layer=='mcp' else 'e2e_acceptance','evidence_refs':[{'ref':'docs/governance/phase_j/PHASE_J_FINAL_CLOSURE_R1_REAL_AGENT_RECEIPT_V1.json','kind':'mcp_test' if layer=='mcp' else 'e2e_acceptance'}],'scenario_match':'actual bounded real-agent MCP read/export','introduced_by_tranche':'PHASE_J_FINAL_CLOSURE_R1'});cell['status']='COVERED_EXISTING'
    obligations=[{'obligation':'real_agent_layer','satisfied':agent_ok}]+[{'obligation':r['scenario_id'],'satisfied':r['execution_witness_satisfied']} for r in outcomes]
    remaining=sum(not o['satisfied'] for o in obligations)
    return {'promotions':promotions,'effective_matrix':effective,'scenario_outcomes':outcomes,'obligations':obligations,'remaining_obligations':remaining,'disposition':'PHASE_J_FINAL_CLOSURE_R1_PASS_CANDIDATE' if not remaining else 'PHASE_J_FINAL_CLOSURE_R1_HARD_BLOCK_EXISTING_PRODUCTION_SEAM_GAP' if any(not o['execution_witness_satisfied'] for o in outcomes) else 'PHASE_J_FINAL_CLOSURE_R1_HARD_BLOCK_REAL_AGENT_HOST_UNAVAILABLE'}

def validate_overlay(proposed,records,agent_receipt=None,server_calls=()):
    expected=derive_overlay(records,agent_receipt,server_calls)
    require(proposed==expected,'OVERLAY_OR_OBLIGATION_LAUNDERING')
    return True

def validate(check_git=True,terminal=False):
    baseline()
    if check_git:
        git=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
        require(git('rev-parse',BASE+'^{tree}')==TREE and git('rev-parse','origin/main')=='6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a','BASELINE_DRIFT')
        require(git('branch','--show-current')=='phase-j/j-b04-a5-bounded-live-source-acceptance','BRANCH_DRIFT')
        paths=git('diff','--name-only',BASE,'HEAD').splitlines()
        allowed=('scripts/validate_phase_j_final_closure_r1.py','tests/helpers/phase_j_closure_r1','tests/acceptance/test_phase_j_final_closure_r1.py','tests/fixtures/phase_j/closure_r1/','docs/governance/phase_j/PHASE_J_FINAL_CLOSURE_R1_')
        require(all(p.startswith(allowed) for p in paths),'PRODUCTION_OR_UNAUTHORIZED_DIFF')
    if terminal:
        ledger=read(DOC/'PHASE_J_FINAL_CLOSURE_R1_WITNESS_LEDGER_V1.json');result=derive_overlay(ledger['scenario_records'])
        require(read(DOC/'PHASE_J_FINAL_CLOSURE_R1_WITNESS_DELTA_V1.json')['promotions']==result['promotions'],'PROMOTION_LAUNDERING')
        require(read(DOC/'PHASE_J_FINAL_CLOSURE_R1_EFFECTIVE_COVERAGE_V1.json')==result['effective_matrix'],'OVERLAY_DIVERGENCE')
        evidence=read(DOC/'PHASE_J_FINAL_CLOSURE_R1_2026-10-11.json')
        require(evidence['disposition']==result['disposition'] and evidence['obligations']==result['obligations'],'FALSE_CLOSURE_PASS')
        require(evidence['host_selector_before']==evidence['host_selector_after'],'HOST_SELECTOR_MUTATION')
        require(not evidence['default_ci']['candidate_only_failure_nodes'],'CANDIDATE_ONLY_CI_FAILURE')
        return {'validator_status':'PASS','closure_disposition':result['disposition'],'remaining_obligations':result['remaining_obligations']}
    return {'validator_status':'PASS','baseline_immutable':True,'witnesses_not_yet_adjudicated':True}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--terminal',action='store_true');args=p.parse_args();print(json.dumps(validate(terminal=args.terminal),indent=2))
