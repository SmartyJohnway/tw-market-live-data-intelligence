from __future__ import annotations
import argparse, hashlib, json, shutil, tempfile
from pathlib import Path
from validate_m5c_promoted_staging_package import validate

def sha_tree(path: Path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(path.rglob('*')) if p.is_file()}
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--package-dir',required=True); ns=p.parse_args(argv)
    package=Path(ns.package_dir); before=sha_tree(package) if package.exists() else {}
    errors=[]
    if not package.exists(): errors.append({'code':'package_missing','path':str(package)})
    else:
        errors += validate(package)
        rollback_plan=package/'rollback_plan.json'
        if not rollback_plan.exists(): errors.append({'code':'rollback_plan_missing'})
        else:
            try:
                plan=json.loads(rollback_plan.read_text())
                if plan.get('committed_package_delete_allowed') is not False: errors.append({'code':'rollback_plan_delete_guard_mismatch'})
                if plan.get('rollback_mode')!='tmp_path_simulation_only': errors.append({'code':'rollback_mode_mismatch','actual':plan.get('rollback_mode')})
            except Exception as exc:
                errors.append({'code':'rollback_plan_invalid_json','detail':str(exc)})
    tmp_root=Path(tempfile.mkdtemp(prefix='m5c_rollback_sim_'))
    cleaned=False
    try:
        if not errors:
            work=tmp_root/'package'
            shutil.copytree(package, work)
            shutil.rmtree(work)
            after=sha_tree(package)
            if before != after: errors.append({'code':'committed_package_changed_during_rollback_simulation'})
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
        cleaned=not tmp_root.exists()
    out={'status':'pass' if not errors else 'blocked','rollback_simulated_in_tmp_path':not errors,'committed_package_deleted':False,'temporary_root_cleaned':cleaned,'errors':errors}
    print(json.dumps(out,indent=2,sort_keys=True)); return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
