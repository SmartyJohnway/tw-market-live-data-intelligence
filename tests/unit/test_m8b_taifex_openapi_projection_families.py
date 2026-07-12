from scripts.m8b_taifex_derivatives_observation import create_observation, CONTEXT_TYPES
from scripts.m8_multi_source_context_builder import build_multi_source_market_context
from scripts.m8_controlled_conversation_context import build_controlled_conversation_context
REG={'sources':[{'source_id':'TAIFEX_OPENAPI','source_family':'TAIFEX_OPENAPI','authority_level':'official_documented','timing_class':'official_statistics_eod','ai_exposure_level':'caveated_context_allowed','runtime_executable':True}]}
def obs(kind,payload,ident=None,agg=None,instrument='futures'):
 return create_observation(endpoint_contract_id=kind,context_type=kind,instrument_type=instrument,product_id=(ident or {}).get('product_id'),contract_identity=ident,aggregate_identity=agg,trade_date='2026-07-09',session=(ident or {}).get('session','regular'),payload=payload,currentness_value={'status':'current_official_derivatives_eod','trade_date':'2026-07-09','caveats':[]})
def project(observations):
 m=build_multi_source_market_context(observations,REG,now_utc='2026-07-09T09:00:00Z')
 return build_controlled_conversation_context(m)['sections'][0]['markdown']
def test_all_taifex_families_have_factual_projection_no_raw_or_signal_words():
 observations=[
  obs(CONTEXT_TYPES['futures'],{'price':{'last':'10','settlement':'9'},'activity':{'volume':1},'open_interest':{'open_interest':2}},{'product_id':'TX','contract_month_or_week':'202607','session':'regular'}),
  obs(CONTEXT_TYPES['options'],{'price':{'close':'3','settlement':'4'},'activity':{'volume':5},'open_interest':{'open_interest':6}},{'product_id':'TXO','contract_month_or_week':'202607F2','strike_price':'40100','option_type':'call','session':'regular'},instrument='options'),
  obs(CONTEXT_TYPES['final_settlement'],{'final_settlement':{'final_settlement_price':'123'}},{'product_id':'TX','final_settlement_day':'2026-07-15','delivery_month':'202607'},instrument='final_settlement'),
  obs(CONTEXT_TYPES['large_trader_oi'],{'large_trader_open_interest':{'top5_buy':1,'top5_sell':2,'top10_buy':3,'top10_sell':4,'market_open_interest':5}},{'product_id':'TX','settlement_month':'202607'},instrument='futures'),
  obs(CONTEXT_TYPES['put_call_ratio'],{'put_call_ratio':{'put_call_volume_ratio_percent':'100.89','put_call_open_interest_ratio_percent':'118.81'}},None,{'trade_date':'2026-07-09'},instrument='aggregate_statistics'),
  obs(CONTEXT_TYPES['block_trade'],{'block_trade':{'volume':7,'highest_price':'8','lowest_price':'6'}},{'product_id':'TX','contract_month_or_week':'202607','session':'regular'},instrument='block_trade'),
 ]
 text=project(observations)
 for token in ['futures EOD','last=10','options EOD','close=3','final_settlement_price=123','not a current market price','large-trader open-interest concentration','top5_buy=1','volume_ratio_percent=100.89%','open_interest_ratio_percent=118.81%','block-trade','highest_price=8','quotation_unit=product_specific_quote_unit']:
  assert token in text
 lower=text.lower()
 for forbidden in ['raw_payload','bullish','bearish','support','resistance','three-institutional']:
  assert forbidden not in lower
