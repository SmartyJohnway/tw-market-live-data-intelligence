import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8c_taifex_mis_probe_common import build_arg_parser, require_confirmed, redact
if __name__=='__main__':
    p=build_arg_parser('TAIFEX MIS SockJS preflight'); p.add_argument('--symbols',nargs='*',default=[]); a=p.parse_args()
    if not require_confirmed(a): print('{"status":"operator_confirmation_required","network_performed":false}'); raise SystemExit(0)
    import requests,json
    s=requests.Session(); r=s.get('https://mis.taifex.com.tw/futures/rt/info',timeout=10)
    info=r.json() if r.headers.get('content-type','').startswith('application/json') else {}
    
    import uuid
    server='000'; sess=uuid.uuid4().hex[:12]
    open_url=f'https://mis.taifex.com.tw/futures/rt/{server}/{sess}/xhr'
    open_status=None; open_frame=None
    try:
        ro=s.post(open_url,headers={'Origin':'https://mis.taifex.com.tw','Referer':'https://mis.taifex.com.tw/futures/'},timeout=10)
        open_status=ro.status_code; open_frame=ro.text[:20]
    except Exception as e:
        open_status=type(e).__name__
    print(json.dumps(redact({'info_status':r.status_code,'info':{k:info.get(k) for k in ('websocket','cookie_needed','origins')},'xhr_open_status':open_status,'xhr_open_frame':open_frame}),ensure_ascii=False))
