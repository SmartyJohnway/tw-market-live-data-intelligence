"""Fail-closed offline validation for the dormant I2-A2 candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
A1_CONTRACT_SHA256 = "6d535e34defb1e82947f64ceec6df5e1859888fb3550e36e6ded1b6a7573d4fb"
EXECUTOR_ID = "phase_i_i2_index_futures_context_executor"


def _read(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate() -> None:
    contract_path = ROOT / "docs/governance/phase_i/PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json"
    if hashlib.sha256(contract_path.read_bytes()).hexdigest() != A1_CONTRACT_SHA256:
        raise ValueError("i2_a1_frozen_contract_hash_changed")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if (contract.get("status"), contract.get("capability_id")) != ("FROZEN_PASS", "index_futures_context"):
        raise ValueError("i2_a1_contract_identity_invalid")

    catalog = _read("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _read("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    source = _read("docs/data_capabilities/phase_i_i2_source_authority.v1.json")
    registry = _read("config/m8r_06_03_executor_registry_metadata.json")
    cap = next(x for x in catalog["data_need_capabilities"] if x.get("capability_id") == "index_futures_context")
    route = next(x for x in routing["routes"] if x.get("capability_id") == "index_futures_context")
    if (cap.get("support_status"), cap.get("runtime_executable"), cap.get("phase_i_activation_state"), cap.get("supported_markets")) != (
        "contract_supported", False, "implementation_candidate_inactive", ["TWSE"]
    ):
        raise ValueError("i2_catalog_not_dormant")
    scope = cap.get("instrument_scope", {})
    if scope != {"instrument_families": ["company_share"], "instrument_types": ["common_share"]}:
        raise ValueError("i2_catalog_target_scope_invalid")
    if (route.get("runtime_executable"), route.get("routing_status"), route.get("selected_executor_id"), route.get("supported_markets"), route.get("batching_scope"), route.get("approval_required"), route.get("network_required")) != (
        False, "plan_only", None, ["TWSE"], "same_source", True, True
    ):
        raise ValueError("i2_routing_not_dormant")
    if route.get("candidate_executor_ids") != [EXECUTOR_ID] or len(route.get("blocking_reasons", [])) < 3:
        raise ValueError("i2_dormant_route_missing_candidate_or_blocks")
    if source.get("active_source_count") != 0 or source.get("runtime_executable") is not False or len(source.get("records", [])) != 1:
        raise ValueError("i2_source_authority_not_inactive")
    source_record = source["records"][0]
    if (source_record.get("source_id"), source_record.get("market"), source_record.get("source_family"), source_record.get("source_contract_id"),
            source_record.get("activation_state"), source_record.get("runtime_executable")) != (
        "I2-TAIFEX-DAILYMARKETREPORTFUT-OPENAPI", "TAIFEX", "TAIFEX_DAILY_MARKET_REPORT_FUT",
        "TAIFEX_DAILY_MARKET_REPORT_FUT_OPENAPI_V1", "inactive", False
    ):
        raise ValueError("i2_source_record_active")
    if any(x.get("capability_id") == "index_futures_context" for x in registry.get("executors", [])):
        raise ValueError("i2_executor_registered_in_production_metadata")

    i1_source = _read("docs/data_capabilities/phase_i_i1_source_authority.v1.json")
    i1_active = {x.get("source_id") for x in i1_source.get("records", []) if x.get("activation_state") == "active" and x.get("runtime_executable") is True}
    if i1_source.get("active_source_count") != 3 or len(i1_active) != 3:
        raise ValueError("i1_active_source_count_changed")
    if any(x.get("capability_id") in {"institutional_positioning_context", "taifex_market_state", "phase_i_i3_context"} for x in catalog.get("data_need_capabilities", [])):
        raise ValueError("i3_scope_added")
    request_v3 = _read("schemas/unified_market_evidence_request.v3.schema.json")
    request_v1 = _read("schemas/unified_market_evidence_request.v1.schema.json")
    request_v2 = _read("schemas/unified_market_evidence_request.v2.schema.json")
    if "index_futures_context" not in request_v3["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]:
        raise ValueError("i2_request_v3_need_missing")
    if any("index_futures_context" in request["properties"]["data_needs"]["items"]["properties"]["type"].get("enum", []) for request in (request_v1, request_v2)):
        raise ValueError("i2_legacy_request_scope_changed")
    result_v3 = _read("schemas/unified_market_evidence_result.v3.schema.json")
    if result_v3["properties"]["targets"]["items"]["properties"]["evidence"]["properties"].get("index_futures_context", {}).get("$ref") != "#/definitions/index_futures_context":
        raise ValueError("i2_result_v3_projection_missing")
    audit_v3 = _read("schemas/unified_market_evidence_audit_package.v3.schema.json")
    phase_i_items = audit_v3["properties"]["phase_i_evidence"]["properties"]["evidence_artifact_references"]["items"].get("oneOf", [])
    phase_i_pairs = {(alt.get("properties", {}).get("capability_id", {}).get("const"), alt.get("properties", {}).get("schema_version", {}).get("const")) for alt in phase_i_items}
    if ("index_futures_context", "index_futures_context_evidence.v1") not in phase_i_pairs:
        raise ValueError("i2_audit_phase_i_reference_missing")
    phase_h_caps = audit_v3["properties"]["phase_h_governance"]["properties"]["evidence_artifact_references"]["items"]["properties"]["capability_id"]["enum"]
    if "index_futures_context" in phase_h_caps:
        raise ValueError("i2_audit_phase_h_separation_invalid")
    if len(catalog.get("mcp_tools", [])) not in {0, 6}:
        raise ValueError("catalog_mcp_surface_invalid")
    sys.path.insert(0, str(ROOT))
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    if build_production_runtime_adapter_registry().routes_for_executor(EXECUTOR_ID):
        raise ValueError("i2_production_registry_route_exists")
    if len(build_tool_contract_snapshot().tools) != 6:
        raise ValueError("mcp_tool_count_changed")

    candidate = _read("docs/governance/phase_i/PHASE_I_I2_A2_DORMANT_OFFLINE_IMPLEMENTATION_CANDIDATE_2026-09-30.json")
    if (candidate.get("status"), candidate.get("owner_authority_reference"), candidate.get("starting_main")) != (
        "DORMANT_IMPLEMENTATION_CANDIDATE_READY_FOR_REVIEW",
        "USER_CHAT_2026-09-30_PHASE_I_I2_A2_DORMANT_OFFLINE_IMPLEMENTATION_AUTHORIZATION",
        "3d5a43f93c9aba84a3cab26fddac13dfc6b61200",
    ):
        raise ValueError("i2_candidate_governance_identity_invalid")
    repair = candidate.get("implementation_candidate", {})
    if (repair.get("review_repair_commit"), repair.get("review_repair_tree")) != (
        "379d0a504900952931ca642f74992205310facb5",
        "bc48ccde64b379729e7ec92567120fb6058d0296",
    ):
        raise ValueError("i2_candidate_review_repair_lineage_invalid")
    repaired_validation = candidate.get("validation_after_review_repair", {})
    if (repaired_validation.get("focused_i2_a2"), repaired_validation.get("cross_boundary_a2_a1_i1_phase_h_v3"),
            repaired_validation.get("default_ci"), repaired_validation.get("full_current"),
            repaired_validation.get("market_network_calls")) != (
        "29 passed", "113 passed", "832 passed, 1 skipped, 5 deselected",
        "1205 passed, 1 skipped, 5 deselected", 0
    ):
        raise ValueError("i2_candidate_review_validation_record_invalid")
    candidate_capability = candidate.get("capability", {})
    if (candidate_capability.get("capability_id"), candidate_capability.get("runtime_executable"),
            candidate_capability.get("routing_status"), candidate_capability.get("selected_executor_id")) != (
        "index_futures_context", False, "plan_only", None
    ):
        raise ValueError("i2_candidate_governance_not_dormant")
    runtime_state = candidate.get("source_and_runtime_state", {})
    if (runtime_state.get("i2_active_sources"), runtime_state.get("i2_normal_production_routes"),
            runtime_state.get("i2_default_registry_executor_present"), runtime_state.get("i1_active_sources"),
            runtime_state.get("mcp_tool_count")) != (0, 0, False, 3, 6):
        raise ValueError("i2_candidate_governance_runtime_state_invalid")
    boundary = candidate.get("governance_boundary", {})
    if (boundary.get("market_network_calls"), boundary.get("live_acceptance"),
            boundary.get("production_activation"), boundary.get("a3_authorized"),
            boundary.get("merge_authorized"), boundary.get("i3_started"),
            boundary.get("phase_j_started")) != (0, "NOT_AUTHORIZED", "NOT_AUTHORIZED", False, False, False, False):
        raise ValueError("i2_candidate_governance_boundary_invalid")
    schema = _read("schemas/index_futures_context_evidence.v1.schema.json")
    import jsonschema
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft7Validator.check_schema(result_v3)
    jsonschema.Draft7Validator.check_schema(audit_v3)
    print("Phase I I2-A2 candidate: PASS (dormant, offline, no market calls)")


if __name__ == "__main__":
    validate()
