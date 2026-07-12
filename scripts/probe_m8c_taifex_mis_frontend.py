import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8c_taifex_mis_probe_common import build_arg_parser, require_confirmed
if __name__=='__main__':
    p=build_arg_parser('TAIFEX MIS frontend preflight')
    a=p.parse_args()
    if not require_confirmed(a): print('{"status":"operator_confirmation_required","network_performed":false}'); raise SystemExit(0)
    import requests, re, json
    r=requests.get('https://mis.taifex.com.tw/futures/',timeout=10)
    text=r.text[:200000]
    print(json.dumps({'status_code':r.status_code,'bytes':len(r.content),'sockjs_1_4_0_hint':'sockjs' in text.lower() and '1.4.0' in text,'api_base_hint':'/futures/api/' in text,'rt_base_hint':'/futures/rt' in text,'script_count':len(re.findall(r'<script',text,re.I))},ensure_ascii=False))
