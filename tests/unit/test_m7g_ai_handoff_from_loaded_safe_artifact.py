import json
from pathlib import Path

FRONTEND = Path('frontend/public/index.html')
DOC = Path('docs/protocol/M7G_AI_HANDOFF_FROM_LOADED_SAFE_ARTIFACT.md')
INV = Path('docs/data_capabilities/twse_mis_rich_field_inventory.json')
PROFILE = Path('config/test_execution_profiles.json')


def html():
    return FRONTEND.read_text(encoding='utf-8')


def handoff_js():
    text = html()
    return text[text.index('function getM7GActiveHandoffContext'):text.index('function renderM7FGovernance')]


def test_handoff_doc_exists_and_records_policy():
    assert DOC.exists()
    text = DOC.read_text(encoding='utf-8')
    for token in [
        'ai_handoff_from_loaded_safe_artifact_defined',
        'active workbench context',
        'loaded_safe_artifact',
        'static_demo',
        'validated loaded safe artifact',
        'Handoff source context mode is explicit',
        'artifact provenance',
        'validation status',
        'currentness/calendar metadata',
        'source health summary',
        'No AI/model call',
        'No backend/API/MCP',
        'No runtime network fetch',
        'No hidden fetch',
        'No refresh execution',
        'Raw forbidden fields are not copied',
        'Not trading advice',
        'M7G-09 controlled manual refresh execution remains mandatory downstream work',
    ]:
        assert token in text


def test_frontend_contains_handoff_source_ui():
    text = html()
    for token in [
        'AI Handoff Source',
        'Handoff source context',
        'Handoff built from active context',
        'static_demo',
        'loaded_safe_artifact',
        'Static demo handoff active',
        'Loaded safe artifact handoff active',
        'Operator-selected local safe artifact',
    ]:
        assert token in text


def test_active_handoff_context_helper_and_loaded_gate():
    js = handoff_js()
    for token in [
        'getM7GActiveHandoffContext',
        'normalizeM7GHandoffProjectionContext',
        'buildM7GHandoffSourceSummary',
        'handoff_source_context_mode',
        'handoff_built_from_active_context',
        'm7gActiveContextMode === M7G_CONTEXT_MODE_LOADED_SAFE_ARTIFACT',
        'm7gActiveSafeArtifact',
        "m7gActiveValidationResult.validation_status === 'accepted'",
        'm7gActiveValidationResult.safe_to_render === true',
        'M7F_DEMO_RICH_CONTEXT',
    ]:
        assert token in js


def test_handoff_projection_includes_safe_metadata():
    js = handoff_js()
    for token in [
        'handoff_source',
        'artifact_provenance',
        'currentness_calendar',
        'source_health',
        'governance_guardrails',
        'selected_fields',
        'selected_symbols',
        'raw_forbidden_omission_notice',
        'source_health_status',
        'source_health_schema_version',
        'source_health_warnings',
    ]:
        assert token in js


def test_markdown_handoff_source_section_exists():
    js = handoff_js()
    for token in [
        '## Handoff Source',
        'Context mode',
        'Handoff built from active context',
        'Artifact ID',
        'Validation status',
        'Observation count',
        'Currentness label',
        'Calendar confidence',
        'Source health status',
        'artifact-reported metadata only',
        'not a live probe',
        'no realtime SLA',
    ]:
        assert token in js


def test_json_handoff_uses_safe_projection_only_and_field_gate_preserved():
    js = handoff_js()
    assert 'JSON.stringify(projection' in js
    for token in ['JSON.stringify(context', 'JSON.stringify(m7gActiveSafeArtifact', 'JSON.stringify(M7F_DEMO_RICH_CONTEXT']:
        assert token not in js
    for token in ['display_allowed === true', 'ai_handoff_allowed === true', 'raw_forbidden === false']:
        assert token in js


def test_no_network_backend_refresh_ai_or_positive_trading_terms_in_handoff_slice():
    js = handoff_js().lower()
    for token in ['fetch(', 'xmlhttprequest', 'websocket', 'eventsource', 'setinterval', 'settimeout', 'navigator.sendbeacon', '/api/', 'mcp', 'localhost', '127.0.0.1', 'openai', 'chatgpt', 'model']:
        assert token not in js
    for token in ['buy', 'sell', 'hold', 'target price', 'support', 'resistance', 'capital flow', 'sector rotation', 'top movers', 'strongest', 'weakest', 'ranking', 'bullish', 'bearish', 'entry', 'exit', 'stop loss', 'take profit']:
        assert token not in js


def test_inventory_status_and_default_ci():
    entry = json.loads(INV.read_text(encoding='utf-8'))['rich_observation_contract']['m7g_local_safe_context_artifact_load']
    assert entry['status'] in {
        'controlled_manual_refresh_execution_gate_defined',
        'loaded_artifact_and_refresh_workflow_security_regression_defined',
        'final_acceptance_pass_with_caveats'
    }
    assert entry['completed_tasks'] in (
        ['M7G-00','M7G-01','M7G-02','M7G-03','M7G-04','M7G-05','M7G-06','M7G-07','M7G-08','M7G-09'],
        ['M7G-00','M7G-01','M7G-02','M7G-03','M7G-04','M7G-05','M7G-06','M7G-07','M7G-08','M7G-09','M7G-10'],
        ['M7G-00','M7G-01','M7G-02','M7G-03','M7G-04','M7G-05','M7G-06','M7G-07','M7G-08','M7G-09','M7G-10','M7G-11']
    )
    for key in ['active_context_handoff_added','handoff_source_panel_added','static_demo_handoff_mode_supported','loaded_safe_artifact_handoff_mode_supported','handoff_source_context_mode_explicit','handoff_built_from_active_context','loaded_artifact_handoff_requires_accepted_validation','artifact_provenance_in_handoff','validation_status_in_handoff','currentness_calendar_in_handoff','source_health_summary_in_handoff','json_handoff_uses_safe_projection_only','markdown_handoff_uses_safe_projection_only','m7g09_controlled_manual_refresh_execution_required']:
        assert entry[key] is True
    for key in ['rejected_artifact_reaches_handoff','raw_forbidden_fields_copied_to_handoff','raw_payload_values_copied_to_handoff','automatic_clipboard_write_added','rejected_artifact_reaches_handoff','raw_forbidden_fields_copied_to_handoff','raw_payload_values_copied_to_handoff','automatic_clipboard_write_added','hidden_fetch_added','ai_model_call_added']:
        assert entry[key] is False
    assert entry['next_task'] in {
        'M7G-10-LOADED-ARTIFACT-AND-REFRESH-WORKFLOW-SECURITY-REGRESSION',
        'M7G-11-LOCAL-SAFE-CONTEXT-ARTIFACT-LOAD-FINAL-ACCEPTANCE',
        'M7H-SOURCE-FAMILY-ROUTE-GOVERNANCE-AND-CONTROLLED-EXPANSION'
    }
    assert entry['refresh_execution_added'] is True
    assert entry['runtime_network_fetch_added'] is True
    assert entry['backend_api_changed'] is True
    paths = json.loads(PROFILE.read_text(encoding='utf-8'))['profiles']['default-ci']['pytest_paths']
    assert 'tests/unit/test_m7g_ai_handoff_from_loaded_safe_artifact.py' in paths
