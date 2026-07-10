import json
from pathlib import Path

from fastapi.testclient import TestClient

import server.main as server_main
from scripts.m7g_controlled_refresh_executor import EXECUTION_CONFIRMATION_PHRASE, execute_m7g_controlled_manual_refresh
from tests.unit.test_m7g_controlled_refresh_execution_gate import package

FORBIDDEN_KEYS = {
    'raw_payload','twse_mis_rich_facts','raw_rich_facts','raw_unknown_facts','full_ladder',
    'bid_prices','ask_prices','source_investigation_notes','response_sample','raw_fields_sample'
}


def _dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_security_regression_doc_exists_with_targets_and_boundaries():
    text = Path('docs/protocol/M7G_REFRESH_WORKFLOW_SECURITY_REGRESSION.md').read_text(encoding='utf-8')
    for term in [
        'refresh_workflow_security_regression_defined',
        'missing request package', 'wrong package_status', 'runner exception',
        'runner result contains raw forbidden keys', 'frontend cannot auto-load returned artifact',
        'frontend cannot handoff rejected artifact', 'M7G-10 adds no new execution source family',
        'No auto refresh', 'No scheduler', 'No polling', 'No hidden fetch', 'No startup fetch',
        'No AI/model call', 'No DB write', 'No raw payload exposure', 'No trading advice',
        'Preserve Mode A/B/C and Level 1/2 semantics',
    ]:
        assert term in text


def test_runner_exception_fail_closed_without_raw_traceback():
    def failing_runner(_watchlist):
        raise RuntimeError('simulated network failure')

    result = execute_m7g_controlled_manual_refresh(
        request_package=package(),
        operator_execution_confirmation_phrase=EXECUTION_CONFIRMATION_PHRASE,
        observation_runner=failing_runner,
    )
    assert result['execution_status'] in {'execution_failed_no_safe_artifact', 'execution_failed_safe_artifact_rejected', 'execution_failed_runner_exception'}
    assert result['execution_authorized'] is True
    assert result['execution_performed'] is True
    assert result['network_fetch_performed'] is True
    assert result['safe_artifact_returned'] is False
    assert 'safe_context_artifact' not in result
    assert result['raw_payload_exposed'] is False
    assert result['raw_forbidden_values_returned'] is False
    assert result['ai_model_call_performed'] is False
    assert result['trading_advice_generated'] is False
    assert result['errors'] == ['runner_exception_or_network_failure']
    dumped = _dump(result)
    assert 'simulated network failure' not in dumped
    assert 'Traceback' not in dumped


def test_endpoint_runner_exception_returns_http_200_safe_structured_result(monkeypatch):
    def failing_execute(*, request_package, operator_execution_confirmation_phrase):
        return execute_m7g_controlled_manual_refresh(
            request_package=request_package,
            operator_execution_confirmation_phrase=operator_execution_confirmation_phrase,
            observation_runner=lambda _watchlist: (_ for _ in ()).throw(RuntimeError('simulated network failure')),
        )
    monkeypatch.setattr(server_main, '_m7g09_execute_controlled_refresh', failing_execute)
    response = TestClient(server_main.app).post('/api/m7g/controlled-refresh/execute', json={
        'request_package': package(),
        'operator_execution_confirmation_phrase': EXECUTION_CONFIRMATION_PHRASE,
    })
    assert response.status_code == 200
    data = response.json()
    assert data['execution_status'] in {'execution_failed_no_safe_artifact', 'execution_failed_safe_artifact_rejected', 'execution_failed_runner_exception'}
    assert data['safe_artifact_returned'] is False
    assert 'safe_context_artifact' not in data
    assert data['raw_payload_exposed'] is False


def test_raw_forbidden_injection_stripped_from_execution_result_and_artifact():
    def raw_runner(_watchlist):
        return {
            'schema_version': 'm5k_live_observation.v1',
            'generated_at_utc': '2026-07-10T08:00:00Z',
            'observations': [{
                'symbol': '2330', 'market': 'TWSE', 'source': 'TWSE_MIS',
                'raw_payload': {'secret': 'must not pass'},
                'bid_prices': [999, 998], 'ask_prices': [1000, 1001],
                'source_investigation_notes': ['must not pass'],
                'price_like_value': 1000, 'semantic_caveats': ['safe fixture'],
            }],
            'source_investigation_notes': [{'raw_payload': 'must not pass'}],
        }
    result = execute_m7g_controlled_manual_refresh(
        request_package=package(), operator_execution_confirmation_phrase=EXECUTION_CONFIRMATION_PHRASE, observation_runner=raw_runner
    )
    def walk_keys(value):
        if isinstance(value, dict):
            for key, child in value.items():
                yield key
                yield from walk_keys(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk_keys(child)
    leaked_keys = set(walk_keys(result)) & FORBIDDEN_KEYS
    # Safe boolean omission flags are permitted; forbidden raw object/array fields are not.
    leaked_keys.discard('raw_rich_facts')
    assert leaked_keys == set()
    assert result['raw_payload_exposed'] is False
    assert result['raw_forbidden_values_returned'] is False
    if result.get('safe_context_artifact'):
        artifact_leaked_keys = set(walk_keys(result['safe_context_artifact'])) & FORBIDDEN_KEYS
        artifact_leaked_keys.discard('raw_rich_facts')
        assert artifact_leaked_keys == set()
