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
def run():
    ev=verify_evidence(RUN_DIR); cand=load(RUN_DIR/'staging_candidate.json')
    pkg=build_frontend_readonly_context_package(readonly_payload_from_candidate(cand))
    ro_errors=validate_frontend_readonly_context_package(pkg)
    out={'evidence_integrity':ev['status'],'receipt_audit':'pass' if ev.get('receipt_audit') else 'blocked','candidate_eligibility':assess(RUN_DIR)['status'],'request_validation':validate_request(REQ)['status'],'simulation_status':simulate(RUN_DIR)['status'],'rollback_readiness':rollback()['status'],'readonly_compatibility':'pass' if not ro_errors and pkg.get('realtime_guaranteed') is False else 'blocked','actual_promotion_performed':False,'next_required_action':'user_authorization'}
    return out
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true',required=True); ap.parse_args(argv)
    out=run(); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if all(v not in ('blocked',) for v in out.values()) else 1
if __name__=='__main__': raise SystemExit(main())
