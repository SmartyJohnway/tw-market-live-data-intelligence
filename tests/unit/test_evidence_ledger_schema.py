from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.json_schema_validation import validate_json_schema_subset

def test_evidence_schema_fields():
 s=load('docs/evidence/evidence_ledger_schema.json'); assert 'hash_sha256' in s['required']; assert s['properties']['hash_sha256']['pattern']=='^[0-9a-f]{64}$'; assert s['properties']['forbidden_for_production']['const'] is True

def test_evidence_schema_rejects_bad_authority_date_extra_and_missing_fixture_caveat():
 schema=load('docs/evidence/evidence_ledger_schema.json')
 entry={'evidence_id':'x','evidence_type':'fixture','source_id':'Fixture_Synthetic','source_authority':'bad','source_risk_flags':['fixture_only'],'retrieval_mode':'fixture_only','fixture_path':'tests/fixtures/x.json','hash_sha256':'0'*64,'created_at':'not-a-date','produced_by':'test','promotion_status':'not_promoted','caveats':['not_production_current_state'],'forbidden_for_production':True,'notes':'x','extra':'bad'}
 codes={e['code'] for e in validate_json_schema_subset(entry, schema)}
 assert {'schema_enum_mismatch','schema_datetime_format','schema_contains_missing','schema_additional_property'} <= codes
