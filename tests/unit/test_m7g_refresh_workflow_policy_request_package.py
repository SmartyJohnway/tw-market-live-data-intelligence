import json
from pathlib import Path

FRONTEND = Path('frontend/public/index.html')
POLICY = Path('docs/protocol/M7G_OPERATOR_REFRESH_WORKFLOW_POLICY_AND_PREFLIGHT.md')
PACKAGE = Path('docs/protocol/M7G_CONTROLLED_REFRESH_REQUEST_PACKAGE.md')
INV = Path('docs/data_capabilities/twse_mis_rich_field_inventory.json')
PROFILE = Path('config/test_execution_profiles.json')
SCRIPT = Path('scripts/m7g_refresh_request_package.py')


def test_docs_exist_and_define_required_statuses_and_gates():
    policy = POLICY.read_text(encoding='utf-8')
    package = PACKAGE.read_text(encoding='utf-8')
    for token in ['operator_refresh_workflow_policy_preflight_defined', 'PREPARE_REFRESH_REQUEST_ONLY', 'M7G-09 controlled manual refresh execution remains mandatory', 'M7G-09 is the earliest task allowed to execute refresh', 'M7G-07/08 does not execute refresh']:
        assert token in policy
    for token in ['controlled_refresh_request_package_defined', 'm7g_controlled_refresh_request_package.v1', 'PREPARE_REFRESH_REQUEST_ONLY', 'M7G-09 controlled manual refresh execution remains mandatory', 'M7G-09 is the earliest task allowed to execute refresh', 'M7G-07/08 does not execute refresh']:
        assert token in package


def refresh_slice():
    text = FRONTEND.read_text(encoding='utf-8')
    return text[text.index('<section id="m7g-refresh-workflow"'):text.index('<h2>Local API Tools</h2>')]


def refresh_js_slice():
    text = FRONTEND.read_text(encoding='utf-8')
    return text[text.index('function getM7GRefreshPreflightContext'):text.index('function renderM7FRichFactBrowser')]


def test_frontend_refresh_workflow_ui_exists():
    text = FRONTEND.read_text(encoding='utf-8')
    for token in ['Operator Refresh Workflow Preflight','Controlled Refresh Request Package','Refresh workflow policy notice','Active context mode','Refresh request eligibility','Requested symbols','Requested source families','Operator confirmation phrase','Build refresh request package','Reset refresh request package','Safe refresh request JSON preview','Safe refresh request Markdown preview','Copy Safe Refresh Request JSON','Copy Safe Refresh Request Markdown','Controlled execution requires EXECUTE_CONTROLLED_REFRESH_ONCE','M7G-09 executes once only after explicit operator click','PREPARE_REFRESH_REQUEST_ONLY']:
        assert token in text


def test_no_execution_controls_in_refresh_section():
    section = refresh_slice()
    for token in ['Execute refresh', 'Run refresh', 'Fetch now', 'Call refresh API', 'Start refresh']:
        assert token not in section


def test_frontend_package_helpers_and_shape_fields_exist():
    js = refresh_js_slice()
    for token in ['getM7GRefreshPreflightContext','buildM7GControlledRefreshRequestPackage','validateM7GControlledRefreshRequestPackage','renderM7GRefreshWorkflowPanel','renderM7GRefreshRequestMarkdown','schema_version','m7g_controlled_refresh_request_package.v1','package_type','controlled_manual_refresh_request','package_status','prepared_not_executed','active_context_mode','source_artifact_id','source_artifact_schema_version','source_validation_status','source_observation_count','requested_symbols','requested_markets','requested_source_families','refresh_scope','bounded_watchlist_only','execution_eligible_for_m7g09','execution_authorized','execution_performed','requires_m7g09_execution_gate','network_intent','declared_for_future_m7g09_only','raw_payload_requested','raw_forbidden_values_requested','ai_model_call_requested','trading_advice_requested','operator_confirmation','governance_guardrails']:
        assert token in js


def test_frontend_no_uncontrolled_timer_or_ai_in_refresh_js_slice_and_script():
    combined = (refresh_js_slice() + SCRIPT.read_text(encoding='utf-8')).lower()
    for token in ['xmlhttprequest', 'websocket', 'eventsource', 'setinterval', 'settimeout', 'navigator.sendbeacon', 'localhost', '127.0.0.1', 'openai', 'chatgpt', 'requests', 'httpx', 'sqlite', 'psycopg', 'sqlalchemy', 'subprocess', 'socket']:
        assert token not in combined
    assert '/api/m7g/controlled-refresh/execute' in combined


def test_handoff_direct_call_hardening_tokens_exist():
    text = FRONTEND.read_text(encoding='utf-8')
    for token in ['normalizeM7GHandoffProjectionContext','context === m7gActiveSafeArtifact','validationResult === m7gActiveValidationResult', "validation_status === 'accepted'", 'safe_to_render === true', 'return active', 'getM7GActiveHandoffContext']:
        assert token in text


def test_inventory_status_and_default_ci_inclusion():
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
    for key in ['operator_refresh_workflow_policy_added','refresh_preflight_ui_added','controlled_refresh_request_package_added','safe_refresh_request_json_preview_added','safe_refresh_request_markdown_preview_added','explicit_refresh_request_copy_buttons_added','operator_confirmation_phrase_required','requested_symbols_bounded_to_active_context','requested_source_families_fixed_allowlist','handoff_direct_call_hardening_added','arbitrary_validation_result_cannot_bypass_active_context_gate','m7g09_controlled_manual_refresh_execution_required']:
        assert entry[key] is True
    for key in ['refresh_execution_added','manual_refresh_execution_added','runtime_network_fetch_added','backend_api_changed']:
        assert entry[key] is True
    for key in ['hidden_fetch_added','ai_model_call_added','db_write_added','raw_payload_requested','raw_forbidden_values_requested','trading_advice_requested']:
        assert entry[key] is False
    assert entry['next_task'] in {
        'M7G-10-LOADED-ARTIFACT-AND-REFRESH-WORKFLOW-SECURITY-REGRESSION',
        'M7G-11-LOCAL-SAFE-CONTEXT-ARTIFACT-LOAD-FINAL-ACCEPTANCE',
        'M7H-SOURCE-FAMILY-ROUTE-GOVERNANCE-AND-CONTROLLED-EXPANSION'
    }
    paths = json.loads(PROFILE.read_text(encoding='utf-8'))['profiles']['default-ci']['pytest_paths']
    assert 'tests/unit/test_m7g_refresh_workflow_policy_request_package.py' in paths
    assert 'tests/unit/test_m7g_refresh_request_package_builder.py' in paths
