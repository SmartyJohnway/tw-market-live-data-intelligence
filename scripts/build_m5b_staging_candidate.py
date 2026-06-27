from __future__ import annotations
import argparse,json
from pathlib import Path
ALLOWED={'2330','0050','00929'}
def build(run_dir):
    p=Path(run_dir); result=json.loads((p/'bounded_probe_result.json').read_text())
    rows=[r for r in result.get('rows',[]) if r.get('symbol') in ALLOWED]
    if len(rows)!=len(result.get('rows',[])): raise ValueError('unauthorized symbol in bounded result')
    candidate={k:result.get(k) for k in ['run_id','source_id','requested_targets','retained_targets','retrieved_at_utc','source_timestamp','http_status','contract_status','parse_status','normalization_status','failed_targets','errors','caveats','production_current_state','realtime_guaranteed','trading_signal','generated_artifact_promoted','frontend_published']}
    candidate.update({'rows':rows,'staging_only':True,'production_ready':False,'promotion_authorized':False,'frontend_publication_authorized':False,'generated_artifact_write':False})
    (p/'staging_candidate.json').write_text(json.dumps(candidate,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    return candidate
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--run-dir',required=True); a=ap.parse_args(argv)
    try: c=build(a.run_dir); print(json.dumps({'ok':True,'path':str(Path(a.run_dir)/'staging_candidate.json'),'retained_targets':c['retained_targets'],'staging_only':True},indent=2,sort_keys=True)); return 0
    except Exception as e: print(json.dumps({'ok':False,'error':str(e)},indent=2)); return 1
if __name__=='__main__': raise SystemExit(main())
