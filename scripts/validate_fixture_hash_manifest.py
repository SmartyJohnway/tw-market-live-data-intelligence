import argparse,json,hashlib
from pathlib import Path
def validate_manifest(manifest):
 e=[]
 for row in manifest.get('files',[]):
  p=Path(row['path'])
  if not p.exists(): e.append({'code':'missing_fixture','path':row['path']}); continue
  h=hashlib.sha256(p.read_bytes()).hexdigest()
  if h!=row.get('sha256'): e.append({'code':'hash_mismatch','path':row['path']})
 return e
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); a=ap.parse_args(argv); errs=validate_manifest(json.loads(Path(a.manifest).read_text())); print(json.dumps({'ok':not errs,'errors':errs},indent=2)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
