import json
from pathlib import Path
from scripts.m8_multi_source_context_builder import build_multi_source_market_context
from scripts.m8a_official_eod_observation import observation_to_context_observation
from scripts.m8a_twse_official_eod_adapter import parse_twse_official_eod_rows
from tests.unit.test_m8a_twse_official_eod_adapter import load
REG=json.loads((Path(__file__).resolve().parents[2]/'docs/data_capabilities/m8_source_capability_registry.json').read_text())
def test_eod_and_liveish_coexist_without_overwrite():
    eod=parse_twse_official_eod_rows(load('twse_normal_rows.json'),requested_symbols=['2330'],retrieved_at_utc='2026-07-10T00:00:00Z')['observations'][0]
    obs=[{'source_id':'TWSE_MIS','symbol':'2330','name':'台積電','market':'listed','instrument_type':'equity','retrieved_at_utc':'2026-07-10T01:00:00Z','safe_fields':{'price_like_value':'1006'}}, observation_to_context_observation(eod,currentness_status='delayed_one_trading_day')]
    r=build_multi_source_market_context(obs,REG,now_utc='2026-07-10T01:05:00Z')
    ctxs=r['instrument_contexts'][0]['contexts']
    assert {c['source_id'] for c in ctxs}=={'TWSE_MIS','TWSE_OPENAPI'}
    assert any(c['context_type']=='official_equity_eod_reference' for c in ctxs)
