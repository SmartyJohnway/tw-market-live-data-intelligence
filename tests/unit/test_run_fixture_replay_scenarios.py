from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.run_fixture_replay_scenarios import run_scenarios
def test_replay_valid_scenarios():
 r=run_scenarios(ROOT/'tests/fixtures/replay_scenarios/valid_replay_scenarios.json'); assert r['failed']==0; assert not r['production_current_state_claim']
