import json
from pathlib import Path
from scripts.m8_controlled_conversation_context import build_controlled_conversation_context
from scripts.m8_multi_source_context_builder import build_multi_source_market_context
from scripts.m8a_official_eod_observation import observation_to_context_observation
from scripts.m8a_twse_official_eod_adapter import parse_twse_official_eod_rows
from tests.unit.test_m8a_twse_official_eod_adapter import load
REG=json.loads((Path(__file__).resolve().parents[2]/'docs/data_capabilities/m8_source_capability_registry.json').read_text())
def test_official_eod_conversation_projection_labels_source_date_currentness():
    obs=parse_twse_official_eod_rows(load('twse_normal_rows.json'),requested_symbols=['2330'],retrieved_at_utc='2026-07-10T00:00:00Z')['observations'][0]
    ctx=build_multi_source_market_context([observation_to_context_observation(obs,currentness_status='matches_expected_latest_trade_date_after_emergency_closure')],REG,now_utc='2026-07-10T01:00:00Z')
    conv=build_controlled_conversation_context(ctx)
    md=conv['sections'][0]['markdown']
    assert 'Official EOD reference — TWSE_OPENAPI' in md
    assert '2026-07-09' in md
    assert 'matches_expected_latest_trade_date_after_emergency_closure' in md
    assert 'realtime official price' not in md.lower()
    assert "today's close" not in md.lower()
    assert conv['no_raw_payload'] is True
