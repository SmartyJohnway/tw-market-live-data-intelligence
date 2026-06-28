from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator
AUTH=Path('docs/authorization/decisions/M5C_TWSE_OPENAPI_STAGING_PROMOTION_AUTHORIZATION.json')
SCHEMA=Path('docs/authorization/m5c_staging_promotion_execution_authorization_schema.json')
REQ=Path('docs/authorization/requests/M5C_TWSE_OPENAPI_STAGING_PROMOTION_REQUEST.json')
RUN=Path('research/live_probe_runs/m5b/m5b_twse_openapi_20260627T015136Z')
DEST='research/staging/m5c/m5c_twse_openapi_20260627_authorized_01'
TARGETS=['2330','0050','00929']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def _schema_errors(data):
    schema=load(SCHEMA)
    return [{'code':'schema_error','path':'$' + ''.join(f'/{x}' for x in e.path),'detail':e.message} for e in Draft202012Validator(schema).iter_errors(data)]
def validate(path=AUTH):
    a=load(path); errs=_schema_errors(a)
    checks=[('merge_sha','11711eacf7795f3074350a0db68b3227b7986215'),('m5c_request_sha256',sha(REQ)),('source_manifest_sha256',sha(RUN/'sha256_manifest.json')),('staging_candidate_sha256',sha(RUN/'staging_candidate.json')),('source_run_dir',str(RUN)),('destination',DEST),('source_id','TWSE_OpenAPI'),('source_run_id','m5b_twse_openapi_20260627T015136Z')]
    for k,v in checks:
        if a.get(k)!=v: errs.append({'code':'binding_mismatch','field':k,'expected':v,'actual':a.get(k)})
    if a.get('targets')!=TARGETS: errs.append({'code':'target_mismatch','actual':a.get('targets')})
    for k in ['single_use','staging_promotion_authorized']:
        if a.get(k) is not True: errs.append({'code':'required_true','field':k})
    for k in ['production_write','frontend_public_write','frontend_publication_authorized','generated_artifact_write','trading_output','realtime_claim_authorized','network_probe_authorized','actual_frontend_publication_authorized','production_ready','current_realtime','realtime_guaranteed']:
        if a.get(k) is not False: errs.append({'code':'required_false','field':k})
    return errs
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--authorization',default=str(AUTH)); ns=ap.parse_args(argv)
    errs=validate(Path(ns.authorization)); print(json.dumps({'status':'pass' if not errs else 'blocked','errors':errs},indent=2,sort_keys=True)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
