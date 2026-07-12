import json
from pathlib import Path
from datetime import datetime, timezone

import pytest

from scripts.m8b_taifex_currentness import map_m8a_currentness_status
from scripts.m8b_taifex_derivatives_observation import FAILURE_STATUSES
from scripts.m8b_taifex_openapi_put_call_ratio_adapter import normalize_taifex_put_call_ratio, MAX_PUT_CALL_RATIO_ROWS
from scripts.m8b_taifex_openapi_final_settlement_adapter import normalize_taifex_final_settlement, MAX_FINAL_SETTLEMENT_ROWS
from scripts.m8b_taifex_openapi_futures_adapter import normalize_taifex_futures_eod

ROOT = Path(__file__).resolve().parents[2]

def load_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def pcr_row(date, ratio='100.89'):
    return {'Date':date,'PutVolume':'100','CallVolume':'100','PutCallVolumeRatio%':ratio,'PutOI':'10','CallOI':'10','PutCallOIRatio%':'100.00'}

def fs_row(day, month, product='TX'):
    return {'TheFinalSettlementDay':day,'DeliveryMonth':month,'Contract':product,'ContractName':product,'TheFinalSettlementPrice':'123'}

def test_registry_active_state_consolidated():
    reg=load_json('docs/data_capabilities/m8_source_capability_registry.json')
    assert reg['status']=='m8_through_m8b_implemented_with_caveats'
    active=reg['m8_active_consolidated_status']
    assert active['twse_mis_runtime_executable'] is True
    assert active['twse_openapi_runtime_executable'] is True
    assert active['tpex_openapi_runtime_executable'] is True
    assert active['taifex_openapi_runtime_executable'] is True
    assert active['taifex_mis_runtime_executable'] is False
    assert active['mops_runtime_executable'] is False
    assert active['trading_signal_allowed'] is False
    assert active['recommendation_allowed'] is False
    assert active['raw_payload_exposure_allowed'] is False
    assert active['next_task']=='M8C-00-TAIFEX-MIS-LIVEISH-DERIVATIVES-CONTEXT-PREFLIGHT'

def test_taifex_currentness_mapping_fails_closed():
    assert map_m8a_currentness_status('current_official_eod') == ('current_official_derivatives_eod', None)
    assert map_m8a_currentness_status('stale_official_eod') == ('stale_official_derivatives_eod', None)
    assert map_m8a_currentness_status('delayed_one_trading_day') == ('delayed_one_trading_day', None)
    assert map_m8a_currentness_status('matches_expected_latest_trade_date_after_emergency_closure') == ('matches_expected_latest_trade_date_after_emergency_closure', None)
    assert map_m8a_currentness_status('new_status') == ('unresolved_date_mismatch', 'unmapped_upstream_currentness_status')

def test_runtime_statuses_documented():
    doc=(ROOT/'docs/protocol/M8B_TAIFEX_DERIVATIVES_CURRENTNESS_AND_SESSION_CONTRACT.md').read_text(encoding='utf-8')
    for status in FAILURE_STATUSES:
        assert f'`{status}`' in doc

def test_adapter_completion_timing_and_metadata():
    r=normalize_taifex_futures_eod(requested_products=['TX'], fetcher=lambda e:[{'bad':'shape'}])
    assert r['completed_at_utc'] >= r['requested_at_utc']
    assert r['duration_ms'] >= 0
    assert r['batch_status']=='schema_drift'
    assert r['retention']['raw_payload_retained'] is False

def test_pcr_bounded_retention_defaults_latest_and_preserves_percent():
    r=normalize_taifex_put_call_ratio(fetcher=lambda e:[pcr_row('20260708'), pcr_row('20260709')])
    assert len(r['observations']) == 1
    assert r['observations'][0]['trade_date']=='2026-07-09'
    assert r['observations'][0]['payload']['put_call_ratio']['put_call_volume_ratio_percent']=='100.89'
    assert r['retention']['retention_limit'] == 1
    assert r['retention']['retention_truncated'] is True
    assert r['retention']['raw_payload_retained'] is False

def test_pcr_selectors_and_limits():
    rows=[pcr_row(f'202607{d:02d}') for d in range(1,8)]
    r=normalize_taifex_put_call_ratio(fetcher=lambda e:rows, latest_n=5, max_retained_rows=20)
    assert [o['trade_date'] for o in r['observations']] == ['2026-07-07','2026-07-06','2026-07-05','2026-07-04','2026-07-03']
    r=normalize_taifex_put_call_ratio(fetcher=lambda e:rows, requested_trade_dates=['2026-07-02','2026-07-05'], latest_n=1)
    assert [o['trade_date'] for o in r['observations']] == ['2026-07-05']
    with pytest.raises(ValueError): normalize_taifex_put_call_ratio(fetcher=lambda e:rows, latest_n=0)
    with pytest.raises(ValueError): normalize_taifex_put_call_ratio(fetcher=lambda e:rows, max_retained_rows=MAX_PUT_CALL_RATIO_ROWS+1)

def test_final_settlement_bounded_retention_and_source_latest():
    rows=[fs_row('20260619','202606'), fs_row('20260715','202607'), fs_row('20260716','202607','MTX')]
    r=normalize_taifex_final_settlement(requested_products=['TX','MTX'], fetcher=lambda e:rows)
    assert len(r['observations']) == 2
    assert {o['product_id']: o['trade_date'] for o in r['observations']} == {'TX':'2026-07-15','MTX':'2026-07-16'}
    assert r['source_latest_reference']['latest_by_product']['TX']=='2026-07-15'
    old=normalize_taifex_final_settlement(requested_products=['TX'], requested_delivery_months=['202606'], fetcher=lambda e:rows)
    assert old['observations'][0]['trade_date']=='2026-06-19'
    assert old['observations'][0]['currentness']['status']=='historical_final_settlement_reference'
    with pytest.raises(ValueError): normalize_taifex_final_settlement(requested_products=['TX'], fetcher=lambda e:rows, max_retained_rows=MAX_FINAL_SETTLEMENT_ROWS+1)

def test_docs_and_boundaries():
    assert (ROOT/'docs/protocol/M8_THROUGH_M8B_CONSOLIDATED_FINAL_ACCEPTANCE.md').exists()
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    assert 'Current M8 architecture' in readme
    assert 'TAIFEX_MIS` is **not implemented yet**' in readme
    m8b=(ROOT/'docs/protocol/M8B_01_TAIFEX_OPENAPI_OFFICIAL_DERIVATIVES_EOD_FINAL_ACCEPTANCE.md').read_text(encoding='utf-8')
    assert 'PR #129' in m8b and 'bounded retention' in m8b
    index=(ROOT/'docs/INDEX.md').read_text(encoding='utf-8')
    assert 'M8_THROUGH_M8B_CONSOLIDATED_FINAL_ACCEPTANCE.md' in index
    forbidden=['scheduler added','polling added','startup fetch','DB persistence','model call','trading recommendation']
    for token in forbidden:
        assert token in readme or token in (ROOT/'docs/protocol/M8_THROUGH_M8B_CONSOLIDATED_FINAL_ACCEPTANCE.md').read_text(encoding='utf-8')


def test_inventory_active_state_and_historical_snapshots():
    inv=load_json('docs/data_capabilities/twse_mis_rich_field_inventory.json')['rich_observation_contract']
    active=inv['m8_active_consolidated_status']
    assert active['m8_00_governance_complete'] is True
    assert active['m8a_twse_tpex_official_eod_complete'] is True
    assert active['m8b_taifex_openapi_complete'] is True
    assert active['taifex_mis_runtime_executable'] is False
    assert active['next_task']=='M8C-00-TAIFEX-MIS-LIVEISH-DERIVATIVES-CONTEXT-PREFLIGHT'
    assert all(active['m8b_taifex_contexts'].values())
    assert 'm8_source_timing_authority_governance' not in inv
    assert 'm8a_official_eod_context' not in inv
    snaps=inv['milestone_snapshots']
    assert snaps['state_at_m8_00_acceptance']['snapshot_type']=='historical'
    assert snaps['state_at_m8a_00_preflight']['snapshot_type']=='historical'
    assert snaps['state_at_m8_00_acceptance']['no_m8a_started'] is True
    assert snaps['state_at_m8a_00_preflight']['adapter_implemented'] is False


def test_invalid_retention_scope_rejected_before_fetch():
    from scripts.m8b_taifex_openapi_execution import execute_taifex_openapi_refresh
    def fail(endpoint):
        raise AssertionError('fetcher must not be called')
    fetchers={'PutCallRatio':fail,'FinalSettlementPrice':fail,'BlockTrade':fail,'OpenInterestOfLargeTradersFutures':fail}
    r=execute_taifex_openapi_refresh(operator_confirmed=True, requested_contexts=['put_call_ratio'], requested_products=[], put_call_ratio_latest_n=0, fetchers=fetchers)
    assert r['overall_status']=='rejected_invalid_scope'
    assert r['endpoint_results']=={}
    r=execute_taifex_openapi_refresh(operator_confirmed=True, requested_contexts=['final_settlement'], requested_products=['TX'], requested_delivery_months=['bad'], fetchers=fetchers)
    assert r['overall_status']=='rejected_invalid_scope'
    r=execute_taifex_openapi_refresh(operator_confirmed=True, requested_contexts=['block_trade'], requested_products=['TX'], max_block_trade_rows=101, fetchers=fetchers)
    assert r['overall_status']=='rejected_invalid_scope'


def test_block_trade_and_large_trader_retention_limits_visible():
    from scripts.m8b_taifex_openapi_block_trade_adapter import normalize_taifex_block_trade
    from scripts.m8b_taifex_openapi_large_trader_oi_adapter import normalize_taifex_large_trader_oi
    block_rows=[{'Date':f'202607{d:02d}','Contract':'TX','ContractMonth(Week)':'202607','StrikePrice':'-','CallPut':'-','Volume':'1','HighestPrice':'2','LowestPrice':'1','TradingSession':'一般'} for d in range(1,4)]
    br=normalize_taifex_block_trade(requested_products=['TX'], max_retained_rows=2, fetcher=lambda e:block_rows)
    assert len(br['observations'])==2
    assert br['retention']['retention_limit']==2
    assert br['retention']['retention_truncated'] is True
    assert 'bounded_retention_limit_applied' in br['caveats']
    oi_rows=[{'Date':f'202607{d:02d}','Contract':'TX','ContractName':'臺指','SettlementMonth':'202607','TypeOfTraders':'all','Top5Buy':'1','Top5Sell':'1','Top10Buy':'1','Top10Sell':'1','OIOfMarket':'1'} for d in range(1,4)]
    lr=normalize_taifex_large_trader_oi(endpoint='OpenInterestOfLargeTradersFutures', requested_products=['TX'], max_retained_rows=2, fetcher=lambda e:oi_rows)
    assert len(lr['observations'])==2
    assert lr['retention']['retention_limit']==2
    assert lr['retention']['retention_truncated'] is True


def test_readme_m8b_command_parser_succeeds_without_network():
    import os, re, subprocess
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    blocks=re.findall(r'```bash\n(.*?)\n```', readme, flags=re.S)
    cmd=next(b for b in blocks if 'validate_m8b_taifex_openapi_live.py' in b)
    cmd=' '.join(line.strip().rstrip('\\') for line in cmd.splitlines())
    env=dict(os.environ, M8B_VALIDATOR_TEST_FIXTURE='1')
    result=subprocess.run(cmd, shell=True, cwd=ROOT, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    payload=json.loads(result.stdout)
    assert payload['raw_payload_retained'] is False
