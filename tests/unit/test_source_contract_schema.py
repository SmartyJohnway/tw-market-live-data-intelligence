from pathlib import Path
import json
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.validate_source_registry import validate_source_registry

def test_source_schema_fields():
 s=load('docs/source_registry/source_contract_schema.json'); assert 'source_id' in s['required']; assert s['additionalProperties'] is False; assert s['properties']['production_current_state_allowed']['const'] is False

def test_source_schema_is_valid_draft_2020_12():
 Draft202012Validator.check_schema(load('docs/source_registry/source_contract_schema.json'))

def test_real_registry_entries_pass_source_schema_validation():
 assert validate_source_registry(load('docs/source_registry/source_authority_registry.json'), load('docs/source_registry/source_risk_flag_catalog.json'), load('docs/source_registry/source_contract_schema.json'), load('docs/source_registry/source_family_coverage_matrix.json')) == []
