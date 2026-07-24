"""Pure future-consumption requirements; no registry or state mutation."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from .canonical import sha256_json
from .models import AuthorizationError
from .preflight import evaluate_authorization_preflight

def build_consumption_binding(authorization):
 scope={k:authorization.get(k) for k in ('authorization_id','authorization_hash','plan_id','plan_hash','scope_hash','approved_operation_ids','approved_operation_bindings','approved_batch_group_ids','approved_batch_membership','approved_capability_ids','approved_executor_ids','expected_evidence_contracts','single_use','replay_policy','maximum_use_count')}
 digest=sha256_json(scope)
 return {'schema_version':'unified_market_evidence_authorization_consumption_binding.v1',**scope,'consumption_binding_id':'umeacb-v1-'+digest[:20],'consumption_binding_hash':digest,'consumption_binding_identity_scope':scope,'consumption_registry_contract':'m8r_05b_03.v1','expected_unused_state':'explicit supplied state required'}
def validate_consumption_binding(binding,authorization,plan):
 schema=json.loads(Path('schemas/unified_market_evidence_authorization_consumption_binding.v1.schema.json').read_text())
 if list(Draft202012Validator(schema).iter_errors(binding)): raise AuthorizationError('consumption_binding_schema_invalid')
 expected=build_consumption_binding(authorization)
 for key,code in [('consumption_binding_hash','consumption_binding_mismatch'),('consumption_binding_id','consumption_binding_mismatch'),('authorization_id','authorization_hash_mismatch'),('authorization_hash','authorization_hash_mismatch'),('plan_id','plan_id_mismatch'),('plan_hash','plan_hash_mismatch'),('scope_hash','scope_hash_mismatch')]:
  if binding.get(key)!=expected.get(key): raise AuthorizationError(code)
 if plan.get('plan_id')!=binding['plan_id'] or plan.get('plan_hash')!=binding['plan_hash']: raise AuthorizationError('plan_binding_mismatch')
 return True
def evaluate_consumption_preflight(authorization,plan,consumption_binding,evaluation_timestamp,supplied_consumption_state):
 evaluate_authorization_preflight(authorization,plan,evaluation_timestamp);validate_consumption_binding(consumption_binding,authorization,plan)
 if not isinstance(supplied_consumption_state,dict): raise AuthorizationError('consumption_record_missing')
 for k in ('authorization_id','authorization_hash','consumption_binding_id','consumption_binding_hash'):
  if supplied_consumption_state.get(k)!=consumption_binding.get(k): raise AuthorizationError('consumption_state_ambiguous')
 if supplied_consumption_state.get('registry_contract_version')!='m8r_05b_03.v1': raise AuthorizationError('consumption_state_ambiguous')
 if supplied_consumption_state.get('state')=='consumed': raise AuthorizationError('authorization_already_consumed')
 if supplied_consumption_state.get('state')!='unused': raise AuthorizationError('consumption_state_ambiguous')
 return {'status':'ready_for_controlled_consumption','consumption_binding_hash':consumption_binding['consumption_binding_hash']}
