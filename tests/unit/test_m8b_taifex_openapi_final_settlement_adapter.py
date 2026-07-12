from scripts.m8b_taifex_openapi_final_settlement_adapter import normalize_taifex_final_settlement
def test_final_settlement_reference_not_daily_quote():
 r=normalize_taifex_final_settlement(requested_products=['TX'],fetcher=lambda e:[{'TheFinalSettlementDay':'20260715','DeliveryMonth':'202607','Contract':'TX','ContractName':'臺指','TheFinalSettlementPrice':'123'}])
 o=r['observations'][0]; assert o['context_type']=='official_derivatives_final_settlement_reference'
 assert 'Volume' not in o['source_fields_present'] and o['session']=='not_applicable'
 assert o['currentness']['status']=='official_final_settlement_reference'
