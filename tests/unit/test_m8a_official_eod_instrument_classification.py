from scripts.m8a_tpex_official_eod_adapter import classify_instrument
from scripts.m8a_official_eod_observation import observation_to_context_observation, create_observation

def test_security_master_primary_classifier_no_symbol_length_heuristic():
    assert classify_instrument("tpex_otc","006201") ["instrument_type"] == "etf"
    un=classify_instrument("tpex_otc","1234")
    assert un["instrument_type"] == "unknown" and un["classification_status"] == "unclassified"

def test_unclassified_context_fail_closed():
    obs=create_observation(source_id="TPEX_OPENAPI",endpoint_contract_id="x",market="tpex_otc",symbol="1234",name="x",instrument_type="unknown",trade_date="2026-07-09")
    ctx=observation_to_context_observation(obs)
    assert ctx["safe_fields"] == {}
    assert "unclassified" in " ".join(ctx["caveats"])
