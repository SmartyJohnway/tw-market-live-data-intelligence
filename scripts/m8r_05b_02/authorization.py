from .canonical import sha256_json,authorization_identity
from .models import AuthorizationError
from datetime import datetime,timezone
MAX_LIFETIME_SECONDS=86400

def _time(s):
 if not isinstance(s,str) or not s.endswith('Z'): raise AuthorizationError('authorization_schema_invalid')
 try:return datetime.fromisoformat(s[:-1]+'+00:00')
 except ValueError: raise AuthorizationError('authorization_schema_invalid')
def _ops(plan): return {o['operation_id']:o for o in plan.get('operations',[]) if o.get('operation_status')=='executable_pending_approval'}
def build_execution_authorization(plan,decision_input):
 decision=dict(decision_input); mode=decision.get('approval_scope_mode'); ops=_ops(plan)
 ids=sorted(decision.get('approved_operation_ids',[])); batches=sorted(decision.get('approved_batch_group_ids',[]))
 membership={k:sorted(v) for k,v in sorted(decision.get('approved_batch_membership',{}).items())}
 if mode=='whole_plan_executable_scope': ids=sorted(ops); batches=[]; membership={}
 if mode=='selected_batches':
  ids=sorted({x for v in membership.values() for x in v})
 scope={'approval_scope_mode':mode,'approved_operation_ids':ids,'approved_batch_group_ids':batches,'approved_batch_membership':membership,'approved_capability_ids':sorted(decision.get('approved_capability_ids',[])),'approved_executor_ids':sorted(decision.get('approved_executor_ids',[])),'expected_evidence_contracts':sorted(decision.get('expected_evidence_contracts',[]))}
 identity={'schema_version':'unified_market_evidence_execution_authorization.v1','owner_identity_reference':decision.get('owner_identity_reference'),'decision':decision.get('decision'),'plan_schema_version':plan.get('schema_version'),'plan_id':plan.get('plan_id'),'plan_hash':plan.get('plan_hash'),'plan_identity_scope_hash':plan.get('plan_identity_scope_hash'),'input_binding_hashes':plan.get('input_bindings'),'issued_at':decision.get('issued_at'),'expires_at':decision.get('expires_at'),'single_use':decision.get('single_use'),'replay_policy':decision.get('replay_policy'),'maximum_use_count':decision.get('maximum_use_count'),**scope}
 digest,aid=authorization_identity(identity)
 return {**identity,'authorization_id':aid,'authorization_hash':digest,'authorization_identity_scope':identity,'decision_reason':decision.get('decision_reason',''),'owner_review_reference':decision.get('owner_review_reference'),'reviewed_at':decision.get('reviewed_at'),'authorization_status':decision.get('authorization_status','approved' if decision.get('decision')=='approved' else 'draft'),'plan_binding_hash':sha256_json({'plan_id':plan.get('plan_id'),'plan_hash':plan.get('plan_hash'),'scope_hash':sha256_json(scope)}),'scope_hash':sha256_json(scope),'execution_authorized':decision.get('decision')=='approved','network_authorized':decision.get('decision')=='approved','supersedes_authorization_id':decision.get('supersedes_authorization_id'),'revocation_reference':decision.get('revocation_reference'),'revoked_at':decision.get('revoked_at'),'caveats':decision.get('caveats',[]),'created_by_component':'m8r_05b_02','contract_version':'m8r_05b_02.v1'}
