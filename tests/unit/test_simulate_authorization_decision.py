from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.simulate_authorization_decision import simulate_decision
def test_simulator_blocks_forbidden_action(): assert not simulate_decision({'allowed_actions':['production_refresh'],'forbidden_actions':[]}, 'production_refresh')['allowed']
def test_simulator_allows_safe_action(): assert simulate_decision({'allowed_actions':['fixture_replay'],'forbidden_actions':[]}, 'fixture_replay')['allowed']
