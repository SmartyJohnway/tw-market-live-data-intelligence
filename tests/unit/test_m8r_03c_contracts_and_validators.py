import json, shutil
from pathlib import Path
import pytest
from scripts.m8r_03c_contracts import *
from scripts.m8r_03c_conversation_contract_validator import *
FIX=Path('tests/fixtures/m8r_03c')
def load(n): return json.loads((FIX/n).read_text())
def test_contract_loader_and_enums_sync():
    c=load_conversation_contract(); e=load_evidence_bundle_contract(); m=compile_contract_metadata()
    assert set(m['scope_modes'])==set(c['scope_modes']['enum'])
    assert set(m['time_modes'])==set(c['time_modes']['enum'])
    assert 'calculated' in m['calculation_statuses'] and 'usable' in m['coverage_states']
def test_loader_fail_closed(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{"schema_version":"bad","conversation_intent":{}}')
    with pytest.raises(M8R03CContractError) as e: load_conversation_contract(p)
    assert e.value.code=='unsupported_contract_schema_version'
    d=load_conversation_contract(); d.pop('conversation_intent'); p.write_text(json.dumps(d))
    with pytest.raises(M8R03CContractError) as e: load_conversation_contract(p)
    assert e.value.code=='required_contract_section_missing'
    d=load_conversation_contract(); d['conversation_intent']['fields'].append(d['conversation_intent']['fields'][0]); p.write_text(json.dumps(d))
    with pytest.raises(M8R03CContractError) as e: load_conversation_contract(p)
    assert e.value.code=='duplicate_field_definition'
def test_valid_intent_and_unknown_map_policy():
    r=load('snapshot_request.json'); r['conversation_intent']['explicit_user_constraints']['freeform']='ok'
    out=validate_conversation_intent(r['conversation_intent']); assert out['explicit_user_constraints']['freeform']=='ok'
    bad=dict(r['conversation_intent'], extra=1)
    with pytest.raises(M8R03CValidationError) as e: validate_conversation_intent(bad)
    assert e.value.code=='unknown_field_rejected'
def test_intent_invariants():
    r=load('snapshot_request.json')['conversation_intent']
    bad=json.loads(json.dumps(r)); bad['scope_modes'].append('watchlist')
    with pytest.raises(M8R03CValidationError): validate_conversation_intent(bad)
    bad=json.loads(json.dumps(r)); bad['scope_modes']=['bad']
    with pytest.raises(M8R03CValidationError): validate_conversation_intent(bad)
    bad=json.loads(json.dumps(r)); bad['time_scope']={'mode':'explicit_range','lookback_trading_days':None,'explicit_range':{'range_type':'calendar_dates','start_date':'2026-07-02','end_date':'2026-07-01','user_text':'7/2到7/1'}}
    with pytest.raises(M8R03CValidationError): validate_conversation_intent(bad)
    bad=json.loads(json.dumps(r)); bad['clarification_required']=True; bad['clarification_reason']=None
    with pytest.raises(M8R03CValidationError): validate_conversation_intent(bad)
    bad=json.loads(json.dumps(r)); bad['scope_modes']=['watchlist_subset']
    with pytest.raises(M8R03CValidationError) as e: validate_conversation_intent(bad)
    assert e.value.code=='watchlist_reference_required'
def test_evidence_request_invariants():
    r=load('snapshot_request.json'); assert validate_evidence_request(r)['request_id']=='m8r03c-snapshot'
    bad=json.loads(json.dumps(r)); bad['original_user_text']='x'
    with pytest.raises(M8R03CValidationError) as e: validate_evidence_request(bad)
    assert e.value.code=='bundle_request_mismatch'
    bad=json.loads(json.dumps(r)); bad['clarification_required']=True
    with pytest.raises(M8R03CValidationError): validate_evidence_request(bad)
    bad=json.loads(json.dumps(r)); bad['persistent_watchlist_reference']['enabled_target_ids'].append('TWSE:2330')
    with pytest.raises(M8R03CValidationError): validate_evidence_request(bad)
    bad=json.loads(json.dumps(r)); bad['dynamic_entity_requests']=[{'input_reference':'AI','entity_role':'theme','selection_reason':'user','priority':'useful','requested_time_range':r['conversation_intent']['time_scope'],'requested_source_timing_class':'official_eod','fallback_behavior':'record_missing','persistent_watchlist_mutation':True}]
    with pytest.raises(M8R03CValidationError) as e: validate_evidence_request(bad)
    assert e.value.code=='dynamic_watchlist_mutation_forbidden'
    bad=json.loads(json.dumps(r)); bad['required_evidence'][0]['priority']='optional'
    with pytest.raises(M8R03CValidationError): validate_evidence_request(bad)
    for flag in ('network_allowed','polling','scheduler'):
        bad=json.loads(json.dumps(r)); bad['execution_policy'][flag]=True
        with pytest.raises(M8R03CValidationError): validate_evidence_request(bad)
