from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_evidence_schema_fields():
 s=load('docs/evidence/evidence_ledger_schema.json'); assert 'hash_sha256' in s['required']; assert s['properties']['hash_sha256']['pattern']=='^[0-9a-f]{64}$'; assert s['properties']['forbidden_for_production']['const'] is True
