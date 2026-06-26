from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_risk_flags_present():
 flags={f['risk_flag'] for f in load('docs/source_registry/source_risk_flag_catalog.json')['risk_flags']}; assert 'unofficial_source_risk' in flags and 'fixture_only' in flags
