from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from m5c_common import RUN_DIR,verify_evidence,forbid_path

def plan(run_dir=RUN_DIR,destination='staging/m5c_candidate.json'):
    ev=verify_evidence(run_dir); blocked=ev['status']!='pass' or forbid_path(destination)
    return {'status':'blocked' if blocked else 'planned_check_only','write_performed':False,'proposed_destination':destination,'artifact_delta':['would copy staging_candidate.json after separate authorization'],'lineage':ev,'caveats':['historical_evidence_snapshot','not_current_realtime','actual_promotion_authorized=false'],'required_authorization':'user_authorization'}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--run-dir',default=str(RUN_DIR)); ap.add_argument('--destination',default='staging/m5c_candidate.json'); ap.add_argument('--check-only',action='store_true',default=True)
    a=ap.parse_args(argv); r=plan(a.run_dir,a.destination); print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r['status']!='blocked' else 1
if __name__=='__main__': raise SystemExit(main())
