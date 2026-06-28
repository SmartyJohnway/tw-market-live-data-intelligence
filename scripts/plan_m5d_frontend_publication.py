from __future__ import annotations
import json
from validate_m5d_frontend_publication_request import validate

def plan():
    errors=validate()
    if errors:
        return {'status':'blocked','plan_only':True,'frontend_public_write':False,'next_required_action':'repair_request_or_package','errors':errors}
    return {'status':'pass','plan_only':True,'frontend_public_write':False,'next_required_action':'user_authorization'}
def main():
    out=plan(); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if out['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
