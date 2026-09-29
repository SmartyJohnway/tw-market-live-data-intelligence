"""Verify the I1 production candidate exists but is unreachable in normal runtime."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
from server.services.phase_i_i1_production_candidate import (
    CAPABILITY_ID,
    EVIDENCE_CONTRACT,
    EXECUTOR_ID,
    MAX_RESPONSE_BYTES,
    SOURCE_DESCRIPTORS,
    TIMEOUT_SECONDS,
    build_i1_candidate_runtime_adapter_registry,
)


def validate() -> None:
    catalog = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8"))
    routing = json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(encoding="utf-8"))
    authority = json.loads((ROOT / "docs/data_capabilities/phase_i_i1_source_authority.v1.json").read_text(encoding="utf-8"))
    candidate = json.loads((ROOT / "config/phase_i_i1_production_executor_candidate.json").read_text(encoding="utf-8"))
    frozen_contract = json.loads((ROOT / "docs/governance/phase_i/PHASE_I_I1_MARKET_STATE_SOURCE_CONTRACT_2026-09-29_FROZEN.json").read_text(encoding="utf-8"))
    cap = next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == CAPABILITY_ID)
    route = next(item for item in routing["routes"] if item["capability_id"] == CAPABILITY_ID)
    if (cap["support_status"], cap["runtime_executable"], cap["phase_i_activation_state"]) != ("contract_supported", False, "implementation_candidate_inactive"):
        raise ValueError("i1_capability_activation_drift")
    if (route["routing_status"], route["runtime_executable"], route["selected_executor_id"], route["network_required"]) != ("plan_only", False, None, False):
        raise ValueError("i1_route_activation_drift")
    if authority["active_source_count"] != 0 or authority["runtime_executable"] is not False:
        raise ValueError("i1_source_authority_activation_drift")
    if candidate.get("candidate_status") != "IMPLEMENTED_NOT_REGISTERED" or candidate.get("live_acceptance") != "NOT_RUN":
        raise ValueError("i1_candidate_governance_state_invalid")
    entries = candidate.get("executor_metadata", {}).get("executors", [])
    if len(entries) != 2 or {item.get("market") for item in entries} != {"TWSE", "TPEX"}:
        raise ValueError("i1_candidate_market_routes_invalid")
    if any(item.get("executor_id") != EXECUTOR_ID or item.get("capability_id") != CAPABILITY_ID or item.get("expected_evidence_contract") != EVIDENCE_CONTRACT or item.get("timeout_seconds") != TIMEOUT_SECONDS or item.get("network_required") is not True or item.get("bounded_execution_supported") is not True or item.get("maximum_result_items") != 1 for item in entries):
        raise ValueError("i1_candidate_executor_contract_invalid")
    if candidate.get("transport") != {"timeout_seconds": 15, "automatic_retry": 0, "maximum_response_bytes_per_get": 65536, "http_success_status": 200, "accepted_media_type": "application/json", "redirects": "rejected", "raw_payload_persistence": "forbidden", "encoding": ["utf-8", "utf-8-sig"]}:
        raise ValueError("i1_candidate_transport_contract_invalid")
    frozen_sources = {item["source_id"]: item for item in frozen_contract.get("sources", [])}
    if set(frozen_sources) != {"I1-TWSE-FMTQIK-OPENAPI", "I1-TWSE-BREADTH-TWTAZU-OPENAPI", "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"}:
        raise ValueError("i1_frozen_source_set_invalid")
    for source_id, descriptor in SOURCE_DESCRIPTORS.items():
        frozen = frozen_sources.get(source_id)
        if frozen is None or descriptor["url"] != frozen["surface"] or descriptor["source_contract_id"] != frozen["source_contract_id"]:
            raise ValueError(f"i1_candidate_source_drift:{source_id}")
    normal_registry = build_production_runtime_adapter_registry()
    if normal_registry.routes_for_executor(EXECUTOR_ID):
        raise ValueError("i1_candidate_leaked_into_normal_runtime")
    candidate_registry = build_i1_candidate_runtime_adapter_registry()
    if len(candidate_registry.routes_for_executor(EXECUTOR_ID)) != 2:
        raise ValueError("i1_candidate_registry_missing")
    if MAX_RESPONSE_BYTES != 65536:
        raise ValueError("i1_response_cap_invalid")
    print("Phase I I1 production candidate: PASS (implemented, bounded, not registered/active)")


if __name__ == "__main__":
    validate()
