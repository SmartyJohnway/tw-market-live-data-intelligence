from copy import deepcopy

from scripts.m5k_common import _parse_mis_item
from scripts.observation_contract import (
    attach_twse_mis_rich_facts_from_row,
    build_empty_twse_mis_rich_facts,
    build_twse_mis_rich_facts_from_row,
    normalize_observation,
)

RETRIEVED = "2026-07-07T05:31:00Z"
INSTRUMENT = {"symbol": "2330", "market": "twse", "instrument_type": "listed_stock"}

CLOSING_AUCTION_ROW = {
    "@": "2330.tw", "tv": "-", "ps": "3552", "pid": "20.tse.tw|2450931", "pz": "2440.0000", "bp": "0",
    "m%": "447115", "^": "20260707", "key": "tse_2330.tw_20260707",
    "a": "2445.0000_2450.0000_2455.0000_2460.0000_2465.0000_", "b": "2440.0000_2435.0000_2430.0000_2425.0000_2420.0000_",
    "c": "2330", "#": "20.tse.tw|2451696", "d": "20260707", "%": "13:27:33", "ch": "2330.tw", "tlong": "1783402053000",
    "f": "62_172_19_103_110_", "g": "572_162_339_98_160_", "ip": "0", "mt": "447115", "h": "2500.0000", "i": "24",
    "it": "12", "l": "2440.0000", "n": "台積電", "o": "2480.0000", "p": "0", "ex": "tse", "s": "-", "t": "13:27:33",
    "u": "2705.0000", "v": "24013", "w": "2215.0000", "nf": "台灣積體電路製造股份有限公司", "y": "2460.0000", "z": "-", "ts": "1",
}

POST_CLOSE_ROW = CLOSING_AUCTION_ROW | {
    "tv": "3721", "ps": "3721", "pid": "20.tse.tw|2502674", "m%": "000000", "#": "20.tse.tw|2504062", "%": "13:30:00",
    "tlong": "1783402200000", "f": "46_186_22_382_391_", "g": "853_175_1003_527_468_", "mt": "000000", "s": "3721",
    "t": "13:30:00", "v": "27734", "z": "2440.0000", "ts": "0",
}

INDEX_ROW = {
    "@": "t00.tw", "pid": "2.tse.tw|3242", "key": "tse_t00.tw_20260707", "^": "20260707", "c": "t00", "#": "2.tse.tw|3242",
    "d": "20260707", "%": "13:33:00", "ch": "t00.tw", "tlong": "1783402380000", "h": "46967.04", "i": "tidx.tw", "it": "t",
    "l": "45432.02", "m": "15235848", "n": "發行量加權股價指數", "o": "46537.34", "r": "4629735", "ex": "tse",
    "t": "13:33:00", "y": "46556.39", "z": "45479.11",
}

PLACEHOLDER_ROW = CLOSING_AUCTION_ROW | {"z": "-", "tv": "-", "ps": "-", "pz": "-", "s": "-", "ts": "0"}
LADDER_MISMATCH_ROW = POST_CLOSE_ROW | {"b": "2440.0000_2435.0000_", "g": "853_", "a": "2445.0000_2450.0000_", "f": "46_186_22_"}
MALFORMED_ROW = POST_CLOSE_ROW | {"z": "abc", "o": "bad-open", "h": "2500.0000", "l": "oops", "u": "bad-up", "w": "-"}


def test_schema_helper_still_deterministic():
    assert build_empty_twse_mis_rich_facts() == build_empty_twse_mis_rich_facts()


def test_attach_helper_does_not_mutate_inputs():
    observation = {"source": "TWSE_MIS", "symbol": "2330", "price_like_value": 2460.0}
    row = deepcopy(POST_CLOSE_ROW)
    original_observation = deepcopy(observation)
    original_row = deepcopy(row)
    attached = attach_twse_mis_rich_facts_from_row(observation, row)
    assert observation == original_observation
    assert row == original_row
    assert attached is not observation
    assert attached["twse_mis_rich_facts"]["price_facts"]["last_value"] == 2440.0


def test_closing_auction_fixture_keeps_rich_last_value_null_and_parses_depth():
    facts = build_twse_mis_rich_facts_from_row(CLOSING_AUCTION_ROW)
    assert facts["instrument_facts"]["instrument_kind_candidate"] == "security"
    assert facts["market_mode_facts"]["market_mode_candidate"] == "regular_board"
    assert facts["price_facts"]["price_domain"] == "equity_price"
    assert facts["price_facts"]["last_value"] is None
    assert facts["price_facts"]["last_value_placeholder"] is True
    assert facts["price_facts"]["previous_close"] == 2460.0
    assert facts["price_facts"]["open"] == 2480.0
    assert facts["price_facts"]["high"] == 2500.0
    assert facts["price_facts"]["low"] == 2440.0
    assert facts["volume_facts"] == facts["volume_facts"] | {"raw_v": "24013", "raw_tv": "-", "raw_ps": "3552"}
    assert facts["auction_or_reference_facts"]["raw_ps"] == "3552"
    assert facts["auction_or_reference_facts"]["raw_pz"] == "2440.0000"
    assert facts["auction_or_reference_facts"]["raw_s"] == "-"
    assert facts["auction_or_reference_facts"]["raw_ts"] == "1"
    assert facts["auction_or_reference_facts"]["observed_in_closing_auction_window"] is True
    assert facts["auction_or_reference_facts"]["observed_in_post_close_snapshot"] is False
    assert facts["session_state_candidate_facts"]["session_state_candidate"] == "closing_auction_candidate"
    assert facts["displayed_depth_facts"]["bid_prices"] == [2440.0, 2435.0, 2430.0, 2425.0, 2420.0]
    assert facts["displayed_depth_facts"]["bid_quantities_raw"] == ["572", "162", "339", "98", "160"]
    assert facts["displayed_depth_facts"]["ask_prices"] == [2445.0, 2450.0, 2455.0, 2460.0, 2465.0]
    assert facts["displayed_depth_facts"]["ask_quantities_raw"] == ["62", "172", "19", "103", "110"]
    assert facts["limit_or_reference_facts"]["limit_up"] == 2705.0
    assert facts["limit_or_reference_facts"]["limit_down"] == 2215.0


def test_post_close_fixture_populates_z_tv_s_ps_pz_and_match_heuristic():
    facts = build_twse_mis_rich_facts_from_row(POST_CLOSE_ROW)
    assert facts["price_facts"]["last_value"] == 2440.0
    assert facts["price_facts"]["last_value_source_field"] == "z"
    assert facts["price_facts"]["last_value_placeholder"] is False
    assert facts["volume_facts"]["raw_v"] == "27734"
    assert facts["volume_facts"]["raw_tv"] == "3721"
    assert facts["volume_facts"]["raw_ps"] == "3721"
    assert facts["auction_or_reference_facts"]["raw_s"] == "3721"
    assert facts["auction_or_reference_facts"]["raw_pz"] == "2440.0000"
    assert facts["auction_or_reference_facts"]["observed_in_post_close_snapshot"] is True
    assert facts["displayed_depth_facts"]["bid_quantities_raw"] == ["853", "175", "1003", "527", "468"]
    assert facts["displayed_depth_facts"]["ask_quantities_raw"] == ["46", "186", "22", "382", "391"]


def test_index_fixture_populates_index_facts_and_disables_security_groups():
    facts = build_twse_mis_rich_facts_from_row(INDEX_ROW)
    assert facts["instrument_facts"]["instrument_kind_candidate"] == "index"
    assert facts["market_mode_facts"]["market_mode_candidate"] == "index"
    assert facts["price_facts"]["price_domain"] == "index_level"
    assert facts["price_facts"]["last_value"] == 45479.11
    assert facts["price_facts"]["previous_close"] == 46556.39
    assert facts["displayed_depth_facts"]["applicable"] is False
    assert facts["displayed_depth_facts"]["applicability_reason"] == "index_observation_has_no_displayed_depth_fields"
    assert facts["limit_or_reference_facts"]["applicable"] is False
    assert facts["limit_or_reference_facts"]["applicability_reason"] == "index_observation_has_no_limit_up_down_fields"
    assert facts["index_market_facts"]["applicable"] is True
    assert facts["index_market_facts"]["raw_m"] == "15235848"
    assert facts["index_market_facts"]["raw_r"] == "4629735"
    assert facts["index_market_facts"]["evidence_level"] == "official_mis_ui_cross_checked_not_field_dictionary"


def test_placeholder_fixture_does_not_infer_rich_last_value_from_pz_midpoint_or_y():
    facts = build_twse_mis_rich_facts_from_row(PLACEHOLDER_ROW)
    assert facts["price_facts"]["last_value"] is None
    assert facts["price_facts"]["last_value_placeholder"] is True
    assert facts["price_facts"]["previous_close"] == 2460.0
    assert facts["auction_or_reference_facts"]["raw_pz"] == "-"
    obs = _parse_mis_item(PLACEHOLDER_ROW, INSTRUMENT, RETRIEVED)
    assert obs["price_source_field"] == "y"
    assert obs["price_like_value"] == 2460.0
    assert obs["reference_only"] is True


def test_ladder_mismatch_fixture_records_quality_flags_without_throwing():
    facts = build_twse_mis_rich_facts_from_row(LADDER_MISMATCH_ROW)
    assert facts["displayed_depth_facts"]["bid_prices"] == [2440.0, 2435.0]
    assert facts["displayed_depth_facts"]["bid_quantities_raw"] == ["853"]
    assert facts["displayed_depth_facts"]["ask_prices"] == [2445.0, 2450.0]
    assert facts["displayed_depth_facts"]["ask_quantities_raw"] == ["46", "186", "22"]
    assert facts["quality_facts"]["ladder_mismatch_flags"] == ["bid_ladder_length_mismatch", "ask_ladder_length_mismatch"]


def test_malformed_numeric_fixture_records_fields_without_throwing():
    facts = build_twse_mis_rich_facts_from_row(MALFORMED_ROW)
    assert {"z", "o", "l", "u"}.issubset(set(facts["quality_facts"]["malformed_fields"]))
    assert facts["price_facts"]["last_value"] is None
    assert facts["price_facts"]["open"] is None
    assert facts["price_facts"]["low"] is None
    assert facts["limit_or_reference_facts"]["limit_up"] is None


def test_runtime_parser_adds_rich_facts_for_twse_mis_and_preserves_top_level_fields():
    before = _parse_mis_item(POST_CLOSE_ROW, INSTRUMENT, RETRIEVED)
    expected = {k: before[k] for k in ["schema_version", "source", "symbol", "price_like_value", "price_source_field", "source_timestamp", "reference_only", "data_quality_flags", "source_risk_flags", "caveats"]}
    obs = _parse_mis_item(POST_CLOSE_ROW, INSTRUMENT, RETRIEVED)
    assert "twse_mis_rich_facts" in obs
    for key, value in expected.items():
        assert obs[key] == value
    assert obs["price_like_value"] == 2440.0
    assert obs["twse_mis_rich_facts"]["limit_or_reference_facts"]["raw_pz"] == "2440.0000"
    assert obs["twse_mis_rich_facts"]["volume_facts"]["raw_ps"] == "3721"


def test_non_twse_mis_observation_does_not_get_rich_facts():
    obs = normalize_observation(symbol="TX", source="TAIFEX", adapter_id="taifex", status="ok", retrieved_at_utc=RETRIEVED)
    assert "twse_mis_rich_facts" not in obs


def test_no_runtime_rich_fact_claims_official_dictionary_or_ai_exposure():
    facts = build_twse_mis_rich_facts_from_row(POST_CLOSE_ROW)
    assert facts["quantity_unit_policy"]["api_field_dictionary_available"] is False
    assert facts["semantic_confidence"]["official_documented"] is False
    assert facts["semantic_confidence"]["unit_verified"] is False
    assert facts["semantic_confidence"]["evidence_level"] == "runtime_parsed_candidate"
    assert facts["ai_exposure_policy"]["safe_for_ai_context"] is False
    assert "official_api_field_dictionary" not in str(facts)

REGULAR_SESSION_ROW = POST_CLOSE_ROW | {"t": "09:05:01", "%": "09:05:01", "tlong": "1783386301000", "tv": "12", "ps": "99", "pz": "2445.0000", "s": "12", "z": "2448.0000", "ts": "0"}
MISSING_FIELDS_ROW = {"c": "2330", "ex": "tse", "z": "-", "y": "2460.0000", "d": "20260707", "t": "09:00:00"}


def test_regular_session_fixture_does_not_trigger_post_close_heuristic():
    facts = build_twse_mis_rich_facts_from_row(REGULAR_SESSION_ROW)
    assert facts["price_facts"]["last_value"] == 2448.0
    assert facts["auction_or_reference_facts"]["observed_in_closing_auction_window"] is False
    assert facts["auction_or_reference_facts"]["observed_in_post_close_snapshot"] is False
    assert facts["volume_facts"]["raw_tv"] == "12"
    assert facts["volume_facts"]["raw_ps"] == "99"


def test_missing_optional_fields_do_not_throw_and_remain_unpopulated():
    facts = build_twse_mis_rich_facts_from_row(MISSING_FIELDS_ROW)
    assert facts["instrument_facts"]["instrument_kind_candidate"] == "security"
    assert facts["volume_facts"]["raw_tv"] is None
    assert facts["displayed_depth_facts"]["applicable"] is False
    assert facts["limit_or_reference_facts"]["raw_pz"] is None
    assert facts["quality_facts"]["field_presence"]["z"] is True
