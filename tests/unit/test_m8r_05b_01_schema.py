import copy
import json
from pathlib import Path
import jsonschema
import pytest

SCHEMA=json.loads(Path('schemas/unified_market_evidence_orchestration_plan.v1.schema.json').read_text())
V=jsonschema.Draft7Validator(SCHEMA)
H='a'*64

def valid_plan():
 op={'operation_id':'umeop-op-v1-'+'b'*20,'capability_id':'current_observation','canonical_target_ids':['TWSE:2330'],'market':'TWSE','security_types':['equity'],'parameters':{},'executor_id':'adapter','batch_group_id':'umeop-batch-v1-'+'c'*20,'operation_status':'executable_pending_approval','network_required':True,'capability_requires_execution_approval':True,'expected_evidence_contract':'bounded observation','blocking_reason_codes':[],'warnings':[],'executor_invocation_eligible':True}
 return {'schema_version':'unified_market_evidence_orchestration_plan.v1','plan_id':'umeop-v1-'+'d'*20,'plan_hash':H,'execution_authorized':False,'input_bindings':{'original_request_hash':H,'normalized_request_hash':H,'f3_validation_output_hash':H,'security_master_evidence_references':['fixture'], 'security_master_artifact_hashes':[H],'capability_catalog_hash':H,'planner_version':'m8r_05b_01.v1','routing_matrix_version':'v1','routing_matrix_hash':H,'handoff_contract_version':'v1','handoff_contract_hash':H},'planner_metadata':{'planning_timestamp':'2026-07-23T00:00:00Z','offline':True,'deterministic':True,'limit_source':'catalog.default_operation_limit'},'plan_status':'plan_ready','operations':[op],'batch_groups':[{'batch_group_id':op['batch_group_id'],'executor_id':'adapter','capability_id':'current_observation','market':'TWSE','operation_ids':[op['operation_id']],'network_required':True,'capability_requires_execution_approval':True}],'accounting':{'logical_operation_count':1,'batch_group_count':1,'executor_invocation_count':1,'network_request_estimate':1,'planned_evidence_bundle_count':1},'warnings':[],'blocked_operations':[],'omitted_optional_capabilities':[],'evidence_references':['fixture'],'package_approval_requirements':{'package_requires_owner_approval':True,'authorization_eligible':True,'approval_policy':'strictest_operation_controls_package','approval_reason_codes':['execution_approval_required']}}

def errors(value): return list(V.iter_errors(value))
def test_valid_plan_passes(): assert not errors(valid_plan())
def test_additional_property_rejected():
 p=valid_plan(); p['actual_evidence_bundle_count']=1; assert errors(p)
def test_execution_authorized_true_rejected():
 p=valid_plan(); p['execution_authorized']=True; assert errors(p)
def test_invalid_status_rejected():
 p=valid_plan(); p['plan_status']='authorized'; assert errors(p)
def test_plan_only_cannot_have_batch():
 p=valid_plan(); o=p['operations'][0]; o.update(operation_status='plan_only_not_executable',batch_group_id='umeop-batch-v1-'+'c'*20,network_required=False,executor_invocation_eligible=False); assert errors(p)
def test_blocked_requires_reason():
 p=valid_plan(); p['blocked_operations']=[{'capability_id':'session_status','canonical_target_ids':[],'market':'TWSE','parameters':{},'executor_id':None,'batch_group_id':None,'network_required':False,'expected_evidence_contract':'session','blocking_reason_codes':[],'executor_invocation_eligible':False}]; assert errors(p)
def test_omitted_optional_is_not_an_operation_status():
 p=valid_plan(); p['operations'][0]['operation_status']='omitted_optional'; assert errors(p)
