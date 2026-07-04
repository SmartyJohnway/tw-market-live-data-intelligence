import json, shutil, subprocess, sys

from pathlib import Path
from scripts.m5c_common import RUN_DIR, verify_evidence, candidate_hash, manifest_hash, forbid_path, load, readonly_payload_from_candidate, TARGETS
from scripts.assess_m5c_staging_candidate import assess
from scripts.validate_m5c_staging_promotion_request import validate_request
from scripts.plan_m5c_staging_promotion import plan
from scripts.simulate_m5c_staging_rollback import simulate as rollback
from scripts.run_m5c_staging_promotion_preflight import run
from scripts.build_frontend_readonly_context_package import build_frontend_readonly_context_package
REQ='docs/authorization/requests/M5C_TWSE_OPENAPI_STAGING_PROMOTION_REQUEST.json'
def copy_run(tmp_path):
    dst=tmp_path/RUN_DIR.name; shutil.copytree(RUN_DIR,dst); return dst
def write_json(path,obj): path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
def test_valid_m5b_evidence_eligible(): assert assess()['status']=='eligible_for_user_authorization'
def test_tampered_manifest_blocked(tmp_path):
    d=copy_run(tmp_path); p=d/'staging_candidate.json'; p.write_text(p.read_text().replace('TWSE_OpenAPI','BAD',1)); codes={e['code'] for e in verify_evidence(d)['errors']}; assert 'manifest_sha256_mismatch' in codes
def test_missing_manifest_artifact_and_ledger_blocked(tmp_path):
    d=copy_run(tmp_path); (d/'evidence_ledger.json').unlink(); codes={e['code'] for e in verify_evidence(d)['errors']}; assert {'manifest_artifact_missing','missing_required_artifact'} <= codes
def test_untracked_json_artifact_blocked(tmp_path):
    d=copy_run(tmp_path); (d/'extra.json').write_text('{}'); codes={e['code'] for e in verify_evidence(d)['errors']}; assert 'manifest_untracked_artifact' in codes
def test_receipt_audit_uses_authorization_validator(tmp_path):
    d=copy_run(tmp_path); r=load(d/'execution_receipt.json'); r['authorization_id']='wrong'; write_json(d/'execution_receipt.json',r); codes={e['code'] for e in verify_evidence(d)['errors']}; assert 'receipt_authorization_mismatch' in codes
def test_contract_status_failed_is_semantic_block(tmp_path):
    d=copy_run(tmp_path)
    for fn in ['staging_candidate.json','run_summary.json','execution_receipt.json','sha256_manifest.json']:
        obj=load(d/fn); obj['contract_status']='failed'; write_json(d/fn,obj)
    codes={e['code'] for e in verify_evidence(d)['errors']}
    assert 'contract_status_blocked' in codes
def test_malformed_json_returns_structured_blocked(tmp_path):
    d=copy_run(tmp_path); (d/'staging_candidate.json').write_text('{bad')
    codes={e['code'] for e in verify_evidence(d)['errors']}
    assert 'json_read_failed' in codes
    req=tmp_path/'bad_request.json'; req.write_text('{bad')
    assert validate_request(req)['status']=='blocked'
    assert validate_request(req)['errors'][0]['code']=='json_read_failed'
def test_exact_binding_request_and_schema():
    r=validate_request(REQ); assert r['status']=='pass'
    q=json.loads(Path(REQ).read_text()); assert q['source_manifest_sha256']==manifest_hash(); assert q['staging_candidate_sha256']==candidate_hash(); assert q['targets']==TARGETS
def test_request_rejects_duplicate_targets_and_noncanonical_run_dir(tmp_path):
    q=json.loads(Path(REQ).read_text()); q['targets']=['2330','2330','00929']; q['source_run_dir']=str(tmp_path/RUN_DIR.name); p=tmp_path/'bad_request.json'; write_json(p,q); codes={e['code'] for e in validate_request(p)['errors']}; assert 'schema_error' in codes and 'canonical_run_dir_mismatch' in codes
def test_no_decision_or_token(tmp_path):
    q=json.loads(Path(REQ).read_text()); q['approval_token']='forbidden'; p=tmp_path/'bad_request.json'; write_json(p,q); codes={e['code'] for e in validate_request(p)['errors']}; assert 'schema_error' in codes and 'decision_or_token_forbidden' in codes
def test_historical_not_current_readonly():
    pkg=build_frontend_readonly_context_package(readonly_payload_from_candidate(load(RUN_DIR/'staging_candidate.json'))); assert pkg['realtime_guaranteed'] is False; assert all(s['freshness_status']=='stale' for s in pkg['symbols'])
def test_default_plan_no_write_and_forbidden_paths():
    p=plan(); assert p['write_performed'] is False; assert plan(destination='frontend/public/x.json')['status']=='blocked'; assert forbid_path('research/generated/x')
def test_forbidden_paths_absolute_windows_and_traversal():
    assert forbid_path('/tmp/repo/production/out.json'); assert forbid_path('C:\\repo\\frontend\\public\\x.json'); assert forbid_path('safe/../prod/out.json')
def test_blocked_cli_returns_nonzero(tmp_path):
    d=copy_run(tmp_path); (d/'evidence_ledger.json').unlink(); r=subprocess.run([sys.executable,'scripts/assess_m5c_staging_candidate.py','--run-dir',str(d),'--check-only'],capture_output=True,text=True); assert r.returncode != 0
    r=subprocess.run([sys.executable,'scripts/plan_m5c_staging_promotion.py','--destination','production/out.json','--check-only'],capture_output=True,text=True); assert r.returncode != 0
def test_rollback_failure_injection_no_mutation(tmp_path):
    r=rollback(str(tmp_path)); assert r['write_performed'] is False and r['delete_performed'] is False and r['overwrite_performed'] is False
    results={s['scenario']:s for s in r['scenarios']}; assert r['status']=='rollback_ready_check_only'; assert 'manifest_sha256_mismatch' in results['tampered_manifest']['observed_error_codes']; assert 'manifest_artifact_missing' in results['missing_artifact']['observed_error_codes']; assert 'target_drift' in results['unauthorized_target']['observed_error_codes']; assert 'contract_status_blocked' in results['contract_failure']['observed_error_codes']; assert 'forbidden_flag' in results['forbidden_realtime_trading_flag']['observed_error_codes']; assert 'partial_write_detected' in results['partial_write_simulation']['observed_error_codes']
def test_rollback_rejects_forbidden_tmp_roots():
    for bad in ["frontend/public/test", "research/generated/test", "production/test", "prod/test", "research/live_probe_runs/m5b/test", "docs/rollback-test", "scripts/tmp", "."]:
        r = rollback(bad)
        assert r["status"] == "blocked"
        assert r["errors"][0]["code"] == "forbidden_tmp_root"


def test_one_command_preflight_shape():
    out=run();
    for k in ['evidence_integrity','receipt_audit','candidate_eligibility','request_validation','simulation_status','rollback_readiness','readonly_compatibility','actual_promotion_performed','next_required_action']: assert k in out
    assert out['actual_promotion_performed'] is False and out['next_required_action']=='user_authorization'
def test_rollback_main_nonzero_on_simulation_failed(monkeypatch, capsys):
    import scripts.simulate_m5c_staging_rollback as rb
    monkeypatch.setattr(rb, 'simulate', lambda: {'status':'simulation_failed','write_performed':False,'delete_performed':False,'overwrite_performed':False,'scenarios':[]})
    assert rb.main([]) == 1
def test_preflight_success_whitelist_rejects_simulation_failed(monkeypatch):
    import scripts.run_m5c_staging_promotion_preflight as pf
    out={'evidence_integrity':'pass','receipt_audit':'pass','candidate_eligibility':'eligible_for_user_authorization','request_validation':'pass','simulation_status':'simulation_failed','rollback_readiness':'rollback_ready_check_only','readonly_compatibility':'pass','actual_promotion_performed':False,'next_required_action':'user_authorization'}
    assert pf.is_success(out) is False
def test_preflight_malformed_candidate_returns_structured_blocked(tmp_path):
    d=copy_run(tmp_path); (d/'staging_candidate.json').write_text('{bad')
    out=run(d)
    assert out['evidence_integrity']=='blocked'
    assert out['actual_promotion_performed'] is False
    assert 'errors' in out
