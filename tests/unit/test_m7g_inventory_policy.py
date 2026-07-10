import json
from pathlib import Path


def test_m7g_inventory_status_and_boundaries():
    entry = json.loads(Path('docs/data_capabilities/twse_mis_rich_field_inventory.json').read_text(encoding='utf-8'))['rich_observation_contract']['m7g_local_safe_context_artifact_load']
    assert entry['status'] == 'manual_safe_artifact_load_policy_schema_validator_ui_defined'
    assert entry['completed_tasks'] == ['M7G-00','M7G-01','M7G-02','M7G-03']
    assert entry['operator_selected_artifact_only'] is True
    assert entry['validate_before_load_required'] is True
    assert entry['safe_artifact_validator_added'] is True
    assert entry['raw_forbidden_rejection_gate_added'] is True
    assert entry['rejected_artifact_reaches_renderer'] is False
    assert entry['real_artifact_loading_added'] is True
    assert entry['real_artifact_loading_scope'] == 'operator_selected_local_safe_artifact_only'
    for key in ['runtime_behavior_changed','fastapi_changed','mcp_changed','backend_api_changed','live_probe_added','runtime_network_fetch_added','hidden_fetch_added','auto_refresh_added','manual_refresh_added','refresh_execution_added','ai_model_call_added','db_write_added','raw_payload_exposure_allowed','trading_advice_allowed']:
        assert entry[key] is False
    assert entry['m7g09_controlled_manual_refresh_execution_required'] is True
    assert entry['next_task'] == 'M7G-04-05-RICH-FACT-BROWSER-REAL-SAFE-ARTIFACT-RENDERING-AND-PROVENANCE-CURRENTNESS-SOURCE-HEALTH-PANEL'


def test_default_ci_includes_m7g_tests():
    paths = json.loads(Path('config/test_execution_profiles.json').read_text(encoding='utf-8'))['profiles']['default-ci']['pytest_paths']
    for test_path in ['tests/unit/test_m7g_safe_context_artifact_schema.py','tests/unit/test_m7g_safe_artifact_validator.py','tests/unit/test_m7g_frontend_manual_artifact_load_ui.py','tests/unit/test_m7g_inventory_policy.py']:
        assert test_path in paths
