from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_evidence_schema_fields(): assert 'hash_sha256' in load('docs/evidence/evidence_ledger_schema.json')['required_fields']
