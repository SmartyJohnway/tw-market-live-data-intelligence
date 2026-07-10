import json
from pathlib import Path

HTML = Path('frontend/public/index.html').read_text(encoding='utf-8')


def test_provenance_source_health_doc_exists_and_defines_boundaries():
    text = Path('docs/protocol/M7G_ARTIFACT_PROVENANCE_CURRENTNESS_SOURCE_HEALTH_PANEL.md').read_text(encoding='utf-8')
    for expected in ['artifact_provenance_currentness_source_health_panel_defined','Artifact provenance panel','Currentness panel','Source health panel','artifact-reported source health metadata only','not a live probe','does not imply realtime SLA','missing source_health metadata','M7G-09 controlled manual refresh execution remains mandatory downstream work','M7G-04/05 does not execute refresh']:
        assert expected in text


def test_frontend_provenance_currentness_source_health_ui_terms():
    for expected in ['Loaded artifact state','Artifact provenance','Artifact currentness','Source health','Observation summary','artifact_id','schema_version','artifact_type','created_at_utc','generated_by','source_scope','market','timezone','validation_status','observation_count','session_state','freshness_state','currentness_label','calendar_confidence','trading_day_status','source_health','artifact_reported','local_safe_artifact']:
        assert expected in HTML


def test_source_health_missing_metadata_fallback_text():
    assert 'source_health' in HTML
    assert 'unknown' in HTML
    assert 'missing optional source_health metadata in safe artifact' in HTML


def test_inventory_m7g_04_05_status():
    entry = json.loads(Path('docs/data_capabilities/twse_mis_rich_field_inventory.json').read_text(encoding='utf-8'))['rich_observation_contract']['m7g_local_safe_context_artifact_load']
    expected_true = ['active_context_mode_added','static_demo_mode_supported','loaded_safe_artifact_mode_supported','loaded_artifact_state_panel_added','artifact_provenance_panel_added','artifact_currentness_panel_added','source_health_panel_added','observation_summary_panel_added','source_health_is_artifact_reported_only','source_health_missing_metadata_allowed','validated_artifact_renders_rich_fact_browser','reset_to_static_demo_supported','operator_selected_artifact_only','m7g09_controlled_manual_refresh_execution_required']
    assert entry['status'] in {'real_safe_artifact_rendering_and_provenance_source_health_defined', 'ai_handoff_from_loaded_safe_artifact_defined', 'refresh_workflow_policy_and_request_package_defined', 'controlled_manual_refresh_execution_gate_defined', 'loaded_artifact_and_refresh_workflow_security_regression_defined'}
    assert entry['completed_tasks'] in (['M7G-00','M7G-01','M7G-02','M7G-03','M7G-04','M7G-05'], ['M7G-00','M7G-01','M7G-02','M7G-03','M7G-04','M7G-05','M7G-06'], ['M7G-00','M7G-01','M7G-02','M7G-03','M7G-04','M7G-05','M7G-06','M7G-07','M7G-08'], ['M7G-00','M7G-01','M7G-02','M7G-03','M7G-04','M7G-05','M7G-06','M7G-07','M7G-08','M7G-09'], ['M7G-00','M7G-01','M7G-02','M7G-03','M7G-04','M7G-05','M7G-06','M7G-07','M7G-08','M7G-09','M7G-10'])
    assert entry['source_health_schema_version'] == 'm7g_source_health.v1'
    for key in expected_true:
        assert entry[key] is True
    for key in ['source_health_live_probe_added','rejected_artifact_reaches_renderer','hidden_fetch_added']:
        assert entry[key] is False
    assert entry['next_task'] in {'M7G-06-AI-HANDOFF-FROM-LOADED-SAFE-ARTIFACT', 'M7G-07-08-OPERATOR-REFRESH-WORKFLOW-POLICY-AND-CONTROLLED-REFRESH-REQUEST-PACKAGE', 'M7G-09-CONTROLLED-MANUAL-REFRESH-EXECUTION-INTEGRATION-GATE', 'M7G-10-LOADED-ARTIFACT-AND-REFRESH-WORKFLOW-SECURITY-REGRESSION', 'M7G-11-LOCAL-SAFE-CONTEXT-ARTIFACT-LOAD-FINAL-ACCEPTANCE'}
