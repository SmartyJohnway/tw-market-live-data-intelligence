import copy,pytest
from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding,validate_consumption_binding,evaluate_consumption_preflight
from scripts.m8r_05b_02.models import AuthorizationError
from tests.unit.test_m8r_05b_02_authorization import plan,decision
def fixture():
 a=build_execution_authorization(plan(),decision());return a,plan(),build_consumption_binding(a)
def state(a,b): return {'authorization_id':a['authorization_id'],'authorization_hash':a['authorization_hash'],'consumption_binding_id':b['consumption_binding_id'],'consumption_binding_hash':b['consumption_binding_hash'],'registry_contract_version':'m8r_05b_03.v1','state':'unused'}
def test_valid_schema_binding():
 a,p,b=fixture();assert validate_consumption_binding(b,a,p)
def test_deterministic_binding():
 a,_,_=fixture();assert build_consumption_binding(a)==build_consumption_binding(a)
@pytest.mark.parametrize('field,code',[('consumption_binding_hash','consumption_binding_hash_mismatch'),('consumption_binding_id','consumption_binding_id_mismatch'),('authorization_id','authorization_id_mismatch'),('authorization_hash','authorization_hash_mismatch'),('plan_id','plan_id_mismatch'),('plan_hash','plan_hash_mismatch'),('scope_hash','scope_hash_mismatch'),('approved_operation_ids','approved_operation_set_mismatch'),('approved_operation_bindings','approved_operation_binding_mismatch'),('approved_batch_group_ids','approved_batch_set_mismatch'),('approved_batch_membership','batch_membership_mismatch'),('approved_capability_ids','capability_binding_mismatch'),('approved_executor_ids','executor_binding_mismatch'),('expected_evidence_contracts','expected_evidence_contract_mismatch'),('single_use','single_use_required'),('replay_policy','replay_policy_invalid'),('maximum_use_count','maximum_use_count_invalid'),('consumption_registry_contract','registry_contract_mismatch')])
def test_binding_field_drift(field,code):
 a,p,b=fixture();b=copy.deepcopy(b); alternatives={'consumption_binding_hash':'0'*64,'consumption_binding_id':'umeacb-v1-'+'0'*20,'authorization_id':'umea-v1-'+'0'*20,'authorization_hash':'0'*64,'plan_hash':'0'*64,'scope_hash':'0'*64,'approved_batch_group_ids':['umeop-batch-v1-'+'0'*20],'approved_batch_membership':{'umeop-batch-v1-'+'0'*20:['umeop-op-v1-'+'0'*20]},'single_use':False,'replay_policy':'allow_replay','maximum_use_count':2,'consumption_registry_contract':'m8r_05b_03.v2'}; b[field]=alternatives.get(field, [] if isinstance(b[field],list) else 'x')
 with pytest.raises(AuthorizationError) as e: validate_consumption_binding(b,a,p)
 assert e.value.code==code
@pytest.mark.parametrize('kind,code',[('none','consumption_record_missing'),('list','consumption_state_ambiguous'),('extra','consumption_state_schema_invalid'),('bad_hash','consumption_state_schema_invalid'),('wrong_auth','consumption_authorization_mismatch'),('wrong_binding','consumption_binding_state_mismatch'),('registry','registry_contract_mismatch'),('consumed','authorization_already_consumed'),('unknown','consumption_state_schema_invalid')])
def test_state_contract(kind,code):
 a,p,b=fixture();x=state(a,b)
 if kind=='none': x=None
 elif kind=='list': x=[x,x]
 elif kind=='extra': x['extra']=1
 elif kind=='bad_hash': x['authorization_hash']='x'
 elif kind=='wrong_auth': x['authorization_id']='umea-v1-'+'0'*20
 elif kind=='wrong_binding': x['consumption_binding_id']='umeacb-v1-'+'0'*20
 elif kind=='registry': x['registry_contract_version']='x'
 elif kind=='consumed': x['state']='consumed'
 elif kind=='unknown': x['state']='other'
 with pytest.raises(AuthorizationError) as e:evaluate_consumption_preflight(a,p,b,'2026-07-23T00:30:00Z',x)
 assert e.value.code==code
