from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.validate_governance_policy_manifest import validate_manifest
def test_manifest_valid(): assert validate_manifest(load('docs/governance/governance_policy_manifest.json')) == []
def test_manifest_required_boundaries():
 m=load('docs/governance/governance_policy_manifest.json'); assert 'frontend/public/' in m['forbidden_paths']; assert 'trading_signal' in m['forbidden_behaviors']
