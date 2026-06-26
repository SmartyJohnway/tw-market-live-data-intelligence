from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_release_gate_current_local_only(): assert load('docs/release/release_gate_matrix.json')['current_allowed_level']=='local_only_fixture_only'
