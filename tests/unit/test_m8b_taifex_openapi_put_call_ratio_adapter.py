from scripts.m8b_taifex_openapi_put_call_ratio_adapter import normalize_taifex_put_call_ratio
def test_put_call_ratio_percent_preserved_no_sentiment():
 r=normalize_taifex_put_call_ratio(fetcher=lambda e:[{'Date':'20260709','PutVolume':'100','CallVolume':'0','PutCallVolumeRatio%':'100.89','PutOI':'200','CallOI':'100','PutCallOIRatio%':'118.81'}])
 o=r['observations'][0]; p=o['payload']['put_call_ratio']
 assert p['put_call_volume_ratio_percent']=='100.89' and p['put_call_open_interest_ratio_percent']=='118.81'
 assert 'bullish' not in str(o).lower() and 'bearish' not in str(o).lower()
 assert o['aggregate_identity']['trade_date']=='2026-07-09'
