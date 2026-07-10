import json
from pathlib import Path

from scripts.m5k_common import source_plan_for_instrument
from scripts.m7g_controlled_refresh_executor import DECLARED_SOURCE_FAMILIES, EXECUTION_SUPPORTED_SOURCE_FAMILIES


def test_route_semantics_doc_contains_required_taxonomy():
    text = Path('docs/protocol/M7G_TWSE_MIS_MARKET_ROUTE_SEMANTICS.md').read_text(encoding='utf-8')
    for term in [
        'twse_mis_market_route_semantics_defined',
        '上市即時：TWSE_MIS / tse_{symbol}.tw',
        '上櫃即時：TWSE_MIS / otc_{symbol}.tw',
        '期貨即時：TAIFEX_MIS',
        '上市盤後/官方參考：TWSE_OPENAPI',
        '上櫃盤後/官方參考：TPEX_OPENAPI',
        '期交所盤後/官方參考：TAIFEX_OPENAPI',
        'Do not introduce TPEX_MIS',
        'TPEX_OPENAPI is not a Level 2 live quote source family',
        'ROTC / rotc_ must not be declared as supported or candidate in M7G',
        'Emerging stock live route is not supported in M7G',
    ]:
        assert term in text


def test_m5k_market_routes_for_twse_tpex_otc_and_taifex():
    twse = source_plan_for_instrument({'symbol': '2330', 'market': 'twse', 'instrument_type': 'equity'})
    assert twse['source'] == 'TWSE_MIS'
    assert twse['adapter_id'] == 'twse_mis_equity_etf_quote'
    assert twse['ex_ch'] == 'tse_2330.tw'

    for market in ['tpex', 'otc']:
        plan = source_plan_for_instrument({'symbol': '8069', 'market': market, 'instrument_type': 'equity'})
        assert plan['source'] == 'TWSE_MIS'
        assert plan['adapter_id'] == 'twse_mis_equity_etf_quote'
        assert plan['ex_ch'] == 'otc_8069.tw'

    taifex = source_plan_for_instrument({'symbol': 'TX', 'market': 'taifex', 'instrument_type': 'futures'})
    assert taifex['source'] == 'TAIFEX'
    assert taifex['adapter_id'] == 'taifex_mis_tx_futures_quote'
    assert taifex['route'] == 'taifex_mis_getQuoteList'


def test_no_tpex_mis_or_rotc_declared_in_m7g_runtime_taxonomy_and_inventory():
    assert 'TPEX_MIS' not in DECLARED_SOURCE_FAMILIES
    assert 'TPEX_MIS' not in EXECUTION_SUPPORTED_SOURCE_FAMILIES
    assert 'ROTC_MIS' not in DECLARED_SOURCE_FAMILIES
    inv = json.loads(Path('docs/data_capabilities/twse_mis_rich_field_inventory.json').read_text(encoding='utf-8'))
    entry = inv['rich_observation_contract']['m7g_local_safe_context_artifact_load']
    assert entry['tpex_mis_declared'] is False
    assert entry['tpex_mis_executable'] is False
    assert entry['emerging_stock_live_route_supported'] is False
    assert entry['rotc_route_declared'] is False
    assert entry['rotc_candidate_added'] is False


def test_m7g_current_execution_files_do_not_declare_tpex_mis_or_rotc_routes():
    paths = [
        Path('frontend/public/index.html'),
        Path('scripts/m7g_controlled_refresh_executor.py'),
        Path('scripts/m7g_refresh_request_package.py'),
        Path('docs/data_capabilities/twse_mis_rich_field_inventory.json'),
    ]
    for path in paths:
        text = path.read_text(encoding='utf-8')
        assert 'TPEX_MIS' not in text
        assert 'ROTC_MIS' not in text
        if path.name == 'twse_mis_rich_field_inventory.json':
            assert '"rotc_route_declared": false' in text
            assert '"rotc_candidate_added": false' in text
            stripped = text.replace('"rotc_route_declared": false', '').replace('"rotc_candidate_added": false', '')
            assert 'rotc_' not in stripped
        else:
            assert 'rotc_' not in text
