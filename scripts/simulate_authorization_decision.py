import argparse,json
FORBIDDEN={'live_probe','production_refresh','frontend_publication','trading_signal'}
def simulate_decision(token, action):
 return {'action':action,'allowed': action in token.get('allowed_actions',[]) and action not in token.get('forbidden_actions',[]) and action not in FORBIDDEN,'reason':'simulation_only'}
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--token'); ap.add_argument('--action',required=True); a=ap.parse_args(argv); token=json.loads(Path(a.token).read_text()) if a.token else {'allowed_actions':[],'forbidden_actions':list(FORBIDDEN)}; print(json.dumps(simulate_decision(token,a.action),indent=2)); return 0
from pathlib import Path
if __name__=='__main__': raise SystemExit(main())
