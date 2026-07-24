"""Pure future-consumption requirements; no registry or state mutation."""
from .canonical import sha256_json
from .models import AuthorizationError
from .preflight import evaluate_authorization_preflight
def build_consumption_binding(authorization):
 scope={k:authorization.get(k) for k in ('schema_version','authorization_id','authorization_hash','plan_id','plan_hash','scope_hash','approved_operation_ids','approved_batch_group_ids','approved_executor_ids','approved_capability_ids','expected_evidence_contracts','single_use','replay_policy','maximum_use_count')}
 digest=sha256_json(scope)
 return {**scope,'consumption_binding_id':'umeacb-v1-'+digest[:20],'consumption_binding_hash':digest,'consumption_binding_identity_scope':scope,'consumption_registry_contract':'M8R-05B-03 durable atomic registry','expected_unused_state':'explicit supplied state required'}
def evaluate_consumption_preflight(authorization,plan,consumption_binding,evaluation_timestamp,supplied_consumption_state):
 evaluate_authorization_preflight(authorization,plan,evaluation_timestamp)
 expected=build_consumption_binding(authorization)
 if consumption_binding.get('consumption_binding_hash')!=expected['consumption_binding_hash']: raise AuthorizationError('consumption_binding_mismatch')
 if supplied_consumption_state is None: raise AuthorizationError('consumption_record_missing')
 if not isinstance(supplied_consumption_state,dict) or supplied_consumption_state.get('authorization_id')!=authorization['authorization_id']: raise AuthorizationError('consumption_state_ambiguous')
 if supplied_consumption_state.get('state')=='consumed': raise AuthorizationError('authorization_already_consumed')
 if supplied_consumption_state.get('state')!='unused': raise AuthorizationError('consumption_state_ambiguous')
 return {'status':'ready_for_controlled_consumption','consumption_binding_hash':expected['consumption_binding_hash']}
