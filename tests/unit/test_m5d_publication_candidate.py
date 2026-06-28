import json, shutil
from pathlib import Path
from scripts.m5d_publication_common import CAND, DEST, ROOT, frontend_inventory, validate_candidate, PR57_MERGE_SHA
from scripts.simulate_m5d_frontend_publication_transaction import simulate
from scripts.simulate_m5d_frontend_publication_rollback import sim as rollback_sim
from scripts.validate_m5d_frontend_publication_request import validate as validate_request

def load(p): return json.loads((ROOT / p).read_text())

def copy_candidate(tmp_path):
    d = tmp_path / 'cand'
    shutil.copytree(ROOT / CAND, d)
    return d

def write_json(p, obj): p.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')

def test_candidate_validates(): assert validate_candidate(CAND) == []

def test_request_validator_calls_candidate_validator_for_payload_tampering(tmp_path):
    d = copy_candidate(tmp_path)
    (d / 'market-context.json').write_text('{}\n')
    req = load(Path('docs/authorization/requests/M5D_FRONTEND_PUBLICATION_REQUEST.json'))
    req['candidate_dir'] = str(d.relative_to(ROOT)) if d.is_relative_to(ROOT) else str(d)
    req_path = tmp_path / 'request.json'
    write_json(req_path, req)
    errs = validate_request(req_path)
    assert any(e.get('code') == 'candidate_validation_failed' for e in errs)

def test_candidate_payload_tampering(tmp_path):
    d = copy_candidate(tmp_path); (d / 'market-context.json').write_text('{}\n')
    assert any('candidate_payload_tampering' in e for e in validate_candidate(d))

def test_missing_caveat(tmp_path):
    d = copy_candidate(tmp_path); p = d / 'market-context.json'; x = json.loads(p.read_text()); x['global_caveats'] = []; write_json(p, x)
    assert any('missing_caveat' in e for e in validate_candidate(d))

def test_temporary_path_leakage(tmp_path):
    d = copy_candidate(tmp_path); p = d / 'candidate_summary.json'; p.write_text(p.read_text().replace('TWSE_OpenAPI', '/tmp/leak'))
    assert 'temporary_path_leakage' in validate_candidate(d)

def test_forbidden_flags_all_artifacts(tmp_path):
    d = copy_candidate(tmp_path); p = d / 'publication_plan.json'; x = json.loads(p.read_text()); x['trading_signal'] = True; write_json(p, x)
    assert any('forbidden_flag' in e for e in validate_candidate(d))

def test_wrong_proposed_destination_request_validator_blocks(tmp_path):
    req = load(Path('docs/authorization/requests/M5D_FRONTEND_PUBLICATION_REQUEST.json'))
    req['proposed_destination'] = 'frontend/public/wrong.json'
    req_path = tmp_path / 'request.json'; write_json(req_path, req)
    assert any(e.get('code') == 'proposed_destination_mismatch' for e in validate_request(req_path))

def test_missing_authorization_and_fake_token_validator_blocks(tmp_path):
    req = load(Path('docs/authorization/requests/M5D_FRONTEND_PUBLICATION_REQUEST.json'))
    assert req['authorization_token_issued'] is False and 'authorization_token' not in req
    req['authorization_token'] = 'fake'
    req_path = tmp_path / 'request.json'; write_json(req_path, req)
    assert any(e.get('code') == 'approval_material_forbidden' for e in validate_request(req_path))

def test_manifest_final_false_fails_candidate_validator(tmp_path):
    d = copy_candidate(tmp_path); p = d / 'sha256_manifest.json'; x = json.loads(p.read_text()); x['manifest_final'] = False; write_json(p, x)
    assert 'manifest_final_not_true' in validate_candidate(d)

def test_upstream_binding_mutation_fails_candidate_validator(tmp_path):
    d = copy_candidate(tmp_path); p = d / 'sha256_manifest.json'; x = json.loads(p.read_text()); x['pr57_merge_sha'] = '0' * 40; write_json(p, x)
    assert 'pr57_merge_sha_mismatch' in validate_candidate(d)

def test_exact_artifact_set_rejects_extra_file(tmp_path):
    d = copy_candidate(tmp_path); (d / 'extra.json').write_text('{}\n')
    assert 'artifact_set_mismatch' in validate_candidate(d)

def test_frontend_public_baseline_recomputed_matches_current():
    assert frontend_inventory() == load(CAND / 'frontend_public_baseline.json')

def test_frontend_public_baseline_drift_detection(tmp_path, monkeypatch):
    d = copy_candidate(tmp_path)
    monkeypatch.setattr('scripts.m5d_publication_common.frontend_inventory', lambda: {'drifted': True})
    assert 'frontend_public_baseline_drift' in validate_candidate(d)

def test_destination_already_exists_simulation(): assert simulate(existing=True)['destination_already_exists'] is True

def test_atomic_replace_failure(): assert simulate(fail_replace=True)['status'] == 'blocked'

def test_rollback_existing_destination_failure(): assert rollback_sim(fail=True, existing=True)['status'] == 'blocked'

def test_rollback_no_existing_destination_deletes_new_file():
    out = rollback_sim(existing=False)
    assert out['rollback_mode'] == 'delete_new_destination'
    assert out['destination_exists_after_rollback'] is False

def test_source_package_changed_detection(tmp_path):
    d = copy_candidate(tmp_path); p = d / 'sha256_manifest.json'; x = json.loads(p.read_text()); x['m5c_frontend_readonly_context_package_sha256'] = '0' * 64; write_json(p, x)
    assert 'source_package_changed_after_candidate_build' in validate_candidate(d)

def test_pr57_sha_constant_is_bound(): assert PR57_MERGE_SHA == '3931f19564698926a96a3022c5c3b40b07de6081'
