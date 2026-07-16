import copy
import json
from pathlib import Path

import pytest

from scripts.m8r_03b_design_contract_validator import (
    validate_bundle,
    validate_conversation_intent,
    validate_evidence_request,
    validate_fixture,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "m8r_03b"


def fixture_records():
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(FIXTURE_DIR.glob("*.json"))]


def base_fixture():
    return fixture_records()[0]


def test_all_eight_fixtures_validate_against_reference_contracts():
    records = fixture_records()
    assert len(records) == 8
    for fixture in records:
        validate_fixture(fixture)
        validate_conversation_intent(
            fixture["parsed_conversation_intent"],
            persistent_watchlist_reference=fixture["evidence_request"].get("persistent_watchlist_reference"),
            follow_up_context=fixture.get("follow_up_context"),
        )
        validate_evidence_request(fixture["evidence_request"])
        for bundle in fixture["sample_bundles"]:
            validate_bundle(bundle)


def test_fixtures_use_v2_intent_shape_without_top_level_time_mode():
    for fixture in fixture_records():
        intent = fixture["parsed_conversation_intent"]
        assert intent["schema_version"] == "m8r_ai_market_conversation_intent.v1"
        assert "time_mode" not in intent
        assert set(intent["time_scope"]) == {"mode", "lookback_trading_days", "explicit_range"}


def expect_reject(mutator, message):
    fixture = base_fixture()
    mutator(fixture)
    with pytest.raises(ValueError, match=message):
        validate_fixture(fixture)


def test_unknown_scope_mode_rejected():
    expect_reject(lambda f: f["parsed_conversation_intent"]["scope_modes"].append("whole_market_scan"), "unknown scope mode")


def test_invalid_time_mode_rejected():
    expect_reject(lambda f: f["parsed_conversation_intent"]["time_scope"].__setitem__("mode", "right_now_realtime"), "invalid time_scope.mode")


def test_explicit_range_without_range_object_rejected():
    def mutate(f):
        f["parsed_conversation_intent"]["time_scope"]["mode"] = "explicit_range"
        f["parsed_conversation_intent"]["time_scope"]["explicit_range"] = None
    expect_reject(mutate, "explicit_range must be an object")


def test_clarification_true_with_null_reason_rejected():
    def mutate(f):
        f["parsed_conversation_intent"]["clarification_required"] = True
        f["parsed_conversation_intent"]["clarification_reason"] = None
    expect_reject(mutate, "clarification_reason must be a non-empty string")


def test_clarification_false_with_non_null_reason_rejected():
    def mutate(f):
        f["parsed_conversation_intent"]["clarification_required"] = False
        f["parsed_conversation_intent"]["clarification_reason"] = "should ask"
    expect_reject(mutate, "clarification_reason must be null")


def test_dynamic_entity_mutation_true_rejected():
    fixture = next(item for item in fixture_records() if item["evidence_request"].get("dynamic_entity_requests"))
    fixture = copy.deepcopy(fixture)
    fixture["evidence_request"]["dynamic_entity_requests"][0]["persistent_watchlist_mutation"] = True
    with pytest.raises(ValueError, match="dynamic entity cannot mutate"):
        validate_fixture(fixture)


def test_watchlist_target_missing_from_coverage_rejected():
    def mutate(f):
        f["expected_requested_target_ids"].append("missing_target")
        f["sample_bundles"][0]["coverage"]["requested_target_ids"].append("missing_target")
    expect_reject(mutate, "every enabled requested target")


def test_unavailable_without_reason_code_rejected():
    def mutate(f):
        f["expected_target_coverage"][0]["coverage_state"] = "unavailable"
        f["expected_target_coverage"][0]["reason_code"] = None
    expect_reject(mutate, "reason_code")


def test_partial_without_missing_field_groups_rejected():
    def mutate(f):
        f["expected_target_coverage"][0]["coverage_state"] = "partial"
        f["expected_target_coverage"][0]["missing_field_groups"] = []
    expect_reject(mutate, "partial coverage requires missing_field_groups")


def test_derived_metric_without_formula_id_rejected():
    def mutate(f):
        del f["sample_derived_metric"]["formula_id"]
    expect_reject(mutate, "formula_id")


def test_current_mis_reuse_without_freshness_flag_rejected():
    fixture = next(item for item in fixture_records() if item.get("follow_up_context"))
    fixture = copy.deepcopy(fixture)
    fixture["evidence_request"]["follow_up_context"]["freshness_recheck_required"] = False
    with pytest.raises(ValueError, match="freshness_recheck_required=true"):
        validate_fixture(fixture)
