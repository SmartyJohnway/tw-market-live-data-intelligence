import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
POLICY={'recommendation_allowed','trading_signal_allowed','no_recommendation','no_trading_advice','no_trading_signal','allowed_interpretations','prohibited_inferences','disallowed_topics','prohibitions'}
def test_active_evidence_schema_has_no_product_policy_fields():
    schema=json.loads((ROOT/'docs/contracts/schemas/m8r_watchlist_ai_context_package.v1.schema.json').read_text())
    assert not (POLICY & set(schema['properties']))
    assert not (POLICY & set(schema['properties']['targets']['items']['properties']))
def test_evidence_layers_do_not_import_agent_policy():
    for path in [ROOT/'scripts/m8r_03e_watchlist_ai_context_builder.py',ROOT/'scripts/m8r_03e_context_validator.py',ROOT/'scripts/m8r_03d_watchlist_controlled_executor.py']:
        assert 'agent_policy' not in path.read_text()
def test_no_mutable_writer_root_state():
    for path in [ROOT/'scripts/m8r_03d_watchlist_controlled_executor.py',ROOT/'scripts/run_m8r_03e_watchlist_ai_context_handoff.py']:
        assert '._authorized_root' not in path.read_text()
