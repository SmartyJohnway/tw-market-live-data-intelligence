from pathlib import Path

DOCS = {
    Path('docs/protocol/M7G_LOCAL_SAFE_CONTEXT_ARTIFACT_LOAD_POLICY.md'): 'local_safe_context_artifact_load_policy_defined',
    Path('docs/protocol/M7G_SAFE_CONTEXT_ARTIFACT_SCHEMA_AND_MANIFEST.md'): 'm7g_safe_context_artifact.v1',
    Path('docs/protocol/M7G_LOCAL_SAFE_ARTIFACT_VALIDATOR_AND_REJECTION_GATE.md'): 'local_safe_artifact_validator_rejection_gate_defined',
    Path('docs/protocol/M7G_FRONTEND_MANUAL_SAFE_ARTIFACT_LOAD_UI.md'): 'frontend_manual_safe_artifact_load_ui_defined',
}

def test_m7g_docs_exist_with_statuses():
    for path, status in DOCS.items():
        text = path.read_text(encoding='utf-8')
        assert status in text
    assert 'm7g_safe_context_manifest.v1' in Path('docs/protocol/M7G_SAFE_CONTEXT_ARTIFACT_SCHEMA_AND_MANIFEST.md').read_text(encoding='utf-8')

def test_m7g_policy_declares_mandatory_m7g09_gate():
    text = Path('docs/protocol/M7G_LOCAL_SAFE_CONTEXT_ARTIFACT_LOAD_POLICY.md').read_text(encoding='utf-8')
    assert 'M7G-09 controlled manual refresh execution is mandatory downstream work' in text
    assert 'M7G-00/03 does not execute refresh' in text
    assert 'M7G-09 will be the earliest task allowed to execute controlled manual refresh' in text
