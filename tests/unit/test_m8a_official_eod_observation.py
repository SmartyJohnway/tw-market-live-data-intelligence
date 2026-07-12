from scripts.m8a_official_eod_observation import create_observation, parse_decimal_text, parse_int_text, parse_roc_yyyymmdd

def test_identity_and_date_price_int_contracts():
    assert parse_roc_yyyymmdd("1150709")[0] == "2026-07-09"
    assert parse_roc_yyyymmdd("1151332")[0] is None
    assert parse_decimal_text("+1,000.50")[0] == "1000.50"
    assert parse_decimal_text("-1", allow_negative=False)[0] is None
    assert parse_decimal_text("-1", allow_negative=True)[0] == "-1"
    assert parse_int_text("1,234")[0] == 1234

def test_observation_shape_no_float_or_raw_payload():
    obs=create_observation(source_id="TWSE_OPENAPI",endpoint_contract_id="x",market="listed",symbol="0050",name="元大",instrument_type="etf",trade_date="2026-07-09",price={"close":"1.1"},activity={"trade_volume":1})
    assert obs["schema_version"] == "m8a_official_eod_observation.v1"
    assert obs["symbol"] == "0050"
    assert isinstance(obs["price"]["close"], str)
    assert "raw_payload" not in str(obs)

def test_invalid_empty_symbol_rejected():
    obs=create_observation(source_id="TWSE_OPENAPI",endpoint_contract_id="x",market="listed",symbol="",name=None,trade_date="2026-07-09")
    assert obs["observation_status"] == "invalid"
