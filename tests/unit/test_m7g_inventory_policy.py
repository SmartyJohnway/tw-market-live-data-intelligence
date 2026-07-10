import json
from pathlib import Path


def test_m7g_inventory_status_and_boundaries():
    entry = json.loads(Path('docs/data_capabilities/twse_mis_rich_field_inventory.json').read_text(encoding='utf-8'))['rich_observation_contract']['m7g_local_safe_context_artifact_load']
    assert entry['status'] == 'loaded_artifact_and_refresh_workflow_security_regression_defined'
    assert entry['completed_tasks'] == ['M7G-00','M7G-01','M7G-02','M7G-03','M7G-04','M7G-05','M7G-06','M7G-07','M7G-08','M7G-09','M7G-10']
    for key in ['controlled_manual_refresh_execution_added','controlled_refresh_backend_endpoint_added','controlled_refresh_executor_added','refresh_execution_confirmation_phrase_required','prepare_phrase_distinct_from_execution_phrase','unsupported_source_families_fail_closed','safe_artifact_validation_required_before_render','execution_report_added','refreshed_safe_artifact_returned','refreshed_safe_artifact_load_ui_added','refreshed_artifact_updates_active_context','refreshed_artifact_updates_ai_handoff','mode_abc_unchanged','level_1_2_unchanged','level2_output_only','runtime_behavior_changed','backend_api_changed','runtime_network_fetch_added','live_probe_added','manual_refresh_execution_added','refresh_execution_added','refresh_workflow_security_regression_added','runner_exception_fail_closed_added','runner_exception_returns_safe_structured_result','raw_forbidden_injection_regression_added','frontend_auto_load_regression_added','frontend_auto_execution_regression_added','frontend_rejected_result_render_regression_added','frontend_rejected_artifact_handoff_regression_added','twse_mis_market_route_semantics_added']:
        assert entry[key] is True
    assert entry['refresh_workflow_security_regression_doc'] == 'docs/protocol/M7G_REFRESH_WORKFLOW_SECURITY_REGRESSION.md'
    assert entry['twse_mis_market_route_semantics_doc'] == 'docs/protocol/M7G_TWSE_MIS_MARKET_ROUTE_SEMANTICS.md'
    assert entry['controlled_refresh_endpoint_path'] == '/api/m7g/controlled-refresh/execute'
    assert entry['refresh_execution_confirmation_phrase'] == 'EXECUTE_CONTROLLED_REFRESH_ONCE'
    assert entry['execution_supported_source_families'] == ['TWSE_MIS']
    assert entry['declared_source_families'] == ['TWSE_MIS','TAIFEX_MIS','TWSE_OPENAPI','TPEX_OPENAPI','TAIFEX_OPENAPI']
    assert entry['level1_reference_source_families'] == ['TWSE_OPENAPI','TPEX_OPENAPI','TAIFEX_OPENAPI']
    assert entry['level2_live_observation_source_families'] == ['TWSE_MIS','TAIFEX_MIS']
    assert entry['declared_but_not_yet_executable_source_families'] == ['TAIFEX_MIS','TWSE_OPENAPI','TPEX_OPENAPI','TAIFEX_OPENAPI']
    assert entry['twse_mis_twse_listed_route'] == 'tse_{symbol}.tw'
    assert entry['twse_mis_tpex_otc_listed_route'] == 'otc_{symbol}.tw'
    assert entry['tpex_live_quote_source_family'] == 'TWSE_MIS'
    assert entry['tpex_openapi_level1_reference_only'] is True
    assert entry['taifex_mis_level2_live_family'] is True
    assert entry['mixed_supported_and_unsupported_source_families_fail_closed'] is True
    assert entry['partial_source_family_execution_allowed'] is False
    assert entry['runtime_network_fetch_scope'] == 'explicit_operator_controlled_refresh_only'
    for key in ['runner_exception_returns_http_500','raw_forbidden_injection_reaches_execution_result','raw_forbidden_injection_reaches_safe_artifact','tpex_live_quote_separate_source_family_added','tpex_mis_declared','tpex_mis_executable','tpex_openapi_level2_live_family','taifex_mis_executable_in_m7g10','emerging_stock_live_route_supported','rotc_route_declared','rotc_candidate_added','new_source_execution_support_added','rejected_execution_result_reaches_renderer','rejected_safe_artifact_reaches_renderer','mode_d_added','level_3_added','m5f_mutated','level1_mutated','hidden_fetch_added','auto_refresh_added','scheduler_added','polling_added','startup_fetch_added','ai_model_call_added','db_write_added','raw_payload_exposure_allowed','raw_forbidden_values_rendered','raw_forbidden_values_copied','raw_payload_returned_in_execution_result','raw_payload_returned_in_safe_artifact','trading_advice_allowed','trading_signal_allowed','recommendation_allowed']:
        assert entry[key] is False
    assert entry['next_task'] == 'M7G-11-LOCAL-SAFE-CONTEXT-ARTIFACT-LOAD-FINAL-ACCEPTANCE'


def test_default_ci_includes_m7g_tests():
    paths = json.loads(Path('config/test_execution_profiles.json').read_text(encoding='utf-8'))['profiles']['default-ci']['pytest_paths']
    for test_path in ['tests/unit/test_m7g_safe_context_artifact_schema.py','tests/unit/test_m7g_safe_artifact_validator.py','tests/unit/test_m7g_frontend_manual_artifact_load_ui.py','tests/unit/test_m7g_inventory_policy.py','tests/unit/test_m7g_real_safe_artifact_rendering.py','tests/unit/test_m7g_provenance_currentness_source_health_panel.py','tests/unit/test_m7g_ai_handoff_from_loaded_safe_artifact.py','tests/unit/test_m7g_refresh_workflow_policy_request_package.py','tests/unit/test_m7g_refresh_request_package_builder.py','tests/unit/test_m7g_controlled_refresh_execution_gate.py','tests/unit/test_m7g_refreshed_safe_artifact_result_contract.py','tests/unit/test_m7g_controlled_refresh_frontend_execution_ui.py','tests/unit/test_m7g_refresh_workflow_security_regression.py','tests/unit/test_m7g_twse_mis_market_route_semantics.py']:
        assert test_path in paths
