from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from jsonschema import Draft202012Validator
AUDIT=Path('research/staging/m5c/supplemental_audit/M5C_TWSE_OPENAPI_STAGING_PROMOTION_AUTHORIZED_01_AUDIT.json')
SCHEMA=Path('docs/authorization/m5c_supplemental_audit_schema.json')
PKG=Path('research/staging/m5c/m5c_twse_openapi_20260627_authorized_01')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def validate(path=AUDIT, package_dir=PKG):
    package_dir=Path(package_dir)
    data=load(path); schema=load(SCHEMA); errs=[]
    errs += [{'code':'schema_error','path':'$' + ''.join(f'/{x}' for x in e.path),'detail':e.message} for e in Draft202012Validator(schema).iter_errors(data)]
    if data.get('package_dir') != str(package_dir): errs.append({'code':'audit_package_dir_mismatch','expected':str(package_dir),'actual':data.get('package_dir')})
    manifest_path=package_dir/'sha256_manifest.json'
    if not manifest_path.exists(): errs.append({'code':'package_manifest_missing','path':str(manifest_path)}); return errs
    if data.get('package_manifest_sha256') != sha(manifest_path): errs.append({'code':'package_manifest_sha_mismatch'})
    expected={p.name: sha(p) for p in package_dir.iterdir() if p.is_file()}
    artifacts=data.get('artifacts',[]); actual={a.get('path'): a.get('sha256') for a in artifacts}
    if set(actual) != set(expected): errs.append({'code':'audit_artifact_set_mismatch','expected':sorted(expected),'actual':sorted(actual)})
    for name,h in expected.items():
        if actual.get(name) != h: errs.append({'code':'audit_artifact_hash_mismatch','path':name})
    manifest_entries=[a for a in artifacts if a.get('artifact_type')=='package_manifest']
    if len(manifest_entries)!=1: errs.append({'code':'audit_manifest_artifact_count_mismatch','actual':len(manifest_entries)})
    for a in artifacts:
        path=a.get('path'); typ=a.get('artifact_type')
        expected_type='package_manifest' if path=='sha256_manifest.json' else 'package_artifact'
        if typ != expected_type: errs.append({'code':'audit_artifact_type_mismatch','path':path,'expected':expected_type,'actual':typ})
    if data.get('canonical_source_id') != 'TWSE_OpenAPI': errs.append({'code':'audit_source_id_mismatch'})
    return errs
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--audit',default=str(AUDIT)); ap.add_argument('--package-dir',default=str(PKG)); ns=ap.parse_args(argv)
    errs=validate(Path(ns.audit), Path(ns.package_dir)); print(json.dumps({'status':'pass' if not errs else 'blocked','errors':errs},indent=2,sort_keys=True)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
