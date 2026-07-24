import json
from pathlib import Path
from jsonschema import Draft202012Validator
from .canonical import authorization_identity,sha256_json
from .models import AuthorizationError
from .authorization import _time,MAX_LIFETIME_SECONDS,_derived

def _schema(): return json.loads(Path('schemas/unified_market_evidence_execution_authorization.v1.schema.json').read_text())
def validate_execution_authorization(a,plan):
 if list(Draft202012Validator(_schema()).iter_errors(a)): raise AuthorizationError('authorization_schema_invalid')
 h,i=authorization_identity(a['authorization_identity_scope'])
 if (a['authorization_hash'],a['authorization_id'])!=(h,i): raise AuthorizationError('authorization_hash_mismatch')
 for k,code in [('plan_schema_version','plan_schema_mismatch'),('plan_id','plan_id_mismatch'),('plan_hash','plan_hash_mismatch'),('plan_identity_scope_hash','plan_identity_scope_hash_mismatch'),('input_binding_hashes','input_binding_hash_mismatch')]:
  if a.get(k)!=({'plan_schema_version':plan.get('schema_version'),'plan_id':plan.get('plan_id'),'plan_hash':plan.get('plan_hash'),'plan_identity_scope_hash':plan.get('plan_identity_scope_hash'),'input_binding_hashes':plan.get('input_bindings')}[k]): raise AuthorizationError(code)
 start,end=_time(a['issued_at']),_time(a['expires_at'])
 if end<=start or (end-start).total_seconds()>MAX_LIFETIME_SECONDS: raise AuthorizationError('authorization_lifetime_exceeded')
 derived=_derived(plan,a['approval_scope_mode'],a)
 for k,v in derived.items():
  if a.get(k)!=v: raise AuthorizationError('capability_binding_mismatch')
 if a['scope_hash']!=sha256_json(derived): raise AuthorizationError('approval_scope_invalid')
 bind={'schema_version':plan.get('schema_version'),'plan_id':plan.get('plan_id'),'plan_hash':plan.get('plan_hash'),'plan_identity_scope_hash':plan.get('plan_identity_scope_hash'),'input_bindings':plan.get('input_bindings'),'scope':derived}
 if a['plan_binding_hash']!=sha256_json(bind): raise AuthorizationError('plan_binding_hash_mismatch')
 return True
