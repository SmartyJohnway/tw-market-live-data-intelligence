import pytest

from scripts.m7g_refresh_request_package import (
    ALLOWED_SOURCE_FAMILIES,
    CONFIRMATION_PHRASE,
    REFRESH_REQUEST_PACKAGE_SCHEMA_VERSION,
    build_m7g_controlled_refresh_request_package,
    validate_m7g_controlled_refresh_request_package,
)


def context():
    return {
        'schema_version': 'm7g_safe_context_artifact.v1',
        'artifact_id': 'safe-context-demo-20260709',
        'market_clock_session_state': {'currentness_label': 'live_candidate', 'calendar_confidence': 'controlled_twse_holiday_schedule_artifact', 'trading_day_status': 'trading_day'},
        'source_health': {'health_status': 'artifact_reported', 'schema_version': 'm7g_source_health.v1'},
        'observations': [{'symbol': '2330', 'market': 'TWSE'}],
    }


def build(**kw):
    args = dict(active_context=context(), active_context_mode='loaded_safe_artifact', validation_result={'validation_status': 'accepted', 'safe_to_render': True}, requested_symbols=['2330'], requested_source_families=['TWSE_MIS'], operator_confirmation_phrase=CONFIRMATION_PHRASE)
    args.update(kw)
    return build_m7g_controlled_refresh_request_package(**args)


def test_loaded_safe_artifact_package_shape_future_eligible_not_executed():
    package = build()
    assert package['schema_version'] == REFRESH_REQUEST_PACKAGE_SCHEMA_VERSION
    assert package['package_type'] == 'controlled_manual_refresh_request'
    assert package['package_status'] == 'prepared_not_executed'
    assert package['active_context_mode'] == 'loaded_safe_artifact'
    assert package['source_validation_status'] == 'accepted'
    assert package['execution_eligible_for_m7g09'] is True
    assert package['execution_authorized'] is False
    assert package['execution_performed'] is False
    assert package['requires_m7g09_execution_gate'] is True
    assert package['raw_payload_requested'] is False
    assert package['raw_forbidden_values_requested'] is False
    assert package['ai_model_call_requested'] is False
    assert package['trading_advice_requested'] is False
    assert validate_m7g_controlled_refresh_request_package(package)['validation_status'] == 'accepted'


def test_static_demo_package_preview_not_execution_eligible():
    package = build(active_context_mode='static_demo', validation_result={'validation_status': 'static_demo', 'safe_to_render': True})
    assert package['active_context_mode'] == 'static_demo'
    assert package['source_artifact_id'] == 'static_demo'
    assert package['execution_eligible_for_m7g09'] is False
    assert package['execution_authorized'] is False
    assert package['execution_performed'] is False


def test_confirmation_phrase_required_for_prepared_status():
    package = build(operator_confirmation_phrase='WRONG')
    assert package['package_status'] == 'preflight_failed'
    assert package['operator_confirmation']['confirmed'] is False
    assert package['operator_confirmation']['confirmation_phrase_matched'] is False


def test_requested_symbols_are_bounded_to_active_context():
    with pytest.raises(ValueError):
        build(requested_symbols=['9999'])


def test_source_family_allowlist():
    assert ALLOWED_SOURCE_FAMILIES == {'TWSE_MIS', 'TWSE_OPENAPI', 'TAIFEX_OPENAPI'}
    with pytest.raises(ValueError):
        build(requested_source_families=['UNSUPPORTED'])


def test_validator_rejects_execution_raw_ai_trading_and_raw_forbidden_keys():
    package = build()
    package['execution_authorized'] = True
    package['raw_payload'] = {'x': 1}
    result = validate_m7g_controlled_refresh_request_package(package)
    assert result['validation_status'] == 'rejected'
    assert 'execution_authorized_must_be_false' in result['errors']
    assert 'raw_forbidden_keys_detected' in result['errors']
