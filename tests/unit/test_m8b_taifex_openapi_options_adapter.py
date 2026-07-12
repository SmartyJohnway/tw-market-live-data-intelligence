from scripts.m8b_taifex_openapi_options_adapter import normalize_taifex_options_eod
ROW={'Date':'20260709','Contract':'TXO','ContractMonth(Week)':'202607F2','StrikePrice':'40100','CallPut':'買權','Open':'1','High':'2','Low':'1','Close':'2','Volume':'0','SettlementPrice':'2','OpenInterest':'0','BestBid':'1','BestAsk':'2','TradingSession':'一般'}
def test_options_bounded_close_settlement_no_last():
 r=normalize_taifex_options_eod(requested_products=['TXO'],requested_contract_months=['202607F2'],requested_strikes=['40100'],requested_option_types=['call'],fetcher=lambda e:[ROW,dict(ROW,StrikePrice='40200')])
 o=r['observations'][0]; assert r['row_count_retained']==1 and o['contract_identity']['option_type']=='call'
 assert o['payload']['price']['close']=='2' and o['payload']['price']['settlement']=='2' and 'last' not in o['payload']['price']
def test_options_unbounded_unknown_callput_missing_strike_rejected():
 assert normalize_taifex_options_eod(requested_products=['TXO'],fetcher=lambda e:[ROW])['batch_status']=='rejected_invalid_scope'
 assert normalize_taifex_options_eod(requested_products=['TXO'],requested_contract_months=['202607F2'],requested_strikes=['40100'],requested_option_types=['call'],fetcher=lambda e:[dict(ROW,CallPut='X')])['row_count_retained']==0
