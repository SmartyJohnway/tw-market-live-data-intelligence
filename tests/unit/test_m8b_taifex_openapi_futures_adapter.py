from scripts.m8b_taifex_openapi_futures_adapter import normalize_taifex_futures_eod
ROW={'Date':'20260709','Contract':'TX','ContractMonth(Week)':'202607','Open':'1','High':'2','Low':'1','Last':'2','Change':'-1','%':'100.89','Volume':'0','SettlementPrice':'2','OpenInterest':'10','BestBid':'1','BestAsk':'2','TradingSession':'一般'}
def test_futures_valid_zero_bounded_no_raw():
 r=normalize_taifex_futures_eod(requested_products=['TX'],fetcher=lambda e:[ROW,dict(ROW,Contract='MTX')])
 assert r['row_count_retained']==1 and r['observations'][0]['payload']['activity']['volume']==0
 assert r['observations'][0]['payload']['price']['change_percent']=='100.89'
 assert r['provenance']['raw_payload_retained'] is False
 assert r['observations'][0]['quotation_unit']!='TWD'
def test_futures_duplicate_and_unknown_session():
 r=normalize_taifex_futures_eod(requested_products=['TX'],fetcher=lambda e:[ROW,ROW])
 assert r['batch_status']=='identity_parse_failure'
 r=normalize_taifex_futures_eod(requested_products=['TX'],fetcher=lambda e:[dict(ROW,TradingSession='X')])
 assert r['observations'][0]['session']=='unknown' and 'session_semantics_unresolved' in r['observations'][0]['caveats']
def test_futures_invalid_date_reject_mixed_dates():
 assert normalize_taifex_futures_eod(requested_products=['TX'],fetcher=lambda e:[dict(ROW,Date='bad')])['row_count_rejected']==1
 assert normalize_taifex_futures_eod(requested_products=['TX'],fetcher=lambda e:[ROW,dict(ROW,ContractMonth='x',**{'Date':'20260710','ContractMonth(Week)':'202608'})])['batch_status']=='date_mismatch'
