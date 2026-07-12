from scripts.m8b_taifex_openapi_large_trader_oi_adapter import normalize_taifex_large_trader_oi
BASE={'Date':'20260709','Contract':'TX','ContractName':'臺指','SettlementMonth':'202607','TypeOfTraders':'所有契約','Top5Buy':'1','Top5Sell':'2','Top10Buy':'3','Top10Sell':'4','OIOfMarket':'5'}
def test_large_trader_futures_and_options_factual():
 r=normalize_taifex_large_trader_oi(endpoint='OpenInterestOfLargeTradersFutures',requested_products=['TX'],fetcher=lambda e:[BASE])
 assert r['observations'][0]['payload']['large_trader_open_interest']['top5_buy']==1
 assert 'large trader open-interest concentration' in ' '.join(r['observations'][0]['caveats'])
 assert 'three-institutional' not in ' '.join(r['observations'][0]['caveats'])
 ro=normalize_taifex_large_trader_oi(endpoint='OpenInterestOfLargeTradersOptions',requested_products=['TX'],requested_option_types=['put'],fetcher=lambda e:[dict(BASE,CallPut='賣權')])
 assert ro['observations'][0]['contract_identity']['option_type']=='put'
