import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((ROOT / "docs/data_capabilities/m8r_03b_conversation_scope_contract.json").read_text(encoding="utf-8"))
BUNDLES = json.loads((ROOT / "docs/data_capabilities/m8r_03b_evidence_bundle_contracts.json").read_text(encoding="utf-8"))
FIXTURE_DIR = ROOT / "tests/fixtures/m8r_03b"


def fixture_records():
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(FIXTURE_DIR.glob("*.json"))]


def intent_scope_enum():
    return set(CONTRACT["scope_modes"]["enum"])


def time_enum():
    return set(CONTRACT["time_modes"]["enum"])


def validate_intent(intent, *, watchlist_reference=None, follow_up_context=None):
    assert intent["scope_modes"], "scope_modes required"
    unknown_scopes = set(intent["scope_modes"]) - intent_scope_enum()
    assert not unknown_scopes, f"unknown scope mode: {unknown_scopes}"
    assert intent["time_mode"] in time_enum() or intent.get("time_scope", {}).get("mode") in time_enum()
    if intent.get("clarification_required") is True:
        assert intent.get("clarification_reason")
    if intent.get("clarification_required") is False:
        assert intent.get("clarification_reason") is None
    if "watchlist_subset" in intent["scope_modes"]:
        assert watchlist_reference or (follow_up_context or {}).get("parent_evidence_request_id")


def test_contracts_define_required_top_level_validator_shapes():
    intent_fields = {field["field_name"] for field in CONTRACT["conversation_intent"]["fields"]}
    assert {"schema_version", "original_user_text", "scope_modes", "time_scope", "evidence_depth", "explicit_user_constraints", "inferred_defaults", "clarification_required", "clarification_reason"}.issubset(intent_fields)
    request_fields = {field["field_name"] for field in BUNDLES["common_evidence_request"]["fields"]}
    assert {"conversation_intent", "persistent_watchlist_reference", "dynamic_entity_requests", "market_context_requests", "required_evidence", "useful_evidence", "optional_evidence", "execution_policy", "identity_resolver_output", "follow_up_context"}.issubset(request_fields)


def test_unknown_scope_mode_is_rejected_by_contract_validator():
    bad = {"scope_modes": ["watchlist", "whole_market_scan"], "time_mode": "current", "clarification_required": False, "clarification_reason": None}
    try:
        validate_intent(bad)
    except AssertionError as exc:
        assert "unknown scope mode" in str(exc)
    else:
        raise AssertionError("unknown scope mode accepted")


def test_invalid_time_mode_is_rejected_by_contract_validator():
    bad = {"scope_modes": ["watchlist"], "time_mode": "right_now_realtime", "clarification_required": False, "clarification_reason": None}
    try:
        validate_intent(bad)
    except AssertionError:
        pass
    else:
        raise AssertionError("invalid time mode accepted")


def test_clarification_invariants_hold_for_all_fixtures():
    for fixture in fixture_records():
        intent = dict(fixture["parsed_conversation_intent"])
        decision = fixture["clarification_decision"]
        intent["clarification_required"] = decision["clarification_required"]
        intent["clarification_reason"] = decision["reason"]
        validate_intent(intent, watchlist_reference=fixture["evidence_request"].get("persistent_watchlist_reference"), follow_up_context=fixture.get("follow_up_context"))


def test_dynamic_research_cannot_mutate_persistent_watchlist():
    dynamic_type = BUNDLES["record_types"]["dynamic_entity_request"]
    mutation_field = next(field for field in dynamic_type["fields"] if field["field_name"] == "persistent_watchlist_mutation")
    assert mutation_field["default"] is False
    assert "must be false" in mutation_field["invariants"]
    for fixture in fixture_records():
        for item in fixture["evidence_request"].get("dynamic_entity_requests", []):
            assert item["persistent_watchlist_mutation"] is False


def test_watchlist_target_coverage_is_complete_for_watchlist_fixtures():
    for fixture in fixture_records():
        if fixture["evidence_request"].get("persistent_watchlist_reference") is None:
            continue
        coverage = fixture["expected_target_coverage"]
        target_ids = [item["target_id"] for item in coverage]
        assert len(target_ids) == len(set(target_ids))
        for item in coverage:
            assert item["coverage_state"] in {"usable", "partial", "unavailable"}
            if item["coverage_state"] == "unavailable":
                assert item.get("reason_code")
            if item["coverage_state"] == "partial":
                assert item.get("missing_field_groups")
            if item["coverage_state"] == "usable":
                assert item.get("present_field_groups")


def test_unavailable_target_requires_reason_code_contract_invariant():
    coverage_type = BUNDLES["record_types"]["target_coverage_record"]
    assert "unavailable -> reason_code required" in coverage_type["invariants"]


def test_derived_metrics_require_formula_metadata():
    required = {field["field_name"] for field in BUNDLES["record_types"]["derived_metric_record"]["fields"] if field.get("required", True)}
    assert {"metric_id", "value", "formula_id", "input_period", "source_dependencies", "calculation_status", "as_of"}.issubset(required)
    statuses = next(field for field in BUNDLES["record_types"]["derived_metric_record"]["fields"] if field["field_name"] == "calculation_status")["enum"]
    assert {"calculated", "partial", "input_unavailable", "formula_not_applicable", "stale_inputs", "error"}.issubset(set(statuses))


def test_current_mis_reuse_requires_freshness_check():
    assert CONTRACT["follow_up_context"]["current_mis_reuse"] == "freshness_check_required"


def test_market_pulse_missing_capabilities_remain_explicitly_represented():
    market_pulse = next(bundle for bundle in BUNDLES["bundles"] if bundle["bundle"] == "market_pulse")
    groups = market_pulse["field_group_contract"]
    group_ids = {group["field_group_id"] for group in groups}
    assert {"index_direction_taiex", "index_direction_tpex", "turnover_rolling_baselines", "breadth_counts", "style_concentration", "cash_institutional_positioning", "tx_current_reference", "basis", "futures_volume_oi", "institutional_derivatives_positions", "put_call_ratios", "atm_option_evidence", "volatility_oi_structure"}.issubset(group_ids)
    missing_or_partial = [group for group in groups if "not_integrated" in group["allowed_availability_status"] or "source_not_yet_probed" in group["allowed_availability_status"]]
    assert missing_or_partial
