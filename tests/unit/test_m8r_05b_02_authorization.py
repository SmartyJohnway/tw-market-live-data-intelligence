from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.validator import validate_execution_authorization
from scripts.m8r_05b_02.preflight import evaluate_authorization_preflight
import pytest

def plan(): return {'schema_version':'unified_market_evidence_orchestration_plan.v1','plan_id':'p','plan_hash':'a'*64,'plan_identity_scope_hash':'b'*64,'input_bindings':{'x':'y'},'operations':[{'operation_id':'o','operation_status':'executable_pending_approval','capability_id':'cap','executor_id':'exec','expected_evidence_contract':'e'}]}
def decision(**x):
 d={'decision':'approved','owner_identity_reference':'owner','owner_review_reference':'review','reviewed_at':'2026-07-23T00:00:00Z','issued_at':'2026-07-23T00:00:00Z','expires_at':'2026-07-23T01:00:00Z','approval_scope_mode':'whole_plan_executable_scope','approved_operation_ids':[],'approved_batch_group_ids':[],'approved_batch_membership':{},'approved_capability_ids':[],'approved_executor_ids':[],'expected_evidence_contracts':[],'single_use':True,'replay_policy':'deny_replay','maximum_use_count':1};d.update(x);return d
def test_build_validate_and_preflight():
 a=build_execution_authorization(plan(),decision());assert validate_execution_authorization(a,plan());assert evaluate_authorization_preflight(a,plan(),'2026-07-23T00:30:00Z')['status']=='authorized_for_future_controlled_consumption'
def test_identity_stable_and_reason_not_identity():
 a=build_execution_authorization(plan(),decision());b=build_execution_authorization(plan(),decision(decision_reason='note'));assert a['authorization_id']==b['authorization_id']
def test_expiry_fails_closed():
 with pytest.raises(Exception) as e:evaluate_authorization_preflight(build_execution_authorization(plan(),decision()),plan(),'2026-07-23T01:00:00Z')
 assert e.value.code=='authorization_expired'
def test_plan_drift_fails():
 a=build_execution_authorization(plan(),decision());q=plan();q['plan_hash']='x'
 with pytest.raises(Exception) as e:validate_execution_authorization(a,q)
 assert e.value.code=='plan_hash_mismatch'
