from __future__ import annotations
import argparse,json
from pathlib import Path
REQ=Path('docs/authorization/requests/M5D_FRONTEND_PUBLICATION_REQUEST.json')
def validate(path=REQ):
 d=json.loads(Path(path).read_text()); errs=[]
 for k in ['actual_frontend_publication_authorized','publication_performed']:
  if d.get(k) is not False: errs.append({'code':'must_be_false','field':k})
 if d.get('next_required_action')!='user_authorization': errs.append({'code':'next_action_must_be_user_authorization'})
 return errs
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument('--request',default=str(REQ)); ns=p.parse_args(argv); errs=validate(ns.request)
 print(json.dumps({'status':'pass' if not errs else 'blocked','errors':errs},indent=2)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
