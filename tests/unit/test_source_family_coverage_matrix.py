from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_coverage_production_false(): assert all(not v['production_allowed'] for v in load('docs/source_registry/source_family_coverage_matrix.json')['families'].values())
