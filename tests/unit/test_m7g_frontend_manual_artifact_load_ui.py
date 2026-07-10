from pathlib import Path

HTML = Path('frontend/public/index.html').read_text(encoding='utf-8')
SLICE = HTML.split('let m7gPendingArtifactText', 1)[1].split('function getM7FHandoffAllowedFields', 1)[0]


def test_frontend_manual_load_ui_exists():
    for text in ['Local Safe Context Artifact Load','Manual local artifact load','Paste safe JSON artifact','Validate artifact','Load validated artifact','Reset to static demo','Validation result','Loaded artifact manifest','Rejection summary']:
        assert text in HTML


def test_frontend_manual_action_only_and_no_forbidden_runtime_api_in_m7g_slice():
    assert 'FileReader' in SLICE
    assert 'JSON.parse' in SLICE
    assert "addEventListener('click'" in SLICE
    assert 'renderM7FRichFactBrowser(m7gValidatedArtifact)' in SLICE
    for forbidden in ['fetch(', 'XMLHttpRequest', 'WebSocket', 'EventSource', 'setInterval', 'setTimeout', 'navigator.sendBeacon', '/api/', 'mcp', 'localhost', '127.0.0.1']:
        assert forbidden not in SLICE


def test_rejected_artifact_cannot_render_without_accepted_gate():
    assert 'm7gValidatedArtifact' in SLICE
    assert "m7gValidationResult.validation_status === 'accepted'" in SLICE
    assert 'm7gValidationResult.safe_to_render === true' in SLICE
    gated = SLICE.split("loadButton.addEventListener('click'", 1)[1].split("resetButton.addEventListener", 1)[0]
    assert 'renderM7FRichFactBrowser(m7gValidatedArtifact)' in gated


def test_raw_forbidden_keys_only_appear_as_catalog_or_rejection_gate_metadata():
    for key in ['raw_payload','twse_mis_rich_facts','raw_rich_facts','raw_unknown_facts','full_ladder','bid_prices','ask_prices','source_investigation_notes','response_sample','raw_fields_sample']:
        assert key in HTML
    assert 'detectM7GRawForbiddenKeys' in HTML
