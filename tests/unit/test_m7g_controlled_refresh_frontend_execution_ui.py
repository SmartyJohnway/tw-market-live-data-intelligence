from pathlib import Path

HTML = Path('frontend/public/index.html').read_text(encoding='utf-8')

def test_frontend_controlled_execution_labels_present():
    for text in ['Controlled Manual Refresh Execution','Execute controlled refresh once','Execution confirmation phrase','EXECUTE_CONTROLLED_REFRESH_ONCE','Refresh execution result','Load refreshed safe artifact','Rejected execution result','No auto refresh','No scheduler','No hidden fetch','Mode A/B/C unchanged','Level 1/2 unchanged','Level 2 safe artifact only','M5F not mutated', 'TPEX_OPENAPI', 'TAIFEX_MIS', 'TWSE_MIS — executable in M7G-09', 'declared but not executable in M7G-09', 'Unsupported or not-yet-executable families fail closed']:
        assert text in HTML


def test_frontend_execution_behavior_is_explicit_click_and_validated():
    for text in ['POST', '/api/m7g/controlled-refresh/execute', 'EXECUTE_CONTROLLED_REFRESH_ONCE', 'validateM7GSafeContextArtifact', 'renderM7FRichFactBrowser(m7gActiveSafeArtifact)', 'updateM7GLoadedPanels']:
        assert text in HTML
    controlled = HTML[HTML.index('async function executeM7GControlledRefreshOnce'):HTML.index('function loadM7GRefreshedSafeArtifact')]
    assert "addEventListener('click', executeM7GControlledRefreshOnce)" in HTML
    assert 'setInterval' not in controlled
    assert 'setTimeout' not in controlled
    assert 'WebSocket' not in controlled
    assert 'EventSource' not in controlled
    assert 'scheduler' not in controlled.lower()
    assert 'polling' not in controlled.lower()


def test_rejected_execution_cannot_render_and_no_automatic_load():
    load_fn = HTML[HTML.index('function loadM7GRefreshedSafeArtifact'):HTML.index('function renderM7FRichFactBrowser')]
    assert "execution_status === 'executed_safe_artifact_ready'" in load_fn
    assert 'safe_artifact_returned === true' in load_fn
    assert "validation_status === 'accepted'" in load_fn
    assert 'safe_to_render === true' in load_fn
    execute_fn = HTML[HTML.index('async function executeM7GControlledRefreshOnce'):HTML.index('function loadM7GRefreshedSafeArtifact')]
    assert 'renderM7FRichFactBrowser' not in execute_fn


def test_m7g_execute_slice_does_not_auto_render_or_update_active_context():
    execute_fn = HTML[HTML.index('async function executeM7GControlledRefreshOnce'):HTML.index('function loadM7GRefreshedSafeArtifact')]
    for forbidden in ['renderM7FRichFactBrowser', 'renderM7FHandoffPanel', 'updateM7GLoadedPanels']:
        assert forbidden not in execute_fn
    assert "fetch('/api/m7g/controlled-refresh/execute'" in execute_fn


def test_load_refreshed_artifact_is_only_refresh_execution_renderer_gate():
    refresh_slice = HTML[HTML.index('function getM7GRefreshPreflightContext'):HTML.index('function renderM7FRichFactBrowser')]
    load_fn = HTML[HTML.index('function loadM7GRefreshedSafeArtifact'):HTML.index('function renderM7FRichFactBrowser')]
    assert refresh_slice.count('renderM7FRichFactBrowser') == 1
    assert 'renderM7FRichFactBrowser(m7gActiveSafeArtifact)' in load_fn
    for required in ["execution_status === 'executed_safe_artifact_ready'", 'safe_artifact_returned === true', "validation_status === 'accepted'", 'safe_to_render === true']:
        assert required in load_fn


def test_refresh_execution_slice_has_no_auto_refresh_hidden_behavior():
    refresh_slice = HTML[HTML.index('function getM7GRefreshPreflightContext'):HTML.index('function renderM7FRichFactBrowser')]
    for forbidden in ['setInterval', 'setTimeout', 'WebSocket', 'EventSource', 'navigator.sendBeacon']:
        assert forbidden not in refresh_slice
    for forbidden in ['scheduler', 'polling', 'startup']:
        assert forbidden not in refresh_slice.lower()
