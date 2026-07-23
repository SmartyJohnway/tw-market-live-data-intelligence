import copy,json
from pathlib import Path
import jsonschema
from scripts.m8r_05a_f3.capability_validator import validate_capability
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
from scripts.m8r_05a_f3.request_intake import _catalog_valid
from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
FIX=Path('tests/fixtures/m8r_05a_f3')
def artifacts():
 return load_f3_verified_security_master(FIX/'verified_security_master_snapshot.json',FIX/'verified_security_master_snapshot_manifest.json',allow_fixture_snapshot=True),json.loads(Path('docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json').read_text()),json.loads(Path('schemas/unified_market_evidence_request.v1.schema.json').read_text())
def req(targets=[{'input':'2330','market_hint':'TWSE'}], needs=[{'type':'identity','priority':'required'}]): return {'schema_version':'unified_market_evidence_request.v1','request_id':'f3-test','targets':targets,'data_needs':needs,'execution_mode':'preview'}
def run(r, schema=None): s,c,sc=artifacts(); return validate_unified_market_evidence_request(r,security_master=s,capability_catalog=c,request_schema=schema or sc,allow_fixture_snapshot=True)
def test_valid_and_output_schema_and_copy_isolated():
 r=req(); out=run(r); assert out['validation_status']=='valid'; jsonschema.Draft7Validator(json.loads(Path('schemas/unified_market_evidence_request_validation.v1.schema.json').read_text())).validate(out); out['normalized_request']['targets'][0]['input']='changed'; assert r['targets'][0]['input']=='2330'
def test_schema_and_target_cases():
 assert run({'request_id':'x'})['request_schema_status']=='invalid'
 assert run(req([{'input':'2330','market_hint':'TPEX'}]))['target_results'][0]['resolution_status']=='market_mismatch'
 assert run(req([{'input':'NOPE'}]))['target_results'][0]['resolution_status']=='not_found'
 assert run(req([{'input':'重名測試'}]))['target_results'][0]['resolution_status']=='ambiguous'
 assert run(req([{'input':'2330'},{'input':'TWSE:2330'}]))['target_results'][1]['resolution_status']=='duplicate'
 assert run(req([{'input':'2881A'}]))['target_results'][0]['resolution_status']=='unsupported_security_type'
 assert run(req([{'input':'9999'}]))['target_results'][0]['resolution_status']=='quarantined'
def test_capability_and_parameter_cases():
 sc=artifacts()[2]; sc['properties']['data_needs']['items']['properties']['type']['enum'].append('bogus')
 assert run(req(needs=[{'type':'bogus','priority':'optional'}]),sc)['warnings']
 assert run(req(needs=[{'type':'bogus','priority':'required'}]),sc)['validation_status']=='unsupported'
 catalog=artifacts()[1]
 assert validate_capability({'type':'recent_performance','priority':'required','parameters':{}},0,catalog=catalog,target_resolved={'TWSE'})['status']=='contract_supported'
 for value in ('20',None,True,1.5,[],{}): assert validate_capability({'type':'recent_performance','priority':'required','parameters':{'lookback_trading_days':value}},0,catalog=catalog,target_resolved={'TWSE'})['status']=='invalid_parameters'
 assert validate_capability({'type':'recent_performance','priority':'required','parameters':{'unknown':1}},0,catalog=catalog,target_resolved={'TWSE'})['status']=='invalid_parameters'
 assert validate_capability({'type':'recent_performance','priority':'required','parameters':{'lookback_trading_days':0}},0,catalog=catalog,target_resolved={'TWSE'})['status']=='invalid_parameters'
 assert validate_capability({'type':'recent_performance','priority':'required','parameters':{'lookback_trading_days':20}},0,catalog=catalog,target_resolved={'TWSE'})['status']=='contract_supported'
def test_catalog_missing_capability_id_fails_closed():
 c=artifacts()[1]; c['data_need_capabilities']=[{}]; assert not _catalog_valid(c)
def test_catalog_empty_markets_fails_closed():
 c=artifacts()[1]; c['supported_markets']={}; assert not _catalog_valid(c)
def test_catalog_non_object_capability_fails_closed():
 c=artifacts()[1]; c['data_need_capabilities']=[None]; assert not _catalog_valid(c)
def test_catalog_invalid_parameter_rule_fails_closed():
 c=artifacts()[1]; c['data_need_capabilities'][0]['allowed_parameters']={'':{'type':'integer','minimum':1.5}}; assert not _catalog_valid(c)
def test_catalog_non_numeric_parameter_rule_rejects_bounds():
 c=artifacts()[1]; c['data_need_capabilities'][0]['allowed_parameters']={'enabled':{'type':'boolean','minimum':1}}; assert not _catalog_valid(c)
def test_invalid_parameters_make_top_level_invalid():
 assert run(req(needs=[{'type':'recent_performance','priority':'required','parameters':{'lookback_trading_days':0}}]))['validation_status']=='invalid'
def test_catalog_default_limit_bool_rejected():
 c=artifacts()[1]; c['bounds']['default_target_limit']=True; assert not _catalog_valid(c)
def test_schema_recognized_but_catalog_unsupported_market():
 s,c,sc=artifacts(); c['supported_markets'].pop('TAIFEX')
 for cap in c['data_need_capabilities']:
  cap['supported_markets']=[m for m in cap['supported_markets'] if m!='TAIFEX']; cap['provisional_markets']=[m for m in cap['provisional_markets'] if m!='TAIFEX']
 r=req([{'input':'2330','market_hint':'TAIFEX'}]); out=validate_unified_market_evidence_request(r,security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True); assert out['target_results'][0]['resolution_status']=='unsupported_market' and out['validation_status']=='unsupported'
def test_allowed_with_caveat_resolves():
 s,c,sc=artifacts(); original=copy.deepcopy(s); s=copy.deepcopy(s); s.lookup['by_canonical']['TWSE:2330']['execution_eligibility']={'status':'allowed_with_caveat','reason_codes':['capture_observation_freshness_caveat']}; out=validate_unified_market_evidence_request(req(),security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True); assert out['target_results'][0]['resolution_status']=='resolved'; assert 'capture_observation_freshness_caveat' in out['target_results'][0]['reason_codes']; assert original.snapshot['records'][0]['execution_eligibility']['status']=='blocked'
def test_mixed_target_precedence():
 assert run(req([{'input':'2330'},{'input':'重名測試'}]))['validation_status']=='requires_clarification'
 assert run(req([{'input':'2330'},{'input':'2881A'}]))['validation_status']=='unsupported'
 assert run(req([{'input':'NOPE'},{'input':'2881A'}]))['validation_status']=='invalid'
