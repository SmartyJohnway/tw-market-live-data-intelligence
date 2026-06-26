from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.run_m4_readiness_check import run_readiness_check, validate_evidence_ledger, validate_release_gate_matrix
def test_readiness_check():
 r=run_readiness_check(ROOT); assert r['ok'] and not r['network_used'] and not r['production_ready']
def test_readiness_fails_bad_replay_scenario(tmp_path):
 bad=tmp_path/'bad_scenarios.json'; bad.write_text(json.dumps({'scenarios':[{'scenario_id':'bad','description':'bad','payload':{},'expected_validation_status':'valid','expected_frontend_caveats':[],'expected_forbidden_flags':[],'expected_summary_status':'pass','forbidden_behaviors_absent':True}]}))
 r=run_readiness_check(ROOT, bad)
 assert not r['ok']; assert any(c['name']=='fixture_replay' and not c['ok'] for c in r['checks'])
def test_evidence_ledger_detects_hash_mismatch(tmp_path):
 ledger=load('tests/fixtures/evidence/fixture_evidence_ledger.json'); ledger['evidence'][0]['hash_sha256']='0'*64
 p=tmp_path/'ledger.json'; p.write_text(json.dumps(ledger))
 assert validate_evidence_ledger(ROOT, p)[0]['code']=='hash_mismatch'
def test_release_gate_blocks_elevation(tmp_path):
 p=tmp_path/'release.json'; p.write_text(json.dumps({'current_allowed_level':'production','gates':[]}))
 assert validate_release_gate_matrix(ROOT, p)[0]['code']=='current_level_must_remain_local_only_fixture_only'

def test_evidence_ledger_empty_or_missing_fails(tmp_path):
 p=tmp_path/'empty_ledger.json'; p.write_text(json.dumps({'evidence': []}))
 assert validate_evidence_ledger(ROOT, p)[0]['code']=='evidence_empty'
 p2=tmp_path/'missing_ledger.json'; p2.write_text(json.dumps({}))
 assert validate_evidence_ledger(ROOT, p2)[0]['code']=='evidence_missing_or_not_array'
