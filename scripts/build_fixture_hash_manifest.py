import argparse,json,hashlib
from pathlib import Path
FORBIDDEN_PREFIXES=("frontend/public/","research/generated/","credentials/","cookies/","tokens/","broker/","production/","prod/","current_market_state/")
def is_forbidden_changed_path(path):
    path=str(path).replace("\\\\","/")
    return path == ".env" or any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
def build_manifest(files): return {'files':[{'path':str(f),'sha256':hashlib.sha256(Path(f).read_bytes()).hexdigest()} for f in files]}
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('files',nargs='*'); ap.add_argument('--write-output'); a=ap.parse_args(argv); m=build_manifest(a.files);
 if a.write_output:
  if is_forbidden_changed_path(a.write_output): raise SystemExit('forbidden output path')
  Path(a.write_output).write_text(json.dumps(m,indent=2)+'\n')
 print(json.dumps(m,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
