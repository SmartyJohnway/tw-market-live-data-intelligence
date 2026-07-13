import json
from scripts.m8c_taifex_mis_execution import execute_taifex_mis_snapshot
from scripts.m8c_taifex_mis_contracts import validate_selectors, SelectorError
from scripts.m8c_taifex_mis_limits import RuntimeBudget, LimitError
from scripts.m8c_taifex_mis_currentness import evaluate_taifex_mis_currentness
from scripts.m8c_taifex_mis_observation import build_observation
from scripts.m8c_taifex_mis_http_client import read_bounded_response
from scripts.m8c_taifex_mis_sockjs_protocol import SockjsProtocolError
from scripts.m8c_taifex_mis_sockjs_xhr_client import collect_initial_states

class Resp:
    status_code=200
    headers={}
    def __init__(self, obj=None, text=None, status=200, headers=None): self.status_code=status; self.content=(text if text is not None else json.dumps(obj)).encode(); self.text=self.content.decode(); self.headers=headers or {}
    def iter_content(self, chunk_size=16384):
        for i in range(0,len(self.content),chunk_size): yield self.content[i:i+chunk_size]
class FakeSession:
    def __init__(self, fail_mtx=False, partial_quotes=False, http_fail_products=False): self.posts=[]; self.gets=[]; self.closed=False; self.poll=0; self.fail_mtx=fail_mtx; self.partial_quotes=partial_quotes; self.http_fail_products=http_fail_products
    def get(self,u,**kw): self.gets.append((u,kw)); return Resp({'websocket':True})
    def post(self,u,**kw):
        self.posts.append((u,kw))
        if 'getCmdyDDLItemByKind' in u:
            if self.http_fail_products: return Resp({'error':'boom'}, status=500)
            st=kw['json']['SymbolType']; return Resp({'RtCode':'0','RtData':{'QuoteList':[{'CID':'TXF'}] if self.fail_mtx else ([{'CID':'TXF'},{'CID':'MXF'}] if st=='F' else [{'CID':'TXO'}])}})
        if 'getCmdyMonthDDLItemByKind' in u: return Resp({'RtCode':'0','RtData':{'QuoteList':[{'item':'202607'}]}})
        if 'getQuoteListOption' in u: return Resp({'RtCode':'0','RtData':{'QuoteListOption':[{'SymbolID':'TXO20260710000C-O','StrikePrice':'10000.0','CP':'C','CDate':'2026/07/13','CTime':'09:00:10','Status':'1'}]}})
        if 'getQuoteList' in u:
            cid=kw['json']['CID']; sym='MXF202607-F' if cid=='MXF' else 'TXF202607-F'
            return Resp({'RtCode':'0','RtData':{'QuoteList':[{'SymbolID':sym,'CDate':'2026/07/13','CTime':'09:00:10','Status':'1','CLastPrice':'1'}]}})
        if 'getQuoteDetail' in u: return Resp({'RtCode':'0','RtData':{'QuoteDetail':[{'SymbolID':kw['json']['SymbolID'][0],'CDate':'2026/07/13','CTime':'09:00:10','Status':'1','CLastPrice':'2'}]}})
        if u.endswith('/xhr_send'): return Resp(text='')
        if u.endswith('/xhr'):
            if self.poll==0: self.poll+=1; return Resp(text='o')
            msgs=[]
            symbols = ['TXF202607-F'] if self.partial_quotes else ['TXF202607-F','MXF202607-F','TXO20260710000C-O']
            for sym in symbols:
                msgs.append(json.dumps({'type':'quote','mode':1,'quote':{'symbol':sym,'values':{'125':'3','144':'2026/07/13','143':'09:00:20','145':'1','101':'1','102':'2','743':'9'}}}))
            return Resp(text='a'+json.dumps(msgs))
        return Resp({})
    def close(self): self.closed=True

def test_operator_confirmation_no_network():
    assert execute_taifex_mis_snapshot(operator_confirmed=False, requested_contracts=[])['network_performed'] is False

def test_invalid_scope_and_limits_no_network():
    assert execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'after_hours'}])['network_performed'] is False
    for kwargs in ({'max_frames':101},{'max_frames':0},{'max_frames':True},{'max_frames':1.5}):
        try: RuntimeBudget(**kwargs); assert False
        except LimitError: pass
    assert execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'regular'}], max_frames=0)['network_performed'] is False

def test_semantic_selector_validation_month_weekly_and_strike():
    s=validate_selectors([{'instrument_type':'option','requested_product_id':'TXO','contract_month_or_week':'202607','strike_price':'10,000.00','option_type':'C','session':'regular'}])
    assert str(s[0].strike_price)=='10000.00' and s[0].option_type=='call'
    for bad in [
        {'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202613','session':'regular'},
        {'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'2026W1','session':'regular'},
        {'instrument_type':'option','requested_product_id':'TXO','contract_month_or_week':'202607','strike_price':'0','option_type':'call','session':'regular'},
    ]:
        try: validate_selectors([bad]); assert False
        except SelectorError: pass

def test_budget_and_streaming_reader_precheck():
    b=RuntimeBudget(max_total_execution_seconds=1,max_accounted_payload_bytes=10,max_bootstrap_rows=2,max_frames=1,max_decoded_messages=1)
    b.add_response_payload(5); b.add_rest_request_payload(5)
    for fn in (lambda: b.add_response_payload(1), lambda: b.add_rows(3), lambda: (b.add_frame(), b.add_frame()), lambda: b.add_messages(2)):
        try: fn(); assert False
        except LimitError: pass
    try: read_bounded_response(Resp(text='12345', headers={'Content-Length':'5'}), RuntimeBudget(max_accounted_payload_bytes=4)); assert False
    except LimitError: pass

def test_full_future_execution_sockjs_mode1_no_reconnect_unsubscribe_session_closes():
    fs=FakeSession(); res=execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'regular'}], evaluation_time_asia_taipei='2026-07-13T09:01:00+08:00', session_factory=lambda: fs)
    obs=res['observations'][0]
    assert obs['runtime_symbol_id']=='TXF202607-F'
    assert obs['raw_CDate']=='2026/07/13' and obs['raw_CTime']=='09:00:20' and obs['source_status_code']=='1'
    assert obs['normalized_field_candidates']['last_price']==3
    assert obs['field_provenance']['last_price']['field']=='125'
    assert res['transport_summary']['reconnect_attempts']==0 and res['transport_summary']['unsubscribe_sent'] is False and fs.closed
    assert obs['normalized_field_candidates']['canonicalization_status']=='top_of_book_field_family_unresolved'

def test_option_scope_and_identity_not_weekly_synthesized():
    fs=FakeSession(); res=execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'option','requested_product_id':'TXO','contract_month_or_week':'202607','strike_price':'10000','option_type':'call','session':'regular'}], session_factory=lambda: fs)
    assert res['observations'][0]['network_scope']=='whole_requested_contract_month_chain'
    assert res['observations'][0]['retained_scope']=='exact_requested_strike_and_option_type'


def test_partial_quote_receipt_returns_partial_source_success():
    fs=FakeSession(partial_quotes=True)
    res=execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'regular'},{'instrument_type':'future','requested_product_id':'MTX','contract_month_or_week':'202607','session':'regular'}], session_factory=lambda: fs, max_frames=2)
    assert res['status']=='partial_source_success'
    assert res['transport_summary']['accepted_initial_state_count']==1
    assert res['transport_summary']['missing_symbols']==['MXF202607-F']
    assert res['transport_summary']['termination_reason']=='frame_limit_reached'
    assert res['transport_summary']['limit_reached'] is True
    assert len(res['observations'])==2
    assert 'frame_limit_reached' in res['caveats']


def test_partial_accepted_states_survive_total_deadline_limit():
    class DeadlineClock:
        def __init__(self): self.calls=0
        def __call__(self):
            self.calls += 1
            return 0 if self.calls <= 40 else 2
    fs=FakeSession(partial_quotes=True)
    res=execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'regular'},{'instrument_type':'future','requested_product_id':'MTX','contract_month_or_week':'202607','session':'regular'}], session_factory=lambda: fs, monotonic_clock=DeadlineClock(), max_total_execution_seconds=1, max_frames=100)
    assert res['status']=='partial_source_success'
    assert res['transport_summary']['accepted_initial_state_count']==1
    assert res['transport_summary']['missing_symbols']==['MXF202607-F']
    assert res['transport_summary']['termination_reason']=='bounded_time_limit_reached'
    assert res['transport_summary']['limit_reached'] is True
    assert [o['runtime_symbol_id'] for o in res['observations'] if o['raw_CTime']=='09:00:20']==['TXF202607-F']


def test_partial_accepted_states_survive_decoded_message_limit():
    fs=FakeSession(partial_quotes=True)
    res=execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'regular'},{'instrument_type':'future','requested_product_id':'MTX','contract_month_or_week':'202607','session':'regular'}], session_factory=lambda: fs, max_decoded_messages=1, max_frames=10)
    assert res['status']=='partial_source_success'
    assert res['transport_summary']['accepted_initial_state_count']==1
    assert res['transport_summary']['missing_symbols']==['MXF202607-F']
    assert res['transport_summary']['termination_reason']=='decoded_message_limit_reached'
    assert res['transport_summary']['limit_reached'] is True
    assert any(o['runtime_symbol_id']=='TXF202607-F' and o['raw_CTime']=='09:00:20' for o in res['observations'])


def test_protocol_errors_after_acceptance_are_not_bounded_partial_success():
    class ProtocolErrorSession(FakeSession):
        quote_polls=0
        def post(self,u,**kw):
            if u.endswith('/xhr') and self.poll>0:
                self.quote_polls += 1
                if self.quote_polls > 1:
                    return Resp(text='x')
            return super().post(u,**kw)
    fs=ProtocolErrorSession(partial_quotes=True)
    budget=RuntimeBudget(max_frames=10)
    try:
        collect_initial_states(fs, ['TXF202607-F','MXF202607-F'], budget)
        assert False
    except SockjsProtocolError as exc:
        assert 'sockjs_frame_decode_failure' in str(exc)


def test_global_http_error_not_swallowed_as_selector_failure():
    fs=FakeSession(http_fail_products=True)
    res=execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'regular'}], session_factory=lambda: fs)
    assert res['status']=='source_error'
    assert not any(r.get('status')=='identity_resolution_failed' for r in res['selector_results'])

def test_partial_selector_success_preserves_successful_observation():
    fs=FakeSession(fail_mtx=True); res=execute_taifex_mis_snapshot(operator_confirmed=True, requested_contracts=[{'instrument_type':'future','requested_product_id':'TX','contract_month_or_week':'202607','session':'regular'},{'instrument_type':'future','requested_product_id':'MTX','contract_month_or_week':'202607','session':'regular'}], session_factory=lambda: fs)
    assert res['status']=='partial_source_success'
    assert len(res['observations'])==1
    assert any(r['status']=='identity_resolution_failed' for r in res['selector_results'])

def test_missing_zero_fallback_truevalues_ignored():
    class S: requested_product_id='TX'; instrument_type='future'; session='regular'; contract_month_or_week='202607'; strike_price=None; option_type=None
    obs=build_observation(S, {'mis_cid':'TXF','runtime_symbol_id':'TXF-F'}, mode1_quote={'125':'0','144':'2026/07/13','143':'09:00:00','145':'1','trueValues':{'secret':'x'}}, detail_row={'CLastPrice':'99'})
    assert obs['normalized_field_candidates']['last_price']==0
    assert 'trueValues' not in json.dumps(obs, default=str)

def test_currentness_fail_closed_rules():
    old=evaluate_taifex_mis_currentness(accepted_mode_1=True, source_timestamp_asia_taipei='2026-07-13T09:00:00+08:00', evaluation_time_asia_taipei='2026-07-13T09:10:00+08:00', session='regular', market_phase='active_regular_trading')
    assert old['overall_ai_currentness']=='active_session_stale_liveish'
    assert evaluate_taifex_mis_currentness(accepted_mode_1=True, source_timestamp_asia_taipei='2026-07-13T09:00:00+08:00', evaluation_time_asia_taipei='2026-07-13T09:00:01+08:00', session='regular', market_phase='market_phase_unresolved')['overall_ai_currentness']=='market_phase_unresolved'
    assert evaluate_taifex_mis_currentness(accepted_mode_1=True, source_timestamp_asia_taipei='2026-07-13T23:00:00+08:00', evaluation_time_asia_taipei='2026-07-14T00:01:00+08:00', session='after_hours', market_phase='active_regular_trading')['source_timestamp_state']=='ambiguous_after_hours'
    assert evaluate_taifex_mis_currentness(accepted_mode_1=True, source_timestamp_asia_taipei='2026-07-13T09:01:00+08:00', evaluation_time_asia_taipei='2026-07-13T09:00:00+08:00', session='regular', market_phase='active_regular_trading')['quote_age_state']=='future_source_timestamp'
