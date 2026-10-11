"""Acceptance-only typed semantic regression tests; prose is not an oracle."""
import copy
import json
from pathlib import Path

import pytest

from scripts.phase_j_j3_projection import operator_inventory
from scripts.validate_phase_j_j3_golden_expected_semantics import (
    evaluate_scenario, validate_contract, validate_projection,
)

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "docs/governance/phase_j/PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json").read_text())
REGISTRY = json.loads((ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json").read_text())
TRACE = json.loads((ROOT / "docs/governance/phase_j/PHASE_J_J3_SEMANTIC_TRACEABILITY_V1.json").read_text())
BY_ID = {row["scenario_id"]: row for row in GOLDEN["scenarios"]}


def expected_observation(row):
    result = {"facts": {}, "result": {}, "audit": {}, "handoff": {}, "authorization": {}}
    for assertion in row["assertions"]:
        value = assertion["expected"]
        result.setdefault(assertion["context"], {})[assertion["path"]] = value
        result["facts"][assertion["path"]] = value
    return result


def test_j3_contract_maps_all_j1_semantics_and_acceptance_boundaries():
    summary = validate_contract()
    assert summary["scenario_count"] == 27
    assert summary["dimension_count"] == 11
    assert summary["j1_assertions_mapped"] == summary["assertion_projection_count"] == 182
    assert summary["expectation_family_projection_count"] == 27 * 14
    assert summary["forbidden_claim_projection_count"] == summary["j1_forbidden_claims_mapped"] == 178
    assert summary["accepted_fail_closed_projection_count"] == summary["readiness_status_projection_count"] == 27
    assert summary["assertion_operator_inventory"] == {"equals": 128, "is_true": 54}
    assert summary["orphan_assertions"] == summary["dropped_assertions"] == 0
    assert summary["mcp_tools"] == 6


def assert_projection_rejected(golden=None, registry=None, trace=None, match="projection mismatch"):
    with pytest.raises(ValueError, match=match):
        validate_projection(
            copy.deepcopy(registry if registry is not None else REGISTRY),
            copy.deepcopy(golden if golden is not None else GOLDEN),
            copy.deepcopy(trace if trace is not None else TRACE),
        )


@pytest.mark.parametrize("field,bad", [
    ("expected", "changed-result-v9"),
    ("path", "other_schema_path"),
    ("context", "handoff"),
    ("predicate", "present"),
])
def test_same_assertion_id_with_changed_semantic_content_fails(field, bad):
    changed = copy.deepcopy(GOLDEN)
    assertion = next(x for x in changed["scenarios"][0]["assertions"] if x["assertion_id"] == "result_v3_contract")
    assertion[field] = bad
    assert_projection_rejected(golden=changed, match="assertion .* projection mismatch")


@pytest.mark.parametrize("field,bad", [
    ("value", "unified_market_evidence_result.v4"),
    ("path", "different_result_path"),
    ("context", "handoff"),
    ("operator", "is_true"),
])
def test_changed_j1_assertion_content_cannot_be_hidden_by_stable_id(field, bad):
    changed = copy.deepcopy(REGISTRY)
    assertion = next(x for x in changed["scenarios"][0]["expected_semantic_assertions"] if x["assertion_id"] == "result_v3_contract")
    assertion[field] = bad
    assert_projection_rejected(registry=changed, match="assertion .* projection mismatch|unmapped explicit value")


def test_assertion_added_or_dropped_fails_even_if_other_ids_remain():
    dropped = copy.deepcopy(GOLDEN)
    dropped["scenarios"][0]["assertions"].pop()
    assert_projection_rejected(golden=dropped, match="assertion added/dropped")
    added = copy.deepcopy(GOLDEN)
    added["scenarios"][0]["assertions"].append(copy.deepcopy(added["scenarios"][0]["assertions"][0]))
    assert_projection_rejected(golden=added, match="assertion added/dropped|duplicate assertion ID")


def test_j1_assertion_operator_inventory_and_closed_normalization():
    assert operator_inventory(REGISTRY) == {"equals": 128, "is_true": 54}
    source = next(a for row in REGISTRY["scenarios"] for a in row["expected_semantic_assertions"] if a["operator"] == "is_true")
    from scripts.phase_j_j3_projection import normalize_assertion
    normalized = normalize_assertion("J1-01", source)
    assert normalized["predicate"] == "equals" and normalized["expected"] is True
    changed_registry = copy.deepcopy(REGISTRY)
    changed_registry["scenarios"][0]["expected_semantic_assertions"][0]["operator"] = "arbitrary_eval"
    assert_projection_rejected(registry=changed_registry, match="UNMAPPABLE_J1_ASSERTION_OPERATOR")


@pytest.mark.parametrize("scenario_id,family,mutation,expected_match", [
    ("J1-14", "coverage_expectation", "remove", "expectation family projection keys mismatch"),
    ("J1-14", "coverage_expectation", "status", "coverage_expectation: deep projection mismatch"),
    ("J1-14", "coverage_expectation", "scope", "coverage_expectation: deep projection mismatch"),
    ("J1-14", "coverage_expectation", "remove_complete", "coverage_expectation: deep projection mismatch"),
    ("J1-14", "coverage_expectation", "weaken_complete", "coverage_expectation: deep projection mismatch"),
    ("J1-14", "corporate_action_expectation", "change", "corporate_action_expectation: deep projection mismatch"),
    ("J1-05", "timing_expectation", "change", "timing_expectation: deep projection mismatch"),
    ("J1-16", "interpretation_guard_expectation", "weaken", "interpretation_guard_expectation: deep projection mismatch"),
    ("J1-20", "partial_expectation", "change", "partial_expectation: deep projection mismatch"),
    ("J1-22", "missing_expectation", "change", "missing_expectation: deep projection mismatch"),
    ("J1-01", "source_expectation", "change", "source_expectation: deep projection mismatch"),
    ("J1-26", "authorization_expectation", "change", "authorization_expectation: deep projection mismatch"),
    ("J1-27", "resource_bound_expectation", "change", "resource_bound_expectation: deep projection mismatch"),
    ("J1-01", "citation_expectation", "change", "citation_expectation: deep projection mismatch"),
    ("J1-01", "lineage_expectation", "change", "lineage_expectation: deep projection mismatch"),
])
def test_expectation_family_content_mutations_fail(scenario_id, family, mutation, expected_match):
    changed = copy.deepcopy(GOLDEN)
    scenario = next(x for x in changed["scenarios"] if x["scenario_id"] == scenario_id)
    dimension_by_family = {
        "coverage_expectation": ("source", "coverage_expectation"),
        "corporate_action_expectation": ("corporate_action", "corporate_action_expectation"),
        "timing_expectation": ("period", "timing_expectation"),
        "interpretation_guard_expectation": ("corporate_action", "interpretation_guard_expectation"),
        "partial_expectation": ("partial", "partial_expectation"),
        "missing_expectation": ("missing", "missing_expectation"),
        "source_expectation": ("source", "source_expectation"),
        "authorization_expectation": ("authorization", "authorization_expectation"),
        "resource_bound_expectation": ("bounded_execution", "resource_bound_expectation"),
        "citation_expectation": ("citations_lineage", "citation_expectation"),
        "lineage_expectation": ("citations_lineage", "lineage_expectation"),
    }
    dimension, key = dimension_by_family[family]
    value = scenario["dimensions"][dimension]["expectations"][key]
    if mutation == "remove":
        del scenario["dimensions"][dimension]["expectations"][key]
    elif mutation == "status":
        value["status"] = "complete"
    elif mutation == "scope":
        value["scope"] = "all sources and history"
    elif mutation == "remove_complete":
        del value["complete_family_claimed"]
    elif mutation == "weaken_complete":
        value["complete_family_claimed"] = True
    elif mutation == "weaken":
        value["ordinary_return_interpretation"] = "allowed"
    else:
        value[next(iter(value))] = "mutated"
    assert_projection_rejected(golden=changed, match=expected_match)


@pytest.mark.parametrize("field,bad", [
    ("handoff_text_marker", None),
    ("handoff_text_marker", "safe-marker-changed"),
    ("semantic_class", "different_claim_class"),
    ("description", "This claim is now permitted."),
])
def test_forbidden_claim_machine_content_mutation_fails(field, bad):
    changed = copy.deepcopy(GOLDEN)
    claim = changed["scenarios"][0]["forbidden_claims"][0]
    claim[field] = bad
    assert_projection_rejected(golden=changed, match=f"forbidden claim {field} projection mismatch")


def test_changed_j1_forbidden_content_cannot_be_hidden_by_stable_claim_id():
    changed = copy.deepcopy(REGISTRY)
    changed["scenarios"][0]["forbidden_claims"][0]["description"] = "This directional claim is permitted."
    assert_projection_rejected(registry=changed, match="forbidden claim description projection mismatch")


def test_forbidden_claim_cannot_disappear_via_duplicate_replacement_id():
    changed = copy.deepcopy(GOLDEN)
    claims = changed["scenarios"][0]["forbidden_claims"]
    claims[0]["claim_id"] = "replaced_claim"
    assert_projection_rejected(golden=changed, match="forbidden claim IDs mismatch|forbidden claim count mismatch")


@pytest.mark.parametrize("mutation", ["remove", "change", "positive"])
def test_fail_closed_outcomes_are_lossless(mutation):
    changed = copy.deepcopy(GOLDEN)
    row = next(x for x in changed["scenarios"] if x["scenario_id"] == "J1-08")
    if mutation == "remove":
        row["accepted_fail_closed_outcomes"] = []
    elif mutation == "change":
        row["accepted_fail_closed_outcomes"][0] = "revision_relation=supersedes"
    else:
        row["accepted_fail_closed_outcomes"].append("positive correction established")
    assert_projection_rejected(golden=changed, match="accepted fail-closed outcomes projection mismatch")


def test_content_trace_hashes_bind_source_and_target_values():
    validate_projection(REGISTRY, GOLDEN, TRACE)
    assert all(row["match"] and row["source_canonical_sha256"] == row["target_canonical_sha256"]
               for group in ("assertion_content_mappings", "expectation_family_mappings", "forbidden_claim_content_mappings", "accepted_fail_closed_mappings")
               for row in TRACE[group])


@pytest.mark.parametrize("scenario_id", ["J1-01", "J1-07", "J1-08", "J1-10", "J1-11", "J1-12", "J1-13", "J1-14", "J1-16", "J1-18", "J1-20", "J1-22", "J1-23", "J1-24", "J1-25", "J1-26", "J1-27"])
def test_positive_typed_semantic_calibration(scenario_id):
    row = BY_ID[scenario_id]
    assert evaluate_scenario(row, expected_observation(row)) == []


def test_harmless_handoff_wording_changes_do_not_change_semantic_acceptance():
    row = BY_ID["J1-01"]
    first = expected_observation(row) | {"prose": "Observed official evidence, bounded and not realtime."}
    second = expected_observation(row) | {"prose": "The source observation is delayed and scoped."}
    assert evaluate_scenario(row, first) == evaluate_scenario(row, second) == []


@pytest.mark.parametrize("scenario_id,path,bad", [
    ("J1-01", "identity", "ambiguous"),
    ("J1-01", "source", "unofficial_substitute"),
    ("J1-05", "period", "calendar_today"),
    ("J1-21", "currentness_policy", "source_date_equals_today"),
    ("J1-22", "numeric_value", 0),
    ("J1-23", "valid_empty", True),
    ("J1-20", "result_status", "full_success"),
    ("J1-16", "ordinary_return_interpretation", "allowed"),
    ("J1-26", "execution_started", True),
    ("J1-27", "unbounded_execution", True),
    ("J1-01", "citation_source", "other_source"),
    ("J1-01", "audit_result_id", "different-result"),
])
def test_semantic_mutations_fail_for_the_intended_reason(scenario_id, path, bad):
    row = BY_ID[scenario_id]
    observed = expected_observation(row)
    observed["facts"][path] = bad
    if path in {a["path"] for a in row["assertions"]}:
        for assertion in row["assertions"]:
            if assertion["path"] == path:
                observed.setdefault(assertion["context"], {})[path] = bad
    if path == "citation_source": observed["facts"]["evidence_source"] = "official_source"
    if path == "audit_result_id": observed["facts"]["result_id"] = "expected-result"
    if path == "result_status": observed["facts"]["partial"] = True
    if path == "execution_started": observed["facts"]["authorization"] = "refused"
    errors = evaluate_scenario(row, observed)
    expected_reason = {
        "identity": "j1-01_identity", "source": "j1-01_source", "period": "j1-05_period",
        "currentness_policy": "j1-21_currentness_policy", "numeric_value": "missing cannot become zero",
        "valid_empty": "j1-23_valid_empty", "result_status": "partial cannot become full_success",
        "ordinary_return_interpretation": "H4 incomplete coverage must block ordinary return",
        "execution_started": "refusal cannot start execution", "unbounded_execution": "resource bound cannot be bypassed",
        "citation_source": "citation/source mismatch", "audit_result_id": "Result/Audit lineage mismatch",
    }[path]
    assert any(expected_reason in error for error in errors), errors


def test_prose_identical_but_typed_identity_wrong_fails():
    row = BY_ID["J1-01"]
    observed = expected_observation(row)
    observed["facts"]["identity"] = "ambiguous"
    assert any("j1-01_identity" in error for error in evaluate_scenario(row, observed))


def test_global_contradictions_are_rejected():
    row = BY_ID["J1-16"]
    observed = expected_observation(row)
    observed["facts"].update(h4_state="coverage_incomplete", ordinary_return_interpretation="allowed")
    assert "H4 incomplete coverage must block ordinary return" in evaluate_scenario(row, observed)


def test_trading_recommendation_claim_fails_semantic_guard():
    row = BY_ID["J1-01"]
    observed = expected_observation(row)
    observed["violated_forbidden_claim_ids"] = ["investment_recommendation"]
    assert "forbidden semantic claim present" in evaluate_scenario(row, observed)


def test_source_failure_cannot_be_relabelled_as_valid_empty():
    row = BY_ID["J1-23"]
    observed = expected_observation(row)
    observed["facts"].update(source_state="source_failed", valid_empty=True)
    assert "source_failed cannot be valid_empty" in evaluate_scenario(row, observed)
