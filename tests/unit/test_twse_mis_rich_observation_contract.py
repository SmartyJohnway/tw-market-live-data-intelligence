from copy import deepcopy

from scripts.observation_contract import (
    attach_empty_twse_mis_rich_facts,
    build_empty_twse_mis_rich_facts,
)


def test_empty_twse_mis_rich_facts_top_level_contract():
    facts = build_empty_twse_mis_rich_facts()
    assert facts["schema_version"] == "m7a_twse_mis_rich_facts.v1"
    assert facts["source_id"] == "TWSE_MIS"
    assert facts["schema_status"] == "defined_not_populated_by_runtime_parser"


def test_instrument_and_price_facts_support_row_context_and_price_domain():
    facts = build_empty_twse_mis_rich_facts()
    instrument = facts["instrument_facts"]
    assert "instrument_kind_candidate" in instrument
    assert "price_domain" in instrument
    assert instrument["evidence_policy"] == {"official_documented": False, "requires_row_context": True}
    price = facts["price_facts"]
    for key in ["last_value", "previous_close", "open", "high", "low", "price_domain"]:
        assert key in price
    assert price["source_fields"] == ["z", "y", "o", "h", "l"]


def test_market_mode_and_quantity_unit_policy_are_schema_only():
    facts = build_empty_twse_mis_rich_facts()
    market_mode = facts["market_mode_facts"]
    assert market_mode["market_mode_candidate"] is None
    assert market_mode["known_modes"] == ["regular_board", "intraday_odd_lot", "index", "unknown"]
    assert market_mode["semantic_status"] == "schema_defined_not_runtime_populated"
    policy = facts["quantity_unit_policy"]
    assert policy["official_mis_ui_unit_label"] == "交易單位"
    assert policy["api_field_dictionary_available"] is False
    assert policy["market_mode_required"] is True
    assert policy["unit_verified_for_runtime_normalization"] is False


def test_volume_and_displayed_depth_facts_are_unit_unverified_snapshot_schema():
    facts = build_empty_twse_mis_rich_facts()
    volume = facts["volume_facts"]
    assert {"raw_v", "raw_tv", "raw_ps"}.issubset(volume)
    assert volume["unit_status"] == "market_context_required"
    assert volume["community_default_unit_candidate"] == "non_authoritative_regular_board_quantity_candidate"
    assert volume["quantity_unit_policy"]["market_mode_required"] is True
    depth = facts["displayed_depth_facts"]
    assert {"applicable", "applicability_reason"}.issubset(depth)
    assert depth["ladder_source_fields"] == ["b", "g", "a", "f"]
    assert depth["quantity_unit_policy"]["official_mis_ui_unit_label"] == "交易單位"
    for forbidden in ["support_resistance", "true_liquidity", "order_book_truth", "main_force", "trading_signal"]:
        assert forbidden in depth["forbidden_interpretations"]


def test_limit_auction_index_session_and_timestamp_groups_define_candidate_fields():
    facts = build_empty_twse_mis_rich_facts()
    assert facts["limit_or_reference_facts"]["source_fields"] == ["u", "w", "pz", "bp", "ps"]
    auction = facts["auction_or_reference_facts"]
    assert {"raw_ps", "raw_pz", "raw_bp", "raw_s", "raw_ts"}.issubset(auction)
    assert auction["observed_in_closing_auction_window"] is False
    assert auction["observed_in_post_close_snapshot"] is False
    assert auction["ps_candidate_semantic"] == "state_dependent_reference_or_match_volume_candidate"
    assert auction["pz_candidate_semantic"] == "state_dependent_reference_or_match_price_candidate"
    assert auction["s_candidate_semantic"] == "match_volume_shadow_candidate"
    assert auction["ts_candidate_semantic"] == "session_or_trial_state_flag_candidate"
    assert auction["semantic_status"] == "operator_evidence_supported_not_official_dictionary"
    assert auction["unit_policy"]["api_field_dictionary_available"] is False
    session = facts["session_state_candidate_facts"]
    assert {"raw_ip", "raw_p", "raw_s", "raw_ts"}.issubset(session)
    assert session["ts_candidate_semantic"] == "session_or_trial_state_flag_candidate"
    assert "ts=1 observed" in session["known_operator_evidence"]
    index = facts["index_market_facts"]
    assert {"raw_m", "raw_r"}.issubset(index)
    assert index["m_candidate_semantic"] == "index_market_traded_quantity_candidate"
    assert index["r_candidate_semantic"] == "index_market_trade_count_candidate"
    assert index["evidence_level"] == "official_mis_ui_cross_checked_not_field_dictionary"
    assert index["quantity_unit_policy"]["api_field_dictionary_available"] is False
    assert facts["timestamp_facts"]["source_fields"] == ["d", "t", "tlong", "%", "^", "ot"]


def test_raw_unknown_and_quality_facts_preserve_conservative_field_sets():
    facts = build_empty_twse_mis_rich_facts()
    raw_unknown = facts["raw_unknown_facts"]
    for key in ["raw_pid", "raw_hash", "raw_m_percent", "raw_mt", "raw_ip", "raw_i", "raw_it", "raw_p", "raw_q", "raw_oa", "raw_ob", "raw_ot", "raw_nu"]:
        assert key in raw_unknown
    quality = facts["quality_facts"]
    for field in ["v", "tv", "ps", "s", "g", "f", "m", "r"]:
        assert field in quality["unit_unverified_fields"]
    for field in ["pid", "#", "m%", "mt", "ip", "i", "it", "p", "q", "oa", "ob", "ot", "nu"]:
        assert field in quality["unknown_or_raw_only_fields"]
    assert "s" not in quality["unknown_or_raw_only_fields"]
    assert "ts" not in quality["unknown_or_raw_only_fields"]
    assert quality["not_observed_in_m7a_01d_fields"] == ["q", "oa", "ob", "ot"]


def test_semantic_confidence_and_ai_exposure_default_to_schema_only_unsafe():
    facts = build_empty_twse_mis_rich_facts()
    confidence = facts["semantic_confidence"]
    assert confidence["official_documented"] is False
    assert confidence["unit_verified"] is False
    assert confidence["evidence_level"] == "schema_only"
    policy = facts["ai_exposure_policy"]
    assert policy["safe_for_ai_context"] is False
    for forbidden in ["buy_signal", "sell_signal", "hold", "target_price", "support_resistance", "main_force", "true_liquidity", "order_book_truth", "realtime_guarantee", "execution_feed"]:
        assert forbidden in policy["forbidden_interpretations"]


def test_empty_twse_mis_rich_facts_is_deterministic_across_calls():
    assert build_empty_twse_mis_rich_facts() == build_empty_twse_mis_rich_facts()


def test_attach_empty_twse_mis_rich_facts_copies_and_preserves_top_level_fields():
    observation = {
        "symbol": "2330.TW",
        "price_like_value": 100.0,
        "price_source_field": "y",
        "source_timestamp": "2026-07-07T01:02:03Z",
        "reference_only": True,
        "data_quality_flags": ["current_z_unavailable_used_y_reference"],
        "source_risk_flags": ["unofficial_source_risk"],
        "caveats": ["not_official_realtime_api"],
    }
    original = deepcopy(observation)
    attached = attach_empty_twse_mis_rich_facts(observation)
    assert observation == original
    assert attached is not observation
    for key, value in original.items():
        assert attached[key] == value
    assert attached["twse_mis_rich_facts"]["schema_version"] == "m7a_twse_mis_rich_facts.v1"


def test_no_group_claims_official_api_field_dictionary_validation():
    facts = build_empty_twse_mis_rich_facts()
    assert facts["quantity_unit_policy"]["api_field_dictionary_available"] is False
    assert facts["index_market_facts"]["evidence_level"] == "official_mis_ui_cross_checked_not_field_dictionary"
    assert "official_api_field_dictionary" not in str(facts)
    assert "field_dictionary_available': True" not in str(facts)
