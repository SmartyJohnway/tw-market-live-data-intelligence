from scripts.m8b_taifex_openapi_execution import execute_taifex_openapi_refresh
F={'Date':'20260709','Contract':'TX','ContractMonth(Week)':'202607','Open':'1','High':'2','Low':'1','Last':'2','Change':'0','%':'0','Volume':'1','SettlementPrice':'2','OpenInterest':'1','BestBid':'1','BestAsk':'2','TradingSession':'一般'}
P={'Date':'20260709','PutVolume':'1','CallVolume':'1','PutCallVolumeRatio%':'100.89','PutOI':'1','CallOI':'1','PutCallOIRatio%':'118.81'}
def test_execution_scope_confirmation_partial_no_hidden_behaviors():
 assert execute_taifex_openapi_refresh(operator_confirmed=False,requested_contexts=['futures_eod'],requested_products=['TX'])['overall_status']=='operator_confirmation_required'
 assert execute_taifex_openapi_refresh(operator_confirmed=True,requested_contexts=[],requested_products=['TX'])['overall_status']=='rejected_invalid_scope'
 r=execute_taifex_openapi_refresh(operator_confirmed=True,requested_contexts=['futures_eod','options_eod','put_call_ratio'],requested_products=['TX'],requested_contracts=[{'contract_month':'202607','strike_price':'40100','option_type':'call'}],fetchers={'DailyMarketReportFut':lambda e:[F],'DailyMarketReportOpt':lambda e:[],'PutCallRatio':lambda e:[P]})
 assert r['overall_status']=='successful_derivatives_eod_batch'
 assert r['raw_payload_retained'] is False and not r['scheduler_added'] and not r['polling_added'] and not r['startup_fetch_added'] and not r['db_write_added']
def test_put_call_ratio_allowed_aggregate_without_products():
 r=execute_taifex_openapi_refresh(operator_confirmed=True,requested_contexts=['put_call_ratio'],requested_products=[],fetchers={'PutCallRatio':lambda e:[P]})
 assert r['observations'][0]['instrument_type']=='aggregate_statistics'

def test_execution_isolates_unexpected_adapter_exception_and_timestamps():
 def boom(endpoint):
  raise RuntimeError('parser exploded')
 r=execute_taifex_openapi_refresh(operator_confirmed=True,requested_contexts=['futures_eod','put_call_ratio'],requested_products=['TX'],evaluation_time_asia_taipei='2026-07-10T16:00:00+08:00',fetchers={'DailyMarketReportFut':boom,'PutCallRatio':lambda e:[P]})
 assert r['overall_status']=='partial_source_success'
 assert r['endpoint_results']['futures_eod']['batch_status']=='source_error'
 assert r['endpoint_results']['futures_eod']['provenance']['error_type']=='RuntimeError'
 assert r['endpoint_results']['futures_eod']['provenance']['raw_payload_retained'] is False
 assert r['endpoint_results']['put_call_ratio']['observations'][0]['currentness']['status'] in {'current_official_derivatives_eod','delayed_one_trading_day','stale_official_derivatives_eod'}
 assert r['completed_at_utc'] >= r['started_at_utc'] and isinstance(r['duration_ms'], int)


def test_execution_runtime_clock_and_caller_supplied_evaluation_time():
 r=execute_taifex_openapi_refresh(operator_confirmed=True,requested_contexts=['put_call_ratio'],requested_products=[],fetchers={'PutCallRatio':lambda e:[P]})
 assert r['evaluation_time_source']=='runtime_clock' and r['evaluation_timezone']=='Asia/Taipei'
 assert r['observations'][0]['currentness']['evaluation_time_asia_taipei']
 supplied='2026-07-10T16:00:00+08:00'
 s=execute_taifex_openapi_refresh(operator_confirmed=True,requested_contexts=['put_call_ratio'],requested_products=[],evaluation_time_asia_taipei=supplied,fetchers={'PutCallRatio':lambda e:[P]})
 assert s['evaluation_time_source']=='caller_supplied' and s['evaluation_time_asia_taipei']==supplied

def test_historical_final_settlement_status_reachable_at_runtime():
 rows=[{'TheFinalSettlementDay':'20250716','DeliveryMonth':'202507','Contract':'TX','ContractName':'臺指','TheFinalSettlementPrice':'23000'}, {'TheFinalSettlementDay':'20260715','DeliveryMonth':'202607','Contract':'TX','ContractName':'臺指','TheFinalSettlementPrice':'24000'}]
 r=execute_taifex_openapi_refresh(operator_confirmed=True,requested_contexts=['final_settlement'],requested_products=['TX'],fetchers={'FinalSettlementPrice':lambda e:rows})
 statuses={o['trade_date']:o['currentness']['status'] for o in r['observations']}
 assert statuses['2025-07-16']=='historical_final_settlement_reference'
 assert statuses['2026-07-15']=='official_final_settlement_reference'
