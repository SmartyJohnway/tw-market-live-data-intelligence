import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8c_taifex_mis_probe_common import *
API='https://mis.taifex.com.tw/futures/api/'
HEAD={'Origin':'https://mis.taifex.com.tw','Referer':'https://mis.taifex.com.tw/futures/'}

def rows(data):
    rt=data.get('RtData') if isinstance(data,dict) else None
    if isinstance(rt,dict): return rt.get('QuoteList') or rt.get('Items') or []
    return []

def summarize(ep, req, status, ct, body, data):
    rs=rows(data); rt=data.get('RtData') if isinstance(data,dict) else None
    return {'endpoint_id':ep,'request_schema_summary':{k:type(v).__name__ for k,v in req.items()},'status_code':status,'content_type':ct,'RtCode_present':'RtCode' in data,'RtMsg_present':'RtMsg' in data,'RtData_type':type(rt).__name__,'row_count':len(rs),'byte_count':len(body),'identity_fields':[k for k in ('SymbolID','CID','ExpireMonth','StrikePrice','CP','DispEName','DispCName') if rs and k in rs[0]],'field_names':list(rs[0].keys())[:40] if rs else [],'raw_payload_retained':False}

if __name__=='__main__':
 p=build_arg_parser('TAIFEX MIS REST scoped preflight'); a=p.parse_args()
 if not require_confirmed(a): print('{"status":"operator_confirmation_required","network_performed":false}'); raise SystemExit(0)
 import requests
 s=requests.Session(); start=time.monotonic(); out=[]
 try:
  for cid,label in [('TXF','TX'),('MXF','MTX')]:
   req={'MarketType':'0','SymbolType':'F','KindID':'1'}; st,ct,b,d=bounded_json_post(s,API+'getCmdyDDLItemByKind',json_body=req,headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS); out.append(summarize('getCmdyDDLItemByKind',req,st,ct,b,d))
   req={'MarketType':'0','SymbolType':'F','KindID':'1','CID':cid}; st,ct,b,d=bounded_json_post(s,API+'getCmdyMonthDDLItemByKind',json_body=req,headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS); out.append(summarize('getCmdyMonthDDLItemByKind',req,st,ct,b,d)); month=[x['item'] for x in rows(d) if str(x.get('item','')).isdigit()][0]
   req={'MarketType':'0','SymbolType':'F','KindID':'1','CID':cid,'ExpireMonth':month}; st,ct,b,d=bounded_json_post(s,API+'getQuoteList',json_body=req,headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS); rec=summarize('getQuoteList',req,st,ct,b,d); rec['can_narrow_by_contract_month']=rec['row_count']<=2; out.append(rec); sym=next(r['SymbolID'] for r in rows(d) if str(r.get('SymbolID','')).endswith('-F'))
   req={'SymbolID':[sym]}; st,ct,b,d=bounded_json_post(s,API+'getQuoteDetail',json_body=req,headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS); out.append(summarize('getQuoteDetail',req,st,ct,b,d))
  req={'MarketType':'0','SymbolType':'O','KindID':'1','CID':'TXO'}; st,ct,b,d=bounded_json_post(s,API+'getCmdyMonthDDLItemByKind',json_body=req,headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS); out.append(summarize('getCmdyMonthDDLItemByKind',req,st,ct,b,d)); month=[x['item'] for x in rows(d) if str(x.get('item',''))[:6].isdigit()][0]
  base_req={'MarketType':'0','SymbolType':'O','KindID':'1','CID':'TXO','ExpireMonth':month}; variants=[base_req,{**base_req,'RowSize':'10','PageNo':'1'}]
  first_rows=None; opt_sym=None
  for req in variants:
   st,ct,b,d=bounded_json_post(s,API+'getQuoteListOption',json_body=req,headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS); rs=rows(d); first_rows=first_rows or len(rs); opt_sym=opt_sym or next((r['SymbolID'] for r in rs if str(r.get('SymbolID','')).endswith('-O')),None); rec=summarize('getQuoteListOption',req,st,ct,b,d); rec['network_scope']='whole_requested_contract_month_chain'; rec['row_size_page_reduced_network_response']= len(rs)!=first_rows; out.append(rec)
  sample=rows(d)[0]
  req={**base_req,'StrikePrice':sample.get('StrikePrice'),'CP':sample.get('CP')}; st,ct,b,d=bounded_json_post(s,API+'getQuoteListOption',json_body=req,headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS); rec=summarize('getQuoteListOption',req,st,ct,b,d); rec['strike_cp_reduced_network_response']=len(rows(d))!=first_rows; out.append(rec)
  for syms in [[opt_sym], [out[2]['field_names'] and 'TXFG6-F' or opt_sym, opt_sym]]:
   req={'SymbolID':syms}; st,ct,b,d=bounded_json_post(s,API+'getQuoteDetail',json_body=req,headers=HEAD,max_bytes=MAX_BOOTSTRAP_BYTES,start=start,max_seconds=MAX_TOTAL_EXECUTION_SECONDS,timeout=MAX_SINGLE_POLL_SECONDS); out.append(summarize('getQuoteDetail',req,st,ct,b,d))
  print(json.dumps(redact({'status':'rest_scoped_probe_complete','endpoints':out,'raw_payload_retained':False}),ensure_ascii=False))
 finally: s.close()
