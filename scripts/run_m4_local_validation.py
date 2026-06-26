import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_governance_policy_manifest import validate_manifest
from scripts.repo_safety_preflight import evaluate_repo_safety
def run_local_validation(repo_root='.'):
 return {'ok': evaluate_repo_safety(repo_root)['ok'], 'checks':['repo_safety_preflight','governance_policy_manifest'], 'network_used':False}
def main(argv=None): ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true'); a=ap.parse_args(argv); print(json.dumps(run_local_validation(),indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
