from pathlib import Path

HTML = Path('frontend/public/index.html').read_text(encoding='utf-8')
SLICE = HTML.split('const M7G_CONTEXT_MODE_STATIC_DEMO', 1)[1].split('function getM7FHandoffAllowedFields', 1)[0]


def test_rendering_doc_exists_and_defines_boundaries():
    text = Path('docs/protocol/M7G_RICH_FACT_BROWSER_REAL_SAFE_ARTIFACT_RENDERING.md').read_text(encoding='utf-8')
    for expected in ['real_safe_artifact_rendering_defined','static_demo','loaded_safe_artifact','Rejected artifacts never reach renderM7FRichFactBrowser','does not execute refresh','does not fetch live data','does not add backend/API/MCP']:
        assert expected in text


def test_frontend_active_context_mode_state_and_labels():
    for expected in ['M7G_CONTEXT_MODE_STATIC_DEMO','M7G_CONTEXT_MODE_LOADED_SAFE_ARTIFACT','m7gActiveContextMode','m7gActiveSafeArtifact','m7gActiveValidationResult','Active context mode','static_demo','loaded_safe_artifact','Loaded artifact active','Static demo active','Operator-selected local safe artifact']:
        assert expected in HTML


def test_loaded_artifact_renderer_gate_and_reset():
    gated = SLICE.split("loadButton.addEventListener('click'", 1)[1].split("resetButton.addEventListener", 1)[0]
    assert "m7gValidationResult.validation_status === 'accepted'" in gated
    assert 'm7gValidationResult.safe_to_render === true' in gated
    assert 'm7gActiveSafeArtifact = m7gValidatedArtifact' in gated
    assert 'renderM7FRichFactBrowser(m7gActiveSafeArtifact)' in gated
    reset = SLICE.split("resetButton.addEventListener('click'", 1)[1]
    assert 'm7gActiveContextMode = M7G_CONTEXT_MODE_STATIC_DEMO' in reset
    assert 'm7gActiveSafeArtifact = null' in reset
    assert 'renderM7FRichFactBrowser(M7F_DEMO_RICH_CONTEXT)' in reset


def test_no_new_network_backend_refresh_in_m7g_slice():
    for forbidden in ['fetch(', 'XMLHttpRequest', 'WebSocket', 'EventSource', 'setInterval', 'setTimeout', 'navigator.sendBeacon', '/api/', 'mcp', 'localhost', '127.0.0.1']:
        assert forbidden not in SLICE


def test_frontend_source_health_validation_gate_matches_canonical_validator():
    for expected in ['M7G_SOURCE_HEALTH_ALLOWED_STATUSES.includes', 'invalid_source_health', 'm7g_source_health.v1', 'missing_source_health_metadata']:
        assert expected in SLICE
    source_health_gate = SLICE.split('let sourceHealthStatus', 1)[1].split('const rawKeys = detectM7GRawForbiddenKeys', 1)[0]
    assert "sourceHealthStatus = candidate.source_health.health_status || 'unknown'" in source_health_gate
    assert "sourceHealthSchemaVersion !== 'm7g_source_health.v1'" in source_health_gate
    assert '!M7G_SOURCE_HEALTH_ALLOWED_STATUSES.includes(sourceHealthStatus)' in source_health_gate
    assert "reject('invalid_source_health'" in source_health_gate
