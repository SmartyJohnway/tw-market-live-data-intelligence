from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from m5c_common import RUN_DIR,verify_evidence,load,readonly_payload_from_candidate
from assess_m5c_staging_candidate import assess
from validate_m5c_staging_promotion_request import validate_request
from simulate_m5c_staging_promotion import simulate
from simulate_m5c_staging_rollback import simulate as rollback
from build_frontend_readonly_context_package import build_frontend_readonly_context_package, validate_frontend_readonly_context_package
REQ='docs/authorization/requests/M5C_TWSE_OPENAPI_STAGING_PROMOTION_REQUEST.json'
SUCCESS={'evidence_integrity':'pass','receipt_audit':'pass','candidate_eligibility':'eligible_for_user_authorization','request_validation':'pass','simulation_status':'planned_check_only','rollback_readiness':'rollback_ready_check_only','readonly_compatibility':'pass','actual_promotion_performed':False,'next_required_action':'user_authorization'}
def _blocked_summary(ev=None, err=None):
    return {'evidence_integrity': (ev or {}).get('status','blocked'),'receipt_audit':'pass' if (ev or {}).get('receipt_audit') else 'blocked','candidate_eligibility':'blocked','request_validation':'blocked','simulation_status':'blocked','rollback_readiness':'blocked','readonly_compatibility':'blocked','actual_promotion_performed':False,'next_required_action':'user_authorization','errors': ([] if err is None else [err]) + list((ev or {}).get('errors',[]))}
def run(run_dir=RUN_DIR):
    ev=verify_evidence(run_dir)
    if ev['status']!='pass': return _blocked_summary(ev)
    try:
        cand=load(Path(run_dir)/'staging_candidate.json')
        pkg=build_frontend_readonly_context_package(readonly_payload_from_candidate(cand))
        ro_errors=validate_frontend_readonly_context_package(pkg)
    except Exception as exc:
        return _blocked_summary(ev, {'code':'preflight_exception','detail':str(exc)})
    out={'evidence_integrity':ev['status'],'receipt_audit':'pass' if ev.get('receipt_audit') else 'blocked','candidate_eligibility':assess(run_dir)['status'],'request_validation':validate_request(REQ)['status'],'simulation_status':simulate(run_dir)['status'],'rollback_readiness':rollback()['status'],'readonly_compatibility':'pass' if not ro_errors and pkg.get('realtime_guaranteed') is False else 'blocked','actual_promotion_performed':False,'next_required_action':'user_authorization'}
    return out
def is_success(out):
    return all(out.get(k)==v for k,v in SUCCESS.items())
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true',required=True); ap.parse_args(argv)
    out=run(); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if is_success(out) else 1
if __name__=='__main__': raise SystemExit(main())
