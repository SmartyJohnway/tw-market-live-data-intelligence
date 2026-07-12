from scripts.m8_multi_source_context_builder import build_multi_source_market_context
from scripts.m8b_taifex_derivatives_observation import create_observation, CONTEXT_TYPES
REG={'sources':[{'source_id':'TAIFEX_OPENAPI','source_family':'TAIFEX_OPENAPI','authority_level':'official_documented','timing_class':'official_statistics_eod','ai_exposure_level':'caveated_context_allowed','runtime_executable':True},{'source_id':'TWSE_OPENAPI','source_family':'TWSE_OPENAPI','authority_level':'official_documented','timing_class':'official_eod','ai_exposure_level':'caveated_context_allowed','runtime_executable':True}]}
def test_taifex_coexists_context_types_source_specific():
 obs=create_observation(endpoint_contract_id='PutCallRatio',context_type=CONTEXT_TYPES['put_call_ratio'],instrument_type='aggregate_statistics',aggregate_identity={'trade_date':'2026-07-09'},trade_date='2026-07-09',payload={'put_call_ratio':{'put_call_volume_ratio_percent':'100.89'}})
 tw={'source_id':'TWSE_OPENAPI','source_family':'TWSE_OPENAPI','context_type':'official_equity_eod_reference','market':'listed','symbol':'2330','instrument_type':'equity','market_date':'2026-07-09','trading_date':'2026-07-09','retrieved_at_utc':'2026-07-09T00:00:00Z','safe_fields':{'price':{'close':'1'}}}
 ctx=build_multi_source_market_context([obs,tw],REG,now_utc='2026-07-09T00:00:00Z')
 assert len(ctx['sources'])==2
 assert ctx['freshness_summary']['has_official_statistics_eod'] is True
 assert any(c['context_type']==CONTEXT_TYPES['put_call_ratio'] for g in ctx['instrument_contexts'] for c in g['contexts'])
