"""J2-R1 actual headless DOM/Service/MCP acceptance, synthetic local sources only."""
import json
import os
from pathlib import Path
import pytest
from tests.helpers.phase_j_j2_r1_browser import run_scenario, SCENARIOS

pytestmark = pytest.mark.browser

def assert_semantics(record):
    scenario = record['scenario_id']
    assert record['browser'] == 'headless_chromium'
    assert record['browser_local_request_count'] > 0
    assert record['browser_external_request_count'] == 0
    assert record['additional_execution_count'] == 0
    assert record['external_market_GET'] == record['external_market_HEAD'] == record['external_market_POST'] == 0
    if record['classification'] == 'PREEXECUTION_FAIL_CLOSED':
        assert record['result_id'] is None
        assert record['initial_execution_count'] == record['execute_once_request_count'] == 0
        assert 'package' not in record and 'audit' not in record
        if scenario == 'J1-10':
            assert any(i['code'] == 'REQUEST_SCHEMA_INVALID' for i in record['validation']['blocking_issues'])
            assert record['mcp_validation']['isError']
        if scenario == 'J1-12':
            assert not record['preview']['preview']['internal_execution_reference'].get('executable_operation_count',0)
        if scenario == 'J1-24': assert record['validation']['validation_status'] == 'requires_clarification'
        if scenario == 'J1-25': assert record['validation'].get('validation_status') == 'invalid' or record['validation'].get('error') == 'SECURITY_MASTER_NOT_INITIALIZED'
        if scenario == 'J1-26': assert record['service_authorization_refusal']['http_status'] != 200
        if scenario == 'J1-27': assert any(i['code']=='TARGET_LIMIT_EXCEEDED' for i in record['validation']['blocking_issues'])
        return
    assert record['execute_once_request_count'] == 1
    package, audit, handoff = record['package'],record['audit'],record['handoff']
    result = package['canonical_result']
    assert result['schema_version']=='unified_market_evidence_result.v3'
    assert audit['schema_version']=='unified_market_evidence_audit_package.v3'
    assert package['result_id']==audit['result_id']==handoff['result_id']==record['dom_observations']['#mode-c-result-view']['result_id']
    assert package['result_status'] in record['dom_observations']['#mode-c-summary']
    assert record['initial_execution_count']==record['post_workbench_execution_count']==record['post_service_execution_count']==record['post_mcp_execution_count']
    assert record['result_download_sha256'] and record['audit_download_sha256'] and record['handoff_download_sha256']
    assert not any(term in handoff['ai_ready_markdown'].casefold() for term in ('buy','sell','hold','target price','bullish','bearish','買進','賣出','持有','目標價','看多','看空'))
    evidence = package['targets'][0]['evidence']
    if scenario == 'J1-01':
        assert result['status']=='full_success'
        assert package['targets'][0]['canonical_identity']['canonical_target_id']=='TWSE:2330'
        assert set(evidence)=={'current_observation','official_eod_reference'}
        assert package['citation_references']
    if scenario in ('J1-07','J1-22'):
        assert evidence['material_disclosures']['status']=='no_evidence_in_covered_scope'
        assert evidence['material_disclosures']['coverage']['historical_lookup_supported'] is False
        assert 'not a claim of no historical disclosures' in record['dom_observations']['#mode-c-summary']
    if scenario == 'J1-08':
        assert evidence['material_disclosures']['items'][0]['revision_relation']['status']=='unresolved'
    if scenario == 'J1-11':
        coverage=evidence['trading_status_context']['aggregate_coverage']
        assert coverage['status']=='partial'
        assert set(coverage['covered_status_types'])=={'attention','disposition'}
        assert set(coverage['uncovered_status_types'])=={'suspension','resumption','changed_trading_method'}
        assert coverage['declared_scope_complete'] is False
    if scenario in ('J1-13','J1-14','J1-16'):
        safety=evidence['discontinuity_safety']
        assert result['status']=='full_success'
        assert safety['state']=='coverage_incomplete'
        assert safety['ordinary_return_interpretation']=='blocked'
        assert 'CORPORATE_ACTION_COVERAGE_INCOMPLETE' in handoff['ai_ready_markdown']
        assert record['dom_observations']['#mode-c-result-view']['targets'][0]['evidence']['discontinuity_safety']['ordinary_return_interpretation']=='blocked'
        assert audit['phase_h_governance']
    if scenario == 'J1-18':
        assert set(evidence)=={'index_futures_context'}
        assert package['request_summary']['requested_data_needs']==['index_futures_context']
    if scenario == 'J1-20':
        assert result['status']=='partially_failed' and handoff['execution_outcome']=='partial_success'
        assert evidence['current_observation']['status']=='available'
        assert evidence['material_disclosures']['status']=='source_failed'
    if scenario == 'J1-23':
        assert result['status']=='failed' and handoff['execution_outcome']=='failed'
        assert evidence['material_disclosures']['status']=='source_failed'

@pytest.mark.parametrize('scenario',SCENARIOS,ids=SCENARIOS)
def test_scenario_real_workbench_service_mcp(scenario,tmp_path):
    record=run_scenario(scenario,tmp_path/scenario)
    assert_semantics(record)
    capture=os.environ.get('PHASE_J_R1_CAPTURE_ROOT')
    if capture:
        output=Path(capture);output.mkdir(parents=True,exist_ok=True)
        (output/(scenario+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')

def test_j1_25_fresh_install_real_dom(tmp_path):
    record=run_scenario('J1-25',tmp_path/'fresh-install',fresh_install=True)
    assert_semantics(record)
    assert record['validation']['error']=='SECURITY_MASTER_NOT_INITIALIZED'
    assert not (tmp_path/'fresh-install/security/active.json').exists()
    capture=os.environ.get('PHASE_J_R1_CAPTURE_ROOT')
    if capture: (Path(capture)/'J1-25-fresh-install.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
