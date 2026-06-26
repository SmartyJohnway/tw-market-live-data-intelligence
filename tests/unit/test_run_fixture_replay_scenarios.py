from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
from scripts.run_fixture_replay_scenarios import run_scenarios
def test_replay_valid_scenarios():
 r=run_scenarios(ROOT/'tests/fixtures/replay_scenarios/valid_replay_scenarios.json'); assert r['failed']==0; assert not r['production_current_state_claim']
def test_replay_checks_expected_caveats(tmp_path):
 data=json.loads((ROOT/'tests/fixtures/replay_scenarios/valid_replay_scenarios.json').read_text()); data['scenarios'][0]['expected_frontend_caveats']=['missing_caveat']
 p=tmp_path/'scenarios.json'; p.write_text(json.dumps(data))
 r=run_scenarios(p); assert r['failed'] > 0; assert not r['results'][0]['checks']['frontend_caveats']
def test_replay_audit_events_include_caveats_and_package():
 r=run_scenarios(ROOT/'tests/fixtures/replay_scenarios/valid_replay_scenarios.json'); events={e['event_type'] for e in r['audit_events']}
 assert {'frontend_package_built','caveat_emitted','summary_completed'} <= events
