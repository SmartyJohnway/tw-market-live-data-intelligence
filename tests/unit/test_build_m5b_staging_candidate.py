import json
from pathlib import Path

import pytest

from scripts.build_m5b_staging_candidate import build, finalize
from scripts.verify_m5b_manifest import verify


def base_result(contract_status='partial_pass'):
    return {
        'run_id': 'x', 'source_id': 'TWSE_OpenAPI', 'requested_targets': ['2330', '0050', '00929'],
        'retained_targets': ['2330'], 'retrieved_at_utc': '2026-06-27T00:00:00+00:00',
        'source_timestamp': '2026-06-26', 'http_status': 200, 'contract_status': contract_status,
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
    assert any(entry['produced_by'] == 'scripts/run_m5b_controlled_live_probe.py' for entry in ledger['artifacts'])
    assert any(entry['cataloged_by'] == 'scripts/build_m5b_staging_candidate.py' for entry in ledger['artifacts'])
    assert 'staging_candidate.json' in manifest['manifest']
    assert manifest['manifest_final'] is True
    assert verify(tmp_path) == []


def test_build_staging_candidate_rejects_unsafe_rows(tmp_path):
    cases = [
        ([{"symbol": "2317"}], "unauthorized symbol"),
        ([{"symbol": "2330", "recommendation": "buy"}], "forbidden"),
    ]
    for rows, match in cases:
        run_dir = tmp_path / match.replace(" ", "_")
        result = base_result()
        result["rows"] = rows
        write_minimal_run(run_dir, result)
        with pytest.raises(ValueError, match=match):
            build(run_dir)


def test_failure_contract_does_not_create_staging_candidate(tmp_path):
    write_minimal_run(tmp_path, base_result(contract_status='http_failed'))
    final = finalize(tmp_path, create_candidate=False)
    summary = json.loads((tmp_path / 'run_summary.json').read_text())
    assert final['staging_only'] is False
    assert summary['staging_candidate_created'] is False
    assert not (tmp_path / 'staging_candidate.json').exists()
    assert verify(tmp_path) == []


def test_failure_contract_rejects_candidate_creation(tmp_path):
    write_minimal_run(tmp_path, base_result(contract_status='parse_failed'))
    with pytest.raises(ValueError, match='requires successful contract status'):
        build(tmp_path)


def test_duplicate_finalization_rejected_by_default(tmp_path):
    write_minimal_run(tmp_path, base_result())
    build(tmp_path)
    with pytest.raises(ValueError, match='final manifest already exists'):
        build(tmp_path)


def test_manifest_verifier_detects_tamper_and_missing_artifact(tmp_path):
    cases = ["tamper", "missing_artifact"]
    for case in cases:
        run_dir = tmp_path / case
        write_minimal_run(run_dir, base_result())
        build(run_dir)
        if case == "tamper":
            data = json.loads((run_dir / "bounded_probe_result.json").read_text())
            data["retained_targets"] = ["2330", "2317"]
            (run_dir / "bounded_probe_result.json").write_text(json.dumps(data))
            expected_code = "manifest_sha256_mismatch"
        else:
            (run_dir / "request_snapshot.json").unlink()
            expected_code = "manifest_artifact_missing"
        errors = verify(run_dir)
        assert any(error["code"] == expected_code for error in errors)


def test_existing_manifest_rejects_refinalization(tmp_path):
    cases = ["final_false", "malformed_json"]
    for manifest_mutation in cases:
        run_dir = tmp_path / manifest_mutation
        write_minimal_run(run_dir, base_result())
        build(run_dir)
        manifest_path = run_dir / "sha256_manifest.json"
        if manifest_mutation == "final_false":
            manifest = json.loads(manifest_path.read_text())
            manifest["manifest_final"] = False
            manifest_path.write_text(json.dumps(manifest))
        else:
            manifest_path.write_text("{not-json")
        with pytest.raises(ValueError, match="final manifest already exists"):
            build(run_dir)


def test_finalizer_rejects_missing_required_artifact(tmp_path):
    write_minimal_run(tmp_path, base_result())
    (tmp_path / 'execution_receipt.json').unlink()
    with pytest.raises(ValueError, match='missing required evidence artifacts'):
        build(tmp_path)


def test_committed_m5b_manifest_verifies():
    assert verify('research/live_probe_runs/m5b/m5b_twse_openapi_20260627T015136Z') == []
