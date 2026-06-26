from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_fixture_ledger_forbidden_for_production(): assert all(e['forbidden_for_production'] and e['retrieval_mode']=='fixture_only' for e in load('tests/fixtures/evidence/fixture_evidence_ledger.json')['evidence'])
