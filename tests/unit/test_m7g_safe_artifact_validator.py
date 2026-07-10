import copy
import json
from pathlib import Path

from scripts.m7g_safe_artifact_validator import build_m7g_safe_artifact_rejection_summary, validate_m7g_safe_context_artifact


def load_fixture(name):
    return json.loads(Path('tests/fixtures', name).read_text(encoding='utf-8'))


def test_valid_fixture_passes():
    result = validate_m7g_safe_context_artifact(load_fixture('m7g_safe_context_artifact_valid.json'))
    assert result['validation_status'] == 'accepted'
    assert result['safe_to_render'] is True
    assert result['safe_for_ai_handoff'] is True
    assert result['errors'] == []
    assert result['raw_forbidden_keys_detected'] == []
    assert result['raw_payload_exposed'] is False
    assert result['raw_rich_facts_exposed'] is False
    assert result['raw_full_ladder_exposed'] is False
    assert result['source_health_status'] == 'artifact_reported'
    assert result['source_health_schema_version'] == 'm7g_source_health.v1'
    assert result['source_health_warnings'] == []


def test_raw_payload_fixture_rejected_without_raw_values():
    artifact = load_fixture('m7g_safe_context_artifact_rejected_raw_payload.json')
    result = validate_m7g_safe_context_artifact(artifact)
    assert result['validation_status'] == 'rejected'
    assert result['safe_to_render'] is False
    assert result['safe_for_ai_handoff'] is False
    assert 'raw_payload' in result['raw_forbidden_keys_detected']
    summary = build_m7g_safe_artifact_rejection_summary(result)
    dumped = json.dumps(summary, ensure_ascii=False)
    assert 'raw_payload' in dumped
    assert 'unsafe' not in dumped
    assert 'true' not in dumped.lower()


def test_validator_does_not_mutate_artifact():
    artifact = load_fixture('m7g_safe_context_artifact_valid.json')
    before = copy.deepcopy(artifact)
    validate_m7g_safe_context_artifact(artifact)
    assert artifact == before


def test_validator_module_has_no_network_file_ai_db_behavior():
    text = Path('scripts/m7g_safe_artifact_validator.py').read_text(encoding='utf-8')
    for forbidden in ['requests', 'urllib', 'httpx', 'fetch', 'open(', 'Path(', 'sqlite', 'psycopg', 'sqlalchemy', 'subprocess', 'socket', 'mcp', 'FastAPI']:
        assert forbidden not in text


def test_missing_source_health_fixture_passes_with_warning():
    result = validate_m7g_safe_context_artifact(load_fixture('m7g_safe_context_artifact_valid_missing_source_health.json'))
    assert result['validation_status'] == 'accepted'
    assert result['source_health_status'] == 'unknown'
    assert 'missing_source_health_metadata' in result['source_health_warnings']


def test_bad_source_health_fixture_rejected_without_raw_values():
    result = validate_m7g_safe_context_artifact(load_fixture('m7g_safe_context_artifact_rejected_bad_source_health.json'))
    assert result['validation_status'] == 'rejected'
    assert any(error['code'] == 'invalid_source_health' for error in result['errors'])
