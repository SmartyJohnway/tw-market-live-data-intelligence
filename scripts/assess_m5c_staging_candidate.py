from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m5c_common import RUN_DIR,verify_evidence,load,readonly_payload_from_candidate

def assess(run_dir=RUN_DIR):
    v=verify_evidence(run_dir)
    status='eligible_for_user_authorization' if v['status']=='pass' else 'blocked'
    return {'status':status,'evidence_integrity':v,'historical_evidence_snapshot':True,'current_realtime':False,'actual_promotion_authorized':False,'dry_run_only':True}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--run-dir',default=str(RUN_DIR)); ap.add_argument('--check-only',action='store_true',default=True)
    a=ap.parse_args(argv); print(json.dumps(assess(a.run_dir),indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
