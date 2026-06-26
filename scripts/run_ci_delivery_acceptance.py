"""CI wrapper for local delivery acceptance; defaults to check-only and no artifact writes."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from run_local_delivery_acceptance import run_acceptance_checks, write_acceptance_report
from governance_forbidden_path_guard import assert_not_forbidden_repo_write_path
def run_ci_delivery_acceptance(repo_root: str|Path='.') -> dict:
    report=run_acceptance_checks(repo_root); report['ci_wrapper']=True; report['check_only']=True; return report
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--check-only',action='store_true',default=True); ap.add_argument('--write-report')
    a=ap.parse_args(argv); report=run_ci_delivery_acceptance(a.repo_root)
    if a.write_report: assert_not_forbidden_repo_write_path(a.write_report); write_acceptance_report(report,a.write_report)
    print(json.dumps(report,indent=2,sort_keys=True)); return 0 if report.get('ok') else 1
if __name__=='__main__': raise SystemExit(main())
