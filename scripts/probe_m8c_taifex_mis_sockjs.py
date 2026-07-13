import sys, time, uuid, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8c_taifex_mis_probe_common import *

API='https://mis.taifex.com.tw/futures/api/'
RT='https://mis.taifex.com.tw/futures/rt'
HEAD={'Origin':'https://mis.taifex.com.tw','Referer':'https://mis.taifex.com.tw/futures/'}
CANDIDATE_QIDS={'125':'CLastPrice','129':'CRefPrice','143':'CTime','144':'CDate','145':'Status','404':'CTotalVolume','101':'CBidPrice1','102':'CAskPrice1','113':'CBidSize1','114':'CAskSize1','743':'CBestBidPrice','744':'CBestAskPrice','745':'CBestBidSize','746':'CBestAskSize'}

def _rows(data):
    rt=data.get('RtData') if isinstance(data,dict) else None
    if isinstance(rt,dict): return rt.get('QuoteList') or rt.get('Items') or []
    return []

def _first_symbol(rows,suffix):
    for r in rows:
        s=str(r.get('SymbolID',''))
        if s.endswith(suffix): return s
    raise M8CProbeError('option_identity_not_found')

def resolve_symbols(session,budget):
    symbols=[]; evidence=[]
    budget.add_products(3)
    for cid,label in [('TXF','TX'),('MXF','MTX')]:
        st,ct,b,d=budgeted_json_post(session,API+'getCmdyMonthDDLItemByKind',json_body={'MarketType':'0','SymbolType':'F','KindID':'1','CID':cid},headers=HEAD,budget=budget)
        months=[x.get('item') for x in _rows(d) if str(x.get('item','')).isdigit()]
        budget.add_rows(len(_rows(d))); budget.add_months(1)
        month=months[0]
        st,ct,b,d=budgeted_json_post(session,API+'getQuoteList',json_body={'MarketType':'0','SymbolType':'F','KindID':'1','CID':cid,'ExpireMonth':month},headers=HEAD,budget=budget)
        rows=_rows(d); budget.add_rows(len(rows)); sym=_first_symbol(rows,'-F')
        symbols.append(sym); evidence.append({'requested_product_id':label,'mis_cid':cid,'month':month,'runtime_symbol_id':sym,'rows':len(rows),'bytes':len(b)})
    st,ct,b,d=budgeted_json_post(session,API+'getCmdyMonthDDLItemByKind',json_body={'MarketType':'0','SymbolType':'O','KindID':'1','CID':'TXO'},headers=HEAD,budget=budget)
    months=[x.get('item') for x in _rows(d) if str(x.get('item',''))[:6].isdigit()]
    budget.add_rows(len(_rows(d))); budget.add_months(1)
    month=months[0]
    st,ct,b,d=budgeted_json_post(session,API+'getQuoteListOption',json_body={'MarketType':'0','SymbolType':'O','KindID':'1','CID':'TXO','ExpireMonth':month},headers=HEAD,budget=budget)
    opt_rows=_rows(d); budget.add_rows(len(opt_rows),'option_identity_discovery_network_limit_reached')
    opt=next((r for r in opt_rows if str(r.get('SymbolID','')).endswith('-O')), None)
    if not opt: raise M8CProbeError('option_identity_not_found')
    symbols.append(opt['SymbolID']); evidence.append({'requested_product_id':'TXO','mis_cid':'TXO','month':month,'runtime_symbol_id':opt['SymbolID'],'rows':len(opt_rows),'bytes':len(b),'network_scope':'whole_requested_contract_month_chain'})
    budget.add_symbols(len(symbols))
    return symbols,evidence

def quote_summary(message):
    quote=(message.get('quote') or {}); vals=quote.get('values') or {}; tv=quote.get('trueValues') or {}
    present={qid:(qid in vals or name in vals) for qid,name in CANDIDATE_QIDS.items()}
    q=parse_quote_message(message)
    return {'symbol':q['symbol'],'message_type':'quote','mode':q['mode'],'values_key_count':len(vals),'trueValues_key_count':len(tv),'candidate_qid_present':present,'has_CDate':present['144'],'has_CTime':present['143'],'has_Status':present['145']}

if __name__=='__main__':
    p=build_arg_parser('TAIFEX MIS SockJS initial-state preflight'); a=p.parse_args()
    if not require_confirmed(a): print('{"status":"operator_confirmation_required","network_performed":false}'); raise SystemExit(0)
    import requests
    budget=ProbeBudget(); s=requests.Session()
    try:
        symbols,identity=resolve_symbols(s,budget)
        st,ct,info_body=budgeted_get(s,RT+'/info',headers=HEAD,budget=budget,max_response_bytes=4096)
        info=json.loads(info_body.decode('utf-8'))
        sid=uuid.uuid4().hex[:12]; server='000'
        ro=s.post(f'{RT}/{server}/{sid}/xhr',headers=HEAD,timeout=budget.timeout(),stream=True)
        open_body=read_budgeted_response(ro,budget=budget,max_response_bytes=MAX_WIRE_BYTES).decode().strip()
        if open_body!='o': raise M8CProbeError('sockjs_open_frame_missing')
        budget.add_frame()  # open frame
        send_body=encode_sockjs_send([{'type':'subscribe','symbols':symbols}])
        send_status,send_ct,send_resp=budgeted_post_raw(s,f'{RT}/{server}/{sid}/xhr_send',data=send_body,headers={**HEAD,'Content-Type':'text/plain;charset=UTF-8'},budget=budget,max_response_bytes=4096)
        if send_status not in (200,204): raise M8CProbeError('sockjs_send_failure')
        quotes={}
        while budget.remaining() > 0 and set(quotes)!=set(symbols):
            rp=s.post(f'{RT}/{server}/{sid}/xhr',headers=HEAD,timeout=budget.timeout(),stream=True)
            body=read_budgeted_response(rp,budget=budget,max_response_bytes=MAX_WIRE_BYTES).decode().strip()
            budget.add_frame()
            dec=decode_sockjs_frame(body)
            budget.add_messages(len(dec.get('messages',[])))
            if dec['frame_type']=='close': break
            for m in dec.get('messages',[]):
                q=parse_quote_message(m)
                if q['message_type']=='quote' and q.get('symbol') in symbols:
                    quotes[q['symbol']]=quote_summary(m)
        status='successful_initial_state_probe' if set(quotes)==set(symbols) else 'snapshot_incomplete'
        print(json.dumps(redact({'status':status,'symbols':symbols,'identity':identity,'info':{k:info.get(k) for k in ('websocket','cookie_needed','origins')},'open_frame':'o','send_status':send_status,'quotes':list(quotes.values()),'wire_bytes':budget.wire_bytes,'frame_count':budget.frame_count,'decoded_message_count':budget.decoded_message_count,'duration_seconds':round(time.monotonic()-budget.started,3),'raw_payload_retained':False}),ensure_ascii=False))
    finally:
        s.close()
