import copy
from pathlib import Path
from fastapi.testclient import TestClient

from server.main import app
from scripts.m7g_controlled_refresh_executor import (
    DECLARED_BUT_NOT_YET_EXECUTABLE_SOURCE_FAMILIES,
    DECLARED_SOURCE_FAMILIES,
    EXECUTION_CONFIRMATION_PHRASE,
    EXECUTION_SUPPORTED_SOURCE_FAMILIES,
    LEVEL1_REFERENCE_SOURCE_FAMILIES,
    LEVEL2_LIVE_OBSERVATION_SOURCE_FAMILIES,
    execute_m7g_controlled_manual_refresh,
)


def package(families=None):
    return {
        "schema_version": "m7g_controlled_refresh_request_package.v1",
        "package_type": "controlled_manual_refresh_request",
        "package_status": "prepared_not_executed",
        "active_context_mode": "loaded_safe_artifact",
        "requested_symbols": ["2330"],
        "requested_markets": ["TWSE"],
        "requested_source_families": families or ["TWSE_MIS"],
        "refresh_scope": "bounded_watchlist",
        "bounded_watchlist_only": True,
        "execution_eligible_for_m7g09": True,
        "execution_authorized": False,
        "execution_performed": False,
        "requires_m7g09_execution_gate": True,
        "raw_payload_requested": False,
        "raw_forbidden_values_requested": False,
        "ai_model_call_requested": False,
        "trading_advice_requested": False,
        "operator_confirmation": {"required": True, "confirmation_phrase_required": "PREPARE_REFRESH_REQUEST_ONLY", "confirmed": True, "confirmation_phrase_matched": True},
    }


def fake_runner(_watchlist):
    return {"schema_version":"m5k_live_observation.v1","generated_at_utc":"2026-07-10T08:00:00Z","observations":[{"symbol":"2330","display_name":"台積電","market":"TWSE","source":"TWSE_MIS","retrieved_at_utc":"2026-07-10T08:00:00Z","price_like_value":1000,"change_percent":1.2,"volume_candidate":123456,"best_bid_candidate":999,"best_ask_candidate":1000,"semantic_caveats":["safe fixture"]}],"failures":[]}


def test_docs_exist_with_required_policy_terms():
    for path, status in {
        Path('docs/protocol/M7G_CONTROLLED_MANUAL_REFRESH_EXECUTION_GATE.md'): 'controlled_manual_refresh_execution_gate_defined',
        Path('docs/protocol/M7G_REFRESHED_SAFE_ARTIFACT_RESULT_CONTRACT.md'): 'refreshed_safe_artifact_result_contract_defined',
    }.items():
        text = path.read_text(encoding='utf-8')
        for term in [status, 'Mode A/B/C unchanged', 'Level 1/2 unchanged', 'Level 2 temporary safe artifact', 'does not mutate M5F', 'does not create Mode D or Level 3', 'EXECUTE_CONTROLLED_REFRESH_ONCE', 'TWSE_MIS execution supported', 'TPEX_OPENAPI', 'TAIFEX_MIS', 'declared but not executable', 'No auto refresh', 'No scheduler', 'No polling', 'No hidden fetch', 'No raw payload exposure', 'No AI/model call', 'No trading advice']:
            assert term in text


def test_source_family_taxonomy_contains_tpex_openapi_and_taifex_mis():
    assert DECLARED_SOURCE_FAMILIES == {"TWSE_MIS", "TAIFEX_MIS", "TWSE_OPENAPI", "TPEX_OPENAPI", "TAIFEX_OPENAPI"}
    assert LEVEL1_REFERENCE_SOURCE_FAMILIES == {"TWSE_OPENAPI", "TPEX_OPENAPI", "TAIFEX_OPENAPI"}
    assert LEVEL2_LIVE_OBSERVATION_SOURCE_FAMILIES == {"TWSE_MIS", "TAIFEX_MIS"}
    assert EXECUTION_SUPPORTED_SOURCE_FAMILIES == {"TWSE_MIS"}
    assert DECLARED_BUT_NOT_YET_EXECUTABLE_SOURCE_FAMILIES == {"TAIFEX_MIS", "TWSE_OPENAPI", "TPEX_OPENAPI", "TAIFEX_OPENAPI"}


def test_endpoint_exists_and_requires_post():
    routes = [r for r in app.routes if getattr(r, 'path', None) == '/api/m7g/controlled-refresh/execute']
    assert routes
    assert 'POST' in routes[0].methods


def test_missing_execution_confirmation_rejected_without_network():
    result = execute_m7g_controlled_manual_refresh(request_package=package(), operator_execution_confirmation_phrase='', observation_runner=fake_runner)
    assert result['execution_status'] == 'rejected_missing_execution_confirmation'
    assert result['execution_authorized'] is False
    assert result['execution_performed'] is False
    assert result['network_fetch_performed'] is False
    assert result['safe_artifact_returned'] is False


def test_invalid_request_package_rejected_before_network():
    p = package()
    p.update(schema_version='wrong', execution_eligible_for_m7g09=False, execution_authorized=True, raw_payload_requested=True, ai_model_call_requested=True, trading_advice_requested=True)
    result = execute_m7g_controlled_manual_refresh(request_package=p, operator_execution_confirmation_phrase=EXECUTION_CONFIRMATION_PHRASE, observation_runner=fake_runner)
    assert result['execution_status'] == 'rejected_invalid_request_package'
    assert result['network_fetch_performed'] is False
    assert result['safe_artifact_returned'] is False


def test_unsupported_source_family_fail_closed():
    for families in [
        ['TWSE_OPENAPI'],
        ['TPEX_OPENAPI'],
        ['TAIFEX_OPENAPI'],
        ['TAIFEX_MIS'],
        ['TWSE_OPENAPI','TAIFEX_OPENAPI','UNSUPPORTED'],
    ]:
        result = execute_m7g_controlled_manual_refresh(request_package=package(families), operator_execution_confirmation_phrase=EXECUTION_CONFIRMATION_PHRASE, observation_runner=fake_runner)
        assert result['execution_status'] == 'rejected_unsupported_source_family'
        assert result['execution_authorized'] is False
        assert result['execution_performed'] is False
        assert result['network_fetch_performed'] is False
        assert result['safe_artifact_returned'] is False


def test_mixed_supported_and_unsupported_source_families_fail_closed_before_network():
    for families in [
        ['TWSE_MIS', 'TPEX_OPENAPI'],
        ['TWSE_MIS', 'TAIFEX_MIS'],
        ['TWSE_MIS', 'TAIFEX_OPENAPI'],
        ['TWSE_MIS', 'UNSUPPORTED'],
    ]:
        result = execute_m7g_controlled_manual_refresh(request_package=package(families), operator_execution_confirmation_phrase=EXECUTION_CONFIRMATION_PHRASE, observation_runner=fake_runner)
        assert result['execution_status'] == 'rejected_unsupported_source_family'
        assert result['execution_authorized'] is False
        assert result['execution_performed'] is False
        assert result['network_fetch_performed'] is False
        assert result['safe_artifact_returned'] is False


def test_successful_fake_execution_returns_valid_safe_artifact():
    result = execute_m7g_controlled_manual_refresh(request_package=package(), operator_execution_confirmation_phrase=EXECUTION_CONFIRMATION_PHRASE, observation_runner=fake_runner)
    assert result['execution_status'] == 'executed_safe_artifact_ready'
    assert result['execution_authorized'] is True
    assert result['execution_performed'] is True
    assert result['network_fetch_performed'] is True
    assert result['network_fetch_scope'] == 'explicit_operator_controlled_refresh_only'
    assert result['safe_artifact_returned'] is True
    assert result['safe_artifact_validation_status'] == 'accepted'
    artifact = result['safe_context_artifact']
    assert artifact['schema_version'] == 'm7g_safe_context_artifact.v1'
    assert artifact['safe_for_frontend'] is True
    assert artifact['safe_for_ai_handoff'] is True
    for key in ['raw_payload_exposed','raw_forbidden_values_returned','trading_advice_generated','ai_model_call_performed']:
        assert result[key] is False
    for key in ['mode_abc_unchanged','level_1_2_unchanged','level2_output_only']:
        assert result[key] is True
    assert result['m5f_mutated'] is False
    assert result['level1_mutated'] is False


def test_api_endpoint_uses_executor_gate_with_fake_free_rejection():
    client = TestClient(app)
    response = client.post('/api/m7g/controlled-refresh/execute', json={'request_package': package(), 'operator_execution_confirmation_phrase': ''})
    assert response.status_code == 200
    assert response.json()['execution_status'] == 'rejected_missing_execution_confirmation'
