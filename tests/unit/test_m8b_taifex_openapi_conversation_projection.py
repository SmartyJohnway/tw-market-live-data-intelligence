from scripts.m8_controlled_conversation_context import build_controlled_conversation_context
from tests.unit.test_m8b_taifex_openapi_context_integration import REG
from scripts.m8_multi_source_context_builder import build_multi_source_market_context
from scripts.m8b_taifex_derivatives_observation import create_observation, CONTEXT_TYPES
def test_conversation_projection_factual_compact_no_realtime_signal():
 obs=create_observation(endpoint_contract_id='OpenInterestOfLargeTradersFutures',context_type=CONTEXT_TYPES['large_trader_oi'],instrument_type='futures',product_id='TX',contract_identity={'product_id':'TX'},trade_date='2026-07-09',payload={'large_trader_open_interest':{'top5_buy':1}})
 m=build_multi_source_market_context([obs],REG,now_utc='2026-07-09T00:00:00Z')
 c=build_controlled_conversation_context(m)
 text=str(c).lower()
 assert c['no_raw_payload'] is True
 assert 'realtime' in text and 'recommendation' in text
 assert 'sentiment' not in text and 'support signal' not in text
