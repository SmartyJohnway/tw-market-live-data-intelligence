"""Synthetic network-free acceptance of selection/gating; no candidate execution."""
from copy import deepcopy
import json
from pathlib import Path
import socket

import pytest

from scripts import phase_j_j4_regression_authority as j4

FIXTURES = j4.ROOT / 'tests/fixtures/phase_j/j4'


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('J4 acceptance attempted socket transport')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'create_connection', denied)


def manifest(cls='NEW_RELEASE'):
    return j4.load(FIXTURES / (cls.lower() + '.json'))


def rejection(call, code):
    with pytest.raises(ValueError, match=code):
        call()


@pytest.mark.parametrize('cls', j4.CLASSES)
def test_positive_class_plan(cls):
    m = manifest(cls)
    p = j4.select_plan(m)
    assert j4.validate_plan(m, p)
    assert set(j4.SAFETY) <= set(p['selected_scenario_ids'])
    assert all(d == j4.DIMENSIONS for d in p['selected_semantic_dimensions'].values())
    assert p == j4.select_plan(deepcopy(m))
    assert j4.canonical(p) == j4.canonical(j4.select_plan(m))
    assert all(g['authorization'] == 'NOT_GRANTED' for g in p['authorization_gated_layers'])
    if cls in {'NEW_RELEASE', 'NEW_AGENT_HOST'}:
        assert len(p['selected_scenario_ids']) == 27
    if cls == 'NEW_AGENT_HOST':
        assert p['authorization_gated_layers'][0]['layer'] == 'real_agent'
    if cls in {'NEW_SOURCE', 'NEW_EVIDENCE_FAMILY'}:
        assert 'J1-09' in p['selected_scenario_ids']
    if cls == 'NEW_MCP_VERSION':
        assert 'J1-03' in p['selected_scenario_ids']
        assert p['mcp_tool_baseline'] == j4.TOOLS


@pytest.mark.parametrize('classes', [
    ['NEW_RELEASE', 'NEW_MCP_VERSION'],
    ['NEW_SOURCE', 'NEW_RELEASE'],
    ['NEW_AGENT_HOST', 'NEW_MCP_VERSION'],
])
def test_multiclass_union(classes):
    m = manifest(classes[0])
    m['change_classes'] = classes
    if 'NEW_SOURCE' in classes:
        m.update(affected_sources=['synthetic_source'], affected_scenario_ids=['J1-09'], requested_live_revalidation=True)
    p = j4.select_plan(m)
    singles = []
    for cls in classes:
        single = deepcopy(m)
        single['change_classes'] = [cls]
        single['release_candidate'] = cls == 'NEW_RELEASE'
        single['touches_mcp'] = cls == 'NEW_MCP_VERSION'
        single['touches_agent_host'] = cls == 'NEW_AGENT_HOST'
        singles.append(j4.select_plan(single))
    assert set(p['selected_scenario_ids']) == set().union(*(set(x['selected_scenario_ids']) for x in singles))
    assert set(p['required_contract_checks']) == set().union(*(set(x['required_contract_checks']) for x in singles))
    assert {g['layer'] for g in p['authorization_gated_layers']} == set().union(*({g['layer'] for g in x['authorization_gated_layers']} for x in singles))


@pytest.mark.parametrize('field,value,code', [
    ('baseline_hashes', {}, 'BASELINE_DRIFT'),
    ('reviews', {}, 'REVIEW_AUTHORITY_DRIFT'),
    ('mandatory_safety_core', [], 'SAFETY_CORE_DRIFT'),
    ('mcp_tools', j4.TOOLS + ['seventh_tool'], 'MCP_TOOL_COUNT'),
    ('semantic_dimensions', j4.DIMENSIONS[:-1], 'SEMANTIC_DIMENSION_DRIFT'),
    ('layers', j4.LAYERS[:-1], 'LAYER_VOCABULARY_DRIFT'),
    ('global_invariants', {}, 'INVARIANT_DRIFT'),
    ('class_rules', {}, 'CLASS_SELECTION_RULE_DRIFT'),
])
def test_authority_mutations(field, value, code):
    a = j4.load(j4.AUTHORITY)
    a[field] = value
    rejection(lambda: j4.validate_authority(a), code)


@pytest.mark.parametrize('cls', j4.CLASSES)
def test_safety_scenario_cannot_be_removed(cls):
    m = manifest(cls)
    p = j4.select_plan(m)
    p['selected_scenario_ids'].remove('J1-16')
    rejection(lambda: j4.validate_plan(m, p), 'SCENARIO_SCOPE_MISMATCH')


@pytest.mark.parametrize('sid', ['J1-09', 'J1-20', 'J1-23', 'J1-26'])
def test_release_cannot_drop_any_scenario(sid):
    m = manifest()
    p = j4.select_plan(m)
    p['selected_scenario_ids'].remove(sid)
    rejection(lambda: j4.validate_plan(m, p), 'SCENARIO_SCOPE_MISMATCH')


def test_agent_cannot_drop_gate_or_scenario():
    m = manifest('NEW_AGENT_HOST')
    p = j4.select_plan(m)
    p['authorization_gated_layers'] = []
    rejection(lambda: j4.validate_plan(m, p), 'AUTHORIZATION_GATE_MISMATCH')
    p = j4.select_plan(m)
    p['selected_scenario_ids'].pop()
    rejection(lambda: j4.validate_plan(m, p), 'SCENARIO_SCOPE_MISMATCH')


@pytest.mark.parametrize('dimension', j4.DIMENSIONS)
def test_applicable_dimension_cannot_be_selected_away(dimension):
    m = manifest('NEW_SOURCE')
    p = j4.select_plan(m)
    p['selected_semantic_dimensions']['J1-01'].remove(dimension)
    rejection(lambda: j4.validate_plan(m, p), 'DIMENSION_SCOPE_MISMATCH')


@pytest.mark.parametrize('mutation', ['empty', 'unknown', 'omitted', 'self_authorize'])
def test_manifest_fail_closed(mutation):
    m = manifest('NEW_MCP_VERSION')
    if mutation == 'empty':
        m['change_classes'] = []
    if mutation == 'unknown':
        m['change_classes'] = ['UNKNOWN_CHANGE']
    if mutation == 'omitted':
        m['change_classes'] = ['NEW_SOURCE']
    if mutation == 'self_authorize':
        m['bounded_live_authorized'] = True
    rejection(lambda: j4.select_plan(m), 'MANIFEST_INVALID|CHANGE_CLASS_OMITTED|CHANGE_CLASS_UNRESOLVED')


@pytest.mark.parametrize('cls', ['NEW_SOURCE', 'NEW_EVIDENCE_FAMILY'])
def test_unknown_impact_retains_core_and_blocks(cls):
    m = manifest(cls)
    m['affected_scenario_ids'] = []
    m['affected_sources'] = ['unknown_source']
    m['affected_evidence_families'] = ['unknown_family']
    p = j4.select_plan(m)
    assert p['selected_scenario_ids'] == j4.SAFETY
    assert p['gate_disposition'] == 'IMPACT_DECLARATION_REQUIRED'
    assert p['blocking_conditions']


@pytest.mark.parametrize('field', ['intended_source_authority', 'timing', 'missing', 'partial', 'citations'])
def test_evidence_family_requires_semantic_declaration(field):
    m = manifest('NEW_EVIDENCE_FAMILY')
    del m['semantic_impact'][field]
    assert j4.select_plan(m)['gate_disposition'] == 'IMPACT_DECLARATION_REQUIRED'


def test_source_exact_domain_mapping_not_path_guess():
    m = manifest('NEW_SOURCE')
    m.update(affected_scenario_ids=[], affected_data_needs=['monthly_revenue'])
    assert 'J1-09' in j4.select_plan(m)['selected_scenario_ids']
    m.update(affected_data_needs=[], changed_paths=['server/monthly_revenue.py'])
    assert j4.select_plan(m)['gate_disposition'] == 'IMPACT_DECLARATION_REQUIRED'


def test_no_silent_family_substitution():
    m = manifest('NEW_EVIDENCE_FAMILY')
    p = j4.select_plan(m)
    m['affected_evidence_families'] = ['monthly_revenue']
    rejection(lambda: j4.validate_plan(m, p), 'BINDING_OR_POLICY_MISMATCH')


def test_coverage_gap_cannot_be_laundered():
    m = manifest()
    p = j4.select_plan(m)
    assert p['gate_disposition'] == 'REGRESSION_COVERAGE_GAP'
    assert any(c['scenario_id'] == 'J1-02' for c in p['planned_or_missing_layers'])
    p['currently_covered_layers'] += p['planned_or_missing_layers']
    p['planned_or_missing_layers'] = []
    rejection(lambda: j4.validate_plan(m, p), 'COVERAGE_LAUNDERING')


def test_fresh_install_is_required_only_when_applicable():
    m = manifest()
    p = j4.select_plan(m)
    assert [c['scenario_id'] for c in p['required_layers'] if c['layer'] == 'fresh_install'] == ['J1-25']
    p['required_layers'] = [c for c in p['required_layers'] if c['layer'] != 'fresh_install']
    rejection(lambda: j4.validate_plan(m, p), 'BINDING_OR_POLICY_MISMATCH')


def test_refusal_does_not_fabricate_result_integration():
    p = j4.select_plan(manifest())
    assert {c['scenario_id'] for c in p['not_applicable_layers']} == set(j4.PREEXECUTION)
    assert not any(c['scenario_id'] in j4.PREEXECUTION and c['layer'] == 'integration' for c in p['required_layers'])


def test_union_cannot_be_replaced_by_intersection():
    m = manifest('NEW_SOURCE')
    m['change_classes'] += ['NEW_RELEASE']
    p = j4.select_plan(m)
    p['selected_scenario_ids'] = j4.SAFETY
    rejection(lambda: j4.validate_plan(m, p), 'SCENARIO_SCOPE_MISMATCH')


@pytest.mark.parametrize('field', ['regression_authority_hash', 'change_manifest_hash', 'regression_plan_hash', 'candidate_commit', 'candidate_tree', 'selected_scenarios', 'selected_dimensions', 'receipt_hash'])
def test_receipt_binding_mutations(field):
    m = manifest()
    p = j4.select_plan(m)
    r = j4.make_receipt(m, p)
    assert j4.validate_receipt(m, p, r)
    r[field] = [] if field == 'selected_scenarios' else {} if field == 'selected_dimensions' else '0' * (40 if 'candidate' in field else 64)
    rejection(lambda: j4.validate_receipt(m, p, r), 'RECEIPT_BINDING_MISMATCH')


@pytest.mark.parametrize('field', ['bounded_live_authorized', 'real_agent_authorized'])
def test_receipt_cannot_self_authorize(field):
    m = manifest('NEW_AGENT_HOST')
    p = j4.select_plan(m)
    r = j4.make_receipt(m, p)
    r[field] = True
    r['authorization_refs'] = ['synthetic_owner_grant']
    rejection(lambda: j4.validate_receipt(m, p, r), 'SELF_AUTHORIZATION_FORBIDDEN')


def test_semantic_failure_beats_missing_authorization_and_gaps():
    m = manifest('NEW_AGENT_HOST')
    p = j4.select_plan(m)
    r = j4.make_receipt(m, p, semantic_failures=['J1-16: H4 guard removed'])
    assert r['disposition'] == 'REGRESSION_SEMANTIC_FAILURE'
    assert j4.validate_receipt(m, p, r)


def test_j3_typed_observations_are_evaluated_not_prose():
    m = manifest('NEW_AGENT_HOST')
    p = j4.select_plan(m)
    r = j4.make_receipt(m, p, observations={'J1-16': {'facts': {'h4_state': 'coverage_incomplete', 'ordinary_return_interpretation': 'allowed'}, 'message': 'same harmless wording'}})
    assert r['disposition'] == 'REGRESSION_SEMANTIC_FAILURE'
    assert any('H4' in e for e in r['semantic_failures'])
    assert j4.validate_receipt(m, p, r)


def test_missing_execution_is_not_pass_and_synthetic_prose_not_agent_evidence():
    m = manifest('NEW_AGENT_HOST')
    p = j4.select_plan(m)
    r = j4.make_receipt(m, p)
    assert r['disposition'] == 'REGRESSION_COVERAGE_GAP'
    r['test_validator_evidence'] = [{'scenario_id': 'J1-01', 'layer': 'real_agent', 'test_node_id': __file__ + '::test_positive_class_plan', 'passed': True, 'candidate_commit': m['candidate_commit'], 'candidate_tree': m['candidate_tree'], 'synthetic': True}]
    rejection(lambda: j4.validate_receipt(m, p, r), 'EVIDENCE_SCOPE_OR_DUPLICATE')


def test_disposition_precedence_and_live_history_not_authority():
    gates = [{'layer': 'bounded_live', 'authorization': 'NOT_GRANTED'}, {'layer': 'real_agent', 'authorization': 'NOT_GRANTED'}]
    assert j4.gate_disposition([], [], [], gates) == 'REQUIRES_LIVE_AND_REAL_AGENT_AUTHORIZATION'
    assert j4.gate_disposition([], [], [], gates[:1]) == 'REQUIRES_SEPARATE_LIVE_AUTHORIZATION'
    assert j4.gate_disposition([], [], [], gates[1:]) == 'REQUIRES_SEPARATE_REAL_AGENT_AUTHORIZATION'
    assert j4.gate_disposition([], [], [], []) == 'REGRESSION_READY_NETWORK_FREE'
    assert j4.gate_disposition([], ['unresolved'], ['gap'], gates) == 'IMPACT_DECLARATION_REQUIRED'
    p = j4.select_plan(manifest('NEW_SOURCE'))
    assert p['historical_live_evidence']
    assert p['authorization_gated_layers'][0]['authorization'] == 'NOT_GRANTED'


def test_mcp_contract_requirement_cannot_be_removed():
    m = manifest()
    p = j4.select_plan(m)
    p['required_contract_checks'].remove('six_tool_contract')
    rejection(lambda: j4.validate_plan(m, p), 'BINDING_OR_POLICY_MISMATCH')


def test_plan_hash_tamper():
    m = manifest()
    p = j4.select_plan(m)
    p['regression_plan_hash'] = '0' * 64
    rejection(lambda: j4.validate_plan(m, p), 'BINDING_OR_POLICY_MISMATCH')


def test_receipt_failed_execution_cannot_hide_as_pending_authorization():
    m = manifest('NEW_AGENT_HOST')
    p = j4.select_plan(m)
    node = 'tests/acceptance/test_phase_j_j4_regression_authority.py::test_positive_class_plan'
    e = {'scenario_id': 'J1-01', 'layer': 'mcp', 'test_node_id': node, 'passed': False, 'candidate_commit': m['candidate_commit'], 'candidate_tree': m['candidate_tree'], 'synthetic': True}
    r = j4.make_receipt(m, p, [e])
    rejection(lambda: j4.validate_receipt(m, p, r), 'FAILED_EXECUTION_HIDDEN')
    r = j4.make_receipt(m, p, [e], [node])
    assert r['disposition'] == 'REGRESSION_SEMANTIC_FAILURE'
    assert j4.validate_receipt(m, p, r)


def test_synthetic_manifest_cannot_become_real_receipt():
    m = manifest()
    p = j4.select_plan(m)
    r = j4.make_receipt(m, p, synthetic=False)
    rejection(lambda: j4.validate_receipt(m, p, r), 'SYNTHETIC_MANIFEST_NOT_REAL_CANDIDATE')


def test_mcp_plan_tool_drift_is_rejected():
    m = manifest('NEW_MCP_VERSION')
    p = j4.select_plan(m)
    p['mcp_tool_baseline'].pop()
    rejection(lambda: j4.validate_plan(m, p), 'BINDING_OR_POLICY_MISMATCH')


def test_receipt_execution_evidence_binds_candidate_and_explicit_node():
    m = manifest()
    p = j4.select_plan(m)
    e = {'scenario_id': 'J1-01', 'layer': 'mcp', 'test_node_id': 'tests/acceptance/test_phase_j_j4_regression_authority.py::test_positive_class_plan', 'passed': True, 'candidate_commit': '0' * 40, 'candidate_tree': m['candidate_tree'], 'synthetic': True}
    r = j4.make_receipt(m, p, [e])
    rejection(lambda: j4.validate_receipt(m, p, r), 'EVIDENCE_CANDIDATE_MISMATCH')
    e['candidate_commit'] = m['candidate_commit']
    e['test_node_id'] = 'tests/acceptance/test_phase_j_j4_regression_authority.py'
    rejection(lambda: j4.validate_receipt(m, p, j4.make_receipt(m, p, [e])), 'EXPLICIT_TEST_NODE_REQUIRED')


def complete_synthetic_inputs(plan, manifest):
    """Contract-test data only; never actual candidate regression evidence."""
    rows = {r['scenario_id']: r for r in j4.baseline()[2]['scenarios']}
    observations = {}
    for sid in plan['selected_scenario_ids']:
        observed = {}
        for assertion in rows[sid]['assertions']:
            target = observed.setdefault(assertion['context'], {})
            parts = assertion['path'].split('.')
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = assertion['expected']
        observations[sid] = observed
    node = 'tests/acceptance/test_phase_j_j4_regression_authority.py::test_complete_synthetic_receipt_retains_live_gate'
    evidence = [{'scenario_id': c['scenario_id'], 'layer': c['layer'], 'test_node_id': node, 'passed': True, 'candidate_commit': manifest['candidate_commit'], 'candidate_tree': manifest['candidate_tree'], 'synthetic': True} for c in plan['required_layers']]
    checks = [{'check': c, 'passed': True, 'evidence_ref': node, 'candidate_commit': manifest['candidate_commit'], 'candidate_tree': manifest['candidate_tree']} for c in sorted(set(plan['required_validators'] + ['six_tool_contract'] + plan['required_contract_checks']))]
    return evidence, observations, checks


def test_complete_synthetic_receipt_retains_live_gate():
    m = manifest('NEW_SOURCE')
    p = j4.select_plan(m)
    evidence, observations, checks = complete_synthetic_inputs(p, m)
    r = j4.make_receipt(m, p, evidence, observations=observations, check_evidence=checks)
    assert r['semantic_failures'] == []
    assert r['coverage_gaps'] == []
    assert r['disposition'] == 'REQUIRES_SEPARATE_LIVE_AUTHORIZATION'
    assert j4.validate_receipt(m, p, r)


def test_synthetic_receipt_cannot_certify_release_ready():
    m = manifest()
    p = j4.select_plan(m)
    evidence, observations, checks = complete_synthetic_inputs(p, m)
    r = j4.make_receipt(m, p, evidence, observations=observations, check_evidence=checks)
    rejection(lambda: j4.validate_receipt(m, p, r), 'SYNTHETIC_RECEIPT_NOT_PRODUCT_ACCEPTANCE')


def test_missing_required_check_keeps_receipt_coverage_gap():
    m = manifest('NEW_SOURCE')
    p = j4.select_plan(m)
    evidence, observations, checks = complete_synthetic_inputs(p, m)
    checks = [e for e in checks if e['check'] != 'six_tool_contract']
    r = j4.make_receipt(m, p, evidence, observations=observations, check_evidence=checks)
    assert r['disposition'] == 'REGRESSION_COVERAGE_GAP'
    assert {'check': 'six_tool_contract', 'reason': 'missing_passing_check_evidence'} in r['coverage_gaps']
    assert j4.validate_receipt(m, p, r)


def test_nonexistent_test_node_cannot_qualify_receipt_evidence():
    m = manifest()
    p = j4.select_plan(m)
    e = {'scenario_id': 'J1-01', 'layer': 'mcp', 'test_node_id': 'tests/acceptance/test_phase_j_j4_regression_authority.py::test_does_not_exist', 'passed': True, 'candidate_commit': m['candidate_commit'], 'candidate_tree': m['candidate_tree'], 'synthetic': True}
    rejection(lambda: j4.validate_receipt(m, p, j4.make_receipt(m, p, [e])), 'EXPLICIT_TEST_NODE_REQUIRED')
