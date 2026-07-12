from scripts.m8b_taifex_openapi_futures_adapter import normalize_taifex_futures_eod
from scripts.m8b_taifex_openapi_options_adapter import normalize_taifex_options_eod
from scripts.m8b_taifex_openapi_put_call_ratio_adapter import normalize_taifex_put_call_ratio
from scripts.m8b_taifex_openapi_large_trader_oi_adapter import normalize_taifex_large_trader_oi
from scripts.m8b_taifex_openapi_final_settlement_adapter import normalize_taifex_final_settlement
F={'Date':'20260709','Contract':'TX','ContractMonth(Week)':'202607','Open':'1','High':'2','Low':'1','Last':'2','Change':'0','%':'0','Volume':'0','SettlementPrice':'2','OpenInterest':'0','BestBid':'1','BestAsk':'2','TradingSession':'一般'}
O={'Date':'20260709','Contract':'TXO','ContractMonth(Week)':'202607F2','StrikePrice':'40100','CallPut':'買權','Open':'1','High':'2','Low':'1','Close':'2','Volume':'0','SettlementPrice':'2','OpenInterest':'0','BestBid':'1','BestAsk':'2','TradingSession':'一般'}
L={'Date':'20260709','Contract':'TX','ContractName':'臺指','SettlementMonth':'202607','TypeOfTraders':'0','Top5Buy':'1','Top5Sell':'2','Top10Buy':'3','Top10Sell':'4','OIOfMarket':'5'}

def test_schema_drift_empty_array_and_no_matching_scope():
 assert normalize_taifex_futures_eod(requested_products=['TX'],fetcher=lambda e:[{'RenamedDate':'20260709'}])['batch_status']=='schema_drift'
 assert normalize_taifex_futures_eod(requested_products=['TX'],fetcher=lambda e:[])['batch_status']=='empty_non_trading_day'
 assert normalize_taifex_futures_eod(requested_products=['MTX'],fetcher=lambda e:[F])['batch_status']=='no_matching_bounded_scope'

def test_malformed_options_core_numeric_partial_zero_valid():
 r=normalize_taifex_options_eod(requested_products=['TXO'],requested_contract_months=['202607F2'],requested_strikes=['40100'],requested_option_types=['call'],fetcher=lambda e:[dict(O,Close='bad')])
 assert r['observations'][0]['observation_status']=='partial'
 z=normalize_taifex_options_eod(requested_products=['TXO'],requested_contract_months=['202607F2'],requested_strikes=['40100'],requested_option_types=['call'],fetcher=lambda e:[O])
 assert z['observations'][0]['observation_status']=='complete'

def test_malformed_pcr_required_rejected_and_zero_valid():
 bad=normalize_taifex_put_call_ratio(fetcher=lambda e:[{'Date':'20260709','PutVolume':'bad','CallVolume':'1','PutCallVolumeRatio%':'100.89','PutOI':'0','CallOI':'0','PutCallOIRatio%':'118.81'}])
 assert bad['row_count_rejected']==1 and bad['row_count_retained']==0
 ok=normalize_taifex_put_call_ratio(fetcher=lambda e:[{'Date':'20260709','PutVolume':'0','CallVolume':'0','PutCallVolumeRatio%':'100.89','PutOI':'0','CallOI':'0','PutCallOIRatio%':'118.81'}])
 assert ok['observations'][0]['observation_status']=='complete'

def test_malformed_large_trader_core_oi_partial():
 r=normalize_taifex_large_trader_oi(endpoint='OpenInterestOfLargeTradersFutures',requested_products=['TX'],fetcher=lambda e:[dict(L,Top5Buy='bad')])
 assert r['observations'][0]['observation_status']=='partial'
 assert r['observations'][0]['payload']['large_trader_open_interest']['top5_buy'] is None

def test_contract_month_week_pattern_fails_closed():
 r=normalize_taifex_futures_eod(requested_products=['TX'],fetcher=lambda e:[dict(F,**{'ContractMonth(Week)':'JUL26'})])
 assert r['row_count_rejected']==1


def test_options_missing_core_values_partial_and_zero_valid():
 for field in ["Close", "SettlementPrice", "Volume", "OpenInterest"]:
  row=dict(O)
  if field in {"Volume", "OpenInterest"}:
   row.pop(field)
  else:
   row[field]='-'
  r=normalize_taifex_options_eod(requested_products=['TXO'],requested_contract_months=['202607F2'],requested_strikes=['40100'],requested_option_types=['call'],fetcher=lambda e,row=row:[row])
  assert r['observations'][0]['observation_status']=='partial'
  assert r['observations'][0]['field_validation'][field]['valid'] is False
 z=normalize_taifex_options_eod(requested_products=['TXO'],requested_contract_months=['202607F2'],requested_strikes=['40100'],requested_option_types=['call'],fetcher=lambda e:[dict(O,Volume='0',OpenInterest='0')])
 assert z['observations'][0]['observation_status']=='complete'

def test_invalid_matching_rows_not_no_matching_scope():
 pcr=normalize_taifex_put_call_ratio(fetcher=lambda e:[{'Date':'20260709','PutVolume':'bad','CallVolume':'1','PutCallVolumeRatio%':'100.89','PutOI':'0','CallOI':'0','PutCallOIRatio%':'118.81'}])
 assert pcr['matching_scope_rows']==1 and pcr['batch_status']=='invalid_required_fields'
 fs=normalize_taifex_final_settlement(requested_products=['TX'],fetcher=lambda e:[{'TheFinalSettlementDay':'20260709','DeliveryMonth':'202607','Contract':'TX','ContractName':'臺指','TheFinalSettlementPrice':'bad'}])
 assert fs['matching_scope_rows']==1 and fs['batch_status']=='invalid_required_fields'
