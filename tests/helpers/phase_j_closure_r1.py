"""Acceptance-only five-case production execution. No browser or agent simulation."""
from contextlib import contextmanager
import json,os
from pathlib import Path
import httpx
from scripts.run_v1_workbench_browser_e2e import bootstrap_deterministic_fixture_release,start_workbench,stop,source_invocation_count
ROOT=Path(__file__).resolve().parents[2]
SCENARIOS=['J1-02','J1-04','J1-05','J1-19','J1-21']

def request_for(sid):
    assert sid in SCENARIOS
    needs=['official_eod_reference'] if sid in ('J1-02','J1-05') else ['current_observation','official_eod_reference'] if sid=='J1-19' else ['current_observation']
    return {'schema_version':'unified_market_evidence_request.v3','request_id':'closure-r1-'+sid.lower(),'targets':[{'input':'TPEX:6488' if sid=='J1-02' else 'TWSE:2330','resolution_requirement':'exact'}],'data_needs':[{'type':n,'priority':'required','parameters':{}} for n in needs],'execution_mode':'execute'}

@contextmanager
def service(sid,root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    bootstrap_deterministic_fixture_release(root/'security',eligible_targets=('TWSE:2330','TPEX:6488'))
    env=os.environ.copy();env.update(TW_MARKET_SECURITY_MASTER_ROOT=str(root/'security'),TW_MARKET_WATCHLIST_ROOT=str(root/'watchlists'),M8R_06_03_CONTROL_ROOT=str(root/'control'),M8R_06_03_EXECUTION_ENVIRONMENT='test',M8R_06_03_TEST_SOURCE_TRANSPORT='deterministic',M8R_06_03_TEST_INVOCATION_COUNTER=str(root/'invocations'),PHASE_J_CLOSURE_R1_SCENARIO=sid,PHASE_J_CLOSURE_R1_SERVER_LOG=str(root/'server.jsonl'))
    p,port=start_workbench(env,launcher=ROOT/'tests/helpers/phase_j_closure_r1_server.py')
    try:yield 'http://127.0.0.1:'+str(port)
    finally:stop(p)

def seed(sid,root,url):
    root=Path(root)
    with httpx.Client(base_url=url,trust_env=False,timeout=140) as client:
        def post(path,payload):
            r=client.post('/api/unified/'+path,json=payload);assert r.status_code==200,(path,r.text);return r.json()
        req=request_for(sid)
        validation=post('validate-request',{'request':req});assert validation['validation_status']=='valid',validation
        preview=post('preview-request',{'request':req})
        auth=post('authorizations',{'request':req,'expected_preview_id':preview['preview']['internal_execution_reference']['preview_id'],'expected_plan_id':preview['orchestration_plan']['plan_id'],'expected_plan_hash':preview['orchestration_plan']['plan_hash'],'confirm_authorization':True,'approval_scope_mode':'whole_plan_executable_scope'})
        control=auth['control_package_id']
        execution=post('executions',{'control_package_id':control,'confirm_execution':True,'operator_confirmation_reference':'closure-r1-fixture-acceptance','confirm_network_execution':True})
        package=post('result-package',{'control_package_id':control})
        audit=client.get(f'/api/unified/result-package/{control}/audit.json').json()
        handoff=client.get(f'/api/unified/result-package/{control}/handoff').json()
        result=package['canonical_result']
        assert result['result_id']==audit['result_id']==handoff['result_id']
        initial=source_invocation_count(root/'invocations')
        record={'scenario_id':sid,'synthetic':True,'network_free':True,'acceptance_only':True,'package':package,'server_calls':[json.loads(line) for line in (root/'server.jsonl').read_text().splitlines()],'request':req,'validation':validation,'preview':preview,'execution':execution,'control_package_id':control,'result':result,'audit':audit,'handoff':handoff,'initial_execution_count':initial,'additional_execution_count':0,'executed_layers':['integration','service_api'],'production_path':['Local Service validate','Mode B1 planner','Mode B2 authorize','execute_once child','genuine official source adapter with raw fixture HTTP','Result V3 builder','Audit V3 builder','Mode C stored handoff'],'fixture_ref':'tests/fixtures/phase_j/closure_r1/source_rows.json','market_network':{'GET':0,'HEAD':0,'POST':0}}
        assert source_invocation_count(root/'invocations')==initial
        return record
