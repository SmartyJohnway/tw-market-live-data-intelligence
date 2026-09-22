"""H-IMP-6: deterministic, zero-network Result/Audit V3 projection checks."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil

import pytest
from jsonschema import Draft202012Validator

from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.artifact_loader import _load_phase_h_source_attempts, load_projection_inputs
from scripts.m8r_05b_03.canonical import sha256_json
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


def _attempt_metadata(source: dict, *, coverage_result: str, outcome: str, citation_ids: list[str], failure_code: str | None = None,
                      authority_marker: str | None = None) -> dict:
    value = {
        "source_family": source["source_family"],
        "source_contract_id": source["source_contract_id"],
        "source_role": source["source_role"],
        "activation_state": source["activation_state"],
        "license_authority": source["license_authority"],
        "provider_availability": "not_required",
        "coverage_result": coverage_result,
        "outcome": outcome,
        "failure_code": failure_code,
        "citation_ids": citation_ids,
    }
    if authority_marker is not None:
        value["authority_marker"] = authority_marker
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
    phase_h_source_attempts: dict[str, list[dict]] = {}
    for relative_path, artifact in artifacts.items():
        if artifact["schema_version"] == "trading_status_context_evidence.v1":
            phase_h_source_attempts[relative_path] = [_attempt_metadata(
                artifact["source"], coverage_result=artifact["status"], outcome="succeeded", citation_ids=artifact["citation_ids"],
            )]
        elif artifact["schema_version"] == "corporate_action_context_evidence.v1":
            phase_h_source_attempts[relative_path] = [_attempt_metadata(
                source, coverage_result=artifact["status"], outcome="succeeded", citation_ids=artifact["citation_ids"],
            ) for source in artifact["sources"]]
        elif artifact["schema_version"] == "recent_performance_evidence.v1":
            governed_end = artifact["governed_end_observation"]
            phase_h_source_attempts[relative_path] = [_attempt_metadata(
                {
                    "source_family": governed_end["source_family"],
                    "source_contract_id": governed_end["source_contract_id"],
                    "source_role": "research_only", "activation_state": "inactive", "license_authority": None,
                },
                coverage_result=artifact["coverage_status"], outcome="succeeded", citation_ids=artifact["citation_ids"],
                authority_marker=FIXTURE_KIND,
            )]
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
        phase_h_source_attempts=phase_h_source_attempts,
    )


def _build_package(inputs: ProjectionInputs) -> tuple[dict, dict]:
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    citations = build_citation_index(build_lineage_map(inputs), inputs.bundle, result["schema_version"])
    audit = build_audit_package(result, inputs, citations,
        "ai_context/unified_market_evidence_result.v3.json",
        output_schema_version="unified_market_evidence_audit_package.v3")
    return result, audit


def _add_legacy_data_need(inputs: ProjectionInputs, data_need: str, priority: str = "required") -> None:
    inputs.request["data_needs"].append({"type": data_need, "priority": priority, "parameters": {}})


def _add_second_target(inputs: ProjectionInputs) -> None:
    """Add a controlled second target with distinct typed artifacts and citations."""
    identity = {
        "canonical_target_id": "TWSE:2317", "isin": "TW0002317008", "market": "TWSE",
        "security_code": "2317", "security_name_zh": "鴻海", "security_name_en": "Hon Hai",
        "instrument_family": "company_share", "instrument_type": "common_share",
    }
    inputs.request["targets"].append({
        "input": "2317", "market_hint": "TWSE", "resolution_requirement": "exact",
        "client_target_reference": "fixture-2317",
    })
    inputs.f3_validation["target_results"].append({
        "target_index": 1, "original_input": "2317", "resolution_status": "resolved",
        "canonical_identity": identity,
    })
    type_paths = (
        ("trading_status_context", "op-h1-2317", "evidence/phase_h/h1/TWSE_2317.json"),
        ("corporate_action_context", "op-h2-2317", "evidence/phase_h/h2/TWSE_2317.json"),
        ("recent_performance", "op-h3-2317", "evidence/phase_h/h3/TWSE_2317.json"),
    )
    for need, operation_id, new_path in type_paths:
        source_path = next(path for path, artifact in inputs.evidence_artifacts.items()
                           if artifact.get("schema_version") == {
                               "trading_status_context": "trading_status_context_evidence.v1",
                               "corporate_action_context": "corporate_action_context_evidence.v1",
                               "recent_performance": "recent_performance_evidence.v1",
                           }[need])
        citation_id = _build_citation_id(operation_id, new_path)
        artifact = _replace_citations(deepcopy(inputs.evidence_artifacts[source_path]), citation_id)
        artifact["target"] = {
            "canonical_target_id": identity["canonical_target_id"], "market": identity["market"],
            "security_code": identity["security_code"],
        }
        inputs.evidence_artifacts[new_path] = artifact
        reference = {"relative_path": new_path, "sha256": "a" * 64,
                     "schema_version": artifact["schema_version"], "byte_size": 1}
        inputs.bundle["artifact_inventory"].append({**reference, "evidence_contract": artifact["schema_version"]})
        inputs.plan["operations"].append({
            "operation_id": operation_id, "capability_id": need,
            "executor_id": "phase_h_fixture_projection_executor", "market": "TWSE",
            "canonical_target_ids": ["TWSE:2317"], "expected_evidence_contract": artifact["schema_version"],
        })
        inputs.bundle["operation_evidence_entries"].append({
            "operation_id": operation_id, "status": "succeeded", "result_item_count": 1,
            "artifacts": [reference], "warnings": [],
        })
        if need == "recent_performance":
            governed_end = artifact["governed_end_observation"]
            inputs.phase_h_source_attempts[new_path] = [_attempt_metadata(
                {"source_family": governed_end["source_family"], "source_contract_id": governed_end["source_contract_id"],
                 "source_role": "research_only", "activation_state": "inactive", "license_authority": None},
                coverage_result=artifact["coverage_status"], outcome="succeeded", citation_ids=artifact["citation_ids"], authority_marker=FIXTURE_KIND,
            )]
        else:
            sources = artifact["sources"] if "sources" in artifact else [artifact["source"]]
            inputs.phase_h_source_attempts[new_path] = [_attempt_metadata(
                source, coverage_result=artifact["status"], outcome="succeeded", citation_ids=artifact["citation_ids"],
            ) for source in sources]
    h4_source_path = next(path for path, artifact in inputs.evidence_artifacts.items()
                          if artifact.get("schema_version") == "discontinuity_safety_evidence.v1")
    h4_path = "evidence/phase_h/h4/TWSE_2317.json"
    h4 = _replace_citations(deepcopy(inputs.evidence_artifacts[h4_source_path]), _build_citation_id("op-h2-2317", "evidence/phase_h/h2/TWSE_2317.json"))
    h4["target"] = {
        "canonical_target_id": identity["canonical_target_id"], "market": identity["market"],
        "security_code": identity["security_code"],
    }
    inputs.evidence_artifacts[h4_path] = h4
    inputs.bundle["artifact_inventory"].append({
        "relative_path": h4_path, "sha256": "b" * 64, "schema_version": h4["schema_version"],
        "byte_size": 1, "evidence_contract": h4["schema_version"],
    })
    inputs.bundle["total_item_count"] = len(inputs.bundle["artifact_inventory"])


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


@pytest.mark.parametrize("data_need", ["current_observation", "official_eod_reference", "material_disclosures"])
def test_v3_required_inherited_need_without_binding_is_truthful_missing(data_need: str):
    inputs = _inputs()
    _add_legacy_data_need(inputs, data_need)
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    errors = list(Draft202012Validator(json.loads(
        (ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8")
    )).iter_errors(result))
    assert not errors
    assert data_need in result["targets"][0]["coverage"]["missing_needs"]
    assert any(item["reason"] == f"required_evidence_missing:{data_need}" for item in result["partial_failures"])
    assert result["status"] != "full_success"


def test_v3_optional_inherited_need_without_binding_is_truthful_missing():
    inputs = _inputs()
    _add_legacy_data_need(inputs, "session_status", priority="optional")
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    assert "session_status" in result["targets"][0]["coverage"]["missing_needs"]
    assert result["status"] != "full_success"


def test_v3_projects_successful_inherited_v2_compatible_evidence():
    inputs = _inputs()
    _add_legacy_data_need(inputs, "current_observation")
    path = "evidence/legacy/current/TWSE_2330.json"
    citation_id = _build_citation_id("op-current", path)
    artifact = {"schema_version": "m8r_06_03_operation_evidence.v1", "items": [{"price": 100, "timing_class": "delayed"}]}
    reference = {"relative_path": path, "sha256": "c" * 64, "schema_version": artifact["schema_version"], "byte_size": 1}
    inputs.evidence_artifacts[path] = artifact
    inputs.bundle["artifact_inventory"].append({**reference, "evidence_contract": artifact["schema_version"]})
    inputs.plan["operations"].append({"operation_id": "op-current", "capability_id": "current_observation",
        "executor_id": "legacy_fixture", "market": "TWSE", "canonical_target_ids": ["TWSE:2330"]})
    inputs.bundle["operation_evidence_entries"].append({"operation_id": "op-current", "status": "succeeded",
        "result_item_count": 1, "artifacts": [reference], "warnings": []})
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    assert result["targets"][0]["evidence"]["current_observation"]["status"] == "available"
    assert citation_id in {item["citation_id"] for item in result["targets"][0]["citations"]}


def test_v3_multi_target_typed_evidence_and_citations_are_isolated_and_deterministic():
    inputs = _inputs()
    _add_second_target(inputs)
    result, audit = _build_package(inputs)
    first, second = result["targets"]
    assert first["resolution"]["canonical_target_id"] == "TWSE:2330"
    assert second["resolution"]["canonical_target_id"] == "TWSE:2317"
    assert first["evidence"]["trading_status_context"]["target"]["canonical_target_id"] == "TWSE:2330"
    assert second["evidence"]["trading_status_context"]["target"]["canonical_target_id"] == "TWSE:2317"
    assert not {item["citation_id"] for item in first["citations"]} & {item["citation_id"] for item in second["citations"]}
    assert {item["canonical_target_id"] for item in audit["phase_h_governance"]["source_attempts"]} == {"TWSE:2330", "TWSE:2317"}
    assert {item["canonical_target_id"] for item in audit["phase_h_governance"]["h4_derivations"]} == {"TWSE:2330", "TWSE:2317"}
    assert audit["result_id"] == result["result_id"]
    assert audit["result_hash"] == result["result_hash"]
    reversed_inputs = deepcopy(inputs)
    reversed_inputs.evidence_artifacts = dict(reversed(list(reversed_inputs.evidence_artifacts.items())))
    assert _build_package(reversed_inputs) == (result, audit)


def test_wrong_target_typed_artifact_cannot_project_or_lend_citations():
    inputs = _inputs()
    artifact = deepcopy(inputs.evidence_artifacts["evidence/phase_h/h1/TWSE_2330.json"])
    artifact["target"]["canonical_target_id"] = "TWSE:2317"
    path = "evidence/phase_h/h1/wrong-target.json"
    inputs.evidence_artifacts[path] = artifact
    reference = {"relative_path": path, "sha256": "d" * 64, "schema_version": artifact["schema_version"], "byte_size": 1}
    inputs.bundle["artifact_inventory"].append({**reference, "evidence_contract": artifact["schema_version"]})
    inputs.bundle["operation_evidence_entries"][0]["artifacts"].append(reference)
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    assert result["targets"][0]["evidence"]["trading_status_context"]["target"]["canonical_target_id"] == "TWSE:2330"


def test_duplicate_same_target_typed_artifact_fails_closed():
    inputs = _inputs()
    path = "evidence/phase_h/h1/duplicate.json"
    artifact = deepcopy(inputs.evidence_artifacts["evidence/phase_h/h1/TWSE_2330.json"])
    inputs.evidence_artifacts[path] = artifact
    reference = {"relative_path": path, "sha256": "e" * 64, "schema_version": artifact["schema_version"], "byte_size": 1}
    inputs.bundle["artifact_inventory"].append({**reference, "evidence_contract": artifact["schema_version"]})
    inputs.bundle["operation_evidence_entries"][0]["artifacts"].append(reference)
    with pytest.raises(ProjectionError, match="duplicate_phase_h_typed_artifact"):
        build_result(inputs, output_schema_version="unified_market_evidence_result.v3")


def test_h2_audit_uses_each_source_attempt_not_aggregate_status():
    inputs = _inputs()
    path = "evidence/phase_h/h2/TWSE_2330.json"
    artifact = inputs.evidence_artifacts[path]
    second_source = dict(artifact["sources"][0], source_family="H2_TEST_SOURCE_B", source_contract_id="h2-test-b")
    artifact["sources"].append(second_source)
    artifact["status"] = "source_failed"
    artifact["coverage"].update({
        "status": "source_failed", "retrieval_succeeded": False,
        "source_contract_validated": False, "failed_source_families": ["H2_TEST_SOURCE_B"],
    })
    artifact["events"] = []
    first_source = artifact["sources"][0]
    inputs.phase_h_source_attempts[path] = [
        _attempt_metadata(first_source, coverage_result="available", outcome="succeeded", citation_ids=artifact["citation_ids"]),
        _attempt_metadata(second_source, coverage_result="source_failed", outcome="failed", citation_ids=artifact["citation_ids"], failure_code="source_failed:test"),
    ]
    _, audit = _build_package(inputs)
    h2_attempts = [item for item in audit["phase_h_governance"]["source_attempts"] if item["source_contract_id"] in {first_source["source_contract_id"], "h2-test-b"}]
    assert {(item["source_contract_id"], item["outcome"], item["failure_code"]) for item in h2_attempts} == {
        (first_source["source_contract_id"], "succeeded", None), ("h2-test-b", "failed", "source_failed:test"),
    }


def test_audit_preserves_supplied_source_role_activation_and_provider_independently():
    inputs = _inputs()
    path = "evidence/phase_h/h2/TWSE_2330.json"
    artifact = inputs.evidence_artifacts[path]
    optional_source = dict(artifact["sources"][0], source_family="H2_OPTIONAL", source_contract_id="h2-optional",
                           source_role="optional_licensed_provider", activation_state="inactive")
    artifact["sources"].append(optional_source)
    inputs.phase_h_source_attempts[path] = [
        _attempt_metadata(artifact["sources"][0], coverage_result="available", outcome="succeeded", citation_ids=artifact["citation_ids"]),
        {**_attempt_metadata(optional_source, coverage_result="available", outcome="succeeded", citation_ids=artifact["citation_ids"]),
         "provider_availability": "available"},
    ]
    _, audit = _build_package(inputs)
    attempts = {item["source_contract_id"]: item for item in audit["phase_h_governance"]["source_attempts"]}
    assert attempts[artifact["sources"][0]["source_contract_id"]]["source_role"] == "default_candidate"
    assert attempts[artifact["sources"][0]["source_contract_id"]]["activation_state"] == "eligible"
    assert attempts["h2-optional"]["source_role"] == "optional_licensed_provider"
    assert attempts["h2-optional"]["activation_state"] == "inactive"
    assert attempts["h2-optional"]["provider_availability"] == "available"


def test_audit_never_infers_provider_availability_from_source_role():
    inputs = _inputs()
    path = "evidence/phase_h/h1/TWSE_2330.json"
    del inputs.phase_h_source_attempts[path][0]["provider_availability"]
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    citations = build_citation_index(build_lineage_map(inputs), inputs.bundle, result["schema_version"])
    with pytest.raises(ProjectionError, match="phase_h_source_governance_unresolved"):
        build_audit_package(result, inputs, citations, "ai_context/unified_market_evidence_result.v3.json",
                            output_schema_version="unified_market_evidence_audit_package.v3")


def test_h3_audit_requires_explicit_test_only_governance_metadata():
    inputs = _inputs()
    path = "evidence/phase_h/h3/TWSE_2330.json"
    del inputs.phase_h_source_attempts[path]
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    citations = build_citation_index(build_lineage_map(inputs), inputs.bundle, result["schema_version"])
    with pytest.raises(ProjectionError, match="phase_h_source_governance_unresolved"):
        build_audit_package(result, inputs, citations, "ai_context/unified_market_evidence_result.v3.json",
                            output_schema_version="unified_market_evidence_audit_package.v3")


def test_time_lineage_remains_distinct_in_typed_result_and_audit():
    inputs = _inputs()
    h1 = inputs.evidence_artifacts["evidence/phase_h/h1/TWSE_2330.json"]
    h1["items"][0].update({"published_at": "2026-09-20T01:02:03Z", "effective_from": "2026-09-20", "effective_to": "2026-09-25"})
    h2 = inputs.evidence_artifacts["evidence/phase_h/h2/TWSE_2330.json"]
    h2["events"][0]["effective_date"] = "2026-09-21"
    result, audit = _build_package(inputs)
    evidence = result["targets"][0]["evidence"]
    assert evidence["trading_status_context"]["items"][0]["published_at"] == "2026-09-20T01:02:03Z"
    assert evidence["trading_status_context"]["items"][0]["effective_from"] == "2026-09-20"
    assert evidence["corporate_action_context"]["events"][0]["effective_date"] == "2026-09-21"
    assert evidence["recent_performance"]["baselines"][0]["start_observation_date"] != evidence["recent_performance"]["baselines"][0]["end_observation_date"]
    assert audit["phase_h_governance"]["h4_derivations"][0]["comparison_window"] == {
        "start_observation_date": evidence["discontinuity_safety"]["comparison_window"]["start_observation_date"],
        "end_observation_date": evidence["discontinuity_safety"]["comparison_window"]["end_observation_date"],
    }


def test_package_bound_sidecars_supply_governance_without_runtime_injection():
    inputs = _inputs()
    sidecars = {}
    for path, attempts in inputs.phase_h_source_attempts.items():
        artifact = inputs.evidence_artifacts[path]
        capability = {
            "trading_status_context_evidence.v1": "trading_status_context",
            "corporate_action_context_evidence.v1": "corporate_action_context",
            "recent_performance_evidence.v1": "recent_performance",
        }[artifact["schema_version"]]
        sidecars[f"governance/{capability}-{path.rsplit('/', 1)[-1]}.json"] = {
            "schema_version": "phase_h_source_attempt_governance.v1",
            "evidence_artifact_reference": path,
            "canonical_target_id": artifact["target"]["canonical_target_id"],
            "capability_id": capability,
            "attempts": [{key: value for key, value in attempt.items() if key != "authority_marker"} for attempt in attempts],
        }
    loaded = _load_phase_h_source_attempts({**inputs.evidence_artifacts, **sidecars}, plan=inputs.plan, bundle=inputs.bundle)
    assert loaded == {path: [{key: value for key, value in attempt.items() if key != "authority_marker"}
                             for attempt in attempts] for path, attempts in inputs.phase_h_source_attempts.items()}


def test_real_loader_populates_sidecar_governance_from_verified_package(tmp_path: Path):
    """Filesystem-backed loader proof; no post-load governance injection."""
    fixture_root = ROOT / "tests/fixtures/m8r_05c"
    root = tmp_path / "artifact_root"
    shutil.copytree(fixture_root / "artifact_root", root)
    names = ("request_single_target", "f3_validation", "plan_single_target", "authorization", "consumption_binding", "claim", "receipt", "bundle")
    paths = {}
    for name in names:
        source = fixture_root / f"{name}.json"
        destination = tmp_path / source.name
        shutil.copy2(source, destination)
        paths[name] = destination
    bundle = json.loads(paths["bundle"].read_text(encoding="utf-8"))
    for entry in bundle["artifact_inventory"]:
        artifact_path = root / entry["relative_path"]
        entry["sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        entry["byte_size"] = artifact_path.stat().st_size
    inventory_by_path = {entry["relative_path"]: entry for entry in bundle["artifact_inventory"]}
    for operation in bundle["operation_evidence_entries"]:
        for reference in operation["artifacts"]:
            inventory = inventory_by_path[reference["relative_path"]]
            reference["sha256"] = inventory["sha256"]
            reference["byte_size"] = inventory["byte_size"]
    inputs = _inputs()
    for path, attempts in inputs.phase_h_source_attempts.items():
        artifact = inputs.evidence_artifacts[path]
        full_path = root / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
        capability = {"trading_status_context_evidence.v1": "trading_status_context",
                      "corporate_action_context_evidence.v1": "corporate_action_context",
                      "recent_performance_evidence.v1": "recent_performance"}[artifact["schema_version"]]
        sidecar_path = f"governance/{capability}.json"
        sidecar = {"schema_version": "phase_h_source_attempt_governance.v1", "evidence_artifact_reference": path,
                   "canonical_target_id": artifact["target"]["canonical_target_id"], "capability_id": capability,
                   "attempts": [{key: value for key, value in attempt.items() if key != "authority_marker"} for attempt in attempts]}
        sidecar_full_path = root / sidecar_path
        sidecar_full_path.parent.mkdir(parents=True, exist_ok=True)
        sidecar_full_path.write_text(json.dumps(sidecar, ensure_ascii=False), encoding="utf-8")
        for rel_path, payload, contract in ((path, artifact, artifact["schema_version"]), (sidecar_path, sidecar, sidecar["schema_version"])):
            file_path = root / rel_path
            bundle["artifact_inventory"].append({"relative_path": rel_path,
                "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(), "schema_version": payload["schema_version"],
                "byte_size": file_path.stat().st_size, "item_count": 1, "evidence_contract": contract})
    bundle["total_item_count"] = len(bundle["artifact_inventory"])
    body = {key: value for key, value in bundle.items() if key not in {"schema_version", "bundle_id", "bundle_hash"}}
    bundle["bundle_hash"] = sha256_json(body)
    paths["bundle"].write_text(json.dumps(bundle), encoding="utf-8")
    def load_verified_package():
        return load_projection_inputs(request_path=str(paths["request_single_target"]), f3_validation_path=str(paths["f3_validation"]),
            plan_path=str(paths["plan_single_target"]), authorization_path=str(paths["authorization"]),
            consumption_binding_path=str(paths["consumption_binding"]), claim_path=str(paths["claim"]),
            receipt_path=str(paths["receipt"]), bundle_path=str(paths["bundle"]), artifact_root=str(root),
            calculated_at="2026-09-22T00:00:00Z")

    # Inventory and a hash alone are insufficient: these historical operations
    # do not govern the newly added Phase H typed artifacts.
    with pytest.raises(ProjectionError, match="phase_h_source_governance_operation_unresolved"):
        load_verified_package()
    sidecar_file = root / "governance/trading_status_context.json"
    sidecar_file.write_bytes(sidecar_file.read_bytes() + b"\n")
    with pytest.raises(ProjectionError, match="artifact_hash_mismatch"):
        load_verified_package()


@pytest.mark.parametrize("tamper", ["missing", "wrong_target", "wrong_capability", "duplicate"])
def test_package_bound_sidecar_reference_tampering_fails_closed(tamper: str):
    inputs = _inputs()
    path = "evidence/phase_h/h1/TWSE_2330.json"
    artifact = inputs.evidence_artifacts[path]
    sidecar = {
        "schema_version": "phase_h_source_attempt_governance.v1", "evidence_artifact_reference": path,
        "canonical_target_id": artifact["target"]["canonical_target_id"], "capability_id": "trading_status_context",
        "attempts": inputs.phase_h_source_attempts[path],
    }
    evidence = {path: artifact, "governance/h1.json": sidecar}
    if tamper == "missing":
        del evidence[path]
    elif tamper == "wrong_target":
        sidecar["canonical_target_id"] = "TWSE:2317"
    elif tamper == "wrong_capability":
        sidecar["capability_id"] = "recent_performance"
    else:
        evidence["governance/h1-duplicate.json"] = deepcopy(sidecar)
    with pytest.raises(ProjectionError):
        _load_phase_h_source_attempts(evidence, plan=inputs.plan, bundle=inputs.bundle)


def test_execution_lineage_is_required_for_package_bound_governance():
    inputs = _inputs()
    path = "evidence/phase_h/h1/TWSE_2330.json"
    artifact = inputs.evidence_artifacts[path]
    sidecar = {"schema_version": "phase_h_source_attempt_governance.v1", "evidence_artifact_reference": path,
               "canonical_target_id": artifact["target"]["canonical_target_id"], "capability_id": "trading_status_context",
               "attempts": inputs.phase_h_source_attempts[path]}
    evidence = {path: artifact, "governance/h1.json": sidecar}
    assert _load_phase_h_source_attempts(evidence, plan=inputs.plan, bundle=inputs.bundle)[path]
    inputs.bundle["operation_evidence_entries"] = [entry for entry in inputs.bundle["operation_evidence_entries"]
                                                    if entry["operation_id"] != "op-h1"]
    with pytest.raises(ProjectionError, match="phase_h_source_governance_operation_unresolved"):
        _load_phase_h_source_attempts(evidence, plan=inputs.plan, bundle=inputs.bundle)


@pytest.mark.parametrize("coverage_result,outcome,failure_code", [
    ("insufficient", "succeeded", None), ("unavailable", "succeeded", None),
    ("unavailable", "not_attempted", None), ("source_failed", "failed", "source_failed:test"),
    ("unsupported", "not_attempted", None), ("not_applicable", "not_attempted", None),
])
def test_h3_attempt_coverage_and_outcome_are_explicit(coverage_result, outcome, failure_code):
    inputs = _inputs()
    path = "evidence/phase_h/h3/TWSE_2330.json"
    inputs.phase_h_source_attempts[path][0].update({"coverage_result": coverage_result, "outcome": outcome,
                                                     "failure_code": failure_code})
    _, audit = _build_package(inputs)
    attempt = next(item for item in audit["phase_h_governance"]["source_attempts"]
                   if item["source_contract_id"] == inputs.phase_h_source_attempts[path][0]["source_contract_id"])
    assert (attempt["coverage_result"], attempt["outcome"], attempt["failure_code"]) == (coverage_result, outcome, failure_code)
