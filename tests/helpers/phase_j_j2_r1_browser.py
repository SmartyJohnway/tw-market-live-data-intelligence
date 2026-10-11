"""Real DOM scenario acceptance using the existing pinned headless harness.

Fixtures affect only raw source transport in a test execution child. All UI
interactions, validation, authorization, Result/Audit and MCP handlers are real.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import httpx
import os
from pathlib import Path
from scripts.run_v1_workbench_browser_e2e import (
    bootstrap_deterministic_fixture_release, start_workbench, stop,
    guard_local_browser_context, source_invocation_count, wait_until,
)
from server.unified_mcp.local_service_client import UnifiedLocalServiceClient
from server.unified_mcp.server import dispatch_safe_tool
from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ('J1-01','J1-07','J1-08','J1-10','J1-11','J1-12','J1-13','J1-14','J1-16','J1-18','J1-20','J1-22','J1-23','J1-24','J1-25','J1-26','J1-27')

def request_for(scenario):
    needs = {
      'J1-01':['current_observation','official_eod_reference'],
      'J1-07':['material_disclosures'], 'J1-08':['material_disclosures'],
      'J1-10':['financial_statements'], 'J1-11':['trading_status_context'],
      'J1-12':['trading_status_context'], 'J1-13':['recent_performance','corporate_action_context'],
      'J1-14':['recent_performance','corporate_action_context'], 'J1-16':['recent_performance','corporate_action_context'],
      'J1-18':['index_futures_context'], 'J1-20':['current_observation','material_disclosures'],
      'J1-22':['material_disclosures'], 'J1-23':['material_disclosures'],
    }.get(scenario,['current_observation'])
    target='TPEX:6488' if scenario=='J1-11' else '3333' if scenario=='J1-24' else 'UNKNOWN:2330' if scenario=='J1-25' else 'TWSE:2330'
    targets=[{'input':target,'resolution_requirement':'exact'}]
    if scenario=='J1-27': targets*=51
    return {'schema_version':'unified_market_evidence_request.v3','request_id':f'j2-r1-{scenario.lower()}', 'targets':targets,
       'data_needs':[{'type':need,'priority':'required','parameters':{'lookback_trading_days':20} if need=='recent_performance' else {}} for need in needs], 'execution_mode':'execute'}

def run_scenario(scenario, root, *, fresh_install=False):
    from playwright.sync_api import sync_playwright
    root=Path(root); root.mkdir(parents=True,exist_ok=True)
    counter=root/'invocations'; counter.mkdir()
    if not fresh_install:
        bootstrap_deterministic_fixture_release(root/'security',eligible_targets=('TWSE:2330','TPEX:6488'))
    env=os.environ.copy(); env.update(TW_MARKET_SECURITY_MASTER_ROOT=str(root/'security'),TW_MARKET_WATCHLIST_ROOT=str(root/'watchlists'), M8R_06_03_CONTROL_ROOT=str(root/'control'),M8R_06_03_EXECUTION_ENVIRONMENT='test',M8R_06_03_TEST_SOURCE_TRANSPORT='deterministic',M8R_06_03_TEST_INVOCATION_COUNTER=str(counter),PHASE_J_R1_SCENARIO=scenario)
    process,port=start_workbench(env,launcher=ROOT/'tests/helpers/phase_j_j2_r1_workbench_server.py')
    base=f'http://127.0.0.1:{port}'
    record={'scenario_id':scenario,'synthetic':True,'network_free':True,'acceptance_only':True,'dom_observations':{},'external_market_GET':0,'external_market_HEAD':0,'external_market_POST':0}
    try:
      with sync_playwright() as p:
        browser=p.chromium.launch(headless=True); context=browser.new_context(); ledger=guard_local_browser_context(context,base); page=context.new_page()
        page.on('dialog', lambda dialog: dialog.accept('j2-r1-local-acceptance') if dialog.type=='prompt' else dialog.accept())
        page.goto(base+'/workbench/',wait_until='networkidle')
        request=request_for(scenario); page.fill('#request-textarea',json.dumps(request))
        with page.expect_response(lambda r:'/api/unified/validate-request' in r.url) as observed: page.click('#btn-validate')
        validation=observed.value.json(); record['validation']=validation
        record['dom_observations']['#validation-summary']=page.locator('#validation-summary').inner_text()
        record['initial_execution_count']=source_invocation_count(counter)
        if validation.get('validation_status')!='valid':
          assert source_invocation_count(counter)==0
          record['classification']='PREEXECUTION_FAIL_CLOSED'; record['result_id']=None
        else:
          with page.expect_response(lambda r:'/api/unified/preview' in r.url) as preview: page.click('#btn-preview')
          record['preview']=preview.value.json()
          record['dom_observations']['#preview-summary']=page.locator('#preview-summary').inner_text()
          if scenario=='J1-26':
            # Withhold authorization at the real preview/authorize boundary.
            # No click grants it; refused API/MCP checks are tested separately.
            assert page.locator('#btn-execute-once').is_disabled()
            assert not list((root/'control').glob('*/authorization.json'))
            payload={'request':request,'expected_preview_id':record['preview']['preview']['internal_execution_reference']['preview_id'],'expected_plan_id':record['preview']['orchestration_plan']['plan_id'],'expected_plan_hash':record['preview']['orchestration_plan']['plan_hash'],'confirm_authorization':False,'approval_scope_mode':'whole_plan_executable_scope'}
            refusal=httpx.post(base+'/api/unified/authorizations',json=payload)
            record['service_authorization_refusal']={'http_status':refusal.status_code,'body':refusal.json()}
            assert refusal.status_code!=200
            record['classification']='PREEXECUTION_FAIL_CLOSED'; record['authorization_refused']=True; record['result_id']=None
          elif not page.locator('#btn-authorize').is_enabled():
            record['classification']='PREEXECUTION_FAIL_CLOSED'; record['result_id']=None
          else:
            with page.expect_response(lambda r:'/api/unified/authorizations' in r.url) as auth: page.click('#btn-authorize')
            authorization=auth.value.json(); record['control_package_id']=authorization['control_package_id']
            page.check('#confirm-network-execution')
            with page.expect_response(lambda r:'/api/unified/executions' in r.url) as executed: page.click('#btn-execute-once')
            execution=executed.value.json(); record['execution']=execution
            record['initial_execution_count']=source_invocation_count(counter)
            record['dom_observations']['#mode-b2-summary']=page.locator('#mode-b2-summary').inner_text()
            with page.expect_response(lambda r:'/api/unified/result-package' in r.url and r.request.method=='POST') as result_response: page.click('#btn-build-result')
            package=result_response.value.json(); record['package']=package
            wait_until(lambda:'RESULT READY' in page.locator('#mode-c-summary').inner_text(),label='scenario_result')
            record['dom_observations']['#mode-c-summary']=page.locator('#mode-c-summary').inner_text()
            record['dom_observations']['#mode-c-result-view']=json.loads(page.locator('#mode-c-result-view').inner_text())
            # Export by actual user actions; no application state injection.
            for selector,key in [('#btn-download-result','result'),('#btn-download-audit','audit'),('#btn-download-markdown','handoff')]:
                with page.expect_download() as downloaded: page.click(selector)
                content=Path(downloaded.value.path()).read_bytes()
                record[key+'_download_sha256']=hashlib.sha256(content).hexdigest()
                if key=='result': assert json.loads(content)['result_id']==package['result_id']
                if key=='audit': assert json.loads(content)['result_id']==package['result_id']
                if key=='handoff': assert content.decode()==package['ai_ready_markdown']
            record['post_workbench_execution_count']=source_invocation_count(counter)
            result=package['canonical_result']; record['result_id']=result['result_id']; record['classification']='FIXTURE_BACKED_PRODUCTION_PATH'
            control=record['control_package_id']
            from scripts.run_v1_workbench_browser_e2e import get_json
            _,audit=get_json(f'{base}/api/unified/result-package/{control}/audit.json'); _,handoff=get_json(f'{base}/api/unified/result-package/{control}/handoff')
            assert audit['result_id']==handoff['result_id']==result['result_id']
            record['audit']=audit; record['handoff']=handoff; record['post_service_execution_count']=source_invocation_count(counter)
            async def mcp_read():
                client=UnifiedLocalServiceClient(base); snapshot=build_tool_contract_snapshot()
                assert len(snapshot.tools)==6
                read=await dispatch_safe_tool('market_read_result',{'control_package_id':control},client=client,tool_contract_snapshot=snapshot)
                export=await dispatch_safe_tool('market_export_ai_handoff',{'control_package_id':control},client=client,tool_contract_snapshot=snapshot)
                assert not read.isError and not export.isError
                assert read.structuredContent['canonical_result']['result_id']==result['result_id']==export.structuredContent['result_id']
                assert read.structuredContent['result_status']==package['result_status']
                assert export.structuredContent['execution_outcome']==handoff['execution_outcome']
                assert export.structuredContent['ai_ready_markdown']==handoff['ai_ready_markdown']
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(asyncio.run,mcp_read()).result()
            record['post_mcp_execution_count']=source_invocation_count(counter)
            assert record['initial_execution_count']==record['post_mcp_execution_count']
        if record['classification']=='PREEXECUTION_FAIL_CLOSED':
          async def mcp_validation():
            return await dispatch_safe_tool('market_validate_request',{'request':request},client=UnifiedLocalServiceClient(base),tool_contract_snapshot=build_tool_contract_snapshot())
          with ThreadPoolExecutor(max_workers=1) as pool:
            outcome=pool.submit(asyncio.run,mcp_validation()).result()
          record['mcp_validation']={'isError':outcome.isError,'structuredContent':outcome.structuredContent}
        record.setdefault('post_workbench_execution_count',source_invocation_count(counter))
        record['additional_execution_count']=source_invocation_count(counter)-record['initial_execution_count']
        assert record['additional_execution_count']==0
        record['browser_local_request_count']=len(ledger['local_requests']); record['browser_external_request_count']=len(ledger['external_requests']); record['browser_transport']=ledger
        assert not ledger['external_requests']
        record['execute_once_request_count']=sum(r['method']=='POST' and r['path']=='/api/unified/executions' for r in ledger['local_requests'])
        record['browser']='headless_chromium'; record['browser_version']=browser.version
        browser.close()
      return record
    finally: stop(process)
