"""Acceptance-only typed semantic regression tests; prose is not an oracle."""
import copy
import json
from pathlib import Path

import pytest

from scripts.validate_phase_j_j3_golden_expected_semantics import evaluate_scenario, validate_contract

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "docs/governance/phase_j/PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json").read_text())
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
    assert summary == {"scenario_count": 27, "dimension_count": 11, "j1_assertions_mapped": 182, "j1_forbidden_claims_mapped": sum(len(x["forbidden_claims"]) for x in GOLDEN["scenarios"]), "orphan_assertions": 0, "dropped_assertions": 0, "mcp_tools": 6}


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
