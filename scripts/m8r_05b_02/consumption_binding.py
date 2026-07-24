"""Pure future-consumption requirements; no registry or state mutation."""
import json
import re
from pathlib import Path
from jsonschema import Draft202012Validator
from .canonical import sha256_json
from .models import AuthorizationError
from .preflight import evaluate_authorization_preflight
from .validator import validate_execution_authorization
_FIELDS=('schema_version','consumption_binding_identity_scope','consumption_binding_hash','consumption_binding_id','authorization_id','authorization_hash','plan_id','plan_hash','scope_hash','approved_operation_ids','approved_operation_bindings','approved_batch_group_ids','approved_batch_membership','approved_capability_ids','approved_executor_ids','expected_evidence_contracts','single_use','replay_policy','maximum_use_count','consumption_registry_contract','expected_unused_state')
_CODES={'approved_operation_ids':'approved_operation_set_mismatch','approved_operation_bindings':'approved_operation_binding_mismatch','approved_batch_group_ids':'approved_batch_set_mismatch','approved_batch_membership':'batch_membership_mismatch','approved_capability_ids':'capability_binding_mismatch','approved_executor_ids':'executor_binding_mismatch','expected_evidence_contracts':'expected_evidence_contract_mismatch','single_use':'single_use_required','replay_policy':'replay_policy_invalid','maximum_use_count':'maximum_use_count_invalid','consumption_registry_contract':'registry_contract_mismatch','scope_hash':'scope_hash_mismatch'}
def build_consumption_binding(authorization):
 scope={k:authorization.get(k) for k in ('authorization_id','authorization_hash','plan_id','plan_hash','scope_hash','approved_operation_ids','approved_operation_bindings','approved_batch_group_ids','approved_batch_membership','approved_capability_ids','approved_executor_ids','expected_evidence_contracts','single_use','replay_policy','maximum_use_count')}; digest=sha256_json(scope)
 return {'schema_version':'unified_market_evidence_authorization_consumption_binding.v1',**scope,'consumption_binding_id':'umeacb-v1-'+digest[:20],'consumption_binding_hash':digest,'consumption_binding_identity_scope':scope,'consumption_registry_contract':'m8r_05b_03.v1','expected_unused_state':'explicit supplied state required'}
def validate_consumption_binding(binding,authorization,plan):
 validate_execution_authorization(authorization,plan)
 schema=json.loads(Path('schemas/unified_market_evidence_authorization_consumption_binding.v1.schema.json').read_text())
 schema_errors=list(Draft202012Validator(schema).iter_errors(binding))
 actual=sha256_json(binding['consumption_binding_identity_scope'])
 if actual!=binding['consumption_binding_hash']: raise AuthorizationError('consumption_binding_hash_mismatch')
 if 'umeacb-v1-'+actual[:20]!=binding['consumption_binding_id']: raise AuthorizationError('consumption_binding_id_mismatch')
 expected=build_consumption_binding(authorization)
 for key in _FIELDS:
  if binding.get(key)!=expected.get(key):
   if key=='consumption_binding_identity_scope': raise AuthorizationError('consumption_binding_identity_scope_mismatch')
   if key=='consumption_binding_hash': raise AuthorizationError('consumption_binding_hash_mismatch')
   if key=='consumption_binding_id': raise AuthorizationError('consumption_binding_id_mismatch')
   raise AuthorizationError(_CODES.get(key, key+'_mismatch'))
 if schema_errors: raise AuthorizationError('consumption_binding_schema_invalid')
 return True
def evaluate_consumption_preflight(authorization,plan,consumption_binding,evaluation_timestamp,supplied_consumption_state):
 evaluate_authorization_preflight(authorization,plan,evaluation_timestamp);validate_consumption_binding(consumption_binding,authorization,plan)
 if supplied_consumption_state is None: raise AuthorizationError('consumption_record_missing')
 if isinstance(supplied_consumption_state,list): raise AuthorizationError('consumption_state_ambiguous')
 if not isinstance(supplied_consumption_state,dict) or set(supplied_consumption_state)!={'authorization_id','authorization_hash','consumption_binding_id','consumption_binding_hash','registry_contract_version','state'}: raise AuthorizationError('consumption_state_schema_invalid')
 if not re.fullmatch(r'umea-v1-[0-9a-f]{20}', str(supplied_consumption_state.get('authorization_id'))) or not re.fullmatch(r'[0-9a-f]{64}',str(supplied_consumption_state.get('authorization_hash'))) or not re.fullmatch(r'umeacb-v1-[0-9a-f]{20}',str(supplied_consumption_state.get('consumption_binding_id'))) or not re.fullmatch(r'[0-9a-f]{64}',str(supplied_consumption_state.get('consumption_binding_hash'))): raise AuthorizationError('consumption_state_schema_invalid')
 for k in ('authorization_id','authorization_hash'):
  if supplied_consumption_state[k]!=consumption_binding[k]: raise AuthorizationError('consumption_authorization_mismatch')
 for k in ('consumption_binding_id','consumption_binding_hash'):
  if supplied_consumption_state[k]!=consumption_binding[k]: raise AuthorizationError('consumption_binding_state_mismatch')
 if supplied_consumption_state['registry_contract_version']!='m8r_05b_03.v1': raise AuthorizationError('registry_contract_mismatch')
 if supplied_consumption_state['state']=='consumed': raise AuthorizationError('authorization_already_consumed')
 if supplied_consumption_state['state']!='unused': raise AuthorizationError('consumption_state_schema_invalid')
 return {'status':'ready_for_controlled_consumption','consumption_binding_hash':consumption_binding['consumption_binding_hash']}
