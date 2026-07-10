import json
import re
from pathlib import Path

FRONTEND = Path('frontend/public/index.html')
DOC = Path('docs/protocol/M7F_AI_DISCUSSION_HANDOFF_AND_FILTERING.md')
INV = Path('docs/data_capabilities/twse_mis_rich_field_inventory.json')
PROFILE = Path('config/test_execution_profiles.json')
RAW_KEYS = {
    'raw_payload', 'twse_mis_rich_facts', 'raw_unknown_facts', 'full_ladder',
    'bid_prices', 'ask_prices', 'source_investigation_notes'
}


def html():
    return FRONTEND.read_text(encoding='utf-8')


def m7f_js():
    text = html()
    return text[text.index('const M7F_DISPLAY_CATALOG'):text.index('async function executeM7GControlledRefreshOnce')]


def test_doc_exists_and_records_policy():
    text = DOC.read_text(encoding='utf-8')
    for token in [
        'ai_handoff_selection_search_filters_defined',
        'operator-controlled rich fact selection',
        'search', 'filters', 'field grouping',
        'Safe Markdown handoff preview', 'Safe JSON projection preview',
        'Explicit copy buttons', 'display_allowed=true', 'ai_handoff_allowed=true',
        'raw_forbidden=false', 'No hidden fetch', 'No FastAPI/MCP changes',
        'No AI/model call', 'not trading advice',
        'M7F-07-08-FRONTEND-SECURITY-SEMANTIC-REGRESSION-AND-FINAL-ACCEPTANCE',
    ]:
        assert token in text


def test_frontend_contains_handoff_search_filter_ui():
    text = html()
    for token in [
        'AI Discussion Handoff Preview', 'Copy Safe Markdown', 'Copy Safe JSON',
        'Symbol/name search', 'Field group filter', 'Confidence filter',
        'Exposure filter', 'Currentness filter', 'Show caveated fields',
        'Field grouping', 'selected fields', 'safe markdown', 'safe JSON',
    ]:
        assert token in text


def test_in_page_catalog_has_ai_handoff_allowed_and_rules():
    js = m7f_js()
    assert 'ai_handoff_allowed' in js
    assert re.search(r'raw_payload: \{[^}]*display_allowed: false,[^}]*ai_handoff_allowed: false,[^}]*raw_forbidden: true', js)
    for key in ['symbol', 'price_like_value', 'change_percent', 'volume_candidate', 'currentness_label']:
        assert re.search(rf'{key}: \{{[^}}]*display_allowed: true,[^}}]*ai_handoff_allowed: true,[^}}]*raw_forbidden: false', js)


def test_handoff_gate_is_enforced_by_boolean_checks():
    js = m7f_js()
    gate = js[js.index('function getM7FHandoffAllowedFields'):js.index('function m7fFieldMatchesFilters')]
    assert 'meta.display_allowed === true' in gate
    assert 'meta.ai_handoff_allowed === true' in gate
    assert 'meta.raw_forbidden === false' in gate


def test_raw_forbidden_fields_not_selectable_or_copied():
    js = m7f_js()
    demo = js[js.index('const M7F_DEMO_RICH_CONTEXT'):js.index('const M7F_DEFAULT_HANDOFF_FIELDS')]
    defaults = js[js.index('const M7F_DEFAULT_HANDOFF_FIELDS'):js.index('let m7fFilters')]
    projection = js[js.index('function buildM7FSafeHandoffProjection'):js.index('function renderM7FMarkdownHandoff')]
    for key in RAW_KEYS:
        assert f'{key}:' not in demo
        assert key not in defaults
    assert 'raw_forbidden_omission_notice' in projection
    assert 'JSON.stringify(projection' in js
    assert 'JSON.stringify(context' not in js


def test_copy_buttons_require_explicit_action():
    js = m7f_js()
    assert 'Copy Safe Markdown' in js
    assert 'Copy Safe JSON' in js
    assert "addEventListener('click'" in js
    assert 'navigator.clipboard.writeText' in js
    copy_handler = js[js.index('function copyM7FPreviewText'):js.index('function renderM7FHandoffPanel')]
    assert 'navigator.clipboard.writeText' in copy_handler


def test_m7f_section_adds_no_new_network_or_scheduler_behavior():
    js = m7f_js()
    for token in ['fetch(', 'XMLHttpRequest', 'WebSocket', 'EventSource', 'setInterval', 'setTimeout']:
        assert token not in js


def test_m7f_section_has_no_backend_api_mcp_hooks():
    js = m7f_js()
    for token in ['/api/', 'mcp', 'uvicorn', 'localhost', '127.0.0.1']:
        assert token not in js.lower()


def test_m7f_section_has_no_positive_trading_semantics():
    js = m7f_js()
    forbidden = ['Buy', 'Sell', 'Hold', 'Target price', 'Support', 'Resistance', 'Capital flow', 'Sector rotation', 'Top movers', 'Strongest', 'Weakest', 'Ranking', 'bullish', 'bearish']
    for token in forbidden:
        assert token not in js


def test_m7f_section_uses_safe_dom_rendering():
    js = m7f_js()
    for token in ['innerHTML', 'insertAdjacentHTML', 'document.write', 'eval(', 'new Function']:
        assert token not in js
    assert '.textContent' in js
    assert '.value' in js


def test_field_grouping_uses_official_enums_only():
    js = m7f_js()
    for token in ["group: 'provenance'", "group: 'observed_value'", "group: 'order_context'", "group: 'calendar'", "exposure: 'display'", "confidence: 'forbidden'"]:
        assert token not in js
    for token in ['source', 'price_quote', 'price_change', 'volume_trading', 'rich_observation', 'market_clock_currentness', 'trading_calendar_authority', 'caveats_governance', 'raw_forbidden', 'operator_display_allowed', 'caveated_display_allowed']:
        assert token in js


def test_inventory_status_and_flags():
    entry = json.loads(INV.read_text(encoding='utf-8'))['rich_observation_contract']['m7f_rich_fact_browser_operator_workbench']
    expected_true = ['ai_handoff_selection_added', 'safe_markdown_handoff_preview_added', 'safe_json_projection_preview_added', 'explicit_copy_buttons_added', 'search_added', 'field_group_filter_added', 'confidence_filter_added', 'exposure_filter_added', 'currentness_filter_added', 'show_hide_caveated_fields_toggle_added', 'field_grouping_added', 'ai_handoff_allowed_gate_enforced', 'handoff_is_not_trading_signal', 'handoff_is_not_recommendation']
    expected_false = ['raw_forbidden_fields_selectable', 'raw_forbidden_values_copied', 'automatic_clipboard_write_added', 'ai_model_call_added', 'real_artifact_loading_added', 'runtime_behavior_changed', 'fastapi_changed', 'mcp_changed', 'live_probe_added', 'runtime_network_fetch_added', 'hidden_fetch_added', 'auto_refresh_added', 'raw_payload_exposure_allowed', 'trading_advice_allowed']
    assert entry['status'] in {'ai_handoff_selection_search_filters_defined', 'final_acceptance_pass_with_caveats'}
    assert entry['completed_tasks'] in (['M7F-00', 'M7F-01', 'M7F-02', 'M7F-03', 'M7F-04', 'M7F-05', 'M7F-06'], ['M7F-00', 'M7F-01', 'M7F-02', 'M7F-03', 'M7F-04', 'M7F-05', 'M7F-06', 'M7F-07', 'M7F-08'])
    for key in expected_true:
        assert entry[key] is True
    for key in expected_false:
        assert entry[key] is False
    assert entry['next_task'] in {'M7F-07-08-FRONTEND-SECURITY-SEMANTIC-REGRESSION-AND-FINAL-ACCEPTANCE', 'M7G-LOCAL-SAFE-CONTEXT-ARTIFACT-LOAD-AND-OPERATOR-REFRESH-WORKFLOW'}


def test_default_ci_includes_new_test():
    profile = json.loads(PROFILE.read_text(encoding='utf-8'))
    assert 'tests/unit/test_m7f_ai_handoff_search_filters.py' in profile['profiles']['default-ci']['pytest_paths']
