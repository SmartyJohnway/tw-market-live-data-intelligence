"""Offline A1 scope, ledger, source binding and manifest verification."""
from pathlib import Path
import collections
import hashlib
import json
import subprocess

E=Path(__file__).resolve().parent;R=E.parents[4]
ENTRY='405bf16f5f82f4d37062d036ca6815eba27f7c4d'
FRONT=['PROJECT.md','HANDOFF.md','ROADMAP.md','docs/governance/INDEX.md','docs/governance/phase_l/PHASE_L_CURRENT_STATUS_AND_RECOVERY_INDEX_2026-10-14.md']
REPORT='docs/governance/phase_l/PHASE_L_L7_A1_DETERMINISTIC_REQUIRED_CI_AND_HISTORICAL_FAILURE_CLASSIFICATION_2026-10-24.md'
ALLOWED=FRONT+[REPORT,'config/test_execution_profiles.json','config/release_blocking_ci.v1.json','scripts/run_test_profile.py','scripts/phase_i_i2_a4_proof.py','scripts/deterministic_ci_guard.py','scripts/deterministic_ci_node_guard.cjs','scripts/run_deterministic_ci.py','tests/unit/test_l7_a1_deterministic_ci.py','tests/unit/test_m8r_06_03_localhost_vertical.py','tests/unit/test_m8r_06_human_browser_authorize_state.py','tests/unit/test_m8r_08c_r1_launcher_readiness.py','tests/unit/test_phase_h_imp_0_passive_v3_compatibility.py','tests/unit/test_phase_i_i2_a4_activation.py','docs/release/RELEASE_CHECKLIST.md','docs/contributor/TESTING_GUIDE.md']
def load(n):return json.loads((E/(n+'.json')).read_text(encoding='utf-8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(d):return json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def review():
 changed=set(git('diff','--name-only',ENTRY).splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
 prefix=E.relative_to(R).as_posix()+'/'
 assert all(p in ALLOWED or p.startswith(prefix) for p in changed),sorted(changed)
 assert not git('diff','--name-only',ENTRY,'--','server','schemas','docs/contracts','docs/data_capabilities','packaging_native','packaging_docker','requirements.txt','requirements-lock.txt','requirements-browser-e2e.txt','VERSION','.github/workflows')
 ledger=load('failure_adjudication_47');assert len(ledger['rows'])==len({x['nodeid'] for x in ledger['rows']})==47
 assert ledger['unclassified']==ledger['DECISION_REQUIRED']==0
 assert ledger['classification_counts']==dict(collections.Counter(x['A1_final_classification'] for x in ledger['rows']))
 assert all(x['A1_final_classification']!='DECISION_REQUIRED' for x in ledger['rows'])
 result=load('candidate_release_blocking_result');assert result['status']=='PASS' and result['junit_summary']['failed']==0 and result['unexpected_skips']==[] and result['guard_denials']==[]
 assert len(load('release_blocking_profile_members')['included_nodes'])==result['selected_nodes']
 assert load('release_blocking_profile_contract')==json.loads((R/'config/release_blocking_ci.v1.json').read_text(encoding='utf-8'))
 comparison=load('failed_node_comparison');assert comparison['new_candidate_failed_nodes']==comparison['release_blocking_failed_nodes']==[]
 assert len(comparison['resolved_nodes'])==32 and len(comparison['retained_historical_nodes'])==12
 for item in load('implementation_input_binding')['inputs']:
  assert sha((R/item['path']).read_bytes())==item['sha256'],item['path']
 for item in load('historical_diagnostic_coverage_map')['entries']:
  module=item['nodeid'].split('::')[0];assert sha((R/module).read_bytes())==item['original_module_sha256']
 assert len(load('a1_exit_criteria_matrix')['rows'])==29
 assert {x['id'] for x in load('a1_exit_criteria_matrix')['rows'] if x['status']=='PASS'}=={'L7-EXIT-01','L7-EXIT-02','L7-EXIT-03','L7-EXIT-27'}
 assert load('required_validators')['status']=='PASS'
 return {'status':'PASS','entry':ENTRY,'changed_paths':sorted(changed),'protected_product_public_dependency_VERSION_workflow_drift':0,'test_input_hashes_match':True,'historical_tests_preserved':True}
def verify_manifest():
 m=load('manifest');expected=m.pop('self_digest');assert sha(canonical(m))==expected
 for item in m['members']:
  p=(E/item['path']).resolve();assert p.is_relative_to(E.resolve())
  b=p.read_bytes();assert len(b)==item['bytes'] and sha(b)==item['sha256'],item['path']
 return {'status':'PASS','members':len(m['members']),'self_digest':expected}
if __name__=='__main__':print(json.dumps({'review':review(),'manifest':verify_manifest()},indent=2))
