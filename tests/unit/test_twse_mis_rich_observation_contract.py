from copy import deepcopy

from scripts.observation_contract import (
    attach_empty_twse_mis_rich_facts,
    build_empty_twse_mis_rich_facts,
)


def test_empty_twse_mis_rich_facts_identity_and_price_groups():
    facts = build_empty_twse_mis_rich_facts()
    assert facts["schema_version"] == "m7a_twse_mis_rich_facts.v1"
    assert facts["source_id"] == "TWSE_MIS"
    assert facts["schema_status"] == "defined_not_populated_by_runtime_parser"
    assert facts["price_facts"] == {
        "last_price": None,
        "previous_close": None,
        "open": None,
        "high": None,
        "low": None,
        "price_source_fields": [],
        "semantic_status": "schema_defined_candidate_fields",
    }


def test_volume_and_displayed_depth_groups_remain_unverified_and_descriptive():
    facts = build_empty_twse_mis_rich_facts()
    volume = facts["volume_facts"]
    assert volume["raw_v"] is None
    assert volume["raw_tv"] is None
    assert volume["unit_status"] == "unverified"

    depth = facts["displayed_depth_facts"]
    assert depth["bid_prices"] == []
    assert depth["bid_quantities_raw"] == []
    assert depth["ask_prices"] == []
    assert depth["ask_quantities_raw"] == []
    assert depth["ladder_source_fields"] == ["b", "g", "a", "f"]
    assert depth["quantity_unit_status"] == "unverified"
    depth_status = depth["semantic_status"]
    assert depth_status == "displayed_depth_snapshot_only_schema"
    assert "support" not in depth_status
    assert "resistance" not in depth_status
    assert "trading" not in depth_status


def test_quality_and_ai_exposure_policy_guardrails():
    facts = build_empty_twse_mis_rich_facts()
    quality = facts["quality_facts"]
    assert set(quality["unit_unverified_fields"]) == {"v", "tv", "g", "f"}
    assert {"m", "nu"}.issubset(set(quality["unknown_or_raw_only_fields"]))

    policy = facts["ai_exposure_policy"]
    assert policy["safe_for_ai_context"] is False
    forbidden = set(policy["forbidden_interpretations"])
    assert {
        "buy_signal",
        "sell_signal",
        "hold",
        "target_price",
        "support_resistance",
        "main_force",
        "true_liquidity",
        "order_book_truth",
        "realtime_guarantee",
    }.issubset(forbidden)


def test_identity_timestamp_limit_groups_include_candidate_raw_slots():
    facts = build_empty_twse_mis_rich_facts()
    identity = facts["identity_facts"]
    assert identity["unknown_identity_fields"] == {"m": None, "nu": None}
    for key in ["raw_c", "raw_ch", "raw_ex", "raw_name", "raw_nf"]:
        assert key in identity

    timestamp = facts["timestamp_facts"]
    for key in ["raw_d", "raw_t", "raw_tlong", "raw_percent", "raw_ot"]:
        assert key in timestamp

    limit_or_reference = facts["limit_or_reference_facts"]
    for key in ["limit_up", "limit_down", "raw_pz", "raw_bp", "raw_ps"]:
        assert key in limit_or_reference


def test_empty_twse_mis_rich_facts_is_deterministic():
    assert build_empty_twse_mis_rich_facts() == build_empty_twse_mis_rich_facts()


def test_attach_empty_rich_facts_returns_copy_and_preserves_top_level_fields():
    observation = {
        "symbol": "2330",
        "source": "TWSE_MIS",
        "price_like_value": 100.0,
        "price_source_field": "z",
        "reference_only": False,
        "source_timestamp": "2026-07-07T01:00:00Z",
        "data_quality_flags": ["example_flag"],
    }
    original = deepcopy(observation)
    attached = attach_empty_twse_mis_rich_facts(observation)

    assert observation == original
    assert attached is not observation
    for key, value in original.items():
        assert attached[key] == value
    assert attached["twse_mis_rich_facts"] == build_empty_twse_mis_rich_facts()
