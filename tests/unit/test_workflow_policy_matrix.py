from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_workflow_policy_matrix_and_ci_local_only():
 m=load('docs/governance/workflow_policy_matrix.json'); y=(ROOT/'.github/workflows/non-network-ci.yml').read_text(); assert 'run_test_profile.py' in y; assert 'run_all_probes.py' not in y; assert 'live probe' not in y.lower()
