import json, shutil, hashlib
from pathlib import Path
from scripts.m5d_publication_common import CAND, DEST, ROOT, validate_candidate
from scripts.simulate_m5d_frontend_publication_transaction import simulate
from scripts.simulate_m5d_frontend_publication_rollback import sim as rollback_sim

def load(p): return json.loads((ROOT/p).read_text())

def copy_candidate(tmp_path):
    d=tmp_path/'cand'; shutil.copytree(ROOT/CAND,d); return d

def test_candidate_validates(): assert validate_candidate(CAND)==[]
def test_candidate_payload_tampering(tmp_path):
    d=copy_candidate(tmp_path); (d/'market-context.json').write_text('{}\n'); assert validate_candidate(d)
def test_missing_caveat(tmp_path):
    d=copy_candidate(tmp_path); p=d/'market-context.json'; x=json.loads(p.read_text()); x['global_caveats']=[]; p.write_text(json.dumps(x)); assert any('missing_caveat' in e for e in validate_candidate(d))
def test_temporary_path_leakage(tmp_path):
    d=copy_candidate(tmp_path); p=d/'candidate_summary.json'; p.write_text(p.read_text().replace('TWSE_OpenAPI','/tmp/leak')) ; assert 'temporary_path_leakage' in validate_candidate(d)
def test_forbidden_flags(tmp_path):
    d=copy_candidate(tmp_path); p=d/'market-context.json'; x=json.loads(p.read_text()); x['realtime_guaranteed']=True; p.write_text(json.dumps(x)); assert any('forbidden_flag' in e for e in validate_candidate(d))
def test_wrong_proposed_destination_in_request(tmp_path):
    req=load(Path('docs/authorization/requests/M5D_FRONTEND_PUBLICATION_REQUEST.json')); req['proposed_destination']='frontend/public/wrong.json'; assert req['proposed_destination']!=str(DEST)
def test_missing_authorization_and_fake_token():
    req=load(Path('docs/authorization/requests/M5D_FRONTEND_PUBLICATION_REQUEST.json')); assert req['authorization_token_issued'] is False and 'authorization_token' not in req
    req['authorization_token']='fake'; assert 'authorization_token' in req
def test_destination_already_exists_simulation(): assert simulate(existing=True)['destination_already_exists'] is True
def test_atomic_replace_failure(): assert simulate(fail_replace=True)['status']=='blocked'
def test_rollback_failure(): assert rollback_sim(fail=True)['status']=='blocked'
def test_source_package_changed_detection(tmp_path):
    d=copy_candidate(tmp_path); p=d/'sha256_manifest.json'; x=json.loads(p.read_text()); x['m5c_frontend_readonly_context_package_sha256']='0'*64; p.write_text(json.dumps(x)); assert 'source_package_changed_after_candidate_build' in validate_candidate(d)
def test_manifest_finalization_failure(tmp_path):
    d=copy_candidate(tmp_path); p=d/'sha256_manifest.json'; x=json.loads(p.read_text()); x['manifest_final']=False; p.write_text(json.dumps(x)); assert json.loads(p.read_text())['manifest_final'] is False
def test_frontend_public_unchanged_hash_only():
    inv=load(CAND/'frontend_public_baseline.json'); assert inv['hash_only'] is True
