from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from jsonschema import Draft202012Validator
CORRECTION=Path('research/staging/m5c/corrections/M5C_RUN_SUMMARY_DESTINATION_CORRECTION_20260627_01.json')
SCHEMA=Path('docs/authorization/m5c_run_summary_destination_correction_schema.json')
PKG=Path('research/staging/m5c/m5c_twse_openapi_20260627_authorized_01')
DEST='research/staging/m5c/m5c_twse_openapi_20260627_authorized_01'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def validate(path=CORRECTION, package_dir=PKG):
    package_dir=Path(package_dir); data=load(path); schema=load(SCHEMA); errs=[]
    errs += [{'code':'schema_error','path':'$' + ''.join(f'/{x}' for x in e.path),'detail':e.message} for e in Draft202012Validator(schema).iter_errors(data)]
    if data.get('package_dir')!=str(package_dir): errs.append({'code':'correction_package_dir_mismatch','expected':str(package_dir),'actual':data.get('package_dir')})
    run=package_dir/'run_summary.json'; man=package_dir/'sha256_manifest.json'
    if not run.exists(): errs.append({'code':'run_summary_missing'}); return errs
    doc=load(run)
    if data.get('artifact_sha256')!=sha(run): errs.append({'code':'correction_artifact_hash_mismatch'})
    if man.exists() and data.get('applies_to_manifest_sha256')!=sha(man): errs.append({'code':'correction_manifest_hash_mismatch'})
    if data.get('recorded_value')!=doc.get('destination'): errs.append({'code':'correction_recorded_value_mismatch','actual':doc.get('destination')})
    if data.get('canonical_effective_value')!=DEST: errs.append({'code':'correction_effective_destination_mismatch'})
    if data.get('immutable_artifact_rewritten') is not False: errs.append({'code':'correction_must_not_rewrite_immutable_artifact'})
    return errs
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--correction',default=str(CORRECTION)); ap.add_argument('--package-dir',default=str(PKG)); ns=ap.parse_args(argv)
    errs=validate(Path(ns.correction), Path(ns.package_dir)); print(json.dumps({'status':'pass' if not errs else 'blocked','errors':errs},indent=2,sort_keys=True)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
