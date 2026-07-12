from scripts.m8b_taifex_derivatives_observation import *
def test_helpers_decimal_dates_session_units():
    assert parse_yyyymmdd('20260709')[0]=='2026-07-09'
    assert parse_decimal_text('100.89%')[0]=='100.89'
    assert parse_signed_decimal_text('-1.5')[0]=='-1.5'
    assert parse_non_negative_int('1,234')[0]==1234
    assert map_call_put('買權')[0]=='call' and map_call_put('賣權')[0]=='put'
    assert map_session('一般')[0]=='regular'
    obs=create_observation(endpoint_contract_id='x',context_type=CONTEXT_TYPES['futures'],instrument_type='futures',product_id='TX',contract_identity={'x':1},trade_date='2026-07-09',payload={'price':{'change_percent':'1.2'}})
    assert obs['quotation_unit']=='product_specific_quote_unit'
    assert obs['settlement_currency'] is None
    assert 'quotation_unit_unresolved' in obs['caveats']
