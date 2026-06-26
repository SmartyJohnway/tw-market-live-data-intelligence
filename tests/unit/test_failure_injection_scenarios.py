from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.run_fixture_replay_scenarios import run_scenarios

def test_failure_injection_scenarios_present():
    assert len(load('tests/fixtures/replay_scenarios/failure_injection_scenarios.json')['scenarios']) >= 7

def test_failure_injection_scenarios_execute_and_pass_expected_rejections():
    result = run_scenarios(ROOT / 'tests/fixtures/replay_scenarios/failure_injection_scenarios.json')
    assert result['failed'] == 0
    assert any(r['validation_status'] == 'invalid' for r in result['results'])
    assert {'staging_rejected', 'summary_completed'} <= {e['event_type'] for e in result['audit_events']}
