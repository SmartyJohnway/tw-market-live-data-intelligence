import argparse,json,tempfile,hashlib
from pathlib import Path
from m5d_publication_common import DEST

def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sim(fail=False):
 with tempfile.TemporaryDirectory() as td:
  dest=Path(td)/DEST; dest.parent.mkdir(parents=True); backup=dest.with_suffix('.json.bak')
  backup.write_text('{"previous":true}\n'); dest.write_text('{"new":true}\n')
  if fail: backup.unlink(); return {'status':'blocked','errors':['rollback_failure'],'publication_performed':False}
  before=h(backup); dest.write_bytes(backup.read_bytes())
  return {'status':'pass','simulation_only':True,'publication_performed':False,'rollback_hash_restored':h(dest),'matches_backup':h(dest)==before}
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--check-only',action='store_true',required=True); p.add_argument('--fail-rollback',action='store_true'); a=p.parse_args(); out=sim(a.fail_rollback); print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['status']=='pass' else 1)
