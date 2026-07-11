import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_acceptance_docs_and_inventory_closed():
    doc=(ROOT/'docs/protocol/M8A_OFFICIAL_EOD_CONTEXT_FINAL_ACCEPTANCE.md').read_text()
    assert 'm8a_official_eod_context_final_acceptance_pass_with_caveats' in doc
    for name in ['m8a_official_eod_observation.py','m8a_twse_official_eod_adapter.py','m8a_tpex_official_eod_adapter.py','m8a_official_eod_execution.py','m8a_ncdr_dgpa_closure_cap.py','m8a_market_day_currentness_resolver.py']:
        assert (ROOT/'scripts'/name).exists()
    inv=json.loads((ROOT/'docs/data_capabilities/twse_mis_rich_field_inventory.json').read_text())
    flags=inv['m8a_flags']
    assert flags['twse_adapter_implemented'] and flags['tpex_adapter_implemented'] and flags['final_acceptance_completed']
    for forbidden in ['scheduler_added','polling_added','startup_fetch_added','hidden_fetch_added','db_write_added','ai_model_call_added','taifex_scope_added','mops_adapter_added','tpex_mis_introduced','rotc_route_introduced']:
        assert flags[forbidden] is False

def test_readme_static_contracts_and_registry_roles():
    readme=(ROOT/'README.md').read_text()
    for text in ['TWSE_OPENAPI','TPEX_OPENAPI','NCDR_DGPA_CLOSURE_CAP','explicit operator confirmation','no automatic polling']:
        assert text in readme
    assert 'not market price data' in readme
    assert 'official EOD is realtime' not in readme
    reg=json.loads((ROOT/'docs/data_capabilities/m8_source_capability_registry.json').read_text())
    src={s['source_id']:s for s in reg['sources']}
    assert src['TWSE_OPENAPI']['adapter_implemented'] is True
    assert src['TPEX_OPENAPI']['instrument_classification_required'] is True
    assert src['NCDR_DGPA_CLOSURE_CAP']['not_market_price_source'] is True
