from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
SCHEMA=Path('docs/authorization/m5b_live_probe_execution_authorization_schema.json')
TARGETS=['2330','0050','00929']

def _dt(s):
    return datetime.fromisoformat(s.replace('Z','+00:00'))
def sha256_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate_authorization(authorization, request, receipt=None, now=None):
    errors=[]
    try: auth=json.loads(Path(authorization).read_text())
    except Exception as e: return [{'code':'authorization_read_failed','detail':str(e),'path':'$'}]
    schema=json.loads(SCHEMA.read_text())
    for e in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(auth):
        errors.append({'code':'schema_error','path':'$'+''.join(f'/{x}' for x in e.path),'detail':e.message})
    if errors: return errors
    now=now or datetime.now(timezone.utc)
    try:
        at, exp = _dt(auth['authorized_at_utc']), _dt(auth['expires_at_utc'])
        if exp <= at or (exp-at).total_seconds() > 86400: errors.append({'code':'invalid_24h_expiry','path':'$.expires_at_utc'})
        if now > exp: errors.append({'code':'authorization_expired','path':'$.expires_at_utc'})
    except Exception as e: errors.append({'code':'timestamp_parse_failed','detail':str(e),'path':'$.authorized_at_utc'})
    if auth.get('request_sha256') != sha256_file(request): errors.append({'code':'request_sha256_mismatch','path':'$.request_sha256'})
    if sorted(auth.get('allowed_targets',[])) != sorted(TARGETS): errors.append({'code':'target_set_mismatch','path':'$.allowed_targets'})
    forbidden=['production_write','frontend_publication','generated_artifact_write','full_market_scan','trading_signal','source_fallback_allowed','raw_full_response_retention']
    for k in forbidden:
        if auth.get(k) is not False: errors.append({'code':'forbidden_flag_not_false','path':'$.'+k})
    if receipt:
        try: r=json.loads(Path(receipt).read_text())
        except Exception as e: errors.append({'code':'receipt_read_failed','detail':str(e),'path':'$.receipt'}); return errors
        if r.get('authorization_id') != auth.get('authorization_id'): errors.append({'code':'receipt_authorization_mismatch','path':'$.authorization_id'})
        if r.get('authorization_consumed') is not True: errors.append({'code':'authorization_not_consumed','path':'$.authorization_consumed'})
    return errors

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--authorization',required=True); p.add_argument('--request',required=True); p.add_argument('--receipt')
    a=p.parse_args(argv); errors=validate_authorization(a.authorization,a.request,a.receipt)
    print(json.dumps({'ok':not errors,'errors':errors,'network_used':False,'writes':False},indent=2,sort_keys=True))
    return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
