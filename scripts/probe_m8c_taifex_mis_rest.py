import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8c_taifex_mis_probe_common import build_arg_parser, require_confirmed, redact
if __name__=='__main__':
    p=build_arg_parser('TAIFEX MIS REST preflight'); a=p.parse_args()
    if not require_confirmed(a): print('{"status":"operator_confirmation_required","network_performed":false}'); raise SystemExit(0)
    import requests,json
    s=requests.Session(); base='https://mis.taifex.com.tw/futures/api/'
    endpoints=['getCmdyDDLItemByKind','getCmdyMonthDDLItemByKind','getQuoteList','getQuoteListOption','getQuoteDetail','getCalculatedFields']
    out=[]
    for ep in endpoints:
        try:
            r=s.post(base+ep,json={},headers={'Origin':'https://mis.taifex.com.tw','Referer':'https://mis.taifex.com.tw/futures/'},timeout=10)
            js=None
            try: js=r.json()
            except Exception: pass
            rows=js if isinstance(js,list) else (js.get('RtData') if isinstance(js,dict) else None)
            out.append({'endpoint_id':ep,'status_code':r.status_code,'content_type':r.headers.get('content-type'),'bytes':len(r.content),'top_level':type(js).__name__ if js is not None else 'non_json','row_count':len(rows) if isinstance(rows,list) else None,'keys':list(js)[:20] if isinstance(js,dict) else None})
        except Exception as e: out.append({'endpoint_id':ep,'error':type(e).__name__})
    print(json.dumps(redact(out),ensure_ascii=False))
