import argparse,json,hashlib,shutil,tempfile
from pathlib import Path
from m5d_publication_common import CAND,DEST,validate_candidate,ROOT

def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def simulate(existing=False, fail_replace=False):
 e=validate_candidate(CAND); src=ROOT/CAND/'market-context.json'
 if e: return {'status':'blocked','errors':e,'publication_performed':False}
 with tempfile.TemporaryDirectory() as td:
  root=Path(td); dest=root/DEST; dest.parent.mkdir(parents=True)
  before=None
  if existing:
   dest.write_text('{"previous":true}\n'); before=h(dest)
  tmp=dest.with_suffix('.json.tmp')
  shutil.copy2(src,tmp)
  if fail_replace: tmp.unlink(); return {'status':'blocked','errors':['simulated_atomic_replace_failure'],'publication_performed':False,'rollback_required':existing}
  tmp.replace(dest)
  after=h(dest)
  return {'status':'pass','simulation_only':True,'publication_performed':False,'source_sha256':h(src),'destination_sha256_after':after,'destination_sha256_before':before,'destination_already_exists':existing,'hashes_match':h(src)==after}
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--check-only',action='store_true',required=True); p.add_argument('--existing-destination',action='store_true'); p.add_argument('--fail-replace',action='store_true'); a=p.parse_args()
 out=simulate(a.existing_destination,a.fail_replace); print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['status']=='pass' else 1)
