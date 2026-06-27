from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pathlib import Path
from m5c_common import RUN_ID,TARGETS,SOURCE,MERGE_COMMIT,RUN_DIR,verify_evidence,candidate_hash,manifest_hash

def validate_request(path):
    req=json.loads(Path(path).read_text()); errs=[]; ev=verify_evidence(req.get('source_run_dir',RUN_DIR))
    checks={'source_run_id':RUN_ID,'source_id':SOURCE,'merge_commit':MERGE_COMMIT,'source_manifest_sha256':manifest_hash(req.get('source_run_dir',RUN_DIR)),'staging_candidate_sha256':candidate_hash(req.get('source_run_dir',RUN_DIR))}
    for k,v in checks.items():
        if req.get(k)!=v: errs.append({'code':'binding_mismatch','field':k})
    if set(req.get('targets',[]))!=set(TARGETS): errs.append({'code':'target_binding_mismatch'})
    for k in ['dry_run_only']:
        if req.get(k) is not True: errs.append({'code':'required_true','field':k})
    for k in ['actual_promotion_authorized','production_write','frontend_public_write','generated_artifact_write','trading_output']:
        if req.get(k) is not False: errs.append({'code':'required_false','field':k})
    if 'approval_token' in req or 'authorization_decision' in req: errs.append({'code':'decision_or_token_forbidden'})
    if ev['status']!='pass': errs.append({'code':'evidence_blocked','errors':ev['errors']})
    return {'status':'pass' if not errs else 'blocked','errors':errs,'request_path':str(path)}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('request'); a=ap.parse_args(argv); print(json.dumps(validate_request(a.request),indent=2,sort_keys=True)); return 0 if validate_request(a.request)['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
