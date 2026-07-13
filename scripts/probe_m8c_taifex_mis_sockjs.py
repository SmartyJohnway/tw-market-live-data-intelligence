import sys, time, uuid, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8c_taifex_mis_probe_common import *

API='https://mis.taifex.com.tw/futures/api/'
RT='https://mis.taifex.com.tw/futures/rt'
HEAD={'Origin':'https://mis.taifex.com.tw','Referer':'https://mis.taifex.com.tw/futures/'}

def _rows(data):
    rt=data.get('RtData') if isinstance(data,dict) else None
    if isinstance(rt,dict): return rt.get('QuoteList') or rt.get('Items') or []
    return []

def _first_symbol(rows,suffix):
    for r in rows:
        s=str(r.get('SymbolID',''))
        if s.endswith(suffix): return s
    return None

def resolve_symbols(session,start):
    symbols=[]; evidence=[]
    for cid,label in [('TXF','TX'),('MXF','MTX')]:
        st,ct,b,d=bounded_json_post(session,API+'getCmdyMonthDDLItemByKind',json_body={'MarketType':'0','SymbolType':'F','KindID':'1','CID':cid},headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS)
        months=[x.get('item') for x in _rows(d) if str(x.get('item','')).isdigit()]
        month=months[0]
        st,ct,b,d=bounded_json_post(session,API+'getQuoteList',json_body={'MarketType':'0','SymbolType':'F','KindID':'1','CID':cid,'ExpireMonth':month},headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS)
        sym=_first_symbol(_rows(d),'-F'); symbols.append(sym); evidence.append({'requested_product_id':label,'mis_cid':cid,'month':month,'runtime_symbol_id':sym,'rows':len(_rows(d)),'bytes':len(b)})
    st,ct,b,d=bounded_json_post(session,API+'getCmdyMonthDDLItemByKind',json_body={'MarketType':'0','SymbolType':'O','KindID':'1','CID':'TXO'},headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS)
    months=[x.get('item') for x in _rows(d) if str(x.get('item',''))[:6].isdigit()]
    month=months[0]
    st,ct,b,d=bounded_json_post(session,API+'getQuoteListOption',json_body={'MarketType':'0','SymbolType':'O','KindID':'1','CID':'TXO','ExpireMonth':month},headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS)
    opt_rows=_rows(d); enforce_count(len(opt_rows),MAX_OPTION_CHAIN_ROWS,'option_identity_discovery_network_limit_reached')
    opt=next((r for r in opt_rows if str(r.get('SymbolID','')).endswith('-O')), None)
    symbols.append(opt['SymbolID']); evidence.append({'requested_product_id':'TXO','mis_cid':'TXO','month':month,'runtime_symbol_id':opt['SymbolID'],'rows':len(opt_rows),'bytes':len(b),'network_scope':'whole_requested_contract_month_chain'})
    enforce_count(len(symbols),MAX_RUNTIME_SYMBOLS,'symbol_count_limit_reached')
    return symbols,evidence

if __name__=='__main__':
    p=build_arg_parser('TAIFEX MIS SockJS initial-state preflight'); a=p.parse_args()
    if not require_confirmed(a): print('{"status":"operator_confirmation_required","network_performed":false}'); raise SystemExit(0)
    import requests
    start=time.monotonic(); s=requests.Session()
    try:
        symbols,identity=resolve_symbols(s,start)
        info=s.get(RT+'/info',timeout=MAX_SINGLE_POLL_SECONDS).json()
        sid=uuid.uuid4().hex[:12]; server='000'
        ro=s.post(f'{RT}/{server}/{sid}/xhr',headers=HEAD,timeout=MAX_SINGLE_POLL_SECONDS,stream=True)
        open_body=read_bounded_response(ro,max_bytes=MAX_WIRE_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS).decode().strip()
        if open_body!='o': raise M8CProbeError('sockjs_open_frame_missing')
        send_body=encode_sockjs_send([{'type':'subscribe','symbols':symbols}])
        rs=s.post(f'{RT}/{server}/{sid}/xhr_send',data=send_body,headers={**HEAD,'Content-Type':'text/plain;charset=UTF-8'},timeout=MAX_SINGLE_POLL_SECONDS)
        if rs.status_code not in (200,204): raise M8CProbeError('sockjs_send_failure')
        frames=messages=wire=len(open_body.encode())+len(send_body.encode()); quotes={}
        while time.monotonic()-start < MAX_TOTAL_EXECUTION_SECONDS and set(quotes)!=set(symbols):
            enforce_count(frames,MAX_SOCKJS_FRAMES,'frame_limit_reached'); enforce_count(messages,MAX_DECODED_MESSAGES,'decoded_message_limit_reached')
            rp=s.post(f'{RT}/{server}/{sid}/xhr',headers=HEAD,timeout=MAX_SINGLE_POLL_SECONDS,stream=True)
            body=read_bounded_response(rp,max_bytes=MAX_WIRE_BYTES-wire,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS).decode().strip(); wire+=len(body.encode()); frames+=1
            dec=decode_sockjs_frame(body)
            if dec['frame_type']=='close': break
            for m in dec.get('messages',[]):
                messages+=1; q=parse_quote_message(m)
                if q['message_type']=='quote' and q.get('symbol') in symbols:
                    vals=(m.get('quote') or {}).get('values') or {}; tv=(m.get('quote') or {}).get('trueValues') or {}
                    quotes[q['symbol']]={'symbol':q['symbol'],'message_type':'quote','mode':q['mode'],'values_key_count':len(vals),'trueValues_key_count':len(tv),'has_CDate':'144' in vals or 'CDate' in vals,'has_CTime':'143' in vals or 'CTime' in vals,'has_Status':'145' in vals or 'Status' in vals}
        status='successful_initial_state_probe' if set(quotes)==set(symbols) else 'snapshot_incomplete'
        print(json.dumps(redact({'status':status,'symbols':symbols,'identity':identity,'info':{k:info.get(k) for k in ('websocket','cookie_needed','origins')},'open_frame':'o','send_status':rs.status_code,'quotes':list(quotes.values()),'bytes':wire,'frames':frames,'decoded_messages':messages,'duration_seconds':round(time.monotonic()-start,3),'raw_payload_retained':False}),ensure_ascii=False))
    finally:
        s.close()
