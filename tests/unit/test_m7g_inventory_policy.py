import json
from pathlib import Path


def test_m7g_inventory_status_and_boundaries():
    entry = json.loads(Path('docs/data_capabilities/twse_mis_rich_field_inventory.json').read_text(encoding='utf-8'))['rich_observation_contract']['m7g_local_safe_context_artifact_load']
    assert entry['status'] == 'ai_handoff_from_loaded_safe_artifact_defined'
    assert entry['completed_tasks'] == ['M7G-00','M7G-01','M7G-02','M7G-03','M7G-04','M7G-05','M7G-06']
    for key in ['active_context_mode_added','static_demo_mode_supported','loaded_safe_artifact_mode_supported','loaded_artifact_state_panel_added','artifact_provenance_panel_added','artifact_currentness_panel_added','source_health_panel_added','observation_summary_panel_added','source_health_is_artifact_reported_only','source_health_missing_metadata_allowed','validated_artifact_renders_rich_fact_browser','reset_to_static_demo_supported','operator_selected_artifact_only','m7g09_controlled_manual_refresh_execution_required','active_context_handoff_added','handoff_source_panel_added','static_demo_handoff_mode_supported','loaded_safe_artifact_handoff_mode_supported','handoff_source_context_mode_explicit','handoff_built_from_active_context','loaded_artifact_handoff_requires_accepted_validation','artifact_provenance_in_handoff','validation_status_in_handoff','currentness_calendar_in_handoff','source_health_summary_in_handoff','json_handoff_uses_safe_projection_only','markdown_handoff_uses_safe_projection_only']:
        assert entry[key] is True
    assert entry['source_health_schema_version'] == 'm7g_source_health.v1'
    for key in ['runtime_behavior_changed','fastapi_changed','mcp_changed','backend_api_changed','live_probe_added','runtime_network_fetch_added','hidden_fetch_added','auto_refresh_added','manual_refresh_added','refresh_execution_added','ai_model_call_added','db_write_added','raw_payload_exposure_allowed','raw_forbidden_values_rendered','raw_forbidden_values_copied','trading_advice_allowed','source_health_live_probe_added','rejected_artifact_reaches_renderer','rejected_artifact_reaches_handoff','raw_forbidden_fields_copied_to_handoff','raw_payload_values_copied_to_handoff','automatic_clipboard_write_added']:
        assert entry[key] is False
    assert entry['next_task'] == 'M7G-07-08-OPERATOR-REFRESH-WORKFLOW-POLICY-AND-CONTROLLED-REFRESH-REQUEST-PACKAGE'

def test_default_ci_includes_m7g_tests():
    paths = json.loads(Path('config/test_execution_profiles.json').read_text(encoding='utf-8'))['profiles']['default-ci']['pytest_paths']
    for test_path in ['tests/unit/test_m7g_safe_context_artifact_schema.py','tests/unit/test_m7g_safe_artifact_validator.py','tests/unit/test_m7g_frontend_manual_artifact_load_ui.py','tests/unit/test_m7g_inventory_policy.py','tests/unit/test_m7g_real_safe_artifact_rendering.py','tests/unit/test_m7g_provenance_currentness_source_health_panel.py','tests/unit/test_m7g_ai_handoff_from_loaded_safe_artifact.py']:
        assert test_path in paths
