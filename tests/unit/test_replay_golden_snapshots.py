from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_golden_summary(): assert load('tests/fixtures/replay_scenarios/golden_replay_summary.json')['fail']==0
