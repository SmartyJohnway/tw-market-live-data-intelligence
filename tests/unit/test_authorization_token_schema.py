from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_token_schema_fields(): assert 'no_production_write' in load('docs/authorization/authorization_token_schema.json')['required_fields']
