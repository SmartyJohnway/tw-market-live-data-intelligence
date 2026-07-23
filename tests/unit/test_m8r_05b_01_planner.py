import copy,json
from pathlib import Path
import jsonschema,pytest
from scripts.m8r_05b_01.canonical import sha256_json
from scripts.m8r_05b_01.models import PLANNER_VERSION,PlanningError
from scripts.m8r_05b_01.planner import build_plan,ROUTING_VERSION,HANDOFF_VERSION
ROOT=Path('.')
CAT=json.loads((ROOT/'docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json').read_text())
ROUTE=json.loads((ROOT/'docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.json').read_text())
HAND=json.loads((ROOT/'docs/data_capabilities/m8r_05b_orchestration_handoff_contract.json').read_text())
INV=json.loads((ROOT/'docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json').read_text())
SCHEMA=json.loads((ROOT/'schemas/unified_market_evidence_orchestration_plan.v1.schema.json').read_text())

def bindings(v): return {'original_request_hash':'1'*64,'normalized_request_hash':'2'*64,'f3_validation_output_hash':sha256_json(v),'security_master_evidence_references':['master-b','master-a'],'security_master_artifact_hashes':['b'*64,'a'*64],'capability_catalog_hash':sha256_json(CAT),'planner_version':PLANNER_VERSION,'routing_matrix_version':ROUTING_VERSION,'routing_matrix_hash':sha256_json(ROUTE),'handoff_contract_version':HANDOFF_VERSION,'handoff_contract_hash':sha256_json(HAND)}
def validation(cap='current_observation',priority='required',status='runtime_executable',market='TWSE',targets=None):
 targets=targets or ['TWSE:2330']
 trs=[{'target_index':i,'original_input':t,'resolution_requirement':'exact','resolution_status':'resolved','canonical_identity':{'canonical_target_id':t,'market':market,'security_code':t.split(':')[1],'isin':'x','security_name_zh':'x','security_name_en':'x','instrument_type':'equity','instrument_family':'equity'}} for i,t in enumerate(targets)]
 return {'schema_version':'unified_market_evidence_request_validation.v1','request_id':'fixture','validation_status':'valid','request_schema_status':'valid','target_validation_status':'valid','capability_validation_status':'valid','normalized_request':{'data_needs':[{'type':cap,'priority':priority,'parameters':{}}]},'target_results':trs,'capability_results':[{'data_need_index':0,'capability_id':cap,'priority':priority,'status':status}],'blocking_issues':[],'warnings':[],'limits':{'target_count':len(trs),'hard_target_limit':50,'operation_count_computed':False,'operation_count':0,'orchestrator_projection_required':True},'validation_metadata':{'offline':True,'deterministic':True,'allow_fixture_snapshot':True}}
def plan(v,**kw): return build_plan(v,capability_catalog=kw.get('catalog',CAT),routing_matrix=kw.get('routing',ROUTE),handoff_contract=HAND,executor_disposition=kw.get('inventory',INV),input_bindings=kw.get('bindings',bindings(v)),planning_timestamp=kw.get('timestamp','2026-07-23T00:00:00Z'))
def test_resolved_plan_deterministic_schema_and_no_mutation():
 v=validation(); original=copy.deepcopy(v); a=plan(v); b=plan(v,timestamp='2026-07-24T00:00:00Z')
 assert v==original and a['plan_hash']==b['plan_hash'] and a['plan_id']==b['plan_id']
 assert a['operations'][0]['operation_status']=='executable_pending_approval' and a['execution_authorized'] is False
 jsonschema.Draft7Validator(SCHEMA,format_checker=jsonschema.FormatChecker()).validate(a)
def test_multitarget_batches_and_accounting():
 p=plan(validation(targets=['TWSE:2330','TWSE:6488'])); assert len(p['operations'])==2 and p['accounting']=={'logical_operation_count':2,'batch_group_count':1,'executor_invocation_count':1,'network_request_estimate':1,'planned_evidence_bundle_count':1}
def test_plan_only_and_provisional_never_batch():
 for v in (validation('recent_performance',status='contract_supported'),validation('official_eod_reference',status='provisional',market='TAIFEX',targets=['TAIFEX:TX'])):
  p=plan(v); assert p['plan_status']=='plan_only_not_executable' and not p['batch_groups'] and p['accounting']['planned_evidence_bundle_count']==0
def test_session_optional_omitted_required_blocked():
 optional=plan(validation('session_status',priority='optional')); required=plan(validation('session_status'))
 assert optional['plan_status']=='plan_ready_with_warnings' and optional['omitted_optional_capabilities'] and not optional['operations']
 assert required['plan_status']=='blocked' and required['blocked_operations']
def test_hash_pairing_and_invariants_fail_closed():
 v=validation(); b=bindings(v); b['security_master_artifact_hashes']=['a'*64]
 with pytest.raises(PlanningError,match='target_binding_invalid'): plan(v,bindings=b)
 b=bindings(v); b['capability_catalog_hash']='0'*64
 with pytest.raises(PlanningError,match='capability_catalog_hash_mismatch'): plan(v,bindings=b)
 v['limits']['operation_count']=1
 with pytest.raises(PlanningError,match='f3_invariant_mismatch'): plan(v)
def test_selected_executor_is_verified():
 v=validation(); inventory=copy.deepcopy(INV)
 next(x for x in inventory['surfaces'] if x['surface_id']=='m8r_03d_watchlist_controlled_executor_adapter')['reusable_for_05b']=False
 with pytest.raises(PlanningError,match='selected_executor_invalid'): plan(v,inventory=inventory)
def test_hard_operation_limit_fails_closed():
 c=copy.deepcopy(CAT); c['bounds']['hard_operation_limit']=1; v=validation(targets=['TWSE:2330','TWSE:6488']); b=bindings(v); b['capability_catalog_hash']=sha256_json(c)
 with pytest.raises(PlanningError,match='operation_limit_exceeded'): plan(v,catalog=c,bindings=b)
def test_market_and_security_contracts_required_block_optional_omit():
 v=validation('current_observation',market='TAIFEX',targets=['TAIFEX:TX']); assert plan(v)['plan_status']=='blocked'
 optional=plan(validation('current_observation',priority='optional',market='TAIFEX',targets=['TAIFEX:TX'])); assert optional['omitted_optional_capabilities']
 v=validation('current_observation'); v['target_results'][0]['canonical_identity']['instrument_family']='etf'; assert plan(v)['plan_status']=='blocked'
def test_runtime_eod_taifex_is_provisional_plan_only():
 p=plan(validation('official_eod_reference',market='TAIFEX',targets=['TAIFEX:TX'])); assert p['plan_status']=='plan_only_not_executable' and not p['batch_groups']
def test_batching_scope_contracts_and_dependencies():
 r=copy.deepcopy(ROUTE); next(x for x in r['routes'] if x['capability_id']=='current_observation')['batching_scope']='none'; v=validation(targets=['TWSE:2330','TWSE:6488']); b=bindings(v); b['routing_matrix_hash']=sha256_json(r); assert plan(v,routing=r,bindings=b)['accounting']['batch_group_count']==2
 r=copy.deepcopy(ROUTE); next(x for x in r['routes'] if x['capability_id']=='current_observation')['batching_scope']='bogus'; b=bindings(v); b['routing_matrix_hash']=sha256_json(r)
 with pytest.raises(PlanningError,match='batch_contract_invalid'): plan(v,routing=r,bindings=b)
 # source_currentness receives the primary observation ID, not an array position.
 v=validation(); v['normalized_request']['data_needs'].append({'type':'source_currentness','priority':'required','parameters':{}}); v['capability_results'].append({'data_need_index':1,'capability_id':'source_currentness','priority':'required','status':'contract_supported'}); p=plan(v); derived=next(x for x in p['operations'] if x['capability_id']=='source_currentness'); primary=next(x for x in p['operations'] if x['capability_id']=='current_observation'); assert derived['dependency_operation_ids']==[primary['operation_id']] and derived['batch_group_id'] is None
def test_inventory_malformed_and_duplicate_fail_closed():
 v=validation(); bad=copy.deepcopy(INV); bad['surfaces'].append(dict(bad['surfaces'][0]))
 with pytest.raises(PlanningError,match='inventory_surface_id_duplicate'): plan(v,inventory=bad)
 bad=copy.deepcopy(INV); bad['surfaces'][0]=None
 with pytest.raises(PlanningError,match='inventory_surface_not_object'): plan(v,inventory=bad)
