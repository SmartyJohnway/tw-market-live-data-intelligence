import argparse,json,sys
from m5d_publication_common import validate_candidate,CAND
p=argparse.ArgumentParser(); p.add_argument('--candidate-dir',default=str(CAND)); a=p.parse_args()
e=validate_candidate(a.candidate_dir); print(json.dumps({'status':'pass' if not e else 'fail','errors':e},indent=2)); sys.exit(0 if not e else 1)
