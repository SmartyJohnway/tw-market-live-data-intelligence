import json
from scripts.m8c_taifex_mis_execution import execute_taifex_mis_snapshot
from scripts.m8c_taifex_mis_contracts import validate_selectors, SelectorError
from scripts.m8c_taifex_mis_limits import RuntimeBudget, LimitError
from scripts.m8c_taifex_mis_currentness import evaluate_taifex_mis_currentness
from scripts.m8c_taifex_mis_observation import build_observation

class Resp:
    status_code=200
    def __init__(self, obj=None, text=None): self.content=(text if text is not None else json.dumps(obj)).encode(); self.text=self.content.decode()
class FakeSession:
    def __init__(self): self.posts=[]; self.gets=[]; self.closed=False; self.poll=0
    def get(self,u,**kw): self.gets.append(u); return Resp({'websocket':True})
    def post(self,u,**kw):
        self.posts.append((u,kw))
        if 'getCmdyDDLItemByKind' in u:
            st=kw['json']['SymbolType']; return Resp({'RtCode':'0','RtData':{'QuoteList':[{'CID':'TXF'},{'CID':'MXF'}] if st=='F' else [{'CID':'TXO'}]}})
        if 'getCmdyMonthDDLItemByKind' in u: return Resp({'RtCode':'0','RtData':{'QuoteList':[{'item':'202607'}]}})
        if 'getQuoteListOption' in u: return Resp({'RtCode':'0','RtData':{'QuoteListOption':[{'SymbolID':'TXO20260710000C-O','StrikePrice':'10000.0','CP':'C','CDate':'2026/07/13','CTime':'09:00:10','Status':'trading'}]}})
        if 'getQuoteList' in u: return Resp({'RtCode':'0','RtData':{'QuoteList':[{'SymbolID':'TXF202607-F','CDate':'2026/07/13','CTime':'09:00:10','Status':'trading','CLastPrice':'1'}]}})
        if 'getQuoteDetail' in u: return Resp({'RtCode':'0','RtData':{'QuoteDetail':[{'SymbolID':kw['json']['SymbolID'][0],'CDate':'2026/07/13','CTime':'09:00:10','Status':'trading','CLastPrice':'2'}]}})
        if u.endswith('/xhr_send'): return Resp(text='')
        if u.endswith('/xhr'):
            if self.poll==0: self.poll+=1; return Resp(text='o')
            return Resp(text='a['+json.dumps(json.dumps({'type':'quote','mode':1,'quote':{'symbol':'TXF202607-F','values':{'CLastPrice':'3','CDate':'2026/07/13','CTime':'09:00:20','Status':'trading','101':'1','102':'2','743':'9'}}})) +']')
        return Resp({})
    def close(self): self.closed=True

def test_operator_confirmation_no_network():
    assert execute_taifex_mis_snapshot(operator_confirmed=False, requested_contracts=[])['network_performed'] is False

def test_invalid_scope_and_limits_no_network():
    assert execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'after_hours'}])['network_performed'] is False
    try: RuntimeBudget(max_frames=101); assert False
    except LimitError: pass

def test_mixed_sessions_duplicate_decimal_cp_validation():
    s=validate_selectors([{'instrument_type':'option','requested_product_id':'TXO','contract_month_or_week':'202607','strike_price':'10,000.00','option_type':'C','session':'regular'}])
    assert str(s[0].strike_price)=='10000.00' and s[0].option_type=='call'
    for contracts in ([{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'regular'}]*2,):
        try: validate_selectors(contracts); assert False
        except SelectorError: pass

def test_budget_counters_payload_rows_frames_messages():
    b=RuntimeBudget(max_total_execution_seconds=1,max_accounted_payload_bytes=10,max_bootstrap_rows=2,max_frames=1,max_decoded_messages=1)
    b.add_response_payload(5); b.add_rest_request_payload(5)
    for fn in (lambda: b.add_response_payload(1), lambda: b.add_rows(3), lambda: (b.add_frame(), b.add_frame()), lambda: b.add_messages(2)):
        try: fn(); assert False
        except LimitError: pass

def test_full_future_execution_sockjs_mode1_no_reconnect_unsubscribe_session_closes():
    fs=FakeSession(); res=execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'regular'}], evaluation_time_asia_taipei='2026-07-13T09:01:00+08:00', session_factory=lambda: fs)
    assert res['observations'][0]['runtime_symbol_id']=='TXF202607-F'
    assert res['transport_summary']['reconnect_attempts']==0 and res['transport_summary']['unsubscribe_sent'] is False and fs.closed
    assert res['observations'][0]['normalized_field_candidates']['top_of_book_candidates']['family_743_744_745_746']['bid'] is not None
    assert res['observations'][0]['normalized_field_candidates']['canonicalization_status']=='top_of_book_field_family_unresolved'

def test_option_scope_and_identity_not_weekly_synthesized():
    fs=FakeSession(); res=execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'option','requested_product_id':'TXO','contract_month_or_week':'202607','strike_price':'10000','option_type':'call','session':'regular'}], session_factory=lambda: fs)
    assert res['observations'][0]['network_scope']=='whole_requested_contract_month_chain'
    assert res['observations'][0]['retained_scope']=='exact_requested_strike_and_option_type'

def test_missing_zero_fallback_truevalues_ignored():
    class S: requested_product_id='TX'; instrument_type='future'; session='regular'; contract_month_or_week='202607'; strike_price=None; option_type=None
    obs=build_observation(S, {'mis_cid':'TXF','runtime_symbol_id':'TXF-F'}, mode1_quote={'CLastPrice':'0','CDate':'2026/07/13','CTime':'09:00:00','Status':'trading','trueValues':{'secret':'x'}}, detail_row={'CLastPrice':'99'})
    assert obs['normalized_field_candidates']['last_price']==0
    assert 'trueValues' not in json.dumps(obs, default=str)

def test_currentness_old_recent_retrieval_unresolved_market_after_hours():
    old=evaluate_taifex_mis_currentness(accepted_mode_1=True, source_timestamp_asia_taipei='2026-07-13T09:00:00+08:00', evaluation_time_asia_taipei='2026-07-13T09:10:00+08:00', session='regular', market_phase='trading')
    assert old['overall_ai_currentness']=='active_session_stale_liveish'
    assert evaluate_taifex_mis_currentness(accepted_mode_1=True, source_timestamp_asia_taipei='2026-07-13T09:00:00+08:00', evaluation_time_asia_taipei='2026-07-13T09:00:01+08:00', session='regular', market_phase='unresolved')['overall_ai_currentness']=='market_phase_unresolved'
    assert evaluate_taifex_mis_currentness(accepted_mode_1=True, source_timestamp_asia_taipei='2026-07-13T23:00:00+08:00', evaluation_time_asia_taipei='2026-07-14T00:01:00+08:00', session='after_hours', market_phase='trading')['source_timestamp_state']=='ambiguous_after_hours'
