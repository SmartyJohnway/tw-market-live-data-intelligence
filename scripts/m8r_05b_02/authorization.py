from datetime import datetime
from .canonical import sha256_json,authorization_identity
from .models import AuthorizationError
MAX_LIFETIME_SECONDS=86400

def _time(v):
 try:
  if not isinstance(v,str) or not v.endswith('Z'): raise ValueError
  return datetime.fromisoformat(v[:-1]+'+00:00')
 except ValueError: raise AuthorizationError('authorization_schema_invalid')
def _plan_ops(plan): return {x['operation_id']:x for x in plan.get('operations',[]) if isinstance(x,dict)}
def _approvable(plan): return {k:v for k,v in _plan_ops(plan).items() if v.get('operation_status')=='executable_pending_approval'}
def _batch_map(plan): return {b['batch_group_id']:sorted(b.get('operation_ids',[])) for b in plan.get('batch_groups',[]) if isinstance(b,dict)}
def _derived(plan, mode, requested):
 ops=_approvable(plan); batches=_batch_map(plan)
 ids=sorted(requested.get('approved_operation_ids',[])); bids=sorted(requested.get('approved_batch_group_ids',[])); members=requested.get('approved_batch_membership',{})
 if mode=='whole_plan_executable_scope': ids=sorted(ops);bids=[];members={}
 elif mode=='selected_batches':
  if not bids or sorted(members)!=bids: raise AuthorizationError('batch_membership_mismatch')
  for bid in bids:
   if bid not in batches: raise AuthorizationError('unknown_batch_group_id')
   if sorted(members[bid])!=batches[bid] or not batches[bid]: raise AuthorizationError('batch_membership_mismatch')
   if any(x not in ops for x in batches[bid]): raise AuthorizationError('operation_not_approvable')
  ids=sorted({x for b in bids for x in batches[b]});members={b:batches[b] for b in bids}
 elif mode=='selected_operations':
  if not ids: raise AuthorizationError('approval_scope_empty')
 else: raise AuthorizationError('approval_scope_mode_invalid')
 if len(ids)!=len(set(ids)): raise AuthorizationError('duplicate_operation_id')
 if any(x not in ops for x in ids): raise AuthorizationError('operation_not_approvable')
 chosen=[ops[x] for x in ids]
 bindings=[{'operation_id':x['operation_id'],'market':x.get('market'),'security_types':sorted(x.get('security_types',[])),'capability_id':x.get('capability_id'),'executor_id':x.get('executor_id'),'expected_evidence_contract':x.get('expected_evidence_contract'),'batch_group_id':x.get('batch_group_id')} for x in sorted(chosen,key=lambda x:x['operation_id'])]
 return {'approved_operation_bindings':bindings,'approval_scope_mode':mode,'approved_operation_ids':ids,'approved_batch_group_ids':bids,'approved_batch_membership':members,'approved_capability_ids':sorted({x.get('capability_id') for x in chosen}), 'approved_executor_ids':sorted({x.get('executor_id') for x in chosen}), 'expected_evidence_contracts':sorted({x.get('expected_evidence_contract') for x in chosen})}
def build_execution_authorization(plan,decision_input):
 d=dict(decision_input);scope=_derived(plan,d.get('approval_scope_mode'),d)
 identity={'schema_version':'unified_market_evidence_execution_authorization.v1','owner_identity_reference':d.get('owner_identity_reference'),'decision':d.get('decision'),'plan_schema_version':plan.get('schema_version'),'plan_id':plan.get('plan_id'),'plan_hash':plan.get('plan_hash'),'input_binding_hashes':plan.get('input_bindings'),'issued_at':d.get('issued_at'),'expires_at':d.get('expires_at'),'single_use':d.get('single_use'),'replay_policy':d.get('replay_policy'),'maximum_use_count':d.get('maximum_use_count'),**scope}
 h,i=authorization_identity(identity); approved=d.get('decision')=='approved'
 return {**identity,'authorization_id':i,'authorization_hash':h,'authorization_identity_scope':identity,'decision_reason':d.get('decision_reason',''),'owner_review_reference':d.get('owner_review_reference'),'reviewed_at':d.get('reviewed_at'),'authorization_status':d.get('authorization_status','approved' if approved else 'rejected'),'plan_binding_hash':sha256_json({'schema_version':plan.get('schema_version'),'plan_id':plan.get('plan_id'),'plan_hash':plan.get('plan_hash'),'input_bindings':plan.get('input_bindings'),'scope':scope}),'scope_hash':sha256_json(scope),'execution_authorized':approved,'network_authorized':approved,'supersedes_authorization_id':None,'revocation_reference':None,'revoked_at':None,'caveats':d.get('caveats',[]),'created_by_component':'m8r_05b_02','contract_version':'m8r_05b_02.v1'}
