"""Typed currentness integration and witness-integrity regressions, network-free."""
import copy
import json
from pathlib import Path
import pytest
from scripts import validate_phase_j_final_closure_r2 as v
from scripts.m8r_06_03_production_adapter import _assess_current_observation
from tests.helpers.phase_j_closure_r2 import execute

@pytest.fixture(scope='module')
def witness(tmp_path_factory):
    return execute(tmp_path_factory.mktemp('closure-r2'))

@pytest.fixture
def policy():
    return next(s for s in v.read(v.ROOT / 'docs/data_capabilities/m8_source_capability_registry.json')['sources'] if s['source_id'] == 'TWSE_MIS')

def observation(timestamp='2026-10-08T05:59:00Z'):
    return {'source': 'TWSE_MIS', 'source_timestamp': timestamp, 'retrieved_at': '2026-10-08T06:00:00Z'}

@pytest.mark.parametrize('timestamp,status,assessment', [
    ('2026-09-01T05:30:00Z', 'stale', 'stale_intraday_snapshot'),
    ('2026-10-08T05:59:00Z', 'fresh', 'fresh_intraday_snapshot'),
    (None, 'unresolved', 'unknown'),
    ('invalid', 'unresolved', 'unknown'),
    ('2026-10-08T06:01:00Z', 'unresolved', 'unknown'),
])
def test_governed_currentness(timestamp, status, assessment, policy):
    native = observation(timestamp)
    original = copy.deepcopy(native)
    a = _assess_current_observation(native, policy)
    assert a['status'] == status and a['freshness_assessment'] == assessment
    assert a['source_timestamp'] == timestamp and a['retrieved_at_utc'] == native['retrieved_at']
    assert native == original
    assert a == _assess_current_observation(native, policy)
    assert a['not_realtime_guaranteed'] and not a['recommendation_allowed'] and not a['trading_advice_allowed']

def test_policy_controls_threshold_without_duplicate_constant(policy):
    p = copy.deepcopy(policy)
    p['freshness_evaluator_policy']['max_intraday_age_seconds'] = 30
    assert _assess_current_observation(observation(), p)['status'] == 'stale'
    p['freshness_evaluator_policy']['max_intraday_age_seconds'] = 120
    assert _assess_current_observation(observation(), p)['status'] == 'fresh'

def test_absent_policy_is_unresolved(policy):
    policy.pop('freshness_evaluator_policy')
    assert _assess_current_observation(observation('2026-09-01T05:30:00Z'), policy)['status'] == 'unresolved'

def test_policy_source_mismatch_is_unresolved(policy):
    policy['source_id'] = 'TPEX_OPENAPI'
    assert _assess_current_observation(observation(), policy)['status'] == 'unresolved'

def test_absent_retrieval_is_unresolved(policy):
    native = observation()
    native.pop('retrieved_at')
    assert _assess_current_observation(native, policy)['status'] == 'unresolved'

def test_source_unavailable_is_not_stale(policy):
    native = observation('2026-09-01T05:30:00Z')
    native['source_unavailable'] = True
    assert _assess_current_observation(native, policy)['freshness_assessment'] == 'source_unavailable'

def test_official_eod_is_not_intraday_stale():
    p = next(s for s in v.read(v.ROOT / 'docs/data_capabilities/m8_source_capability_registry.json')['sources'] if s['source_id'] == 'TWSE_OPENAPI')
    native = observation('2026-09-01T05:30:00Z')
    native.update(source='TWSE_OPENAPI', market_date='2026-09-01')
    assert _assess_current_observation(native, p)['freshness_assessment'] == 'official_eod_reference'

def test_j1_21_production_path(witness):
    assert v.validate_witness(witness)
    derived = v.derive(witness)
    assert {(p['scenario_id'], p['layer']) for p in derived['promotions']} == {('J1-21', 'integration'), ('J1-21', 'service_api')}
    assert derived['remaining_obligations'] == 1
    assert [o['obligation'] for o in derived['obligations'] if not o['satisfied']] == ['real_agent_layer']
    assert witness['initial_execution_count'] == 1 and witness['additional_execution_count'] == 0
    assert witness['result']['status'] == 'full_success'
    assert witness['result']['targets'][0]['evidence']['current_observation']['status'] == 'available'

def rebind_package(record):
    record['package']['canonical_result'] = record['result']
    for call in record['server_calls']:
        if call['path'] == '/api/unified/result-package':
            call['response_canonical_sha256'] = v.sha(record['package'])

@pytest.mark.parametrize('kind', ['source_timestamp', 'retrieved_at', 'result_candidate', 'fresh', 'unknown', 'source_failed', 'missing', 'unsupported', 'partial', 'official_eod', 'renderer_only', 'realtime_handoff', 'source_hash', 'audit_lineage', 'control_lineage', 'unexecuted_layer', 'real_agent', 'network', 'scenario_id', 'no_policy', 'no_source_time', 'no_execution', 'fixture_only'])
def test_witness_mutations_rejected(kind, witness):
    record = copy.deepcopy(witness)
    envelope = record['result']['targets'][0]['evidence']['current_observation']
    if kind in ('source_timestamp', 'retrieved_at'):
        record['normalized_observation'][kind] = '2026-10-08T05:59:00Z'
    elif kind == 'result_candidate':
        envelope['currentness']['status'] = 'candidate'
    elif kind in ('fresh', 'unknown', 'official_eod'):
        envelope['currentness']['freshness_assessment'] = kind
    elif kind in ('source_failed', 'missing', 'unsupported', 'partial'):
        envelope['status'] = kind
    elif kind == 'renderer_only':
        envelope['currentness']['status'] = 'candidate'
        envelope['currentness']['freshness_assessment'] = 'current candidate'
    elif kind == 'realtime_handoff':
        record['handoff']['ai_ready_markdown'] += '\nCurrent Market Snapshot: realtime price'
    elif kind == 'source_hash':
        record['source_artifact_sha256'] = '0' * 64
    elif kind == 'audit_lineage':
        record['audit']['result_id'] = 'wrong'
    elif kind == 'control_lineage':
        record['handoff']['control_package_id'] = 'wrong'
    elif kind == 'unexecuted_layer':
        record['executed_layers'].append('workbench')
    elif kind == 'real_agent':
        record['real_agent_sessions'] = 1
    elif kind == 'network':
        record['market_network']['GET'] = 1
    elif kind == 'scenario_id':
        record['scenario_id'] = 'J1-04'
    elif kind == 'no_policy':
        record['normalized_observation']['governed_currentness']['source_policy_sha256'] = None
    elif kind == 'no_source_time':
        record['normalized_observation']['source_timestamp'] = None
    elif kind == 'no_execution':
        record['server_calls'] = []
    elif kind == 'fixture_only':
        record['executed_layers'] = ['contract_fixture', 'deterministic_unit']
    rebind_package(record)
    with pytest.raises(ValueError):
        v.validate_witness(record)

def test_historical_authorities_immutable():
    assert v.baseline(check_git=False)

def test_no_algorithm_or_scenario_branch():
    import inspect
    source = inspect.getsource(_assess_current_observation)
    assert 'evaluate_evidence_currentness(' in source
    assert 'build_source_freshness_assessment(' in source
    assert 'J1-21' not in source and '3198600' not in source and '900' not in source

@pytest.mark.parametrize('kind', ['real_agent_promotion', 'mcp_promotion', 'drop_scenario', 'false_closure', 'matrix_status'])
def test_overlay_mutations_fail(kind, witness):
    proposed = v.derive(witness)
    if kind in ('real_agent_promotion', 'mcp_promotion'):
        proposed['promotions'][0]['layer'] = 'real_agent' if kind == 'real_agent_promotion' else 'mcp'
    elif kind == 'drop_scenario':
        proposed['effective_matrix']['scenarios'].pop()
    elif kind == 'false_closure':
        proposed['obligations'][0]['satisfied'] = True
        proposed['remaining_obligations'] = 0
    else:
        proposed['effective_matrix']['scenarios'][0]['layers']['real_agent']['status'] = 'COVERED_EXISTING'
    with pytest.raises(ValueError, match='COVERAGE_OR_OBLIGATION_LAUNDERING'):
        v.validate_overlay(proposed, witness)

@pytest.mark.parametrize('path', ['PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json', 'PHASE_J_J2_R1_EFFECTIVE_COVERAGE_MATRIX_V1.json', 'PHASE_J_FINAL_CLOSURE_R1_2026-10-11.json', 'PHASE_J_FINAL_CLOSURE_GAP_ADJUDICATION_V1.json'])
def test_authority_drift_fails(path, monkeypatch):
    actual = v.file_sha
    monkeypatch.setattr(v, 'file_sha', lambda p: '0' * 64 if Path(p).name == path else actual(p))
    with pytest.raises(ValueError, match='IMMUTABLE_AUTHORITY_DRIFT'):
        v.baseline(check_git=False)

@pytest.mark.parametrize('kind', ['MCP_count', 'market_network', 'agent_provider', 'Phase_K', 'Roadmap', 'selector'])
def test_boundary_mutations(kind):
    evidence = {'MCP_tools': v.r1.MCP_NAMES[:], 'network': {'market_GET': 0, 'agent_provider': 0}, 'state': {'Phase_K': 'NOT_STARTED', 'Roadmap_checkbox': 'UNCHECKED'}, 'host_selector_before': 'unchanged', 'host_selector_after': 'unchanged'}
    assert v.validate_boundary(evidence)
    if kind == 'MCP_count':
        evidence['MCP_tools'].append('stale_tool')
    elif kind == 'market_network':
        evidence['network']['market_GET'] = 1
    elif kind == 'agent_provider':
        evidence['network']['agent_provider'] = 1
    elif kind == 'Phase_K':
        evidence['state']['Phase_K'] = 'STARTED'
    elif kind == 'Roadmap':
        evidence['state']['Roadmap_checkbox'] = 'CHECKED'
    else:
        evidence['host_selector_after'] = 'mutated'
    with pytest.raises(ValueError):
        v.validate_boundary(evidence)
