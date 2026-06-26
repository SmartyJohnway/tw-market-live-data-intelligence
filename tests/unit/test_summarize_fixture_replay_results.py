from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.run_fixture_replay_scenarios import run_scenarios
from scripts.summarize_fixture_replay_results import summarize_replay_results
def test_summary_no_prod_claim(): assert summarize_replay_results(run_scenarios(ROOT/'tests/fixtures/replay_scenarios/valid_replay_scenarios.json'))['production_current_state_claim'] is False
