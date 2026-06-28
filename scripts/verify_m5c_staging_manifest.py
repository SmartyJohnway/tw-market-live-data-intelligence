from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
REQUIRED={'authorization_snapshot.json','request_snapshot.json','source_binding.json','staging_payload.json','promotion_receipt.json','validation_report.json','lineage.json','evidence_ledger.json','rollback_plan.json','frontend_readonly_context_package.json','run_summary.json'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def verify(package_dir):
    d=Path(package_dir); errs=[]; mp=d/'sha256_manifest.json'
    if not mp.exists(): return [{'code':'manifest_missing','path':str(mp)}]
    try: m=load(mp)
    except Exception as exc: return [{'code':'manifest_json_invalid','detail':str(exc)}]
    if m.get('manifest_final') is not True: errs.append({'code':'manifest_not_final'})
    if m.get('immutable') is not True: errs.append({'code':'manifest_not_immutable'})
    manifest=m.get('manifest',{})
    if set(manifest)!=REQUIRED: errs.append({'code':'manifest_artifact_set_mismatch','expected':sorted(REQUIRED),'actual':sorted(manifest)})
    actual={p.name for p in d.iterdir() if p.is_file() and p.name!='sha256_manifest.json'} if d.exists() else set()
    if actual!=REQUIRED: errs.append({'code':'untracked_or_missing_artifacts','expected':sorted(REQUIRED),'actual':sorted(actual)})
    for name, expected in manifest.items():
        p=d/name
        if not p.exists(): errs.append({'code':'manifest_entry_missing','path':name})
        elif sha(p)!=expected: errs.append({'code':'manifest_hash_mismatch','path':name,'expected':expected,'actual':sha(p)})
    return errs
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--package-dir',required=True); ns=ap.parse_args(argv)
    errs=verify(ns.package_dir); print(json.dumps({'status':'pass' if not errs else 'blocked','errors':errs},indent=2,sort_keys=True)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
