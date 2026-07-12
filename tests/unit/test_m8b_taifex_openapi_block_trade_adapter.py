from scripts.m8b_taifex_openapi_block_trade_adapter import normalize_taifex_block_trade
F={'Date':'20260709','Contract':'TX','ContractMonth(Week)':'202607','StrikePrice':'-','CallPut':'-','Volume':'10','HighestPrice':'2','LowestPrice':'1','TradingSession':'一般'}
def test_block_trade_futures_dash_and_options_require_identity():
 r=normalize_taifex_block_trade(requested_products=['TX'],fetcher=lambda e:[F])
 assert r['observations'][0]['payload']['block_trade']['option_type']=='not_applicable'
 bad=normalize_taifex_block_trade(requested_products=['TXO'],fetcher=lambda e:[dict(F,Contract='TXO',StrikePrice='',CallPut='')])
 assert bad['row_count_retained']==0
 opt=normalize_taifex_block_trade(requested_products=['TXO'],requested_strikes=['40100'],requested_option_types=['call'],fetcher=lambda e:[dict(F,Contract='TXO',StrikePrice='40100',CallPut='買權')])
 assert opt['observations'][0]['contract_identity']['option_type']=='call'
