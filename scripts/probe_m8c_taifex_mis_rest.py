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

def post(s, budget, ep, req):
    return budgeted_json_post(s,API+ep,json_body=req,headers=HEAD,budget=budget,max_response_bytes=MAX_BOOTSTRAP_BYTES)

if __name__=='__main__':
 p=build_arg_parser('TAIFEX MIS REST scoped preflight'); a=p.parse_args()
 if not require_confirmed(a): print('{"status":"operator_confirmation_required","network_performed":false}'); raise SystemExit(0)
 import requests
 s=requests.Session(); budget=ProbeBudget(); out=[]; tx_symbol=mtx_symbol=opt_sym=None
 try:
  budget.add_products(3)
  for cid,label in [('TXF','TX'),('MXF','MTX')]:
   req={'MarketType':'0','SymbolType':'F','KindID':'1'}; st,ct,b,d=post(s,budget,'getCmdyDDLItemByKind',req); budget.add_rows(len(rows(d))); out.append(summarize('getCmdyDDLItemByKind',req,st,ct,b,d))
   req={'MarketType':'0','SymbolType':'F','KindID':'1','CID':cid}; st,ct,b,d=post(s,budget,'getCmdyMonthDDLItemByKind',req); rws=rows(d); budget.add_rows(len(rws)); budget.add_months(1); out.append(summarize('getCmdyMonthDDLItemByKind',req,st,ct,b,d)); month=[x['item'] for x in rws if str(x.get('item','')).isdigit()][0]
   req={'MarketType':'0','SymbolType':'F','KindID':'1','CID':cid,'ExpireMonth':month}; st,ct,b,d=post(s,budget,'getQuoteList',req); rws=rows(d); budget.add_rows(len(rws)); rec=summarize('getQuoteList',req,st,ct,b,d); rec['can_narrow_by_contract_month']=rec['row_count']<=2; out.append(rec); sym=next(r['SymbolID'] for r in rws if str(r.get('SymbolID','')).endswith('-F'))
   if label=='TX': tx_symbol=sym
   else: mtx_symbol=sym
   req={'SymbolID':[sym]}; st,ct,b,d=post(s,budget,'getQuoteDetail',req); budget.add_rows(len(rows(d))); out.append(summarize('getQuoteDetail',req,st,ct,b,d))
  req={'MarketType':'0','SymbolType':'O','KindID':'1','CID':'TXO'}; st,ct,b,d=post(s,budget,'getCmdyMonthDDLItemByKind',req); rws=rows(d); budget.add_rows(len(rws)); budget.add_months(1); out.append(summarize('getCmdyMonthDDLItemByKind',req,st,ct,b,d)); month=[x['item'] for x in rws if str(x.get('item',''))[:6].isdigit()][0]
  base_req={'MarketType':'0','SymbolType':'O','KindID':'1','CID':'TXO','ExpireMonth':month}; variants=[base_req,{**base_req,'RowSize':'10','PageNo':'1'}]
  first_rows=None; sample=None
  for req in variants:
   st,ct,b,d=post(s,budget,'getQuoteListOption',req); rws=rows(d); budget.add_rows(len(rws),'option_identity_discovery_network_limit_reached'); first_rows=first_rows or len(rws); sample=sample or rws[0]; opt_sym=opt_sym or next((r['SymbolID'] for r in rws if str(r.get('SymbolID','')).endswith('-O')),None); rec=summarize('getQuoteListOption',req,st,ct,b,d); rec['network_scope']='whole_requested_contract_month_chain'; rec['row_size_page_reduced_network_response']= len(rws)!=first_rows; out.append(rec)
  req={**base_req,'StrikePrice':sample.get('StrikePrice'),'CP':sample.get('CP')}; st,ct,b,d=post(s,budget,'getQuoteListOption',req); rws=rows(d); budget.add_rows(len(rws),'option_identity_discovery_network_limit_reached'); rec=summarize('getQuoteListOption',req,st,ct,b,d); rec['strike_cp_reduced_network_response']=len(rws)!=first_rows; out.append(rec)
  for syms in [[opt_sym], [tx_symbol, mtx_symbol, opt_sym]]:
   req={'SymbolID':syms}; budget.add_symbols(len(syms)); st,ct,b,d=post(s,budget,'getQuoteDetail',req); budget.add_rows(len(rows(d))); out.append(summarize('getQuoteDetail',req,st,ct,b,d))
  req={'SymbolID':[tx_symbol]}; st,ct,b,d=post(s,budget,'getCalculatedFields',req); rec=summarize('getCalculatedFields',req,st,ct,b,d); rec['status_note']='formally_probed_with_dynamic_tx_symbol'; out.append(rec)
  print(json.dumps(redact({'status':'rest_scoped_probe_complete','runtime_symbols':{'TX':tx_symbol,'MTX':mtx_symbol,'TXO':opt_sym},'endpoints':out,'response_and_send_payload_bytes':budget.wire_bytes,'rest_rows':budget.rest_rows,'raw_payload_retained':False}),ensure_ascii=False))
 finally: s.close()
