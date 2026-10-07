"""Fail-closed validation of the Owner-accepted I1 production activation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
from server.services.phase_i_i1_production_candidate import (
    CAPABILITY_ID,
    EVIDENCE_CONTRACT,
    EXECUTOR_ID,
    production_batch_operation_adapter_candidate,
    production_operation_adapter_candidate,
)
from server.unified_mcp.tool_contracts import build_tool_contract_snapshot

EXPECTED = {
    "zip": "de2168534dafe6c6db02ba9ab79496ba0980c0c81aab475eda23055b589714fc",
    "result_v3": "a4138a36c91de3ced4e4f53a3720fbbb6c5084648f7e1bc82728d355f4953f47",
    "audit_v3": "e6b03c2e0de0910f7f762bc607aa2487b884d02f885a5acc47cac3e8c7b17864",
}
EXPECTED_SOURCES = {
    "I1-TWSE-FMTQIK-OPENAPI",
    "I1-TWSE-BREADTH-TWTAZU-OPENAPI",
    "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI",
}
LIVE_TESTED_FILES = (
    "server/services/phase_i_i1_production_candidate.py",
    "server/services/phase_i_market_state_adapters.py",
    "schemas/market_state_context_evidence.v1.schema.json",
)


def _read(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate() -> None:
    catalog = _read("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _read("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    source_authority = _read("docs/data_capabilities/phase_i_i1_source_authority.v1.json")
    descriptors = _read("config/phase_i_i1_dormant_source_descriptors.json")
    candidate = _read("config/phase_i_i1_production_executor_candidate.json")
    metadata = _read("config/m8r_06_03_executor_registry_metadata.json")
    cap = next(item for item in catalog["data_need_capabilities"] if item.get("capability_id") == CAPABILITY_ID)
    route = next(item for item in routing["routes"] if item.get("capability_id") == CAPABILITY_ID)
    if (cap.get("support_status"), cap.get("runtime_executable"), cap.get("phase_i_activation_state")) != ("runtime_executable", True, "selected_route_active"):
        raise ValueError("i1_catalog_activation_candidate_invalid")
    if (route.get("routing_status"), route.get("runtime_executable"), route.get("selected_executor_id"), route.get("network_required"), route.get("batching_scope"), route.get("supported_markets"), route.get("blocking_reasons")) != ("resolved", True, EXECUTOR_ID, True, "same_market", ["TWSE", "TPEX"], []):
        raise ValueError("i1_route_activation_candidate_invalid")
    if route.get("candidate_executor_ids") != [EXECUTOR_ID] or route.get("approval_required") is not True or route.get("capability_requires_execution_approval") is not True or route.get("output_evidence_contract") != EVIDENCE_CONTRACT:
        raise ValueError("i1_route_execution_contract_invalid")
    expected_rule_tokens = ("TWSE", "2 unique official GETs", "TPEx", "1", "3", "retry zero")
    if not all(token in route.get("estimated_operation_rule", "") for token in expected_rule_tokens):
        raise ValueError("i1_network_bound_wording_invalid")

    records = {item.get("source_id"): item for item in source_authority.get("records", [])}
    if source_authority.get("active_source_count") != 3 or source_authority.get("runtime_executable") is not True or set(records) != EXPECTED_SOURCES:
        raise ValueError("i1_source_authority_set_invalid")
    if source_authority.get("owner_decision_ref") != "USER_CHAT_2026-09-30_PHASE_I_I1_FINAL_PRODUCTION_ACTIVATION_ACCEPTANCE" or source_authority.get("final_activation_acceptance_ledger") != "docs/governance/phase_i/PHASE_I_I1_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-09-30.json":
        raise ValueError("i1_final_owner_authority_reference_invalid")
    if any(item.get("activation_state") != "active" or item.get("runtime_executable") is not True for item in records.values()):
        raise ValueError("i1_source_not_active")
    if descriptors.get("runtime_executable") is not True or descriptors.get("network_enabled") is not True or len(descriptors.get("sources", [])) != 3:
        raise ValueError("i1_source_descriptor_state_invalid")
    if any(item.get("activation_state") != "active" or item.get("runtime_executable") is not True or item.get("raw_payload_retention_policy") != "forbidden" or item.get("usage_authority_status") != "OWNER_ACTIVATION_ACCEPTED" for item in descriptors["sources"]):
        raise ValueError("i1_source_descriptor_contract_invalid")
    breadth = next(item for item in descriptors["sources"] if item.get("source_id") == "I1-TWSE-BREADTH-TWTAZU-OPENAPI")
    if breadth.get("required_selector") != {"類型": "股票"}:
        raise ValueError("i1_twse_breadth_selector_changed")

    candidate_entries = candidate.get("executor_metadata", {}).get("executors", [])
    registry_entries = [item for item in metadata.get("executors", []) if item.get("capability_id") == CAPABILITY_ID]
    if len(candidate_entries) != 2 or len(registry_entries) != 2 or {item.get("market") for item in registry_entries} != {"TWSE", "TPEX"}:
        raise ValueError("i1_executor_metadata_route_set_invalid")
    if {json.dumps(item, sort_keys=True) for item in candidate_entries} != {json.dumps(item, sort_keys=True) for item in registry_entries}:
        raise ValueError("i1_executor_metadata_candidate_mismatch")
    if any(item.get("executor_id") != EXECUTOR_ID or item.get("network_required") is not True or item.get("bounded_execution_supported") is not True or item.get("timeout_seconds") != 15 or item.get("maximum_result_items") != 1 or item.get("expected_evidence_contract") != EVIDENCE_CONTRACT for item in registry_entries):
        raise ValueError("i1_executor_metadata_contract_invalid")

    normal = build_production_runtime_adapter_registry()
    registrations = normal.routes_for_executor(EXECUTOR_ID)
    if len(registrations) != 2 or {item.market for item in registrations} != {"TWSE", "TPEX"}:
        raise ValueError("i1_normal_registry_route_set_invalid")
    if any(item.capability_id != CAPABILITY_ID or item.expected_evidence_contract != EVIDENCE_CONTRACT or item.adapter is not production_operation_adapter_candidate or item.batch_adapter is not production_batch_operation_adapter_candidate or item.fake_adapter for item in registrations):
        raise ValueError("i1_normal_registry_adapter_binding_invalid")
    # Later I2 A4 authority is separate from the frozen I1 activation gate.
    if any(item.get("capability_id") == "index_futures_context" for item in metadata.get("executors", [])):
        from scripts.phase_i_i2_a4_proof import verify_candidate_authority
        verify_candidate_authority()
    i2_i3 = {"institutional_positioning", "market_positioning_context"}
    if any(item.get("capability_id") in i2_i3 for item in metadata.get("executors", [])):
        raise ValueError("i2_i3_production_route_added")

    phase_h = routing.get("phase_h_source_authority", {})
    phase_h_active = {item.get("source_id") for item in phase_h.get("records", []) if item.get("activation_state") == "active" and item.get("runtime_executable") is True}
    if phase_h.get("active_source_count") != 4 or phase_h_active != {"H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI", "H3-TWSE-DEFAULT-BOUNDED"}:
        raise ValueError("phase_h_active_routes_changed")
    if len(build_tool_contract_snapshot().tools) != 6:
        raise ValueError("mcp_surface_changed")

    ledger = _read("docs/governance/phase_i/PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-09-30.json")
    zip_path = ROOT / ledger["projection"]["governed_evidence_package_path"]
    if hashlib.sha256(zip_path.read_bytes()).hexdigest() != EXPECTED["zip"]:
        raise ValueError("accepted_live_zip_changed")
    with zipfile.ZipFile(zip_path) as archive:
        for key in ("result_v3", "audit_v3"):
            spec = ledger["projection"][key]
            if hashlib.sha256(archive.read(spec["archive_member"])).hexdigest() != EXPECTED[key]:
                raise ValueError(f"accepted_{key}_changed")

    final_ledger = _read("docs/governance/phase_i/PHASE_I_I1_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-09-30.json")
    if final_ledger.get("status") != "OWNER_ACTIVATION_ACCEPTED" or final_ledger.get("owner_authority_reference") != "USER_CHAT_2026-09-30_PHASE_I_I1_FINAL_PRODUCTION_ACTIVATION_ACCEPTANCE":
        raise ValueError("i1_final_owner_activation_acceptance_missing")
    decision = final_ledger.get("final_decision", {})
    if decision.get("final_owner_activation_acceptance") != "ACCEPTED" or decision.get("merge_authorized") is not True or decision.get("merge_performed") is not False:
        raise ValueError("i1_final_activation_decision_invalid")

    baseline = "0f556ca79134fd8338406ba3299eea83deab3e88"
    for path in LIVE_TESTED_FILES:
        result = subprocess.run(["git", "diff", "--quiet", baseline, "--", path], cwd=ROOT, check=False)
        if result.returncode != 0:
            raise ValueError(f"live_tested_implementation_delta:{path}")
    print("Phase I I1 production activation: PASS (Owner accepted, two bounded routes, 3 active sources, no live-tested semantic delta)")


if __name__ == "__main__":
    validate()
