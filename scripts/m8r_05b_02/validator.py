import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from .canonical import authorization_identity,sha256_json
from .models import AuthorizationError
from .authorization import _time,MAX_LIFETIME_SECONDS,_derived
from scripts.m8r_05b_01.planner import PLAN_VALIDATOR, plan_identity_scope, validate_batch_integrity
from scripts.m8r_05b_01.canonical import plan_hash_and_id, sha256_json as plan_sha
from scripts.m8r_05b_01.models import PLANNER_VERSION

def _schema(): return json.loads(Path('schemas/unified_market_evidence_execution_authorization.v1.schema.json').read_text())
def _validate_plan(plan):
 if list(PLAN_VALIDATOR.iter_errors(plan)): raise AuthorizationError('plan_schema_invalid')
 try: validate_batch_integrity(plan['operations'],plan['batch_groups'])
 except Exception as exc: raise AuthorizationError('batch_membership_mismatch') from exc
 ids=[x.get('operation_id') for x in plan.get('operations',[])]
 if len(ids)!=len(set(ids)): raise AuthorizationError('duplicate_operation_id')
 bids=[x.get('batch_group_id') for x in plan.get('batch_groups',[])]
 if len(bids)!=len(set(bids)): raise AuthorizationError('duplicate_batch_group_id')
 scope=plan_identity_scope(plan)
 h,i=plan_hash_and_id(scope)
 if plan.get('plan_hash')!=h: raise AuthorizationError('plan_hash_mismatch')
 if plan.get('plan_id')!=i: raise AuthorizationError('plan_id_mismatch')

def validate_execution_authorization(a,plan):
 _validate_plan(plan)
 if list(Draft202012Validator(_schema(), format_checker=FormatChecker()).iter_errors(a)): raise AuthorizationError('authorization_schema_invalid')
 h,i=authorization_identity(a['authorization_identity_scope'])
 if a['authorization_hash']!=h: raise AuthorizationError('authorization_hash_mismatch')
 if a['authorization_id']!=i: raise AuthorizationError('authorization_id_mismatch')
 for k,code in [('plan_schema_version','plan_schema_mismatch'),('plan_id','plan_id_mismatch'),('plan_hash','plan_hash_mismatch'),('input_bindings','input_binding_hash_mismatch')]:
  if a.get(k)!=({'plan_schema_version':plan.get('schema_version'),'plan_id':plan.get('plan_id'),'plan_hash':plan.get('plan_hash'),'input_bindings':plan.get('input_bindings')}[k]): raise AuthorizationError(code)
 start,end=_time(a['issued_at']),_time(a['expires_at'])
 if end<=start or (end-start).total_seconds()>MAX_LIFETIME_SECONDS: raise AuthorizationError('authorization_lifetime_exceeded')
 derived=_derived(plan,a['approval_scope_mode'],a)
 for k,v in derived.items():
  if a.get(k)!=v:
   code={'approved_operation_ids':'approved_operation_set_mismatch','approved_batch_group_ids':'approved_batch_set_mismatch','approved_batch_membership':'batch_membership_mismatch','approved_operation_bindings':'approved_operation_binding_mismatch','approved_capability_ids':'capability_binding_mismatch','approved_executor_ids':'executor_binding_mismatch','expected_evidence_contracts':'expected_evidence_contract_mismatch'}.get(k,'approved_operation_binding_mismatch'); raise AuthorizationError(code)
 if a['scope_hash']!=sha256_json(derived): raise AuthorizationError('scope_hash_mismatch')
 bind={'schema_version':plan.get('schema_version'),'plan_id':plan.get('plan_id'),'plan_hash':plan.get('plan_hash'),'input_bindings':plan.get('input_bindings'),'scope':derived}
 if a['plan_binding_hash']!=sha256_json(bind): raise AuthorizationError('plan_binding_hash_mismatch')
 return True
