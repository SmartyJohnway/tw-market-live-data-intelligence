"""H-IMP-6: deterministic, zero-network Result/Audit V3 projection checks."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.canonical import build_audit_package_id_v3, build_result_id_v3
from scripts.m8r_05c.citation_builder import _build_citation_id, build_citation_index
from scripts.m8r_05c.errors import ProjectionError
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.markdown_renderer import render_result_markdown
from scripts.m8r_05c.models import ProjectionInputs
from scripts.m8r_05c.result_builder import build_result
from server.services.unified_mode_c import ModeCError, _OUTPUT_PATHS, build_mode_c_result_package

ROOT = Path(__file__).resolve().parents[2]
# These controlled contract examples exercise a dormant projection only; they
# are not source-acquisition evidence.
FIXTURE_KIND = "NON_AUTHORITATIVE_TEST_ONLY"
EXAMPLES = json.loads((ROOT / "tests/fixtures/phase_h_contract_v3/contract_examples.json").read_text(encoding="utf-8"))


def _replace_citations(value: object, citation_id: str) -> object:
    if isinstance(value, dict):
        return {key: ([citation_id] if key == "citation_ids" else _replace_citations(item, citation_id))
                for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_citations(item, citation_id) for item in value]
    return value


def _inputs(*, include_h1: bool = True, include_h2: bool = True, include_h3: bool = True) -> ProjectionInputs:
    identity = {
        "canonical_target_id": "TWSE:2330", "isin": "TW0002330008", "market": "TWSE",
        "security_code": "2330", "security_name_zh": "台積電", "security_name_en": "TSMC",
        "instrument_family": "company_share", "instrument_type": "common_share",
    }
    specifications = [
        ("trading_status_context", "op-h1", "evidence/phase_h/h1/TWSE_2330.json", "h1_attention_available", include_h1),
        ("corporate_action_context", "op-h2", "evidence/phase_h/h2/TWSE_2330.json", "h2_preannouncement_and_final", include_h2),
        ("recent_performance", "op-h3", "evidence/phase_h/h3/TWSE_2330.json", "h3_5d", include_h3),
    ]
    artifacts, inventory, operations, entries = {}, [], [], []
    for need, operation_id, path, example, enabled in specifications:
        if not enabled:
            continue
        citation_id = _build_citation_id(operation_id, path)
        artifact = _replace_citations(deepcopy(EXAMPLES[example]), citation_id)
        artifacts[path] = artifact
        reference = {"relative_path": path, "sha256": str(len(inventory) + 1) * 64,
                     "schema_version": artifact["schema_version"], "byte_size": 1}
        inventory.append({**reference, "evidence_contract": artifact["schema_version"]})
        operations.append({"operation_id": operation_id, "capability_id": need,
                           "executor_id": "phase_h_fixture_projection_executor", "market": "TWSE",
                           "canonical_target_ids": ["TWSE:2330"],
                           "expected_evidence_contract": artifact["schema_version"]})
        entries.append({"operation_id": operation_id, "status": "succeeded", "result_item_count": 1,
                        "artifacts": [reference], "warnings": []})
    if include_h2 and include_h3:
        h4_path = "evidence/phase_h/h4/TWSE_2330.json"
        h4 = _replace_citations(deepcopy(EXAMPLES["h4_coverage_incomplete"]), _build_citation_id("op-h2", specifications[1][2]))
        artifacts[h4_path] = h4
        inventory.append({"relative_path": h4_path, "sha256": "f" * 64,
                          "schema_version": h4["schema_version"], "byte_size": 1,
                          "evidence_contract": h4["schema_version"]})
    request = deepcopy(EXAMPLES["request_v3"])
    request["execution_mode"] = "preview"
    return ProjectionInputs(
        request=request,
        f3_validation={"target_results": [{"target_index": 0, "original_input": "2330",
            "resolution_status": "resolved", "canonical_identity": identity}]},
        plan={"plan_id": "umeop-v1-" + "1" * 20, "plan_hash": "0" * 64,
              "schema_version": "unified_market_evidence_orchestration_plan.v1", "plan_status": "planned",
              "input_bindings": {"f3_validation_output_hash": "0" * 64}, "operations": operations},
        authorization={"authorization_id": "umea-v1-" + "2" * 20, "authorization_hash": "0" * 64,
                       "schema_version": "unified_market_evidence_execution_authorization.v1"},
        consumption_binding={"consumption_binding_id": "umecb-v1-" + "3" * 20,
                             "consumption_binding_hash": "0" * 64},
        claim={"claim_id": "umecl-v1-" + "4" * 20,
               "schema_version": "unified_market_evidence_consumption_record.v1"},
        receipt={"execution_receipt_id": "umerec-v1-" + "5" * 20, "execution_receipt_hash": "0" * 64,
                 "schema_version": "unified_market_evidence_execution_receipt.v1", "overall_status": "partial_success",
                 "total_operations": len(operations), "succeeded_operations": len(operations), "failed_operations": 0,
                 "finalized_at": "2026-09-22T00:00:00Z"},
        bundle={"bundle_id": "umeb-v1-" + "6" * 20, "bundle_hash": "0" * 64,
                "schema_version": "unified_market_evidence_bundle.v1", "overall_status": "partial_success",
                "total_item_count": len(inventory), "finalized_at": "2026-09-22T00:00:00Z",
                "operation_evidence_entries": entries, "artifact_inventory": inventory},
        artifact_root="NON_AUTHORITATIVE_TEST_ONLY", calculated_at="2026-09-22T00:00:00Z",
        calculated_at_source="fixture", evidence_artifacts=artifacts,
    )


def _build_package(inputs: ProjectionInputs) -> tuple[dict, dict]:
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    citations = build_citation_index(build_lineage_map(inputs), inputs.bundle, result["schema_version"])
    audit = build_audit_package(result, inputs, citations,
        "ai_context/unified_market_evidence_result.v3.json",
        output_schema_version="unified_market_evidence_audit_package.v3")
    return result, audit


def test_h0h_out_001_to_004_and_time_001_v3_typed_projection_and_handoff():
    inputs = _inputs()
    result, audit = _build_package(inputs)
    result_schema = json.loads((ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8"))
    audit_schema = json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(result_schema).iter_errors(result))
    assert not list(Draft202012Validator(audit_schema).iter_errors(audit))
    assert result["result_id"] == build_result_id_v3("phase-h-v3-fixture", inputs.receipt["execution_receipt_id"], inputs.bundle["bundle_id"])
    assert audit["audit_package_id"] == build_audit_package_id_v3(result["result_id"], inputs.bundle["bundle_id"])
    evidence = result["targets"][0]["evidence"]
    assert evidence["trading_status_context"]["status"] == "available"
    assert evidence["corporate_action_context"]["coverage"]["status"] == "partial"
    assert evidence["recent_performance"]["schema_version"] == "recent_performance_evidence.v1"
    assert evidence["discontinuity_safety"]["interpretation_guard"] == "CORPORATE_ACTION_COVERAGE_INCOMPLETE"
    assert len(audit["phase_h_governance"]["source_attempts"]) == 3
    assert audit["phase_h_governance"]["h4_derivations"][0]["comparison_window"] == {
        key: evidence["discontinuity_safety"]["comparison_window"][key]
        for key in ("start_observation_date", "end_observation_date")
    }
    assert result["audit_reference"]["audit_package_id"] == audit["audit_package_id"]
    assert result["result_hash"] == audit["result_hash"]
    handoff = render_result_markdown(result)
    assert "CORPORATE_ACTION_COVERAGE_INCOMPLETE" in handoff
    assert "缺失資料需求" not in handoff  # all requested typed artifacts were supplied
    lowered = handoff.lower()
    assert all(token not in lowered for token in ("buy", "sell", "hold", "bullish", "bearish", "target price", "sentiment", "目標價", "買進", "賣出", "持有", "看多", "看空"))


@pytest.mark.parametrize("missing_need", ["trading_status_context", "corporate_action_context", "recent_performance"])
def test_required_or_typed_missing_phase_h_evidence_never_becomes_full_success(missing_need: str):
    inputs = _inputs(include_h1=missing_need != "trading_status_context", include_h2=missing_need != "corporate_action_context", include_h3=missing_need != "recent_performance")
    if missing_need == "recent_performance":
        inputs.request["data_needs"][-1]["priority"] = "required"
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    assert result["status"] != "full_success"
    assert missing_need in result["targets"][0]["coverage"]["missing_needs"]
    assert missing_need not in result["targets"][0]["evidence"]


def test_phase_h_citation_lineage_mismatch_fails_closed():
    inputs = _inputs()
    inputs.evidence_artifacts["evidence/phase_h/h1/TWSE_2330.json"]["citation_ids"] = ["unbound-citation"]
    with pytest.raises(ProjectionError, match="phase_h_citation_lineage_mismatch"):
        build_result(inputs, output_schema_version="unified_market_evidence_result.v3")


@pytest.mark.parametrize("bad_path", ["/evidence/x.json", "C:/evidence/x.json", "C:\\\\evidence\\\\x.json", "\\\\server\\\\share\\\\x.json", "../x.json", "evidence/../x.json", "file://x", "https://example/x", "evidence\\\\x.json"])
def test_h0h_out_003_audit_v3_rejects_noncanonical_artifact_paths(bad_path: str):
    inputs = _inputs()
    inputs.bundle["artifact_inventory"][0]["relative_path"] = bad_path
    with pytest.raises(ProjectionError, match="audit_package_schema_invalid"):
        _build_package(inputs)


def test_v3_is_deterministic_and_does_not_promote_legacy_generic_recent_performance():
    inputs = _inputs(include_h3=False)
    first = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    second = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    assert first == second
    assert "recent_performance" not in first["targets"][0]["evidence"]


def test_mode_c_v3_output_is_explicit_and_uses_frozen_paths():
    assert FIXTURE_KIND == "NON_AUTHORITATIVE_TEST_ONLY"
    assert _OUTPUT_PATHS["unified_market_evidence_result.v3"][:3] == (
        "ai_context/unified_market_evidence_result.v3.json",
        "ai_context/unified_market_evidence_result.v3.md",
        "audit/unified_market_evidence_audit_package.v3.json",
    )
    with pytest.raises(ModeCError, match="unsupported_output_schema_version"):
        build_mode_c_result_package({"control_package_id": "unused"}, output_schema_version="v3")
