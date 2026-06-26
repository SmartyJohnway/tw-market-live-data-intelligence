import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_fixture_replay_scenarios import run_scenarios
def main(argv=None): ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true'); ap.add_argument('--scenarios',default='tests/fixtures/replay_scenarios/valid_replay_scenarios.json'); a=ap.parse_args(argv); r=run_scenarios(a.scenarios); print(json.dumps(r,indent=2)); return 0 if r['failed']==0 else 1
if __name__=='__main__': raise SystemExit(main())
