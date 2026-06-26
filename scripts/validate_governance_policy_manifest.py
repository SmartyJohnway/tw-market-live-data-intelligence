import argparse,json
from pathlib import Path
REQUIRED={'forbidden_paths','forbidden_behaviors','allowed_local_paths','allowed_fixture_paths','required_caveats','required_false_flags','source_risk_required_sources','no_trading_terms','no_realtime_claim_terms','authorization_levels'}
def validate_manifest(data):
 e=[]
 if not isinstance(data,dict): return [{'code':'not_object'}]
 for k in sorted(REQUIRED-set(data)): e.append({'code':'missing_key','path':k})
 for k in REQUIRED & set(data):
  if not isinstance(data[k],list) or not data[k]: e.append({'code':'invalid_list','path':k})
 return e
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument('--manifest',default='docs/governance/governance_policy_manifest.json'); p.add_argument('--json',action='store_true'); a=p.parse_args(argv); errs=validate_manifest(json.loads(Path(a.manifest).read_text())); print(json.dumps({'ok':not errs,'errors':errs},indent=2)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
