import json
from pathlib import Path

import pytest

from scripts.build_m5b_staging_candidate import build


def base_result():
    return {
        'run_id': 'x', 'source_id': 'TWSE_OpenAPI', 'requested_targets': ['2330', '0050', '00929'],
        'retained_targets': ['2330'], 'retrieved_at_utc': '2026-06-27T00:00:00+00:00',
        'source_timestamp': '2026-06-26', 'http_status': 200, 'contract_status': 'partial_pass',
        'parse_status': 'parsed', 'normalization_status': 'normalized', 'failed_targets': ['0050', '00929'],
        'errors': [], 'caveats': [], 'production_current_state': False, 'realtime_guaranteed': False,
        'trading_signal': False, 'generated_artifact_promoted': False, 'frontend_published': False,
        'rows': [{'symbol': '2330', 'realtime_guaranteed': False}],
    }


def write_minimal_run(run_dir: Path, result: dict):
    run_dir.mkdir(exist_ok=True)
    for name in ['authorization_snapshot.json', 'request_snapshot.json', 'execution_receipt.json']:
        (run_dir / name).write_text(json.dumps({'name': name}))
    (run_dir / 'bounded_probe_result.json').write_text(json.dumps(result))
    (run_dir / 'bounded_normalized_rows.json').write_text(json.dumps(result))
    (run_dir / 'source_contract_assessment.json').write_text(json.dumps({'x': 1}))
    (run_dir / 'freshness_delay_assessment.json').write_text(json.dumps({'x': 1}))
    (run_dir / 'run_summary.json').write_text(json.dumps({'run_id': result['run_id'], 'staging_candidate_created': False}))


def test_build_staging_candidate_finalizes_manifest_and_ledger(tmp_path):
    write_minimal_run(tmp_path, base_result())
    candidate = build(tmp_path)
    assert candidate['staging_only'] and not candidate['production_ready']
    summary = json.loads((tmp_path / 'run_summary.json').read_text())
    ledger = json.loads((tmp_path / 'evidence_ledger.json').read_text())
    manifest = json.loads((tmp_path / 'sha256_manifest.json').read_text())
    assert summary['staging_candidate_created'] is True
    assert ledger['artifacts']
    assert 'staging_candidate.json' in manifest['manifest']
    assert manifest['manifest_final'] is True


def test_build_staging_candidate_rejects_unauthorized_symbol(tmp_path):
    result = base_result()
    result['rows'] = [{'symbol': '2317'}]
    write_minimal_run(tmp_path, result)
    with pytest.raises(ValueError, match='unauthorized symbol'):
        build(tmp_path)


def test_build_staging_candidate_rejects_forbidden_trading_field(tmp_path):
    result = base_result()
    result['rows'] = [{'symbol': '2330', 'recommendation': 'buy'}]
    write_minimal_run(tmp_path, result)
    with pytest.raises(ValueError, match='forbidden'):
        build(tmp_path)
