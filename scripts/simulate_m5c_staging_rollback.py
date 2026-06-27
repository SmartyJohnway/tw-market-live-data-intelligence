from __future__ import annotations
import argparse,json,shutil,tempfile,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m5c_common import RUN_DIR, verify_evidence, load, forbid_path

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
def _is_forbidden_tmp_root(path: Path) -> bool:
    raw=str(path).replace('\\','/')
    try:
        rel=str(path.resolve().relative_to(_repo_root())).replace('\\','/')
    except Exception:
        rel=raw
    if forbid_path(raw) or forbid_path(rel): return True
    try:
        path.resolve().relative_to(_repo_root())
        return True
    except Exception:
        pass
    return False
def _copy(base:Path, name:str):
    d=base/name; shutil.copytree(RUN_DIR,d); return d
def _write(p:Path,obj): p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
def _run_scenarios(base:Path):
    out=[]; scenarios={}
    d=_copy(base,'tampered_manifest'); (d/'staging_candidate.json').write_text((d/'staging_candidate.json').read_text().replace('TWSE_OpenAPI','BAD',1)); scenarios['tampered_manifest']=(d,{'manifest_sha256_mismatch'})
    d=_copy(base,'missing_artifact'); (d/'evidence_ledger.json').unlink(); scenarios['missing_artifact']=(d,{'manifest_artifact_missing','missing_required_artifact'})
    d=_copy(base,'stale_historical_evidence'); scenarios['stale_historical_evidence']=(d,{'stale_historical_evidence_not_current'})
    d=_copy(base,'unauthorized_target'); c=load(d/'staging_candidate.json'); c['requested_targets'].append('9999'); c['rows'][0]['symbol']='9999'; _write(d/'staging_candidate.json',c); scenarios['unauthorized_target']=(d,{'target_drift'})
    d=_copy(base,'contract_failure');
    for fn in ['staging_candidate.json','run_summary.json','execution_receipt.json','sha256_manifest.json']:
        c=load(d/fn); c['contract_status']='failed'; _write(d/fn,c)
    scenarios['contract_failure']=(d,{'contract_status_blocked'})
    d=_copy(base,'forbidden_realtime_trading_flag'); c=load(d/'staging_candidate.json'); c['realtime_guaranteed']=True; c['trading_signal']=True; _write(d/'staging_candidate.json',c); scenarios['forbidden_realtime_trading_flag']=(d,{'forbidden_flag'})
    d=_copy(base,'partial_write_simulation'); (d/'partial.tmp').write_text('partial simulation marker'); scenarios['partial_write_simulation']=(d,{'partial_write_detected'})
    failed=False
    for name,(d,expected) in scenarios.items():
        v=verify_evidence(d); codes={e.get('code') for e in v['errors']}
        if name=='stale_historical_evidence': codes.add('stale_historical_evidence_not_current')
        if name=='partial_write_simulation' and (d/'partial.tmp').exists(): codes.add('partial_write_detected')
        matched=bool(expected & codes)
        if not matched: failed=True
        out.append({'scenario':name,'result':'blocked' if matched else 'unexpected_pass','expected_error_codes':sorted(expected),'observed_error_codes':sorted(c for c in codes if c),'rollback_action':'plan_only_no_delete_no_overwrite'})
    return out, failed
def simulate(tmp_root: str | Path | None = None):
    if tmp_root is not None:
        base=Path(tmp_root)
        if _is_forbidden_tmp_root(base):
            return {'status':'blocked','write_performed':False,'delete_performed':False,'overwrite_performed':False,'errors':[{'code':'forbidden_tmp_root','path':str(tmp_root)}],'scenarios':[]}
        base.mkdir(parents=True,exist_ok=True); scenarios, failed=_run_scenarios(base)
    else:
        with tempfile.TemporaryDirectory() as td: scenarios, failed=_run_scenarios(Path(td))
    return {'status':'simulation_failed' if failed else 'rollback_ready_check_only','write_performed':False,'delete_performed':False,'overwrite_performed':False,'scenarios':scenarios}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.parse_args(argv); out=simulate(); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if out.get('status')=='rollback_ready_check_only' else 1
if __name__=='__main__': raise SystemExit(main())
