import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.controlled_refresh_staging_validator import validate_controlled_refresh_staging_payload
def run_scenarios(path):
 data=json.loads(Path(path).read_text()); results=[]; events=[]
 for s in data.get('scenarios',[]):
  events.append({'event_type':'scenario_loaded','scenario_id':s['scenario_id']})
  payload=json.loads(Path(s['input_fixture']).read_text())
  errs=validate_controlled_refresh_staging_payload(payload); status='valid' if not errs else 'invalid'
  events.append({'event_type':'staging_validated' if not errs else 'staging_rejected','scenario_id':s['scenario_id']})
  results.append({'scenario_id':s['scenario_id'],'validation_status':status,'passed':status==s['expected_validation_status'],'errors':errs})
 events.append({'event_type':'summary_completed'}); return {'total_scenarios':len(results),'passed':sum(r['passed'] for r in results),'failed':sum(not r['passed'] for r in results),'results':results,'audit_events':events,'production_current_state_claim':False}
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--scenarios',default='tests/fixtures/replay_scenarios/valid_replay_scenarios.json'); ap.add_argument('--check-only',action='store_true'); ap.add_argument('--write-output'); a=ap.parse_args(argv); r=run_scenarios(a.scenarios); print(json.dumps(r,indent=2)); return 0 if r['failed']==0 else 1
if __name__=='__main__': raise SystemExit(main())
