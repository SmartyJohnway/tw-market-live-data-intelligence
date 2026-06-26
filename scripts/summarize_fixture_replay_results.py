import argparse,json
from pathlib import Path
def summarize_replay_results(results): return {'total_scenarios':results.get('total_scenarios',0),'pass':results.get('passed',0),'fail':results.get('failed',0),'valid':sum(1 for r in results.get('results',[]) if r.get('validation_status')=='valid'),'invalid':sum(1 for r in results.get('results',[]) if r.get('validation_status')=='invalid'),'caveats':['not_production_current_state'],'forbidden_behavior_detections':sum(len(r.get('errors',[])) for r in results.get('results',[])),'production_current_state_claim':False}
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--results',required=True); a=ap.parse_args(argv); print(json.dumps(summarize_replay_results(json.loads(Path(a.results).read_text())),indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
