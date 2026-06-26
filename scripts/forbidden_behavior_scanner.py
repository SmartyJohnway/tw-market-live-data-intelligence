import argparse,json,re
from pathlib import Path
PATTERNS={'live_probe_execution':r'\b(run|execute|start)\b.*live probe','production_write':r'production write|write.*production','frontend_public_write':r'frontend/public','research_generated_write':r'research/generated','broker_auth_activation':r'broker|auth activation','trading_signal':r'\b(buy|sell|hold)\b|target price|ranking|recommendation','realtime_guarantee':r'realtime guaranteed|real-time guaranteed|official realtime'}
EXCLUSIONS=[r'no .*',r'not .*',r'forbidden .*',r'.* docs?',r'.* blocked',r'.* unauthorized']
def scan_text(text,path='<text>'):
 out=[]
 for i,line in enumerate(text.splitlines(),1):
  l=line.lower()
  if any(re.search(x,l) for x in EXCLUSIONS): continue
  for code,pat in PATTERNS.items():
   if re.search(pat,l): out.append({'code':code,'path':path,'line':i,'text':line.strip()})
 return out
def scan_files(files):
 res=[]
 for f in files: res += scan_text(Path(f).read_text(encoding='utf-8'), f)
 return res
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('files',nargs='*'); ap.add_argument('--json',action='store_true'); a=ap.parse_args(argv); r=scan_files(a.files); print(json.dumps({'ok':not r,'findings':r},indent=2)); return 0 if not r else 1
if __name__=='__main__': raise SystemExit(main())
