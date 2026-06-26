from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
import subprocess, sys
def test_m4_cli_help_safe():
 for s in ['repo_safety_preflight.py','validate_governance_policy_manifest.py','forbidden_behavior_scanner.py','validate_source_registry.py','build_fixture_hash_manifest.py','validate_authorization_ladder.py','simulate_authorization_decision.py','run_m4_local_validation.py','run_m4_fixture_replay.py','run_m4_readiness_check.py']:
  r=subprocess.run([sys.executable, str(ROOT/'scripts'/s), '--help'], text=True, capture_output=True)
  assert r.returncode == 0
  assert 'frontend/public' not in r.stdout.lower()
