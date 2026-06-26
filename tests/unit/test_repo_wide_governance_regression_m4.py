from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.repo_safety_preflight import evaluate_repo_safety
def test_no_forbidden_injected_changed_paths(): assert not evaluate_repo_safety(ROOT, ['frontend/public/x'])['ok']
def test_no_env_committed(): assert not (ROOT/'.env').exists()
def test_workflow_no_probes_or_prod():
 y=(ROOT/'.github/workflows/non-network-ci.yml').read_text().lower(); assert 'run_all_probes' not in y; assert 'production refresh' not in y; assert 'broker' not in y
