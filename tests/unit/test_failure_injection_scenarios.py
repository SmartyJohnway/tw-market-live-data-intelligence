from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_failure_injection_scenarios_present(): assert len(load('tests/fixtures/replay_scenarios/failure_injection_scenarios.json')['scenarios']) >= 7
