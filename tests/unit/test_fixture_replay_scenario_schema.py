from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_replay_schema_fields(): assert 'scenario_id' in load('docs/replay/fixture_replay_scenario_schema.json')['required_fields']
