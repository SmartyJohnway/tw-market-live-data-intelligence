from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_registry_entries():
 ids={s['source_id'] for s in load('docs/source_registry/source_authority_registry.json')['sources']}; assert {'TWSE_OpenAPI','TPEx_OpenAPI','TWSE_MIS','Yahoo_Finance','Fixture_Synthetic','Manual_Operator_Input'} <= ids
def test_registry_no_production_allowed(): assert all(s['production_current_state_allowed'] is False for s in load('docs/source_registry/source_authority_registry.json')['sources'])
