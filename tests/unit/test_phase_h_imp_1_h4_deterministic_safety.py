"""Fixture-only acceptance tests for the pure Phase H H4 derivation kernel."""

from __future__ import annotations

import copy
import json
import socket
import urllib.request
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from scripts.validate_phase_h_v3_contracts import (
    validate_discontinuity_safety_semantics,
    validate_h2_h3_h4_cross_evidence,
)
from server.services.phase_h_discontinuity_safety import H4DerivationError, derive_discontinuity_safety


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = json.loads((ROOT / "tests/fixtures/phase_h_contract_v3/contract_examples.json").read_text(encoding="utf-8"))
TRUTH_TABLE = json.loads((ROOT / "tests/fixtures/phase_h_h4_derivation/truth_table.json").read_text(encoding="utf-8"))
H4_SCHEMA = json.loads((ROOT / "schemas/discontinuity_safety_evidence.v1.schema.json").read_text(encoding="utf-8"))


def h3() -> dict:
    return copy.deepcopy(EXAMPLES["h3_1d"])


def event(*, effective_date: str | None = "2026-08-20", reference: bool = True, lifecycle: str = "effective", revision: str = "officially_linked") -> dict:
    item = copy.deepcopy(EXAMPLES["h2_preannouncement_and_final"]["events"][1])
    item["effective_date"] = effective_date
    item["event_lifecycle"] = lifecycle
    item["official_reference_price"] = {"state": "value", "value": 95} if reference else {"state": "unavailable", "value": None}
    relation_type = {"corrected": "corrects", "amended": "amends", "cancelled": "cancels"}.get(lifecycle, "supersedes")
    item["revision_relation"] = (
        {"status": "officially_linked", "relation_type": relation_type, "related_official_reference": "fixture-pre"}
        if revision == "officially_linked"
        else {"status": "unresolved", "relation_type": None, "related_official_reference": None}
    )
    return item


def h2(*, events: list[dict] | None = None, status: str = "available", uncovered: list[str] | None = None) -> dict:
    value = copy.deepcopy(EXAMPLES["h2_preannouncement_and_final"])
    coverage = value["coverage"]
    coverage.update({
        "status": "complete",
        "declared_scope_complete": True,
        "retrieval_succeeded": True,
        "source_contract_validated": True,
        "exact_target_search_succeeded": True,
        "requested_window": {"start": "2026-08-01", "end": "2026-08-28"},
        "declared_event_subtypes": ["ex_dividend"],
        "covered_event_subtypes": ["ex_dividend"],
        "uncovered_event_subtypes": uncovered or [],
        "failed_source_families": [],
    })
    if uncovered:
        coverage["declared_event_subtypes"] = ["ex_dividend", *uncovered]
        coverage["status"] = "partial"
        coverage["declared_scope_complete"] = False
    if not events and status == "available":
        status = "no_evidence_in_covered_scope" if not uncovered else "partial"
    if status == "source_failed":
        coverage.update({"status": "source_failed", "retrieval_succeeded": False, "source_contract_validated": False, "failed_source_families": ["FIXTURE_SOURCE"]})
    if status == "binding_failed":
        coverage.update({"status": "binding_failed", "exact_target_search_succeeded": False})
    value["status"] = status
    value["events"] = events or []
    value["caveats"] = []
    return value


def derive(h2_value: dict, h3_value: dict | None = None, **kwargs: object) -> dict:
    return derive_discontinuity_safety(
        h2_evidence=h2_value,
        h3_evidence=h3_value or h3(),
        h2_evidence_reference="fixture-h2",
        h3_evidence_reference="fixture-h3",
        **kwargs,
    )


def assert_valid(h2_value: dict, h3_value: dict, h4_value: dict) -> None:
    assert not list(Draft7Validator(H4_SCHEMA).iter_errors(h4_value))
    validate_discontinuity_safety_semantics(h4_value)
    validate_h2_h3_h4_cross_evidence(h2_value, h3_value, h4_value)


def test_fixture_truth_table_and_schema_cross_evidence() -> None:
    cases = {
        "F1": (h2(), {}, "no_material_discontinuity_detected"),
        "F2": (h2(events=[event()]), {"event_evidence_references": {0: "event-final"}, "official_reference_evidence_references": {0: "reference-final"}}, "discontinuity_detected_reference_available"),
        "F3": (h2(events=[event(reference=False)]), {"event_evidence_references": {0: "event-final"}}, "discontinuity_detected_reference_unavailable"),
        "F4": (h2(uncovered=["capital_reduction_resume"]), {}, "coverage_incomplete"),
        "F5": (h2(status="source_failed"), {}, "coverage_incomplete"),
        "F6": (h2(status="binding_failed"), {}, "coverage_incomplete"),
        "F7": (h2(events=[event(effective_date="2026-09-01", lifecycle="scheduled")]), {}, "no_material_discontinuity_detected"),
        "F8": (h2(events=[event(), event(effective_date="2026-08-21")]), {"event_evidence_references": {0: "event-a", 1: "event-b"}, "official_reference_evidence_references": {0: "reference-a", 1: "reference-b"}}, "discontinuity_detected_reference_available"),
        "F9": (h2(events=[event(revision="unresolved")]), {"event_evidence_references": {0: "event-unresolved"}}, "coverage_incomplete"),
        "F10": (h2(events=[event(reference=False)]), {"event_evidence_references": {0: "event-final"}}, "discontinuity_detected_reference_unavailable"),
    }
    for case_id, (h2_value, kwargs, expected) in cases.items():
        result = derive(h2_value, **kwargs)
        assert result["state"] == expected == TRUTH_TABLE["cases"][case_id]
        assert_valid(h2_value, h3(), result)
    assert derive(cases["F8"][0], **cases["F8"][1])["effective_event_evidence_references"] == ["event-a", "event-b"]


def test_precedence_boundaries_and_raw_metric_preservation() -> None:
    incomplete = derive(h2(events=[event(reference=True)], uncovered=["capital_reduction_resume"]), event_evidence_references={0: "event"})
    assert incomplete["state"] == "coverage_incomplete"
    assert incomplete["raw_metric_status"] == "available"
    assert incomplete["ordinary_return_interpretation"] == "blocked"
    assert derive(h2(events=[event(effective_date="2026-08-01")]), event_evidence_references={0: "event"})["state"] == "no_material_discontinuity_detected"
    assert derive(h2(events=[event(effective_date="2026-08-28")]), event_evidence_references={0: "event"}, official_reference_evidence_references={0: "reference"})["state"] == "discontinuity_detected_reference_available"
    mixed = derive(h2(events=[event(), event(effective_date="2026-08-21", reference=False)]), event_evidence_references={0: "a", 1: "b"}, official_reference_evidence_references={0: "ref-a"})
    assert mixed["state"] == "discontinuity_detected_reference_unavailable"
    assert mixed["raw_metric_status"] == "available"


def test_fail_closed_invalid_input_and_window_conditions() -> None:
    other_h3 = h3(); other_h3["target"]["security_code"] = "0050"
    with pytest.raises(H4DerivationError, match="target_identity_mismatch"):
        derive(h2(), other_h3)
    unavailable = h3()
    unavailable.update({"coverage_status": "insufficient", "available_baselines": [], "unavailable_baselines": [1]})
    unavailable["baselines"][0].update({"status": "unavailable", "recent_return_pct": None})
    with pytest.raises(H4DerivationError, match="h3_requires_exactly_one_available_baseline"):
        derive(h2(), unavailable)
    reversed_h3 = h3(); reversed_h3["baselines"][0]["start_observation_date"] = "2026-08-29"
    with pytest.raises(H4DerivationError, match="h3_semantics_invalid"):
        derive(h2(), reversed_h3)
    malformed = h2(); del malformed["coverage"]
    with pytest.raises(H4DerivationError, match="h2_schema_invalid"):
        derive(malformed)
    malformed_h3 = h3(); del malformed_h3["governed_end_observation"]
    with pytest.raises(H4DerivationError, match="h3_schema_invalid"):
        derive(h2(), malformed_h3)
    misaligned = h2(); misaligned["coverage"]["requested_window"]["end"] = "2026-08-27"
    result = derive(misaligned)
    assert result["state"] == "coverage_incomplete"
    assert result["upstream_failures"][0]["failure_type"] == "missing_required_evidence"
    contradictory = h2(events=[event()]); contradictory["coverage"].update({"status": "partial", "declared_scope_complete": False, "uncovered_event_subtypes": ["ex_dividend"]})
    with pytest.raises(H4DerivationError, match="h2_semantics_invalid"):
        derive(contradictory)


def test_failed_source_provenance_is_exact_and_not_invented() -> None:
    failed = h2(status="source_failed")
    source_a = copy.deepcopy(failed["sources"][0]); source_a["source_family"] = "SOURCE_A"
    source_b = copy.deepcopy(source_a); source_b["source_family"] = "SOURCE_B"
    failed["sources"] = [source_a, source_b]
    failed["coverage"]["failed_source_families"] = ["SOURCE_A"]
    result = derive(failed)
    assert result["failed_source_families"] == ["SOURCE_A"]
    unknown_family = h2(status="source_failed")
    unknown_family["coverage"]["failed_source_families"] = []
    result = derive(unknown_family)
    assert result["failed_source_families"] == []
    assert result["upstream_failures"] == [{"failure_type": "source_failed", "evidence_reference": None}]


def test_window_mismatch_accumulates_source_and_binding_failures() -> None:
    source_failed = h2(status="source_failed")
    source_failed["coverage"]["requested_window"]["end"] = "2026-08-27"
    source_failed["coverage"]["failed_source_families"] = ["SOURCE_A"]
    source_result = derive(source_failed)
    assert [item["failure_type"] for item in source_result["upstream_failures"]] == ["missing_required_evidence", "source_failed"]
    assert source_result["failed_source_families"] == ["SOURCE_A"]
    binding_failed = h2(status="binding_failed")
    binding_failed["coverage"]["requested_window"]["end"] = "2026-08-27"
    binding_result = derive(binding_failed)
    assert [item["failure_type"] for item in binding_result["upstream_failures"]] == ["missing_required_evidence", "binding_failed"]


@pytest.mark.parametrize("lifecycle", ["scheduled", "announced", "unresolved"])
def test_in_window_unresolved_lifecycle_is_coverage_incomplete(lifecycle: str) -> None:
    result = derive(h2(events=[event(lifecycle=lifecycle)]), event_evidence_references={0: "event-lifecycle"})
    assert result["state"] == "coverage_incomplete"
    assert result["upstream_failures"] == [{"failure_type": "unresolved_effective_timing", "evidence_reference": "event-lifecycle"}]
    with pytest.raises(H4DerivationError, match="event_evidence_reference_missing"):
        derive(h2(events=[event(lifecycle=lifecycle)]))


@pytest.mark.parametrize("lifecycle", ["corrected", "amended", "cancelled"])
def test_officially_linked_revision_lifecycle_is_not_mislabeled_unresolved(lifecycle: str) -> None:
    result = derive(h2(events=[event(lifecycle=lifecycle)]), event_evidence_references={0: "event-linked"})
    assert result["state"] == "coverage_incomplete"
    assert {item["failure_type"] for item in result["upstream_failures"]} == {"missing_required_evidence"}


def test_unresolved_lifecycle_without_effective_date_is_coverage_incomplete() -> None:
    result = derive(h2(events=[event(lifecycle="unresolved", effective_date=None)]), event_evidence_references={0: "event-no-date"})
    assert result["state"] == "coverage_incomplete"
    assert result["upstream_failures"] == [{"failure_type": "unresolved_effective_timing", "evidence_reference": "event-no-date"}]
    with pytest.raises(H4DerivationError, match="event_evidence_reference_missing"):
        derive(h2(events=[event(lifecycle="unresolved", effective_date=None)]))


def test_schema_valid_semantic_invalid_upstream_evidence_rejects() -> None:
    source_failed_available = h3(); source_failed_available["coverage_status"] = "source_failed"
    with pytest.raises(H4DerivationError, match="h3_schema_invalid|h3_semantics_invalid"):
        derive(h2(), source_failed_available)
    missing_return = h3(); missing_return["baselines"][0]["recent_return_pct"] = None
    with pytest.raises(H4DerivationError, match="h3_semantics_invalid"):
        derive(h2(), missing_return)
    bad_arithmetic = h3(); bad_arithmetic["baselines"][0]["recent_return_pct"] = 19.0
    with pytest.raises(H4DerivationError, match="h3_semantics_invalid"):
        derive(h2(), bad_arithmetic)
    incomplete_no_evidence = h2(); incomplete_no_evidence["coverage"]["declared_scope_complete"] = False
    with pytest.raises(H4DerivationError, match="h2_schema_invalid|h2_semantics_invalid"):
        derive(incomplete_no_evidence)


def test_repeatability_and_network_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: pytest.fail("network attempted"))
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: pytest.fail("network attempted"))
    source = h2(events=[event()])
    kwargs = {"event_evidence_references": {0: "event"}, "official_reference_evidence_references": {0: "reference"}}
    first = derive(source, **kwargs)
    second = derive(source, **kwargs)
    assert first == second
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(second, sort_keys=True, separators=(",", ":"))
