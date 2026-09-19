"""Focused C1 tests for dormant Result v2 projection primitives."""
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from scripts.m8r_05c.artifact_loader import _validate_request_schema
from scripts.m8r_05c.canonical import build_audit_package_id_v2, build_result_id_v2
from scripts.m8r_05c.errors import ProjectionError
from scripts.m8r_05c.evidence_projector import (
    _project_material_disclosures,
    _project_monthly_revenue,
)
from scripts.m8r_05c.citation_builder import build_citation_index
from scripts.m8r_05c.lineage_resolver import OperationBinding, build_lineage_map
from scripts.m8r_05c.models import (
    PartialFailureProjection, ProjectionInputs, ResolutionProjection, TargetProjection,
)
from scripts.m8r_05c.result_builder import _compute_result_status, build_result

ROOT = Path(__file__).resolve().parents[2]


def _binding(need: str, artifact: dict) -> OperationBinding:
    return OperationBinding(
        operation_id="op-1", capability_id=need,
        executor_id="phase_g_official_research_executor",
        canonical_target_id="TWSE:2330", requested_data_need=need,
        market="TWSE", status="succeeded", error_code=None,
        evidence_artifacts=[{"relative_path": "evidence.json"}],
        artifact_objects={"evidence.json": artifact},
    )


def test_v2_ids_are_deterministic_and_separate_from_v1():
    assert build_result_id_v2("r", "e", "b") == build_result_id_v2("r", "e", "b")
    assert build_result_id_v2("r", "e", "b").startswith("umeresult-v2-")
    assert build_audit_package_id_v2("umeresult-v2-" + "a" * 20, "b").startswith("umeap-v2-")


def test_unknown_request_schema_version_fails_closed():
    with pytest.raises(ProjectionError, match="unsupported_request_schema_version"):
        _validate_request_schema({"schema_version": "unified_market_evidence_request.v99"})


def test_material_projection_validates_frozen_ai_schema():
    artifact = {
        "status": "available",
        "source": {"source_family": "MOPS_MATERIAL_DISCLOSURE_OPEN_DATA", "source_contract_id": "t187ap04_L", "transport": "official_csv", "fallback_used": False},
        "observed_at": "2026-09-15T21:30:00+08:00",
        "coverage": {"source_report_date": "2026-09-15", "coverage_through": "2026-09-14", "truncated": False},
        "items": [{"published_at": "2026-09-14T15:02:01+08:00", "source_fact_date": None, "subject": "s", "clause": None, "description_raw": "d", "revision_relation": {"status": "unresolved", "relation_type": None, "related_official_reference": None}}],
        "caveats": [],
    }
    result = _project_material_disclosures(_binding("material_disclosures", artifact), ["cite-1"])
    schema = json.loads((ROOT / "schemas/material_disclosure_evidence.v1.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft7Validator(schema).iter_errors(result))
    assert result["items"][0]["citation_id"] == "cite-1"


def test_monthly_projection_preserves_signed_values_and_null_percentages():
    value = {"currency": "TWD", "unit": "thousand", "current_month_revenue": -1, "previous_month_revenue": 2, "previous_year_same_month_revenue": 3, "mom_pct": None, "yoy_pct": None, "ytd_revenue": 4, "previous_year_ytd_revenue": 5, "ytd_yoy_pct": None, "note": "官方備註"}
    artifact = {"status": "available", "source": {"source_family": "MOPS_MONTHLY_REVENUE_OPEN_DATA", "source_contract_id": "t187ap05_L", "transport": "official_csv", "fallback_used": False}, "observed_at": "2026-09-15T21:30:00+08:00", "coverage": {"reporting_period": "2026-08", "source_report_date": "2026-09-15"}, "value": value, "caveats": []}
    result = _project_monthly_revenue(_binding("monthly_revenue", artifact), ["cite-2"])
    assert result["value"]["current_month_revenue"] == -1
    assert result["value"]["mom_pct"] is None
    schema = json.loads((ROOT / "schemas/monthly_revenue_evidence.v1.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft7Validator(schema).iter_errors(result))


def _projection_inputs(request_version="unified_market_evidence_request.v2"):
    identity = {
        "canonical_target_id": "TWSE:2330", "isin": "TW0002330008", "market": "TWSE",
        "security_code": "2330", "security_name_zh": "台積電", "security_name_en": "TSMC",
        "instrument_family": "company_share", "instrument_type": "common_share",
    }
    material = {
        "status": "available", "source": {"source_family": "MOPS_MATERIAL_DISCLOSURE_OPEN_DATA",
        "source_contract_id": "t187ap04_L", "transport": "official_csv", "fallback_used": False},
        "observed_at": "2026-09-15T21:30:00+08:00",
        "coverage": {"source_report_date": "2026-09-15", "coverage_through": "2026-09-14", "truncated": False},
        "items": [{"published_at": "2026-09-14T15:02:01+08:00", "source_fact_date": "2026-09-14",
        "subject": "重大訊息", "clause": None, "description_raw": "官方說明",
        "revision_relation": {"status": "unresolved", "relation_type": None, "related_official_reference": None}}],
        "caveats": [],
    }
    revenue = {
        "status": "available", "source": {"source_family": "MOPS_MONTHLY_REVENUE_OPEN_DATA",
        "source_contract_id": "t187ap05_L", "transport": "official_csv", "fallback_used": False},
        "observed_at": "2026-09-15T21:30:00+08:00",
        "coverage": {"reporting_period": "2026-08", "source_report_date": "2026-09-15"},
        "value": {"currency": "TWD", "unit": "thousand", "current_month_revenue": 1,
        "previous_month_revenue": 2, "previous_year_same_month_revenue": 3, "mom_pct": None,
        "yoy_pct": None, "ytd_revenue": 4, "previous_year_ytd_revenue": 5,
        "ytd_yoy_pct": None, "note": "官方備註"}, "caveats": [],
    }
    paths = {"material_disclosures": "evidence/g1.json", "monthly_revenue": "evidence/g2.json"}
    artifacts = {paths["material_disclosures"]: material, paths["monthly_revenue"]: revenue}
    operations = []
    entries = []
    inventory = []
    for index, need in enumerate(("material_disclosures", "monthly_revenue"), start=1):
        path = paths[need]
        digest = str(index) * 64
        operations.append({"operation_id": f"op-{index}", "capability_id": need,
                           "executor_id": "phase_g_official_research_executor", "market": "TWSE",
                           "canonical_target_ids": ["TWSE:2330"]})
        art = {"relative_path": path, "sha256": digest,
               "schema_version": f"phase_g_{'material_disclosure' if index == 1 else 'monthly_revenue'}_operation_evidence.v1"}
        entries.append({"operation_id": f"op-{index}", "status": "succeeded", "artifacts": [art]})
        inventory.append({**art, "evidence_contract": art["schema_version"], "byte_size": 1})
    request = {"schema_version": request_version, "request_id": "req-v2", "execution_mode": "execute_once",
               "targets": [{"input": "2330"}], "data_needs": [
                   {"type": "material_disclosures", "priority": "required", "parameters": {}},
                   {"type": "monthly_revenue", "priority": "optional", "parameters": {}},
               ]}
    return ProjectionInputs(
        request=request,
        f3_validation={"target_results": [{"target_index": 0, "original_input": "2330",
                                           "resolution_status": "resolved", "canonical_identity": identity}]},
        plan={"operations": operations}, authorization={}, consumption_binding={}, claim={},
        receipt={"execution_receipt_id": "umerec-v1-" + "a" * 20},
        bundle={"bundle_id": "umeb-v1-" + "b" * 20, "finalized_at": "2026-09-15T21:31:00+08:00",
                "operation_evidence_entries": entries, "artifact_inventory": inventory},
        artifact_root="unused", calculated_at="2026-09-15T21:31:00+08:00",
        evidence_artifacts=artifacts,
    )


@pytest.mark.parametrize("request_version", [
    "unified_market_evidence_request.v1", "unified_market_evidence_request.v2",
])
def test_a06_e01_f01_f02_result_v2_schema_and_citation_graph(request_version):
    result = build_result(_projection_inputs(request_version),
                          output_schema_version="unified_market_evidence_result.v2")
    schema = json.loads((ROOT / "schemas/unified_market_evidence_result.v2.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft7Validator(schema).iter_errors(result))
    assert result["request_summary"]["request_schema_version"] == request_version
    target = result["targets"][0]
    assert target["canonical_identity"]["isin"] == "TW0002330008"
    assert set(target["evidence"]) == {"material_disclosures", "monthly_revenue"}
    resolved = {citation["citation_id"] for citation in target["citations"]}
    emitted = set(target["evidence"]["material_disclosures"]["citation_ids"])
    emitted.update(target["evidence"]["monthly_revenue"]["citation_ids"])
    assert emitted == resolved
    assert result["result_id"].startswith("umeresult-v2-")
    assert result["audit_reference"]["audit_package_id"].startswith("umeap-v2-")


def test_e02_optional_research_failure_is_partial_coverage():
    inputs = _projection_inputs()
    inputs.request["data_needs"][0]["priority"] = "optional"
    inputs.evidence_artifacts["evidence/g1.json"]["status"] = "source_failed"
    inputs.evidence_artifacts["evidence/g1.json"]["items"] = []
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v2")
    assert result["status"] == "success_with_partial_coverage"
    assert result["targets"][0]["evidence"]["monthly_revenue"]["status"] == "available"


def test_e03_required_research_failure_is_partially_failed():
    inputs = _projection_inputs()
    inputs.evidence_artifacts["evidence/g1.json"]["status"] = "binding_failed"
    inputs.evidence_artifacts["evidence/g1.json"]["items"] = []
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v2")
    assert result["status"] == "partially_failed"
    assert result["partial_failures"][0]["data_need"] == "material_disclosures"


def test_e04_all_required_executable_evidence_failed():
    target = TargetProjection(resolution=ResolutionProjection(status="resolved"))
    failure = PartialFailureProjection(target_index=0, data_need="material_disclosures",
                                       reason="required_evidence_missing", reason_code="required_evidence_missing")
    assert _compute_result_status([target], [failure]) == "failed"


def test_e05_multi_target_failure_is_isolated_and_partial():
    successful = TargetProjection(resolution=ResolutionProjection(status="resolved"),
                                  coverage_provided_needs=["monthly_revenue"])
    failed = TargetProjection(resolution=ResolutionProjection(status="resolved"),
                              coverage_missing_needs=["material_disclosures"])
    failure = PartialFailureProjection(target_index=1, data_need="material_disclosures",
                                       reason="required_evidence_missing", reason_code="required_evidence_missing")
    assert successful.coverage_provided_needs == ["monthly_revenue"]
    assert failed.coverage_provided_needs == []
    assert _compute_result_status([successful, failed], [failure]) == "partially_failed"


def test_same_operation_multi_target_research_artifacts_are_exactly_isolated():
    inputs = _projection_inputs()
    second_identity = {
        "canonical_target_id": "TWSE:2317", "isin": "TW0002317005", "market": "TWSE",
        "security_code": "2317", "security_name_zh": "鴻海", "security_name_en": "Hon Hai",
        "instrument_family": "company_share", "instrument_type": "common_share",
    }
    inputs.request["targets"].append({"input": "2317"})
    inputs.f3_validation["target_results"].append({
        "target_index": 1, "original_input": "2317", "resolution_status": "resolved",
        "canonical_identity": second_identity,
    })
    inputs.request["data_needs"] = [inputs.request["data_needs"][0]]
    inputs.plan["operations"] = [{
        "operation_id": "op-shared", "capability_id": "material_disclosures",
        "executor_id": "phase_g_official_research_executor", "market": "TWSE",
        "canonical_target_ids": ["TWSE:2330", "TWSE:2317"],
    }]
    base = inputs.evidence_artifacts["evidence/g1.json"]
    first = {**base, "schema_version": "phase_g_material_disclosure_operation_evidence.v1",
             "target": {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}}
    second = {**base, "schema_version": "phase_g_material_disclosure_operation_evidence.v1",
              "target": {"canonical_target_id": "TWSE:2317", "market": "TWSE", "security_code": "2317"},
              "items": [{**base["items"][0], "subject": "2317-only"}]}
    inputs.evidence_artifacts = {"evidence/2330.json": first, "evidence/2317.json": second}
    artifacts = [
        {"relative_path": path, "sha256": digit * 64,
         "schema_version": "phase_g_material_disclosure_operation_evidence.v1"}
        for path, digit in (("evidence/2330.json", "1"), ("evidence/2317.json", "2"))
    ]
    inputs.bundle["operation_evidence_entries"] = [{
        "operation_id": "op-shared", "status": "succeeded", "artifacts": artifacts,
    }]
    inputs.bundle["artifact_inventory"] = [
        {**artifact, "evidence_contract": artifact["schema_version"], "byte_size": 1}
        for artifact in artifacts
    ]

    lineage = build_lineage_map(inputs)
    assert list(lineage.bindings["TWSE:2330"]["material_disclosures"].artifact_objects) == ["evidence/2330.json"]
    assert list(lineage.bindings["TWSE:2317"]["material_disclosures"].artifact_objects) == ["evidence/2317.json"]
    citations = build_citation_index(lineage, inputs.bundle, "unified_market_evidence_result.v2")
    first_ids = citations.target_need_citations["TWSE:2330::material_disclosures"]
    second_ids = citations.target_need_citations["TWSE:2317::material_disclosures"]
    assert first_ids and second_ids and set(first_ids).isdisjoint(second_ids)
    audit_targets = {entry.citation_id: entry.canonical_target_id for entry in citations.audit_entries}
    assert audit_targets[first_ids[0]] == "TWSE:2330"
    assert audit_targets[second_ids[0]] == "TWSE:2317"


def test_v1_citation_source_family_remains_legacy_executor_identity():
    inputs = _projection_inputs()
    lineage = build_lineage_map(inputs)
    citations = build_citation_index(lineage, inputs.bundle)
    assert {citation.source_family for citation in citations.all_citations.values()} == {
        "phase_g_official_research_executor"
    }
    assert all(citation.source_report_date is None for citation in citations.all_citations.values())
