from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m8r_05c.markdown_renderer import render_result_markdown
from scripts.m8r_05c.result_builder import build_result
from scripts.validate_l5_extension_semantic_conformance import FAILURE_CODES, compare_trace
from tests.unit.test_phase_g_result_v2_projection import _projection_inputs


@pytest.mark.parametrize("field,category", [
    ("normalized_facts", "A3_NORMALIZATION_SEMANTIC_DRIFT"),
    ("timing", "A3_TIMING_SEMANTIC_DRIFT"),
    ("currentness", "A3_CURRENTNESS_SEMANTIC_DRIFT"),
    ("status_matrix", "A3_MISSING_UNSUPPORTED_FAILURE_COLLAPSE"),
    ("target_identity", "A3_LINEAGE_TARGET_MISMATCH"),
    ("operation_id", "A3_LINEAGE_OPERATION_MISMATCH"),
    ("artifact_reference", "A3_CITATION_ARTIFACT_MISMATCH"),
    ("result_projection", "A3_RESULT_SEMANTIC_DRIFT"),
    ("audit_identity", "A3_RESULT_AUDIT_IDENTITY_MISMATCH"),
    ("audit_provenance", "A3_AUDIT_PROVENANCE_DRIFT"),
    ("mandatory_caveats", "A3_HANDOFF_CAVEAT_LOSS"),
    ("handoff_citations", "A3_HANDOFF_CITATION_DRIFT"),
    ("public_contract_versions", "A3_PUBLIC_CONTRACT_CHANGE_REQUIRED"),
])
def test_trace_mutations_fail_with_stable_category(field: str, category: str):
    expected = {key: "canonical" for key in (
        "normalized_facts", "timing", "currentness", "status_matrix", "target_identity",
        "operation_id", "artifact_reference", "result_projection", "audit_identity",
        "audit_provenance", "mandatory_caveats", "handoff_citations", "public_contract_versions",
    )}
    actual = deepcopy(expected)
    actual[field] = "mutated"
    assert compare_trace(expected, actual) == [category]


def test_absent_operation_remains_missing_not_source_failed():
    inputs = _projection_inputs("unified_market_evidence_request.v2")
    inputs.request["data_needs"] = inputs.request["data_needs"][:1]
    inputs.plan["operations"] = []
    inputs.bundle["operation_evidence_entries"] = []
    inputs.bundle["artifact_inventory"] = []
    inputs.evidence_artifacts = {}
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    target = result["targets"][0]
    assert target["coverage"]["missing_needs"] == ["material_disclosures"]
    assert "material_disclosures" not in target["evidence"]
    assert "source_failed" not in str(target)


def test_v3_handoff_includes_phase_i_typed_evidence_and_citation():
    evidence = {
        "schema_version": "market_state_context_evidence.v1",
        "status": "partial",
        "coverage": {"covered": ["advance_decline"], "missing": ["turnover"]},
        "retrieved_at": "2026-09-29T06:00:00Z",
        "caveats": ["fixture caveat"],
        "citation_ids": ["cite-phase-i-1"],
    }
    result = {
        "schema_version": "unified_market_evidence_result.v3",
        "request_summary": {"request_id": "fixture", "request_schema_version": "unified_market_evidence_request.v3"},
        "targets": [{"canonical_identity": {"canonical_target_id": "TPEX:6488"},
                     "coverage": {"provided_needs": ["market_state_context"], "missing_needs": []},
                     "evidence": {"market_state_context": evidence},
                     "citations": [{"citation_id": "cite-phase-i-1", "source_family": "fixture", "retrieved_at": "2026-09-29T06:00:00Z", "artifact_reference": "evidence.json"}]}],
        "audit_reference": {},
    }
    markdown = render_result_markdown(result)
    for token in ("market_state_context", "partial", "turnover", "fixture caveat", "cite-phase-i-1", "retrieved_at"):
        assert token in markdown


def test_trace_comparison_accepts_identical_semantics():
    trace = {field: {"value": field} for field in (
        "normalized_facts", "timing", "currentness", "status_matrix", "target_identity",
        "operation_id", "artifact_reference", "result_projection", "audit_identity",
        "audit_provenance", "mandatory_caveats", "handoff_citations", "public_contract_versions",
    )}
    assert compare_trace(trace, deepcopy(trace)) == []
    assert len(FAILURE_CODES) >= 13
