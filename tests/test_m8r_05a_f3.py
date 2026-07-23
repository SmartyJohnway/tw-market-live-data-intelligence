import copy,json
from pathlib import Path
import jsonschema
import pytest
from scripts.m8r_05a_f3.capability_validator import validate_capability
from scripts.m8r_05a_f3.request_intake import validate_unified_market_evidence_request
from scripts.m8r_05a_f3.request_intake import _catalog_valid
from scripts.m8r_05a_f3.security_master_loader import load_f3_verified_security_master
FIX=Path('tests/fixtures/m8r_05a_f3')
def artifacts():
 return load_f3_verified_security_master(FIX/'verified_security_master_snapshot.json',FIX/'verified_security_master_snapshot_manifest.json',allow_fixture_snapshot=True),json.loads(Path('docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json').read_text()),json.loads(Path('schemas/unified_market_evidence_request.v1.schema.json').read_text())
def req(targets=[{'input':'2330','market_hint':'TWSE'}], needs=[{'type':'identity','priority':'required'}]): return {'schema_version':'unified_market_evidence_request.v1','request_id':'f3-test','targets':targets,'data_needs':needs,'execution_mode':'preview'}
def run(r, schema=None): s,c,sc=artifacts(); return validate_unified_market_evidence_request(r,security_master=s,capability_catalog=c,request_schema=schema or sc,allow_fixture_snapshot=True)
def validate_output(out): jsonschema.Draft7Validator(json.loads(Path('schemas/unified_market_evidence_request_validation.v1.schema.json').read_text())).validate(out)
def test_valid_and_output_schema_and_copy_isolated():
 r=req(); out=run(r); assert out['validation_status']=='valid'; jsonschema.Draft7Validator(json.loads(Path('schemas/unified_market_evidence_request_validation.v1.schema.json').read_text())).validate(out); out['normalized_request']['targets'][0]['input']='changed'; assert r['targets'][0]['input']=='2330'
def test_request_schema_invalid_output_shape():
 out=run({'request_id':'x'}); assert out['request_schema_status']=='invalid'; validate_output(out)
def test_catalog_invalid_output_shape():
 s,c,sc=artifacts(); c['supported_markets']={}; out=validate_unified_market_evidence_request(req(),security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True); assert out['blocking_issues'][0]['code']=='CAPABILITY_CATALOG_INVALID'; validate_output(out)
def test_target_limit_exceeded_output_shape():
 s,c,sc=artifacts(); c['bounds']['hard_target_limit']=1; c['bounds']['default_target_limit']=1; out=validate_unified_market_evidence_request(req([{'input':'2330'},{'input':'6488'}]),security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True); assert out['blocking_issues'][0]['code']=='TARGET_LIMIT_EXCEEDED'; validate_output(out)
def test_schema_and_target_cases():
 assert run({'request_id':'x'})['request_schema_status']=='invalid'
 for target,status in [({'input':'2330','market_hint':'TPEX'},'market_mismatch'),({'input':'NOPE'},'not_found'),({'input':'重名測試'},'ambiguous'),({'input':'2881A'},'unsupported_security_type'),({'input':'9999'},'quarantined')]:
  out=run(req([target])); assert out['target_results'][0]['resolution_status']==status; validate_output(out)
 out=run(req([{'input':'2330'},{'input':'TWSE:2330'}])); assert out['target_results'][1]['resolution_status']=='duplicate'; validate_output(out)
def test_capability_and_parameter_cases():
 sc=artifacts()[2]; sc['properties']['data_needs']['items']['properties']['type']['enum'].append('bogus')
 optional=run(req(needs=[{'type':'bogus','priority':'optional'}]),sc); assert optional['warnings'] and optional['validation_status']=='valid'; validate_output(optional)
 required=run(req(needs=[{'type':'bogus','priority':'required'}]),sc); assert required['validation_status']=='unsupported' and required['capability_validation_status']=='unsupported'; validate_output(required)
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
 out=run(req(needs=[{'type':'recent_performance','priority':'required','parameters':{'lookback_trading_days':0}}])); assert out['validation_status']=='invalid' and out['request_schema_status']=='invalid'; validate_output(out)
def test_capability_invalid_parameters_output_shape_after_request_schema():
 s,c,sc=artifacts(); sc=copy.deepcopy(sc); sc['properties']['data_needs']['items']['allOf'][0]['then']['properties']['parameters']['properties']['lookback_trading_days']['minimum']=0
 out=validate_unified_market_evidence_request(req(needs=[{'type':'recent_performance','priority':'required','parameters':{'lookback_trading_days':0}}]),security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True)
 assert out['request_schema_status']=='valid' and out['capability_results'][0]['status']=='invalid_parameters' and out['capability_validation_status']=='invalid' and out['validation_status']=='invalid'; validate_output(out)
def test_requires_target_resolution_is_dependency_not_unsupported():
 out=run(req([{'input':'重名測試'}],[{'type':'identity','priority':'required'}])); assert out['target_validation_status']=='requires_clarification' and out['capability_results'][0]['status']=='requires_target_resolution' and out['capability_validation_status']=='valid' and out['validation_status']=='requires_clarification'; validate_output(out)
def test_catalog_default_limit_bool_rejected():
 c=artifacts()[1]; c['bounds']['default_target_limit']=True; assert not _catalog_valid(c)
def test_schema_recognized_but_catalog_unsupported_market():
 s,c,sc=artifacts(); c['supported_markets'].pop('TAIFEX')
 for cap in c['data_need_capabilities']:
  cap['supported_markets']=[m for m in cap['supported_markets'] if m!='TAIFEX']; cap['provisional_markets']=[m for m in cap['provisional_markets'] if m!='TAIFEX']
 r=req([{'input':'2330','market_hint':'TAIFEX'}]); out=validate_unified_market_evidence_request(r,security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True); assert out['target_results'][0]['resolution_status']=='unsupported_market' and out['validation_status']=='unsupported'; validate_output(out)
def test_allowed_with_caveat_resolves():
 s,c,sc=artifacts(); original=copy.deepcopy(s); s=copy.deepcopy(s); s.lookup['by_canonical']['TWSE:2330']['execution_eligibility']={'status':'allowed_with_caveat','reason_codes':['capture_observation_freshness_caveat']}; out=validate_unified_market_evidence_request(req(),security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True); assert out['target_results'][0]['resolution_status']=='resolved'; assert 'capture_observation_freshness_caveat' in out['target_results'][0]['reason_codes']; assert original.snapshot['records'][0]['execution_eligibility']['status']=='blocked'; validate_output(out)
def test_resolved_plus_ambiguous_requires_clarification():
 out=run(req([{'input':'2330'},{'input':'重名測試'}])); assert out['validation_status']=='requires_clarification'; validate_output(out)
def test_resolved_plus_unsupported_is_unsupported():
 out=run(req([{'input':'2330'},{'input':'2881A'}])); assert out['validation_status']=='unsupported'; validate_output(out)
def test_invalid_plus_unsupported_is_invalid():
 out=run(req([{'input':'NOPE'},{'input':'2881A'}])); assert out['validation_status']=='invalid'; validate_output(out)
def test_runtime_parameter_type_matrix():
 c=artifacts()[1]; cap=c['data_need_capabilities'][0]; cap['allowed_parameters']={'number':{'type':'number'},'text':{'type':'string'},'enabled':{'type':'boolean'},'choice':{'type':'string','enum':['a','b']}}
 assert validate_capability({'type':'identity','priority':'required','parameters':{'number':1.5,'text':'x','enabled':True,'choice':'a'}},0,catalog=c,target_resolved={'TWSE'})['status']=='contract_supported'
 assert validate_capability({'type':'identity','priority':'required','parameters':{'number':True}},0,catalog=c,target_resolved={'TWSE'})['status']=='invalid_parameters'
 assert validate_capability({'type':'identity','priority':'required','parameters':{'choice':'z'}},0,catalog=c,target_resolved={'TWSE'})['status']=='invalid_parameters'

def test_provisional_capability_full_pipeline_output_contract():
 s,c,sc=artifacts(); s=copy.deepcopy(s); record=s.lookup['by_canonical']['TWSE:2330']; record['classification']['market']='TAIFEX'; s.lookup['by_code'][('TAIFEX','2330')]=[record]
 out=validate_unified_market_evidence_request(req([{'input':'2330','market_hint':'TAIFEX'}],[{'type':'official_eod_reference','priority':'required'}]),security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True)
 assert out['request_schema_status']=='valid' and out['target_results'][0]['resolution_status']=='resolved' and out['capability_results'][0]['status']=='provisional' and out['capability_validation_status']=='valid' and out['validation_status']=='valid' and out['capability_results'][0]['known_limitations']; validate_output(out)
@pytest.mark.parametrize('priority,top,issues', [('required','unsupported','blocking_issues'),('optional','valid','warnings')], ids=['required','optional'])
def test_existing_capability_unsupported_on_resolved_market(priority,top,issues):
 s,c,sc=artifacts(); c=copy.deepcopy(c); cap=next(x for x in c['data_need_capabilities'] if x['capability_id']=='current_observation'); cap['supported_markets']=[]; cap['provisional_markets']=[]
 out=validate_unified_market_evidence_request(req(needs=[{'type':'current_observation','priority':priority}]),security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True)
 assert out['capability_results'][0]['status']=='unsupported' and out['validation_status']==top and out[issues]; validate_output(out)
def test_unsupported_instrument_family_maps_to_unsupported_security_type():
 s,c,sc=artifacts(); original=copy.deepcopy(s); s=copy.deepcopy(s); r=s.lookup['by_canonical']['TWSE:2330']; r['execution_eligibility']={'status':'blocked','reason_codes':['unsupported_instrument_family']}
 out=validate_unified_market_evidence_request(req(),security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True); t=out['target_results'][0]
 assert t['resolution_status']=='unsupported_security_type' and 'TARGET_SECURITY_TYPE_UNSUPPORTED' in t['reason_codes'] and 'unsupported_instrument_family' in t['reason_codes'] and out['validation_status']=='unsupported'; assert original.snapshot['records'][0]['execution_eligibility']['status']=='blocked'; validate_output(out)
@pytest.mark.parametrize('field', ['canonical_target_id','market'], ids=['missing-canonical-id','missing-market'])
def test_incomplete_selected_identity_is_quarantined(monkeypatch, field):
 import scripts.m8r_05a_f3.target_validator as tv
 base={'canonical_target_id':'TWSE:2330','identity':{'security_code':'2330','isin':'TW0002330008','security_name_zh':'台積電','security_name_en':'TSMC'},'classification':{'market':'TWSE','instrument_type':'common_share','instrument_family':'equity'},'execution_eligibility':{'status':'allowed','reason_codes':[]}}
 if field=='canonical_target_id': base.pop(field)
 else: base['classification'].pop(field)
 monkeypatch.setattr(tv,'resolve_verified_security_identity',lambda *a,**k:{'resolution_status':'resolved','selected':base,'candidates':[],'reason_codes':[]})
 s,c,sc=artifacts(); out=validate_unified_market_evidence_request(req(),security_master=s,capability_catalog=c,request_schema=sc,allow_fixture_snapshot=True)
 assert out['target_results'][0]['resolution_status']=='quarantined' and 'TARGET_IDENTITY_QUARANTINED' in out['target_results'][0]['reason_codes'] and out['validation_status']=='unsupported'; validate_output(out)
@pytest.mark.parametrize('rule,value,status', [
 pytest.param({'type':'number'},1,'contract_supported',id='number-int'), pytest.param({'type':'number'},'1','invalid_parameters',id='number-string'),
 pytest.param({'type':'string'},1,'invalid_parameters',id='string-integer'), pytest.param({'type':'boolean'},0,'invalid_parameters',id='boolean-zero'), pytest.param({'type':'boolean'},'true','invalid_parameters',id='boolean-string'),
 pytest.param({'type':'integer','minimum':1,'maximum':2},1,'contract_supported',id='bounds-minimum'), pytest.param({'type':'integer','minimum':1,'maximum':2},2,'contract_supported',id='bounds-maximum'), pytest.param({'type':'integer','minimum':1,'maximum':2},3,'invalid_parameters',id='bounds-above')])
def test_parameter_runtime_matrix_remaining(rule,value,status):
 c=artifacts()[1]; c['data_need_capabilities'][0]['allowed_parameters']={'value':rule}; result=validate_capability({'type':'identity','priority':'required','parameters':{'value':value}},0,catalog=c,target_resolved={'TWSE'}); assert result['status']==status
def test_required_parameter_missing_is_invalid_parameters():
 c=artifacts()[1]; c['data_need_capabilities'][0]['allowed_parameters']={'value':{'type':'integer','required':True}}; result=validate_capability({'type':'identity','priority':'required','parameters':{}},0,catalog=c,target_resolved={'TWSE'}); assert result['status']=='invalid_parameters' and 'missing_parameter:value' in result['reason_codes']
