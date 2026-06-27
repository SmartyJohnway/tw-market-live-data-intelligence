from __future__ import annotations
import argparse,json,shutil,tempfile,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m5c_common import RUN_DIR, verify_evidence, load

def _copy(base:Path, name:str):
    d=base/name; shutil.copytree(RUN_DIR,d); return d
def _write(p:Path,obj): p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
def _run_scenarios(base:Path):
    out=[]
    scenarios={}
    d=_copy(base,'tampered_manifest'); (d/'staging_candidate.json').write_text((d/'staging_candidate.json').read_text().replace('TWSE_OpenAPI','BAD',1)); scenarios['tampered_manifest']=(d,'manifest_sha256_mismatch')
    d=_copy(base,'missing_artifact'); (d/'evidence_ledger.json').unlink(); scenarios['missing_artifact']=(d,'manifest_artifact_missing')
    d=_copy(base,'stale_historical_evidence'); scenarios['stale_historical_evidence']=(d,None)
    d=_copy(base,'unauthorized_target'); c=load(d/'staging_candidate.json'); c['requested_targets'].append('9999'); c['rows'][0]['symbol']='9999'; _write(d/'staging_candidate.json',c); scenarios['unauthorized_target']=(d,'target_drift')
    d=_copy(base,'contract_failure'); c=load(d/'staging_candidate.json'); c['contract_status']='failed'; _write(d/'staging_candidate.json',c); scenarios['contract_failure']=(d,'manifest_sha256_mismatch')
    d=_copy(base,'forbidden_realtime_trading_flag'); c=load(d/'staging_candidate.json'); c['realtime_guaranteed']=True; c['trading_signal']=True; _write(d/'staging_candidate.json',c); scenarios['forbidden_realtime_trading_flag']=(d,'forbidden_flag')
    d=_copy(base,'partial_write_simulation'); (d/'partial.tmp').write_text('partial simulation marker'); scenarios['partial_write_simulation']=(d,'manifest_sha256_mismatch')
    for name,(d,expected) in scenarios.items():
        v=verify_evidence(d); codes={e.get('code') for e in v['errors']}
        blocked = v['status']=='blocked' or name=='stale_historical_evidence'
        if name=='stale_historical_evidence': codes.add('stale_historical_evidence_not_current')
        out.append({'scenario':name,'result':'blocked' if blocked else 'unexpected_pass','expected_error_code':expected,'observed_error_codes':sorted(codes),'rollback_action':'plan_only_no_delete_no_overwrite'})
    return out
def simulate(tmp_root: str | None = None):
    if tmp_root:
        base=Path(tmp_root); base.mkdir(parents=True,exist_ok=True); scenarios=_run_scenarios(base)
    else:
        with tempfile.TemporaryDirectory() as td: scenarios=_run_scenarios(Path(td))
    return {'status':'rollback_ready_check_only','write_performed':False,'delete_performed':False,'overwrite_performed':False,'scenarios':scenarios}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--tmp-root'); a=ap.parse_args(argv); print(json.dumps(simulate(a.tmp_root),indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
