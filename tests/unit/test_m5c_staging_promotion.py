import json, shutil
from pathlib import Path
from scripts.m5c_common import RUN_DIR, verify_evidence, candidate_hash, manifest_hash, forbid_path, load, readonly_payload_from_candidate
from scripts.assess_m5c_staging_candidate import assess
from scripts.validate_m5c_staging_promotion_request import validate_request
from scripts.plan_m5c_staging_promotion import plan
from scripts.simulate_m5c_staging_rollback import simulate as rollback
from scripts.run_m5c_staging_promotion_preflight import run
from scripts.build_frontend_readonly_context_package import build_frontend_readonly_context_package
REQ='docs/authorization/requests/M5C_TWSE_OPENAPI_STAGING_PROMOTION_REQUEST.json'
def copy_run(tmp_path):
    dst=tmp_path/RUN_DIR.name; shutil.copytree(RUN_DIR,dst); return dst
def test_valid_m5b_evidence_eligible(): assert assess()['status']=='eligible_for_user_authorization'
def test_tampered_manifest_blocked(tmp_path):
    d=copy_run(tmp_path); p=d/'staging_candidate.json'; p.write_text(p.read_text().replace('TWSE_OpenAPI','BAD',1)); assert verify_evidence(d)['status']=='blocked'
def test_missing_evidence_blocked(tmp_path):
    d=copy_run(tmp_path); (d/'execution_receipt.json').unlink(); assert assess(d)['status']=='blocked'
def test_exact_binding_request():
    r=validate_request(REQ); assert r['status']=='pass'
    q=json.loads(Path(REQ).read_text()); assert q['source_manifest_sha256']==manifest_hash(); assert q['staging_candidate_sha256']==candidate_hash(); assert set(q['targets'])=={'2330','0050','00929'}
def test_no_decision_or_token():
    q=json.loads(Path(REQ).read_text()); assert 'approval_token' not in q and 'authorization_decision' not in q and q['actual_promotion_authorized'] is False
def test_historical_not_current_readonly():
    pkg=build_frontend_readonly_context_package(readonly_payload_from_candidate(load(RUN_DIR/'staging_candidate.json'))); assert pkg['realtime_guaranteed'] is False; assert all(s['freshness_status']=='stale' for s in pkg['symbols'])
def test_default_plan_no_write_and_forbidden_paths():
    p=plan(); assert p['write_performed'] is False; assert plan(destination='frontend/public/x.json')['status']=='blocked'; assert forbid_path('research/generated/x')
def test_rollback_no_mutation():
    r=rollback(); assert r['write_performed'] is False and r['delete_performed'] is False and r['overwrite_performed'] is False
def test_one_command_preflight_shape():
    out=run();
    for k in ['evidence_integrity','receipt_audit','candidate_eligibility','request_validation','simulation_status','rollback_readiness','readonly_compatibility','actual_promotion_performed','next_required_action']: assert k in out
    assert out['actual_promotion_performed'] is False and out['next_required_action']=='user_authorization'
