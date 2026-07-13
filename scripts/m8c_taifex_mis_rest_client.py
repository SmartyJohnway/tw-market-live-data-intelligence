from __future__ import annotations
import json
from .m8c_taifex_mis_limits import MAX_SINGLE_REQUEST_SECONDS, MAX_RESPONSE_PAYLOAD_BYTES
from .m8c_taifex_mis_http_client import read_bounded_response
class RestError(ValueError): pass
BASE='https://mis.taifex.com.tw/futures/api/'

def _loads_body(resp,budget):
    body=read_bounded_response(resp,budget,per_response_limit=MAX_RESPONSE_PAYLOAD_BYTES)
    try: return json.loads(body.decode())
    except Exception as exc: raise RestError('rest_json_decode_failure') from exc

def _rows(data):
    rt=data.get('RtData')
    if isinstance(rt,dict):
        for k in ('QuoteList','QuoteListOption','QuoteDetail','Items','Data'):
            if isinstance(rt.get(k),list): return rt[k]
        if isinstance(rt.get('data'),list): return rt['data']
    if isinstance(rt,list): return rt
    raise RestError('rest_rtdata_shape_invalid')
class TaifexMisRestClient:
    def __init__(self, session, budget, base_url=BASE): self.session=session; self.budget=budget; self.base_url=base_url
    def post(self, endpoint, body, *, option=False):
        payload=json.dumps(body,separators=(',',':')).encode(); self.budget.add_rest_request_payload(len(payload))
        r=self.session.post(self.base_url+endpoint, json=body, timeout=self.budget.timeout(MAX_SINGLE_REQUEST_SECONDS), stream=True)
        data=_loads_body(r,self.budget)
        if str(data.get('RtCode','0')) not in ('0','0000',''): raise RestError('rtcode_not_ok')
        rows=_rows(data); self.budget.add_rows(len(rows), option=option); return rows
    def products(self, market_type='0', symbol_type='F'): return self.post('getCmdyDDLItemByKind', {'MarketType':market_type,'SymbolType':symbol_type,'KindID':''})
    def months(self,cid, market_type='0', symbol_type='F'): return self.post('getCmdyMonthDDLItemByKind', {'MarketType':market_type,'SymbolType':symbol_type,'KindID':'','CID':cid})
    def quote_list(self,cid,month, symbol_type='F'): return self.post('getQuoteList', {'MarketType':'0','SymbolType':symbol_type,'KindID':'','CID':cid,'ExpireMonth':month})
    def option_chain(self,cid,month): return self.post('getQuoteListOption', {'MarketType':'0','SymbolType':'O','KindID':'','CID':cid,'ExpireMonth':month}, option=True)
    def detail(self,symbols): return self.post('getQuoteDetail', {'SymbolID':list(symbols)})
