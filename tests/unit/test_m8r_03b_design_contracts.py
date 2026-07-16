import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "m8r_03b"


def load(name):
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))


def test_watchlist_current_maps_to_mis_and_eod():
    fixture = load("scenario_a_current_watchlist")
    assert fixture["parsed_conversation_intent"]["scope_modes"] == ["watchlist"]
    assert fixture["parsed_conversation_intent"]["time_mode"] == "current"
    assert "watchlist_snapshot" in fixture["expected_bundle_types"]
    assert "twse_mis_listed_liveish" in fixture["required_capability_ids"]
    assert "twse_official_eod" in fixture["required_capability_ids"]


def test_watchlist_recent_maps_primarily_to_eod():
    fixture = load("scenario_b_recent_watchlist")
    assert fixture["parsed_conversation_intent"]["time_mode"] == "recent"
    assert fixture["expected_bundle_types"] == ["watchlist_performance"]
    assert "twse_official_eod" in fixture["required_capability_ids"]
    assert "twse_mis_listed_liveish" not in fixture["required_capability_ids"]


def test_ambiguous_watchlist_defaults_to_current_plus_recent():
    fixture = load("scenario_c_ambiguous_watchlist")
    assert fixture["parsed_conversation_intent"]["time_mode"] == "current_plus_recent"
    assert fixture["clarification_decision"]["clarification_required"] is False


def test_market_overview_does_not_default_to_watchlist():
    fixture = load("scenario_d_current_market_pulse")
    assert fixture["parsed_conversation_intent"]["scope_modes"] == ["market_overview"]
    assert fixture["evidence_request"]["persistent_watchlist_reference"] is None


def test_dynamic_research_does_not_mutate_persistent_watchlist():
    fixture = load("scenario_f_dynamic_ai_tech")
    assert fixture["parsed_conversation_intent"]["scope_modes"] == ["dynamic_research"]
    assert fixture["evidence_request"]["dynamic_entity_requests"][0]["persistent_watchlist_mutation"] is False


def test_composite_scope_is_representable():
    fixture = load("scenario_g_composite_followup")
    assert fixture["parsed_conversation_intent"]["scope_modes"] == ["dynamic_research", "watchlist_subset", "market_overview"]
    assert fixture["follow_up_context"]["parent_evidence_request_id"] == "prior-dynamic-research"


def test_explicit_time_range_contract_preserves_constraints():
    contract = json.loads((ROOT / "docs" / "data_capabilities" / "m8r_03b_conversation_scope_contract.json").read_text(encoding="utf-8"))
    assert "explicit_range" in contract["time_modes"]["enum"]


def test_facts_derived_assumptions_missing_remain_distinct():
    contract = json.loads((ROOT / "docs" / "data_capabilities" / "m8r_03b_evidence_bundle_contracts.json").read_text(encoding="utf-8"))
    assert contract["ai_input_layers"] == ["facts", "derived_metrics", "resolution_assumptions", "missing_evidence"]


def test_current_mis_reuse_requires_freshness_check():
    contract = json.loads((ROOT / "docs" / "data_capabilities" / "m8r_03b_conversation_scope_contract.json").read_text(encoding="utf-8"))
    assert contract["follow_up_context"]["current_mis_reuse"] == "freshness_check_required"
