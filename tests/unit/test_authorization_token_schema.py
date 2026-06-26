from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_token_schema_fields():
 s=load('docs/authorization/authorization_token_schema.json'); assert 'no_production_write' in s['required']; assert s['properties']['no_production_write']['const'] is True; assert 'production_refresh_authorized' in s['properties']['authorization_level']['enum']
