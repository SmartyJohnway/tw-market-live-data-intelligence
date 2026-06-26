from pathlib import Path
import json
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.json_schema_validation import validate_json_schema

def test_evidence_schema_fields():
 s=load('docs/evidence/evidence_ledger_schema.json'); assert 'hash_sha256' in s['required']; assert s['properties']['hash_sha256']['pattern']=='^[0-9a-f]{64}$'; assert s['properties']['forbidden_for_production']['const'] is True

def test_evidence_schema_is_valid_draft_2020_12():
 Draft202012Validator.check_schema(load('docs/evidence/evidence_ledger_schema.json'))

def test_real_evidence_entries_pass_schema_validation():
 schema=load('docs/evidence/evidence_ledger_schema.json')
 for entry in load('tests/fixtures/evidence/fixture_evidence_ledger.json')['evidence']:
  assert validate_json_schema(entry, schema) == []

def test_evidence_schema_rejects_bad_authority_date_extra_and_missing_fixture_caveat():
 schema=load('docs/evidence/evidence_ledger_schema.json')
 entry={'evidence_id':'x','evidence_type':'fixture','source_id':'Fixture_Synthetic','source_authority':'bad','source_risk_flags':['fixture_only'],'retrieval_mode':'fixture_only','fixture_path':'tests/fixtures/x.json','hash_sha256':'0'*64,'created_at':'not-a-date','produced_by':'test','promotion_status':'not_promoted','caveats':['not_production_current_state'],'forbidden_for_production':True,'notes':'x','extra':'bad'}
 codes={e['code'] for e in validate_json_schema(entry, schema)}
 assert {'schema_enum_mismatch','schema_format','schema_contains_missing','schema_additional_property'} <= codes
