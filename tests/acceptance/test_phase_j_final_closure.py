"""Closure decision mutation tests; no new scenario acceptance execution."""
from copy import deepcopy
import socket
import pytest

from scripts import validate_phase_j_final_closure as closure
from scripts import phase_j_j4_regression_authority as j4


@pytest.fixture(autouse=True)
def network_denied(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('closure must not use socket transport')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'create_connection', denied)


def reject(call, reason):
    with pytest.raises(ValueError, match=reason):
        call()


def decision():
    return closure.derive_decision()


def cell(d, sid, layer):
    return next(r for r in d['gap_adjudication']['cells'] if r['scenario_id'] == sid and r['layer'] == layer)


def test_exit_decision_is_derived_and_conservatively_blocked():
    d = decision()
    assert closure.validate_decision(d)
    assert d == decision()
    assert d['disposition'] == 'PHASE_J_FINAL_CLOSURE_HARD_BLOCK'
    assert [r['criterion_id'] for r in d['exit_criteria_results'] if r['status'] == 'FAIL'] == ['E16', 'E17']
    s = d['summary']
    assert s['total_matrix_cells'] == s['covered_cells'] + s['not_applicable_matrix_cells'] + s['remaining_gap_count'] == 243
    assert sum(s['classification_counts'].values()) == s['remaining_gap_count']
    assert s['layer_witness_count'] == 8 and s['unsatisfied_layer_count'] == 1
    assert d['blocker_obligations'][0]['minimum_missing_witnesses'] == 1
    assert len([r for r in d['blocker_cells'] if r.endswith('/real_agent')]) == 27
    assert {o.get('scenario_id') for o in d['blocker_obligations'] if 'scenario_id' in o} == {'J1-02','J1-04','J1-05','J1-19','J1-21'}


def test_every_remaining_matrix_gap_has_exactly_one_adjudication():
    d = decision()
    matrix = j4.load(j4.ROOT / closure.MATRIX)
    expected = {r['scenario_id'] + '/' + layer for r in matrix['scenarios'] for layer, c in r['layers'].items() if c['status'] not in closure.COVERED | {'NOT_APPLICABLE'}}
    assert expected == {r['cell_id'] for r in d['gap_adjudication']['cells']}
    assert len(expected) == len(d['gap_adjudication']['cells'])


@pytest.mark.parametrize('mutation,reason', [('drop','GAP_UNIVERSE_INCOMPLETE'),('duplicate','DUPLICATE_GAP_ADJUDICATION'),('matrix_status','MATRIX_STATUS_LAUNDERED'),('blocker_flag','BLOCKER_FLAG_INCONSISTENT'),('unknown_class','UNKNOWN_CLOSURE_CLASSIFICATION')])
def test_gap_universe_and_closed_classification_mutations(mutation, reason):
    d = decision()
    rows = d['gap_adjudication']['cells']
    if mutation == 'drop':
        rows.pop()
    if mutation == 'duplicate':
        rows.append(deepcopy(rows[0]))
    if mutation == 'matrix_status':
        rows[0]['accepted_matrix_status'] = 'COVERED_EXISTING'
    if mutation == 'blocker_flag':
        rows[0]['is_phase_j_blocker'] = not rows[0]['is_phase_j_blocker']
    if mutation == 'unknown_class':
        rows[0]['closure_classification'] = 'PROBABLY_COVERED'
    reject(lambda: closure.validate_decision(d), reason)


def test_blocker_cannot_become_future_gap_without_authority():
    d = decision()
    r = cell(d, 'J1-01', 'real_agent')
    r.update(closure_classification='AUTHORIZATION_GATED_FUTURE_LAYER', closure_reason_code='SEPARATE_REAL_AGENT_AUTHORIZATION_REQUIRED', is_phase_j_blocker=False)
    reject(lambda: closure.validate_decision(d), 'CLASSIFICATION_OR_AUTHORITY_UNPROVEN')


@pytest.mark.parametrize('sid,layer', [('J1-03','service_api'),('J1-09','contract_fixture'),('J1-17','workbench')])
def test_supported_missing_evidence_cannot_be_hidden_as_unsupported(sid, layer):
    d = decision()
    r = cell(d,sid,layer)
    assert r['closure_classification'] == 'FUTURE_REGRESSION_COVERAGE_GAP'
    r.update(closure_classification='ACCEPTED_FAIL_CLOSED_OR_UNSUPPORTED',closure_reason_code='SCENARIO_UNSUPPORTED_BY_ACCEPTED_CONTRACT')
    reject(lambda: closure.validate_decision(d), 'CLASSIFICATION_OR_AUTHORITY_UNPROVEN')


def test_unsupported_capital_reduction_cannot_be_marked_supported():
    d = decision()
    r = cell(d,'J1-15','service_api')
    assert r['closure_classification'] == 'ACCEPTED_FAIL_CLOSED_OR_UNSUPPORTED'
    r['accepted_readiness_status'] = 'SUPPORTED_BOUNDED'
    reject(lambda: closure.validate_decision(d), 'CLASSIFICATION_OR_AUTHORITY_UNPROVEN')


def test_fresh_install_fail_closed_context_does_not_relabel_supported_scenario():
    d = decision()
    r = cell(d,'J1-01','fresh_install')
    assert r['accepted_readiness_status'] == 'SUPPORTED_BOUNDED'
    assert r['classification_scope'] == 'EMPTY_INSTALLATION_IDENTITY_AUTHORITY_BOUNDARY_NOT_POSITIVE_SCENARIO_EXECUTION'
    assert r['accepted_matrix_status'] == 'PLANNED'
    assert any('fresh_install' in a['ref'] for a in r['authority_refs'])
    r['accepted_readiness_status'] = 'UNSUPPORTED_FAIL_CLOSED'
    reject(lambda: closure.validate_decision(d), 'CLASSIFICATION_OR_AUTHORITY_UNPROVEN')


def test_remove_bounded_live_witness():
    d = decision()
    row = next(w for w in d['layer_exit_witnesses'] if w['layer'] == 'bounded_live')
    row['accepted_witnesses'] = []
    row['closure_disposition'] = 'FAIL'
    reject(lambda: closure.validate_decision(d), 'LAYER_WITNESS_OR_DEFERRAL_UNPROVEN')


def test_no_real_agent_witness_or_deferral_cannot_claim_pass():
    d = decision()
    real = next(w for w in d['layer_exit_witnesses'] if w['layer'] == 'real_agent')
    assert real['accepted_witnesses'] == real['deferral_authority_if_any'] == []
    assert real['closure_disposition'] == 'FAIL'
    d['disposition'] = 'PHASE_J_FINAL_CLOSURE_PASS_CANDIDATE'
    reject(lambda: closure.validate_decision(d), 'PASS_FORBIDDEN_CURRENT_BLOCKER')


def test_invented_real_agent_deferral_does_not_waive_phase_j():
    d = decision()
    real = next(w for w in d['layer_exit_witnesses'] if w['layer'] == 'real_agent')
    real['deferral_authority_if_any'] = [{'ref':'Phase K later','review_id':'5482700449'}]
    real['closure_disposition'] = 'PASS'
    reject(lambda: closure.validate_decision(d), 'LAYER_WITNESS_OR_DEFERRAL_UNPROVEN')
    c = j4.load(closure.CONTRACT)
    c['layer_exit_policy']['real_agent_accepted_deferrals'] = ['5482700449']
    reject(lambda: closure.validate_contract(c), 'INVENTED_LAYER_DEFERRAL_OR_WITNESS')


@pytest.mark.parametrize('mutation,reason', [('B03_removed','J_B03_NOT_CLOSED'),('B04_removed','J_B04_NOT_CLOSED'),('Phase_I_removed','PHASE_I_NOT_CLOSED'),('roadmap_completed','ROADMAP_PHASE_J_CHECKBOX_CHANGED')])
def test_prerequisite_and_roadmap_mutations(mutation, reason):
    c = j4.load(closure.CONTRACT)
    docs = closure.validate_authorities(c)
    if mutation == 'B03_removed':
        docs[closure.B03]['decision'] = 'OPEN'
    if mutation == 'B04_removed':
        docs[closure.B04]['terminal_disposition'] = 'HARD_BLOCK'
    if mutation == 'Phase_I_removed':
        docs[closure.PHASE_I]['status'] = 'INCOMPLETE'
    if mutation == 'roadmap_completed':
        docs['ROADMAP.md'] = docs['ROADMAP.md'].replace('# [ ] Phase J — Integrated Research Acceptance','# [x] Phase J — Integrated Research Acceptance')
    reject(lambda: closure.validate_authorities(c, docs), reason)


def test_j_b03_role_cannot_be_j_b04_review():
    c = j4.load(closure.CONTRACT)
    assert c['J_B03_authority']['authority_kind'] == 'governance_record' and c['J_B03_authority']['review_id'] is None
    c['J_B03_authority'] = {'review_id':'5479527453','authority_kind':'GitHub_review'}
    reject(lambda: closure.validate_contract(c), 'J_B03_AUTHORITY_ROLE_INVALID')


@pytest.mark.parametrize('path', [closure.GOLDEN, closure.REGRESSION])
def test_golden_and_regression_hashes_cannot_drift(path):
    c = j4.load(closure.CONTRACT)
    c['immutable_artifact_hashes'][path] = '0' * 64
    reject(lambda: closure.validate_contract(c), 'ACCEPTED_ARTIFACT_HASH_DRIFT')


@pytest.mark.parametrize('mutation,reason', [('MCP7','MCP_TOOL_COUNT_OR_NAME_DRIFT'),('Phase_K_started','PHASE_K_UNAUTHORIZED_START'),('J4_review_changed','INDEPENDENT_REVIEW_ROLE_DRIFT')])
def test_public_and_authority_boundary_mutations(mutation, reason):
    c = j4.load(closure.CONTRACT)
    if mutation == 'MCP7':
        c['MCP_tools'].append('closure_tool')
    if mutation == 'Phase_K_started':
        c['Phase_K'] = 'STARTED'
    if mutation == 'J4_review_changed':
        c['accepted_reviews']['J4']['review_id'] = '5482393445'
    reject(lambda: closure.validate_contract(c), reason)


def test_future_gap_preserves_original_matrix_and_j4_obligation():
    before = j4.file_hash(j4.ROOT / closure.MATRIX)
    d = decision()
    r = cell(d,'J1-03','workbench')
    assert r['closure_classification'] == 'FUTURE_REGRESSION_COVERAGE_GAP'
    assert r['accepted_matrix_status'] == 'PLANNED'
    p = j4.select_plan(j4.load(j4.ROOT/'tests/fixtures/phase_j/j4/new_release.json'))
    assert any(c['scenario_id']=='J1-03' and c['layer']=='workbench' for c in p['planned_or_missing_layers'])
    assert j4.file_hash(j4.ROOT / closure.MATRIX) == before


def test_pass_cannot_be_independent_of_blocker_counts_or_layer_summary():
    d = decision()
    d['summary']['classification_counts']['CURRENT_PHASE_J_BLOCKER'] = 0
    d['summary']['unsatisfied_layer_count'] = 0
    d['disposition'] = 'PHASE_J_FINAL_CLOSURE_PASS_CANDIDATE'
    reject(lambda: closure.validate_decision(d), 'PASS_FORBIDDEN_CURRENT_BLOCKER')


def test_bounded_live_witness_is_integrated_scope_not_all_sources_claim():
    d = decision()
    live = next(w for w in d['layer_exit_witnesses'] if w['layer']=='bounded_live')
    a6 = next(w for w in live['accepted_witnesses'] if 'GET_dispatches_historical' in w)
    assert a6['GET_dispatches_historical'] == 3 and a6['new_GET_dispatches'] == 0
    assert a6['scenario_ids'] == ['J1-14','J1-16','J1-17']
    assert a6['authority']['review']['review_id'] == '5479527453'


def test_non_every_scenario_every_layer_does_not_waive_missing_phase_layer():
    c = j4.load(closure.CONTRACT)
    assert c['layer_exit_policy']['every_scenario_every_layer_required'] is False
    assert c['layer_exit_policy']['roadmap_requires_all_nine_layers'] is True
    assert c['layer_exit_policy']['Phase_K_substitutes_for_Phase_J_real_agent'] is False
    assert c['layer_exit_policy']['authorization_not_granted_is_deferral'] is False


def test_all_18_criteria_and_9_layers_are_explicit():
    d = decision()
    assert [e['criterion_id'] for e in d['exit_criteria_results']] == ['E'+str(i) for i in range(1,19)]
    assert [w['layer'] for w in d['layer_exit_witnesses']] == j4.LAYERS
    assert len(j4.load(closure.CONTRACT)['semantic_dimensions']) == 11


@pytest.mark.parametrize('sid', ['J1-02','J1-04','J1-05','J1-19','J1-21'])
def test_supported_must_have_with_no_execution_witness_is_not_future_only(sid):
    d = decision()
    r = cell(d,sid,'service_api')
    assert r['closure_classification'] == 'CURRENT_PHASE_J_BLOCKER'
    assert r['closure_reason_code'] == 'SUPPORTED_SCENARIO_WITNESS_MISSING'
    r.update(closure_classification='FUTURE_REGRESSION_COVERAGE_GAP',closure_reason_code='FUTURE_CHANGED_CANDIDATE_REGRESSION_SCOPE',is_phase_j_blocker=False)
    reject(lambda: closure.validate_decision(d), 'CLASSIFICATION_OR_AUTHORITY_UNPROVEN')



def test_pass_layer_guard_rejects_no_witness_even_with_empty_blocker_list():
    d = decision()
    synthetic_criteria = [dict(e, status='PASS') for e in d['exit_criteria_results']]
    # Negative gate fixture only. No accepted deferral is invented for a positive case.
    reject(lambda: closure.require_pass_eligibility(synthetic_criteria, [], d['layer_exit_witnesses']), 'PASS_FORBIDDEN_LAYER_WITNESS_MISSING')


def test_derived_counts_cannot_be_hand_maintained_to_hide_gap():
    d = decision()
    d['summary']['remaining_gap_count'] -= 1
    reject(lambda: closure.validate_decision(d), 'CLOSURE_DECISION_NOT_MACHINE_DERIVED')


def test_missing_canonical_j_b03_record_is_rejected():
    c = j4.load(closure.CONTRACT)
    docs = closure.validate_authorities(c)
    del docs[closure.B03]
    reject(lambda: closure.validate_authorities(c, docs), 'ACCEPTED_AUTHORITY_MISSING')
