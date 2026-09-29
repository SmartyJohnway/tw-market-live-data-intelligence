"""Fail-closed semantic checks for the offline, dormant Phase I1 candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
FROZEN = {
    "docs/governance/phase_i/Phase_I_I0_Evidence_Value_Source_Identity_Timing_Decision_Record_2026-09-29_FROZEN.md": (28251, "02e031e8c39eee96664457735432b7bf08ac9e8b03c07252921f425d05c8f7c5"),
    "docs/governance/phase_i/PHASE_I_I1_MARKET_STATE_SOURCE_CONTRACT_2026-09-29_FROZEN.json": (13438, "0073c606f8319fdcb7a97b0330db2afd996b09038497a64c8d26cb613b0d2cf7"),
    "docs/governance/phase_i/Phase_I_I1_Market_State_Source_Contract_2026-09-29_FROZEN.md": (5355, "5c6a75072981e289ff344d64b81cb657b3a8ddc577d4d091196125291269f506"),
}


class I1ValidationError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise I1ValidationError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def _json(path: str) -> Any:
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise I1ValidationError(f"current_authority_json_invalid:{path}") from exc


def _validate_typed_failure_semantics(evidence_schema: dict[str, Any], result_v3: dict[str, Any]) -> None:
    """Prove I1 failures are representable without weakening complete evidence."""
    evidence_validator = jsonschema.Draft202012Validator(
        evidence_schema, format_checker=jsonschema.FormatChecker()
    )
    result_validator = jsonschema.Draft7Validator(
        result_v3, format_checker=jsonschema.FormatChecker()
    )
    component = {
        "status": "source_failed",
        "official_date": None,
        "source": {
            "source_id": "I1-TWSE-FMTQIK-OPENAPI",
            "source_family": "TWSE_FMTQIK_OFFICIAL_OPENAPI",
            "source_contract_id": "TWSE_FMTQIK_V1",
            "url": "https://example.invalid/fixture",
            "authority": "official",
            "retrieved_at": "2026-09-29T06:00:00Z",
        },
        "observed_fields": {},
        "unit_metadata": {},
    }
    base: dict[str, Any] = {
        "schema_version": "market_state_context_evidence.v1",
        "status": "source_failed",
        "market": "TWSE",
        "currentness_status": "unknown",
        "retrieved_at": "2026-09-29T06:00:00Z",
        "components": {"fmtqik": component},
        "citation_ids": [],
        "caveats": ["fixture failure state; no market values observed"],
    }
    for status in ("unavailable", "source_failed", "binding_failed"):
        item = {**base, "status": status}
        try:
            evidence_validator.validate(item)
        except jsonschema.ValidationError as exc:
            raise I1ValidationError(f"i1_failure_not_representable:{status}") from exc
        projected = {**item, "target": {"canonical_target_id": "TWSE:2330", "market": "TWSE"}}
        try:
            jsonschema.Draft7Validator(result_v3["definitions"]["market_state_context"], format_checker=jsonschema.FormatChecker()).validate(projected)
        except jsonschema.ValidationError as exc:
            raise I1ValidationError(f"i1_result_failure_not_representable:{status}") from exc

    required_success = {"trade_date", "benchmark", "turnover", "breadth", "breadth_unit", "source_unit_metadata"}
    evidence_complete_required = set(evidence_schema.get("allOf", [{}])[0].get("then", {}).get("required", []))
    result_complete_required = set(result_v3["definitions"]["market_state_context"].get("allOf", [{}])[0].get("then", {}).get("required", []))
    if not required_success <= evidence_complete_required or not required_success <= result_complete_required:
        raise I1ValidationError("i1_complete_observation_fields_not_required")
    complete = {**base, "status": "complete"}
    if evidence_validator.is_valid(complete):
        raise I1ValidationError("i1_complete_without_observations_accepted")
    complete_result = {**complete, "target": {"canonical_target_id": "TWSE:2330", "market": "TWSE"}}
    if jsonschema.Draft7Validator(result_v3["definitions"]["market_state_context"], format_checker=jsonschema.FormatChecker()).is_valid(complete_result):
        raise I1ValidationError("i1_result_complete_without_observations_accepted")
    partial = {**base, "status": "partial"}
    for key in ("trade_date", "benchmark", "turnover", "breadth", "breadth_unit", "source_unit_metadata"):
        partial.pop(key, None)
    if not evidence_validator.is_valid(partial):
        raise I1ValidationError("i1_partial_without_observation_component_rejected")


def validate_phase_i_i1_contracts() -> None:
    for rel, (size, digest) in FROZEN.items():
        data = (ROOT / rel).read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise I1ValidationError(f"frozen_authority_mismatch:{rel}")

    catalog = _json("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _json("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    registry = _json("config/m8r_06_03_executor_registry_metadata.json")
    source_authority = _json("docs/data_capabilities/phase_i_i1_source_authority.v1.json")
    descriptors = _json("config/phase_i_i1_dormant_source_descriptors.json")
    request_v3 = _json("schemas/unified_market_evidence_request.v3.schema.json")
    request_v1 = _json("schemas/unified_market_evidence_request.v1.schema.json")
    request_v2 = _json("schemas/unified_market_evidence_request.v2.schema.json")
    evidence_schema = _json("schemas/market_state_context_evidence.v1.schema.json")
    result_v3 = _json("schemas/unified_market_evidence_result.v3.schema.json")
    audit_v3 = _json("schemas/unified_market_evidence_audit_package.v3.schema.json")

    capability = next((x for x in catalog.get("data_need_capabilities", []) if x.get("capability_id") == "market_state_context"), None)
    route = next((x for x in routing.get("routes", []) if x.get("capability_id") == "market_state_context"), None)
    if not capability or (capability.get("support_status"), capability.get("runtime_executable"), capability.get("phase_i_activation_state")) != ("contract_supported", False, "implementation_candidate_inactive"):
        raise I1ValidationError("i1_catalog_not_dormant")
    if capability.get("supported_markets") != ["TWSE", "TPEX"] or capability.get("instrument_scope") != {"instrument_families":["company_share"],"instrument_types":["common_share"]}:
        raise I1ValidationError("i1_catalog_scope_invalid")
    if not route or (route.get("routing_status"), route.get("runtime_executable"), route.get("selected_executor_id"), route.get("network_required"), route.get("approval_required"), route.get("batching_scope")) != ("plan_only", False, None, False, True, "same_market"):
        raise I1ValidationError("i1_route_not_dormant")
    if route.get("output_evidence_contract") != "market_state_context_evidence.v1":
        raise I1ValidationError("i1_output_contract_mismatch")
    if catalog.get("phase_h_contract", {}).get("active_phase_h_source_count") != 2 or routing.get("phase_h_source_authority", {}).get("active_source_count") != 2:
        raise I1ValidationError("phase_h_source_count_changed")
    active = {x.get("source_id") for x in routing.get("phase_h_source_authority", {}).get("records", []) if x.get("activation_state") == "active" and x.get("runtime_executable") is True}
    if active != {"H1-TPEX-ATTENTION-OPENAPI", "H3-TWSE-DEFAULT-BOUNDED"}:
        raise I1ValidationError("phase_h_active_set_changed")
    if source_authority.get("active_source_count") != 0 or source_authority.get("runtime_executable") is not False or any(x.get("activation_state") != "inactive" or x.get("runtime_executable") is not False for x in source_authority.get("records", [])):
        raise I1ValidationError("phase_i_source_authority_not_dormant")
    if descriptors.get("network_enabled") is not False or descriptors.get("runtime_executable") is not False:
        raise I1ValidationError("i1_source_descriptor_not_dormant")
    if len(descriptors.get("sources", [])) != 3 or any(
        source.get("activation_state") != "inactive"
        or source.get("runtime_executable") is not False
        or source.get("usage_authority_status") != "FROZEN_SOURCE_CONTRACT_PASS_LIVE_ACCEPTANCE_PENDING"
        or source.get("raw_payload_retention_policy") != "forbidden"
        or not source.get("source_owner")
        or not source.get("source_role")
        or not source.get("official_endpoint_surface")
        for source in descriptors.get("sources", [])
    ):
        raise I1ValidationError("i1_source_descriptor_fields_invalid")
    if any(x.get("capability_id") == "market_state_context" for x in registry.get("executors", [])):
        raise I1ValidationError("i1_executor_registered")

    enum_v3 = request_v3["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]
    enum_v1 = request_v1["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]
    enum_v2 = request_v2["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]
    if "market_state_context" not in enum_v3 or "market_state_context" in enum_v1 or "market_state_context" in enum_v2:
        raise I1ValidationError("i1_request_version_scope_invalid")
    if evidence_schema.get("$id", "").endswith("market_state_context_evidence:v1") is False:
        raise I1ValidationError("i1_evidence_schema_invalid")
    target_evidence = result_v3["properties"]["targets"]["items"]["properties"]["evidence"]["properties"]
    if target_evidence.get("market_state_context", {}).get("$ref") != "#/definitions/market_state_context":
        raise I1ValidationError("i1_result_v3_projection_missing")
    if "phase_i_evidence" not in audit_v3.get("properties", {}):
        raise I1ValidationError("i1_audit_lineage_missing")
    phase_h_capability_enum = audit_v3["properties"]["phase_h_governance"]["properties"]["evidence_artifact_references"]["items"]["properties"]["capability_id"]["enum"]
    phase_i_reference = audit_v3["properties"]["phase_i_evidence"]["properties"]["evidence_artifact_references"]["items"]["properties"]
    if "market_state_context" in phase_h_capability_enum:
        raise I1ValidationError("i1_capability_allowed_in_phase_h_audit")
    if phase_i_reference.get("capability_id", {}).get("const") != "market_state_context" or phase_i_reference.get("schema_version", {}).get("const") != "market_state_context_evidence.v1":
        raise I1ValidationError("i1_phase_i_audit_reference_not_exclusive")
    _validate_typed_failure_semantics(evidence_schema, result_v3)
    sys.path.insert(0, str(ROOT))
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    if len(build_tool_contract_snapshot().tools) != 6:
        raise I1ValidationError("mcp_surface_changed")
    capability_ids = {item.get("capability_id") for item in catalog.get("data_need_capabilities", [])}
    if capability_ids & {
        "index_futures_context",
        "taifex_market_state",
        "institutional_positioning",
        "institutional_positioning_context",
        "market_positioning_context",
    }:
        raise I1ValidationError("i2_i3_scope_added")
    print("Phase I I1 contracts: PASS (dormant, V3-only, zero-network authority)")


if __name__ == "__main__":
    validate_phase_i_i1_contracts()
