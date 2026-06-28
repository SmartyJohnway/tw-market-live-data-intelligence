from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
from jsonschema import Draft202012Validator
try:
    from verify_m5c_staging_manifest import verify as verify_manifest
    from validate_m5c_promoted_staging_package import validate as validate_package
    from validate_m5c_supplemental_audit import validate as validate_audit
except ModuleNotFoundError:
    from scripts.verify_m5c_staging_manifest import verify as verify_manifest
    from scripts.validate_m5c_promoted_staging_package import validate as validate_package
    from scripts.validate_m5c_supplemental_audit import validate as validate_audit
REQ=Path('docs/authorization/requests/M5D_FRONTEND_PUBLICATION_REQUEST.json')
SCHEMA=Path('docs/authorization/m5d_frontend_publication_request_schema.json')

try:
    from m5d_publication_common import validate_candidate
except ModuleNotFoundError:
    from scripts.m5d_publication_common import validate_candidate

CANONICAL='research/staging/m5c/m5c_twse_openapi_20260627_authorized_01'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def validate(path=REQ):
    d=load(path); errs=[]
    schema=load(SCHEMA)
    errs += [{'code':'schema_error','path':'$' + ''.join(f'/{x}' for x in e.path),'detail':e.message} for e in Draft202012Validator(schema).iter_errors(d)]
    for k in ['actual_frontend_publication_authorized','publication_performed']:
        if d.get(k) is not False: errs.append({'code':'must_be_false','field':k})
    for k in ['request_only','single_use']:
        if d.get(k) is not True: errs.append({'code':'must_be_true','field':k})
    if d.get('authorization_token_issued') is not False: errs.append({'code':'token_must_not_be_issued'})
    if d.get('next_required_action')!='user_authorization': errs.append({'code':'next_action_must_be_user_authorization'})
    if d.get('m5c_staging_package_dir')!=CANONICAL: errs.append({'code':'package_dir_mismatch'})
    if d.get('proposed_destination')!='frontend/public/market-context.json': errs.append({'code':'proposed_destination_mismatch'})
    if 'approval_token' in d or 'authorization_decision' in d or 'authorization_token' in d: errs.append({'code':'approval_material_forbidden'})
    cdir=Path(d.get('candidate_dir',''))
    cman=cdir/'sha256_manifest.json'
    if not cman.exists(): errs.append({'code':'candidate_manifest_missing'})
    elif d.get('candidate_manifest_sha256') != sha(cman): errs.append({'code':'candidate_manifest_sha_mismatch','expected':sha(cman),'actual':d.get('candidate_manifest_sha256')})
    for candidate_error in validate_candidate(cdir):
        errs.append({'code':'candidate_validation_failed','detail':candidate_error})
    pkg=Path(d.get('m5c_staging_package_dir',''))
    if not (pkg/'sha256_manifest.json').exists(): errs.append({'code':'package_manifest_missing'})
    else:
        actual=sha(pkg/'sha256_manifest.json')
        if d.get('m5c_staging_manifest_sha256')!=actual: errs.append({'code':'staging_manifest_sha_mismatch','expected':actual,'actual':d.get('m5c_staging_manifest_sha256')})
        errs += verify_manifest(pkg)
        errs += validate_package(pkg)
        errs += validate_audit(package_dir=pkg)
    return errs
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--request',default=str(REQ)); ns=p.parse_args(argv); errs=validate(ns.request)
    print(json.dumps({'status':'pass' if not errs else 'blocked','errors':errs},indent=2,sort_keys=True)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
