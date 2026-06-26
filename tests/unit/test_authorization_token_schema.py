from pathlib import Path
import json
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.json_schema_validation import validate_json_schema

def sample_token():
 return {'token_id':'x','authorization_level':'fixture_replay','authorized_by':'op','authorized_at':'2026-06-26T00:00:00Z','expires_at':'2099-01-01T00:00:00Z','allowed_actions':['fixture_replay'],'forbidden_actions':['production_refresh'],'allowed_sources':['Fixture_Synthetic'],'allowed_target_universe':{'mode':'fixture','full_market_scan':False},'output_path_policy':'safe_tmp_only','no_trading_signal':True,'no_realtime_guarantee':True,'no_production_write':True}

def test_token_schema_fields():
 s=load('docs/authorization/authorization_token_schema.json'); assert 'no_production_write' in s['required']; assert s['properties']['no_production_write']['const'] is True; assert 'production_refresh_authorized' in s['properties']['authorization_level']['enum']

def test_authorization_schema_is_valid_draft_2020_12():
 Draft202012Validator.check_schema(load('docs/authorization/authorization_token_schema.json'))

def test_authorization_token_sample_passes_schema_validation():
 assert validate_json_schema(sample_token(), load('docs/authorization/authorization_token_schema.json')) == []

def test_authorization_schema_rejects_extra_property_and_false_safety_flag_and_bad_datetime():
 schema=load('docs/authorization/authorization_token_schema.json')
 token=sample_token(); token['no_production_write']=False; token['authorized_at']='not-a-date'; token['extra']='bad'
 codes={e['code'] for e in validate_json_schema(token, schema)}
 assert {'schema_const_mismatch','schema_additional_property','schema_format'} <= codes
