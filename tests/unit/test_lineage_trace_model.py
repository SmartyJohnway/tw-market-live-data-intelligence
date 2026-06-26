from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_lineage_steps(): assert 'frontend readonly package' in load('docs/evidence/lineage_trace_model.json')['lineage_steps']
