from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_source_schema_fields(): assert 'source_id' in load('docs/source_registry/source_contract_schema.json')['required_source_fields']
