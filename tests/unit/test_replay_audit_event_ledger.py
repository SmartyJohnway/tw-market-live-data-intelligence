from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_audit_event_types(): assert 'summary_completed' in load('docs/replay/replay_audit_event_schema.json')['event_types']
