"""A4 current production-candidate proofs. All source delegates are fake."""
import copy
import json
from pathlib import Path

import pytest

from scripts.phase_i_i2_a4_proof import (
    ROOT, BASELINE, CATALOG, ROUTING, SOURCE, EXECUTOR, CAPABILITY,
    baseline_json, current_json, production_preview, record, rollback_authority,
    run_production_offline_proof, verify_a3_hashes, verify_candidate_authority,
)
from scripts.run_phase_i_i2_a3_bounded_live_acceptance import deterministic_fixture_payload
from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext
from scripts.m8r_05b_03.errors import OrchestrationError
from server.services import phase_i_i2_production_candidate as candidate


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("A4 external network forbidden")
    monkeypatch.setattr("socket.socket.connect", deny)
    monkeypatch.setattr("socket.create_connection", deny)


def test_current_catalog_source_and_unique_passive_registry():
    verify_candidate_authority()
    verify_a3_hashes()


@pytest.mark.parametrize("targets,ops,requests", [(('1101',), 1, 1), (('1101', '1102'), 2, 1)])
def test_ordinary_preview_has_no_overlay_and_requires_approval(targets, ops, requests):
    _, _, _, result = production_preview(targets)
    assert result['preview']['status'] == 'ready_for_confirmation'
    plan = result['orchestration_plan']
    assert len(plan['operations']) == ops and len(plan['batch_groups']) == 1
    assert plan['accounting']['network_request_estimate'] == requests
    for operation in plan['operations']:
        assert operation['executor_id'] == EXECUTOR
        assert operation['operation_status'] == 'executable_pending_approval'
        assert operation['network_required']


def test_tpex_remains_nonexecutable():
    _, _, _, result = production_preview(('6488',))
    assert all(op.get('executor_id') != EXECUTOR for op in result['orchestration_plan']['operations'])


@pytest.mark.parametrize('status', ['complete', 'partial', 'unavailable', 'source_failed', 'binding_failed'])
def test_normal_production_governed_chain_status_and_same_source(tmp_path, status):
    rows = json.loads(deterministic_fixture_payload())
    selected = rows[1]
    if status == 'partial':
        selected['Open'] = '-'
    elif status == 'unavailable':
        for row in rows:
            row['Contract'] = 'MTX'
    elif status == 'source_failed':
        selected['Last'] = 'malformed'
    elif status == 'binding_failed':
        rows.append(copy.deepcopy(selected))
    payload = json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode()
    proof = run_production_offline_proof(tmp_path / status, payload)
    assert proof['fake_acquisitions'] == 1 and proof['external_market_calls'] == 0
    assert proof['raw_persistence'] == 'NONE'
    assert len(proof['evidence']) == 2
    failed = status in {'source_failed', 'binding_failed'}
    for evidence, result in zip(proof['evidence'], proof['execution']['dispatch_outcomes']):
        assert evidence['status'] == status
        assert result['status'] == ('failed' if failed else 'succeeded')
        assert result['error_code'] == (status if failed else None)
        assert result['result_item_count'] == 1 and result['evidence_artifacts']
    assert proof['execution']['consumption_state'] == ('consumed_failed' if failed else 'consumed_success')


def test_i2_roll_001_exact_baseline_and_passive_preview():
    rolled, registry = rollback_authority()
    assert record(rolled[CATALOG], 'data_need_capabilities') == record(baseline_json(CATALOG), 'data_need_capabilities')
    assert record(rolled[ROUTING], 'routes') == record(baseline_json(ROUTING), 'routes')
    assert rolled[SOURCE] == baseline_json(SOURCE)
    assert not registry.routes_for_executor(EXECUTOR)
    from scripts.phase_i_i2_a4_proof import historical_dormant_authority
    with historical_dormant_authority():
        _, _, _, result = production_preview()
        assert result['orchestration_plan']['accounting']['network_request_estimate'] == 0
        assert all(op['operation_status'] == 'plan_only_not_executable' and op['executor_id'] is None for op in result['orchestration_plan']['operations'])
    verify_candidate_authority()
    verify_a3_hashes()


def valid_requests(tmp_path):
    out = run_production_offline_proof(tmp_path / 'requests', deterministic_fixture_payload())
    # Preflight requests are durable governed files, not fabricated requests.
    return out['execution_requests']


@pytest.mark.parametrize('field,value', [
    ('executor_id', 'wrong'), ('capability_id', 'recent_performance'), ('market', 'TPEX'),
    ('network_authorized', False), ('timeout_seconds', 15), ('maximum_records', 2),
    ('parameters', {'lookback_trading_days': 1}), ('approved_security_types', ['etf']),
    ('approved_security_identifiers', ['TPEX:6488']), ('approved_security_identifiers', ['TWSE:bad']),
])
def test_entire_batch_validated_before_transport(tmp_path, monkeypatch, field, value):
    requests = valid_requests(tmp_path)
    assert len(requests) == 2
    requests[1][field] = value
    calls = []
    monkeypatch.setattr(candidate, '_read_once', lambda *args: calls.append(args))
    with pytest.raises(OrchestrationError):
        candidate.production_batch_operation_adapter_candidate(tuple(requests), DispatchRuntimeContext(str(tmp_path), 'execute-approved'))
    assert calls == []


def test_nonapproved_mode_and_51_targets_fail_before_transport(tmp_path, monkeypatch):
    requests = valid_requests(tmp_path)
    calls = []
    monkeypatch.setattr(candidate, '_read_once', lambda *args: calls.append(args))
    for requests_, mode in ((requests, 'dry-run'), (requests * 26, 'execute-approved')):
        with pytest.raises(OrchestrationError):
            candidate.production_batch_operation_adapter_candidate(tuple(requests_), DispatchRuntimeContext(str(tmp_path), mode))
    assert not calls


def test_50_targets_allowed_and_second_acquisition_denied_before_io(tmp_path, monkeypatch):
    base = valid_requests(tmp_path)[0]
    requests = []
    for i in range(50):
        req = copy.deepcopy(base)
        req['operation_id'] = 'umeop-op-v1-' + f'{i:020x}'
        req['execution_request_id'] = 'umereq-v2-' + f'{i:020x}'
        req['relative_contained_output_path'] = f"operations/{req['operation_id']}.execution-request.json"
        req['approved_security_identifiers'] = [f'TWSE:{1100+i}']
        requests.append(req)
    calls = []
    def fake(*args):
        calls.append(args)
        return 200, {'Content-Type': 'application/octet-stream'}, deterministic_fixture_payload()
    monkeypatch.setattr(candidate, '_read_once', fake)
    ctx = DispatchRuntimeContext(str(tmp_path / 'batch50'), 'execute-approved')
    assert len(candidate.production_batch_operation_adapter_candidate(tuple(requests), ctx)) == 50
    with pytest.raises(OrchestrationError, match='reservation_failed'):
        candidate.production_batch_operation_adapter_candidate(tuple(requests), ctx)
    assert len(calls) == 1


@pytest.mark.parametrize('status,mime,body', [(302, 'application/json', b'[]'), (500, 'application/json', b'[]'),
    (200, 'text/html', b'bad'), (200, 'application/json', b'\xff'),
    (200, 'application/json', b'x' * 2097153), (200, 'application/json', b'{}')],
    ids=['redirect', 'http-failure', 'bad-mime', 'invalid-utf8', 'oversize', 'wrong-root'])
def test_transport_failure_retains_honest_normalized_failure(tmp_path, monkeypatch, status, mime, body):
    requests = valid_requests(tmp_path)
    calls = []
    def fake(*args):
        calls.append(args)
        return status, {'Content-Type': mime}, body
    monkeypatch.setattr(candidate, '_read_once', fake)
    results = candidate.production_batch_operation_adapter_candidate(tuple(requests), DispatchRuntimeContext(str(tmp_path / 'failure'), 'execute-approved'))
    assert len(calls) == 1
    for result in results:
        assert result['status'] == 'failed' and result['error_code'] == 'source_failed'
        evidence = json.loads((tmp_path / 'failure' / result['evidence_artifacts'][0]['relative_path']).read_bytes())
        assert evidence['status'] == 'source_failed' and 'market_data' not in evidence
        assert evidence['transport']['retry_count'] == 0
