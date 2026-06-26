"""Local-only repository safety preflight checks."""
from __future__ import annotations
import argparse,json
from pathlib import Path
FORBIDDEN_PREFIXES=("frontend/public/","research/generated/","credentials/","cookies/","tokens/","broker/","production/","prod/","current_market_state/")
FORBIDDEN_EXACT={".env"}
REQUIRED_UPSTREAM_FILES=[".github/workflows/non-network-ci.yml","pytest.ini","README.md","docs/DELIVERY_INDEX.md","docs/RELEASE_READINESS.md","docs/INDEX.md","docs/GLOSSARY.md","scripts/controlled_refresh_staging_writer.py","scripts/controlled_refresh_staging_validator.py","scripts/build_frontend_readonly_context_package.py","scripts/run_local_delivery_acceptance.py","scripts/run_ci_delivery_acceptance.py","scripts/governance_forbidden_path_guard.py","scripts/check_pr_body_changed_files_consistency.py"]
def is_forbidden_changed_path(p):
    p=str(p).replace('\\','/')
    return p in FORBIDDEN_EXACT or any(p.startswith(x) for x in FORBIDDEN_PREFIXES)
def evaluate_repo_safety(repo_root, changed_files=None, required_files=None):
    root=Path(repo_root); changed_files=changed_files or []; required_files=required_files or REQUIRED_UPSTREAM_FILES
    errors=[]
    if not root.exists(): errors.append({'code':'repo_root_missing','path':str(root)})
    for f in required_files:
        if not (root/f).exists(): errors.append({'code':'required_file_missing','path':f})
    for f in changed_files:
        if is_forbidden_changed_path(f): errors.append({'code':'forbidden_changed_path','path':f})
    return {'ok':not errors,'errors':errors,'checked_changed_files':changed_files}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--changed-files',nargs='*',default=[]); ap.add_argument('--changed-files-file'); ap.add_argument('--json',action='store_true')
    a=ap.parse_args(argv); files=list(a.changed_files)
    if a.changed_files_file: files += [x.strip() for x in Path(a.changed_files_file).read_text().splitlines() if x.strip()]
    r=evaluate_repo_safety(a.repo_root, files)
    print(json.dumps(r,indent=2,sort_keys=True) if a.json else ('OK' if r['ok'] else 'FAILED'))
    return 0 if r['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
