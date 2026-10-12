"""Frozen-policy alignment, real production-path receipts and negative mutations."""
import copy
import inspect
import pytest
from scripts import validate_phase_j_final_closure_r2_r1 as v
from scripts.m8r_06_03_production_adapter import _assess_current_observation
from tests.helpers.phase_j_closure_r2_r1 import execute

@pytest.fixture
def policy():
    return v.baseline()

def observation(retrieved='2026-10-08T06:00:00Z', source=None):
    return {'source': 'TWSE_MIS', 'source_timestamp': source, 'retrieved_at': retrieved}

@pytest.mark.parametrize('clock,status,label,age', [
    ('2026-10-08T06:00:00Z', 'fresh', 'fresh_intraday_snapshot', 0),
    ('2026-10-08T06:14:59Z', 'fresh', 'fresh_intraday_snapshot', 899),
    ('2026-10-08T06:15:00Z', 'fresh', 'fresh_intraday_snapshot', 900),
    ('2026-10-08T06:15:01Z', 'stale', 'stale_intraday_snapshot', 901),
    ('2026-10-08T05:59:59Z', 'unresolved', 'unknown', None),
    ('invalid', 'unresolved', 'unknown', None),
    ('', 'unresolved', 'unknown', None),
])
def test_retrieval_age_delegates_to_frozen_m8(policy, clock, status, label, age):
    native = observation()
    original = copy.deepcopy(native)
    a = _assess_current_observation(native, policy, now_utc=clock)
    assert (a['status'], a['freshness_assessment'], a['age_seconds']) == (status, label, age)
    assert a['source_timestamp'] is None and a['retrieved_at_utc'] == native['retrieved_at']
    assert all(a[k] is True for k in ('retrieved_time_only', 'exchange_timestamp_absent', 'not_realtime_guaranteed'))
    assert native == original

@pytest.mark.parametrize('field,value', [
    ('allow_retrieved_at_only_intraday_freshness', False),
    ('allow_retrieved_at_only_intraday_freshness', None),
    ('requires_exchange_timestamp_for_fresh', True),
    ('requires_exchange_timestamp_for_fresh', None),
    ('max_intraday_age_seconds', None),
    ('max_intraday_age_seconds', '900'),
    ('max_intraday_age_seconds', True),
    ('max_intraday_age_seconds', -1),
])
def test_insufficient_policy_cannot_self_authorize_fresh(policy, field, value):
    policy['freshness_evaluator_policy'][field] = value
    a = _assess_current_observation(observation(), policy)
    assert a['status'] == 'unresolved' and a['freshness_assessment'] == 'unknown'
    assert not a['safe_for_ai_context']

@pytest.mark.parametrize('retrieved', [None, 'invalid', '2026-10-08T06:00:00'])
def test_missing_invalid_or_non_authoritative_timing(policy, retrieved):
    a = _assess_current_observation(observation(retrieved), policy)
    assert a['status'] == 'unresolved' and a['freshness_assessment'] == 'unknown'

def test_malformed_policy_is_unresolved(policy):
    policy['freshness_evaluator_policy'] = ['invalid']
    assert _assess_current_observation(observation(), policy)['status'] == 'unresolved'

def test_source_timestamp_remains_authority(policy):
    a = _assess_current_observation(observation(source='2026-09-01T05:30:00Z'), policy)
    assert a['status'] == 'stale' and a['age_seconds'] == a['delay_seconds'] == 3198600
    assert a['freshness_assessment'] == 'stale_intraday_snapshot' and not a['safe_for_ai_context']
    assert not a['retrieved_time_only'] and not a['exchange_timestamp_absent']

@pytest.fixture(scope='module')
def recent(tmp_path_factory):
    return execute(tmp_path_factory.mktemp('closure-r2-r1-recent'))

def test_recent_production_result_audit_handoff(recent):
    assert v.validate_recent(recent)
    assert recent['result']['status'] == 'full_success'
    assert recent['initial_execution_count'] == 1 and recent['additional_execution_count'] == 0

@pytest.mark.parametrize('mutation', [
    'unresolved', 'stale', 'exchange_time', 'retrieved_time_only',
    'exchange_timestamp_absent', 'not_realtime_guaranteed', 'handoff',
    'renderer', 'audit_hash', 'real_agent', 'network', 'realtime_guarantee',
])
def test_production_receipt_mutations_rejected(recent, mutation):
    r = copy.deepcopy(recent)
    ev = r['result']['targets'][0]['evidence']['current_observation']
    if mutation in ('unresolved', 'stale'):
        ev['currentness']['status'] = mutation
    elif mutation == 'exchange_time':
        r['normalized_observation']['source_timestamp'] = r['normalized_observation']['retrieved_at_utc']
    elif mutation in ('retrieved_time_only', 'exchange_timestamp_absent', 'not_realtime_guaranteed'):
        ev['currentness'].pop(mutation)
    elif mutation == 'handoff':
        r['handoff']['canonical_result']['status'] = 'failed'
    elif mutation == 'renderer':
        ev['observed_fields']['freshness_context']['status'] = 'stale'
    elif mutation == 'realtime_guarantee':
        r['handoff']['ai_ready_markdown'] += '\nrealtime guaranteed quote'
    elif mutation == 'audit_hash':
        r['source_artifact_sha256'] = '0' * 64
    elif mutation == 'real_agent':
        r['real_agent_sessions'] = 1
    else:
        r['market_network']['GET'] = 1
    with pytest.raises(ValueError):
        v.validate_recent(r)

def test_no_parallel_threshold_or_renderer_classifier():
    source = inspect.getsource(_assess_current_observation)
    assert '900' not in source and 'J1-21' not in source
    renderer = (v.ROOT / 'scripts/m8r_05c/markdown_renderer.py').read_text()
    assert 'evaluate_evidence_currentness' not in renderer
    assert 'build_source_freshness_assessment' not in renderer
