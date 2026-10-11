"""Closure-R1 acceptance/mutation tests. Production gaps must remain explicit."""
import copy,json
from pathlib import Path
import pytest
from tests.helpers.phase_j_closure_r1 import SCENARIOS,service,seed
from scripts import validate_phase_j_final_closure_r1 as v

@pytest.fixture(scope='module')
def records(tmp_path_factory):
    root=tmp_path_factory.mktemp('closure-r1')
    out=[]
    for sid in SCENARIOS:
        with service(sid,root/sid) as url:out.append(seed(sid,root/sid,url))
    return out

def row(records,sid):return copy.deepcopy(next(r for r in records if r['scenario_id']==sid))

@pytest.mark.parametrize('sid',SCENARIOS)
def test_production_scenario(sid,records):
    r=row(records,sid)
    if sid=='J1-21':
        with pytest.raises(ValueError,match='j1-21_evidence_state'):v.validate_scenario(r)
        native=r['result']['targets'][0]['evidence']['current_observation']['currentness']
        assert native['delay_seconds']==3198600
        assert native['freshness_assessment']=='current observation candidate; realtime status not guaranteed by M5K'
    else:assert v.validate_scenario(r)

def test_immutable_baselines():assert v.baseline()

def test_no_agent_or_stale_witness_fabricated(records):
    result=v.derive_overlay(records)
    assert result['disposition']=='PHASE_J_FINAL_CLOSURE_R1_HARD_BLOCK_EXISTING_PRODUCTION_SEAM_GAP'
    assert result['remaining_obligations']==2
    assert len(result['promotions'])==8
    assert not any(p['scenario_id']=='J1-21' or p['layer'] in ('real_agent','mcp','workbench') for p in result['promotions'])
    original=v.read(v.ROOT/v.historic.MATRIX)
    for old,new in zip(original['scenarios'],result['effective_matrix']['scenarios']):
        for layer in ('bounded_live','real_agent','workbench','mcp','fresh_install'):
            assert old['layers'][layer]==new['layers'][layer]

@pytest.mark.parametrize('mutation,code',[
 ('no_execution','NO_PRODUCTION_EXECUTION_WITNESS'),('fixture_only','NO_PRODUCTION_EXECUTION_WITNESS'),
 ('capability_only','NO_INDEPENDENT_EXECUTION_RECEIPT'),('wrong_scenario','SCENARIO_EXECUTION_IDENTITY_MISMATCH'),
 ('market_network','MARKET_NETWORK_NONZERO'),('no_audit','RESULT_AUDIT_HANDOFF_LINEAGE_MISMATCH'),
 ('source_substitution','EOD_SOURCE_SUBSTITUTED'),('fake_package','RESULT_SERVER_RECEIPT_MISMATCH')])
def test_scenario_witness_mutations(records,mutation,code):
    r=row(records,'J1-02')
    if mutation=='no_execution':r['executed_layers']=[]
    elif mutation=='fixture_only':r['executed_layers']=['contract_fixture','deterministic_unit']
    elif mutation=='capability_only':r['server_calls']=[]
    elif mutation=='wrong_scenario':r['request']['request_id']='closure-r1-j1-05'
    elif mutation=='market_network':r['market_network']['GET']=1
    elif mutation=='no_audit':r['audit']['result_id']='other'
    elif mutation=='source_substitution':r['result']['targets'][0]['evidence']['official_eod_reference']['source_id']='TWSE_OPENAPI'
    elif mutation=='fake_package':r['package']['result_status']='fake'
    # Mutations to Result must also update package; receipt hash then rejects
    # tampering before it can be laundered into semantic acceptance.
    with pytest.raises(ValueError):v.validate_scenario(r)

@pytest.mark.parametrize('sid,path,value',[('J1-04','not_realtime_guaranteed',False),('J1-19','source_timestamp','2026-10-08T06:00:00Z'),('J1-21','freshness_assessment','fresh')])
def test_currentness_and_timing_mutations_rejected(records,sid,path,value):
    r=row(records,sid);r['result']['targets'][0]['evidence']['current_observation']['currentness'][path]=value
    g=next(s for s in v.read(v.DOC/'PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json')['scenarios'] if s['scenario_id']==sid)
    assert v.evaluate_scenario(g,v.observe(r))

def test_eod_not_substituted_with_current_observation(records):
    r=row(records,'J1-05');r['request']['data_needs']=[{'type':'current_observation'}]
    with pytest.raises(ValueError,match='WRONG_REQUEST_EVIDENCE_FAMILY'):v.validate_scenario(r)

def test_duplicate_package_cannot_witness_another_scenario(records):
    r=copy.deepcopy(records);r[1]=copy.deepcopy(r[0]);r[1]['scenario_id']='J1-04'
    with pytest.raises(ValueError,match='DUPLICATE_SCENARIO_EXECUTION'):v.derive_overlay(r)

@pytest.mark.parametrize('mutation,code',[
 ('transcript_only','NO_INDEPENDENT_SERVER_RECEIPT'),('scripted','FAKE_OR_SCRIPTED_AGENT'),
 ('canned','FAKE_OR_SCRIPTED_AGENT'),('internal','AGENT_HOST_BOUNDARY_INVALID'),
 ('seventh_tool','MCP_COUNT_OR_NAME_DRIFT'),('wrong_scenario','AGENT_SCENARIO_NOT_EXECUTED'),
 ('lineage','AGENT_LINEAGE_MISSING'),('fake_server','AGENT_SERVER_RECEIPT_MISMATCH')])
def test_unproven_agent_receipts_fail(records,mutation,code):
    # Synthetic negative specimen, never a real-agent receipt or execution.
    r=row(records,'J1-02');operation={'scenario_id':'J1-02','tool_name':'market_read_result','result_id':r['result']['result_id'],'audit_package_id':r['audit']['audit_package_id'],'control_package_id':r['control_package_id'],'response_canonical_sha256':'not-an-independent-server-response'}
    receipt={'host_kind':'actual_ai_host','execution_kind':'current_unscripted_agent_session','boundary':'real_mcp_stdio_to_local_service','direct_internal_calls':False,'MCP_tools':v.MCP_NAMES,'market_network':{'GET':0,'HEAD':0,'POST':0},'secret_material_recorded':False,'scenario_ids':['J1-02'],'tool_call_count':2,'actual_tool_operations':[operation,operation|{'tool_name':'market_export_ai_handoff'}]}
    calls=[{'result_id':'wrong','response_canonical_sha256':'wrong'}]
    if mutation=='transcript_only':calls=[]
    elif mutation=='scripted':receipt['execution_kind']='scripted_sequence'
    elif mutation=='canned':receipt['host_kind']='canned_response'
    elif mutation=='internal':receipt['boundary']='python_internal_call'
    elif mutation=='seventh_tool':receipt['MCP_tools']=v.MCP_NAMES+['closure_tool']
    elif mutation=='wrong_scenario':receipt['scenario_ids']=['J1-03']
    elif mutation=='lineage':
        for op in receipt['actual_tool_operations']:op['audit_package_id']=None
    with pytest.raises(ValueError,match=code):v.validate_agent(receipt,records,calls)

def test_timing_unknown_dates_are_not_inferred(records):
    facts=v.observe(row(records,'J1-19'))['facts'];t=facts['typed_timing']
    assert t['observed_at']=='2026-10-08T05:59:00Z'
    assert t['official_source_date']=='2026-10-07'
    assert t['retrieved_at']=='2026-10-08T06:00:00Z'
    assert t['effective_date'] is None and t['publication_date'] is None
    assert facts['effective_date_distinct'] and facts['publication_date_distinct']

@pytest.mark.parametrize('name',['PHASE_J_J2_R1_EFFECTIVE_COVERAGE_MATRIX_V1.json','PHASE_J_FINAL_CLOSURE_GAP_ADJUDICATION_V1.json','PHASE_J_FINAL_CLOSURE_2026-10-11.json'])
def test_accepted_matrix_and_62_historical_blocker_cells_cannot_be_rewritten(monkeypatch,name):
    original=v.file_sha
    monkeypatch.setattr(v,'file_sha',lambda path:'f'*64 if Path(path).name==name else original(path))
    with pytest.raises(ValueError,match='DRIFT'):v.baseline()

@pytest.mark.parametrize('mutation',['promote_unexecuted_workbench','promote_unexecuted_real_agent','false_zero_obligations','stale_claimed_pass','erase_historical_status'])
def test_coverage_overlay_cannot_overpromote_or_claim_false_pass(records,mutation):
    out=v.derive_overlay(records)
    if mutation=='promote_unexecuted_workbench':out['promotions'][0]['layer']='workbench'
    elif mutation=='promote_unexecuted_real_agent':out['effective_matrix']['scenarios'][1]['layers']['real_agent']['status']='COVERED_EXISTING'
    elif mutation=='false_zero_obligations':out['remaining_obligations']=0
    elif mutation=='stale_claimed_pass':out['scenario_outcomes'][-1]['execution_witness_satisfied']=True
    elif mutation=='erase_historical_status':out['promotions'][0]['baseline_status']='COVERED_EXISTING'
    with pytest.raises(ValueError,match='LAUNDERING'):v.validate_overlay(out,records)

def test_eod_and_currentness_citation_lineage_remains_bound(records):
    for r in records:
        assert r['result']['result_id']==r['audit']['result_id']==r['handoff']['result_id']
        assert r['initial_execution_count']==len(r['request']['data_needs'])
        assert r['additional_execution_count']==0
        assert r['execution']['test_transport_active'] is True
        assert r['execution']['external_market_network_attempted'] is False


def test_effective_summary_recomputed_from_actual_cells(records):
    from collections import Counter
    d=v.derive_overlay(records);m=d['effective_matrix']
    counts=Counter(c['status'] for r in m['scenarios'] for c in r['layers'].values())
    assert m['coverage_summary']['status_counts']==dict(counts)
    assert counts['COVERED_EXISTING']==81 and counts['PLANNED']==82
    assert m['coverage_summary']['promoted_cell_count']==8
    assert m['baseline_binding']['sha256']=='8fe53871a764d66dcca6d3a5531d4801008c58f77e74ace7eede637f15436c3a'
