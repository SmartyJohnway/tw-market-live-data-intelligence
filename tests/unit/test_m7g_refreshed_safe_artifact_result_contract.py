import json
from pathlib import Path
from scripts.m7g_controlled_refresh_executor import EXECUTION_CONFIRMATION_PHRASE, execute_m7g_controlled_manual_refresh
from tests.unit.test_m7g_controlled_refresh_execution_gate import package, fake_runner

FORBIDDEN = ['raw_payload','twse_mis_rich_facts','raw_rich_facts','raw_unknown_facts','full_ladder','bid_prices','ask_prices','source_investigation_notes','response_sample','raw_fields_sample']

def walk_keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)

def test_result_contract_states_and_safe_artifact_no_forbidden_keys():
    text = Path('docs/protocol/M7G_REFRESHED_SAFE_ARTIFACT_RESULT_CONTRACT.md').read_text(encoding='utf-8')
    for state in ['executed_safe_artifact_ready','rejected_invalid_request_package','rejected_missing_execution_confirmation','rejected_unsupported_source_family','execution_failed_no_safe_artifact','execution_failed_safe_artifact_rejected']:
        assert state in text
    result = execute_m7g_controlled_manual_refresh(request_package=package(), operator_execution_confirmation_phrase=EXECUTION_CONFIRMATION_PHRASE, observation_runner=fake_runner)
    keys = set(walk_keys(result))
    assert not (keys & set(FORBIDDEN))
    assert result['safe_context_artifact']['source_scope'] == 'bounded_watchlist'
    assert result['safe_context_artifact']['source_health']['schema_version'] == 'm7g_source_health.v1'


def test_mode_level_regression_flags_in_result():
    result = execute_m7g_controlled_manual_refresh(request_package=package(), operator_execution_confirmation_phrase=EXECUTION_CONFIRMATION_PHRASE, observation_runner=fake_runner)
    assert result['mode_abc_unchanged'] is True
    assert result['level_1_2_unchanged'] is True
    assert result['level2_output_only'] is True
    assert result['m5f_mutated'] is False
    assert result['level1_mutated'] is False
    assert result['mode_d_added'] is False
    assert result['level_3_added'] is False
