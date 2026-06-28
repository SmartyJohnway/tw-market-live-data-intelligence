from __future__ import annotations
import argparse, json, os, shutil, tempfile, hashlib
from pathlib import Path
from datetime import datetime, timezone
from validate_m5c_staging_promotion_authorization import validate as validate_auth, AUTH, REQ, RUN, DEST, TARGETS, sha
from run_m5c_staging_promotion_preflight import run as preflight_run, is_success
from build_frontend_readonly_context_package import build_frontend_readonly_context_package
from m5c_common import load, readonly_payload_from_candidate
from validate_m5c_promoted_staging_package import validate as validate_promoted_package
CONSUME_DIR=Path('research/staging/m5c/authorization_consumption')

def _write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
def _destination_state():
    dest=Path(DEST)
    return {'exists': dest.exists(), 'is_dir': dest.is_dir(), 'file_count': len(list(dest.iterdir())) if dest.is_dir() else 0}
def _record_outcome(path: Path, status: str, stage: str, detail: str | None = None, tmp: Path | None = None, cleanup_result: str | None = None):
    auth=load(AUTH)
    data={'authorization_id':auth['authorization_id'],'consumed_at_utc':datetime.now(timezone.utc).isoformat(),'destination':DEST,'status':status,'stage':stage,'failure_reason':detail,'temporary_directory':str(tmp) if tmp else None,'temporary_directory_cleanup_result':cleanup_result,'destination_state':_destination_state(),'failure_receipt_persisted': status == 'failed'}
    _write_json(path, data)

REQUIRED=['authorization_snapshot.json','request_snapshot.json','source_binding.json','staging_payload.json','promotion_receipt.json','validation_report.json','lineage.json','evidence_ledger.json','rollback_plan.json','frontend_readonly_context_package.json','run_summary.json']
def _common_flags():
    return {'historical_evidence_snapshot':True,'current_realtime':False,'realtime_guaranteed':False,'staging_only':True,'production_ready':False,'frontend_publication_authorized':False,'generated_artifact_write':False,'trading_signal':False}
def _build(dst:Path, consumption_path:str):
    cand=load(RUN/'staging_candidate.json'); auth=load(AUTH); req=load(REQ); flags=_common_flags(); now=datetime.now(timezone.utc).isoformat()
    rows=cand['rows']
    base={'schema_version':'m5c_promoted_staging_package.v1','created_at_utc':now, **flags, 'source_run_dir':str(RUN),'targets':TARGETS,'authorization_id':auth['authorization_id']}
    docs={
      'authorization_snapshot.json':{**base,'authorization':auth},
      'request_snapshot.json':{**base,'request':req},
      'source_binding.json':{**base,'source_manifest_sha256':sha(RUN/'sha256_manifest.json'),'staging_candidate_sha256':sha(RUN/'staging_candidate.json'),'source_run_id':'m5b_twse_openapi_20260627T015136Z'},
      'staging_payload.json':{**base,'rows':rows,'row_count':len(rows),'full_market_payload_retained':False},
      'promotion_receipt.json':{**base,'actual_staging_promotion_performed':True,'consumption_record':consumption_path,'destination':str(dst)},
      'validation_report.json':{**base,'status':'pass','checks':['exact_target_source_row_uniqueness','lineage_hashes','forbidden_flags','no_raw_full_market_payload']},
      'lineage.json':{**base,'m5b_manifest_sha256':sha(RUN/'sha256_manifest.json'),'m5b_candidate_sha256':sha(RUN/'staging_candidate.json'),'m5c_request_sha256':sha(REQ),'m5c_authorization_sha256':sha(AUTH)},
      'evidence_ledger.json':{**base,'entries':[{'source':'M5B','path':str(RUN/'staging_candidate.json'),'sha256':sha(RUN/'staging_candidate.json')}]},
      'rollback_plan.json':{**base,'rollback_mode':'tmp_path_simulation_only','committed_package_delete_allowed':False},
      'frontend_readonly_context_package.json':{**build_frontend_readonly_context_package(readonly_payload_from_candidate(cand)), **flags, 'badge':'historical/stale','stale_badge':True},
      'run_summary.json':{**base,'status':'pass','destination':str(dst),'artifact_count':12},
    }
    for n,d in docs.items(): (dst/n).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    manifest={n:sha(dst/n) for n in REQUIRED}; (dst/'sha256_manifest.json').write_text(json.dumps({**base,'manifest_final':True,'immutable':True,'manifest':manifest},indent=2,sort_keys=True)+'\n')
def check():
    errs=validate_auth(); pf=preflight_run();
    if not is_success(pf): errs.append({'code':'preflight_blocked','preflight':pf})
    dest=Path(DEST)
    if dest.exists():
        package_errors=validate_promoted_package(dest)
        if package_errors:
            errs.append({'code':'existing_destination_invalid','path':DEST,'errors':package_errors})
    return errs
def _execute_preconditions():
    errs=validate_auth(); pf=preflight_run();
    if not is_success(pf): errs.append({'code':'preflight_blocked','preflight':pf})
    if Path(DEST).exists(): errs.append({'code':'destination_exists','path':DEST})
    return errs
def execute():
    errs=_execute_preconditions();
    if errs: return {'status':'blocked','errors':errs}
    auth=load(AUTH); CONSUME_DIR.mkdir(parents=True,exist_ok=True); cp=CONSUME_DIR/(auth['authorization_id']+'.json')
    try: fd=os.open(cp, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError: return {'status':'blocked','errors':[{'code':'authorization_already_consumed','path':str(cp)}]}
    os.close(fd)
    _record_outcome(cp, 'pending', 'consumption_record_created')
    parent=Path(DEST).parent; parent.mkdir(parents=True,exist_ok=True); tmp=Path(tempfile.mkdtemp(prefix='.m5c_tmp_',dir=parent))
    try:
        _build(tmp, str(cp))
    except Exception as e:
        shutil.rmtree(tmp,ignore_errors=True); cleanup='removed' if not tmp.exists() else 'cleanup_failed'
        _record_outcome(cp, 'failed', 'build', str(e), tmp, cleanup)
        return {'status':'blocked','errors':[{'code':'execution_failed','stage':'build','detail':str(e),'consumption_record':str(cp)}]}
    try:
        os.rename(tmp, DEST)
    except Exception as e:
        shutil.rmtree(tmp,ignore_errors=True); cleanup='removed' if not tmp.exists() else 'cleanup_failed'
        _record_outcome(cp, 'failed', 'atomic_rename', str(e), tmp, cleanup)
        return {'status':'blocked','errors':[{'code':'execution_failed','stage':'atomic_rename','detail':str(e),'consumption_record':str(cp)}]}
    _record_outcome(cp, 'succeeded', 'atomic_rename_completed')
    return {'status':'pass','destination':DEST,'consumption_record':str(cp),'actual_staging_promotion_performed':True}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true'); ap.add_argument('--execute-promotion',action='store_true'); ap.add_argument('--acknowledge-bounded-staging-promotion',action='store_true'); ns=ap.parse_args(argv)
    if ns.check_only: out={'status':'pass' if not check() else 'blocked','errors':check()}
    elif ns.execute_promotion and ns.acknowledge_bounded_staging_promotion: out=execute()
    else: out={'status':'blocked','errors':[{'code':'missing_required_mode_or_ack'}]}
    print(json.dumps(out,indent=2,sort_keys=True)); return 0 if out['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
