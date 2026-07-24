from .canonical import authorization_identity,sha256_json
from .models import AuthorizationError
from .authorization import _time,MAX_LIFETIME_SECONDS,_ops

def validate_execution_authorization(a,plan):
 for k in ('authorization_id','authorization_hash','authorization_identity_scope','decision','plan_id','plan_hash','scope_hash'): 
  if k not in a: raise AuthorizationError('authorization_schema_invalid')
 d,i=authorization_identity(a['authorization_identity_scope'])
 if a['authorization_hash']!=d: raise AuthorizationError('authorization_hash_mismatch')
 if a['authorization_id']!=i: raise AuthorizationError('authorization_id_mismatch')
 if a['plan_id']!=plan.get('plan_id'): raise AuthorizationError('plan_id_mismatch')
 if a['plan_hash']!=plan.get('plan_hash'): raise AuthorizationError('plan_hash_mismatch')
 if a.get('plan_schema_version')!=plan.get('schema_version'): raise AuthorizationError('plan_schema_mismatch')
 if a.get('input_binding_hashes')!=plan.get('input_bindings'): raise AuthorizationError('input_binding_hash_mismatch')
 start,end=_time(a['issued_at']),_time(a['expires_at'])
 if end<=start: raise AuthorizationError('approval_scope_invalid')
 if (end-start).total_seconds()>MAX_LIFETIME_SECONDS: raise AuthorizationError('authorization_lifetime_exceeded')
 if a['decision']=='approved':
  if not a.get('execution_authorized') or not a.get('network_authorized'): raise AuthorizationError('authorization_not_approved')
  if not a.get('single_use'): raise AuthorizationError('single_use_required')
  if a.get('replay_policy')!='deny_replay': raise AuthorizationError('replay_policy_invalid')
  if a.get('maximum_use_count')!=1: raise AuthorizationError('maximum_use_count_invalid')
 elif a.get('execution_authorized') or a.get('network_authorized'): raise AuthorizationError('authorization_not_approved')
 ops=_ops(plan); ids=a.get('approved_operation_ids',[]); mode=a.get('approval_scope_mode')
 if mode not in {'whole_plan_executable_scope','selected_operations','selected_batches'}: raise AuthorizationError('approval_scope_mode_invalid')
 if not ids or len(ids)!=len(set(ids)): raise AuthorizationError('approval_scope_empty')
 if mode=='whole_plan_executable_scope' and sorted(ids)!=sorted(ops): raise AuthorizationError('approval_scope_invalid')
 for x in ids:
  if x not in ops: raise AuthorizationError('operation_not_approvable')
 scope={k:a.get(k) for k in ('approval_scope_mode','approved_operation_ids','approved_batch_group_ids','approved_batch_membership','approved_capability_ids','approved_executor_ids','expected_evidence_contracts')}
 if sha256_json(scope)!=a['scope_hash']: raise AuthorizationError('approval_scope_invalid')
 return True
