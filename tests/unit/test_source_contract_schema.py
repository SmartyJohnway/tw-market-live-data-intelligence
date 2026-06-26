from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_source_schema_fields():
 s=load('docs/source_registry/source_contract_schema.json'); assert 'source_id' in s['required']; assert s['additionalProperties'] is False; assert s['properties']['production_current_state_allowed']['const'] is False
