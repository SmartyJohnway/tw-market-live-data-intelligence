from scripts.m8a_official_eod_execution import execute_official_eod_refresh
from scripts.m8a_twse_official_eod_adapter import parse_twse_official_eod_rows
from tests.unit.test_m8a_twse_official_eod_adapter import load

def ok(symbols): return parse_twse_official_eod_rows(load('twse_normal_rows.json'),requested_symbols=symbols,retrieved_at_utc='2026-07-10T00:00:00Z')
def fail(symbols): return {'source_id':'TPEX_OPENAPI','source_status':'error','reported_trade_dates':[],'observations':[]}
def test_execution_gates_and_partial_success():
    assert execute_official_eod_refresh(['2330'],['TWSE_OPENAPI'],False)['overall_status']=='rejected_not_confirmed'
    assert execute_official_eod_refresh([],['TWSE_OPENAPI'],True)['overall_status']=='rejected_invalid_scope'
    assert execute_official_eod_refresh(['2330'],['BAD'],True)['overall_status']=='rejected_invalid_scope'
    r=execute_official_eod_refresh(['2330'],['TWSE_OPENAPI','TPEX_OPENAPI'],True,twse_adapter=ok,tpex_adapter=fail)
    assert r['overall_status']=='partial_success' and len(r['normalized_observations'])==1
    assert r['safe_projection_scope']['retained_scope']=='bounded_requested_symbols'
def test_closure_fetcher_only_on_mismatch():
    calls=[]
    def closure(td): calls.append(td); return {'events':[]}
    execute_official_eod_refresh(['2330'],['TWSE_OPENAPI'],True,twse_adapter=ok,closure_fetcher=closure,evaluation_time_asia_taipei='2026-07-09T16:00:00+08:00')
    assert calls==[]
    execute_official_eod_refresh(['2330'],['TWSE_OPENAPI'],True,twse_adapter=ok,closure_fetcher=closure,evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00')
    assert calls==['2026-07-10']
