#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist, preflight

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def main():
    p=argparse.ArgumentParser(description='Run M8R-03D governed watchlist controlled execution')
    p.add_argument('--request',required=True); p.add_argument('--mode',choices=['preflight','fixture','execute'],required=True); p.add_argument('--bundle-type',choices=['snapshot','performance'],required=True)
    p.add_argument('--authorization'); p.add_argument('--fixture-source-data'); p.add_argument('--artifact-root',default='artifacts/m8r_03d'); p.add_argument('--run-id'); p.add_argument('--generated-at-utc')
    for bad in ('poll','schedule','watch','continuous'): p.add_argument('--'+bad,action='store_true')
    a=p.parse_args()
    if a.poll or a.schedule or a.watch or a.continuous: print('polling/scheduler/continuous execution rejected',file=sys.stderr); return 2
    req=load(a.request); auth=load(a.authorization) if a.authorization else None; fixture=load(a.fixture_source_data) if a.fixture_source_data else None
    out=execute_watchlist(req,mode=a.mode,bundle_type=a.bundle_type,authorization=auth,fixture_source_data=fixture,artifact_root=a.artifact_root,run_id=a.run_id,generated_at_utc=a.generated_at_utc)
    print(json.dumps({'mode':out['mode'],'run_id':out['run_id'],'request_hash':out['request_hash'],'target_count':len(req['persistent_watchlist_reference']['enabled_target_ids']),'planned_source_calls':len(out['source_execution_summary']['planned_source_call_groups']),'observation_count':out['observation_count'],'bundle_status':out['status'],'artifact_paths':out.get('artifact_paths',{})},ensure_ascii=False,sort_keys=True,indent=2))
    return 0 if out['status'] in {'success','success_with_partial_coverage','blocked_preflight'} else 1
if __name__=='__main__': raise SystemExit(main())
