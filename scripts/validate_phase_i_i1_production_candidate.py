"""Verify accepted I1 source/transport implementation and live evidence remain intact."""
from __future__ import annotations

import hashlib
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
    MAX_BATCH_TARGETS,
    MAX_RESPONSE_BYTES,
    SOURCE_DESCRIPTORS,
    TIMEOUT_SECONDS,
    build_i1_candidate_runtime_adapter_registry,
    production_batch_operation_adapter_candidate,
    production_operation_adapter_candidate,
)

EXPECTED = {
    "zip": "de2168534dafe6c6db02ba9ab79496ba0980c0c81aab475eda23055b589714fc",
    "result": "a4138a36c91de3ced4e4f53a3720fbbb6c5084648f7e1bc82728d355f4953f47",
    "audit": "e6b03c2e0de0910f7f762bc607aa2487b884d02f885a5acc47cac3e8c7b17864",
}


def _read(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate() -> None:
    if MAX_BATCH_TARGETS != 50 or MAX_RESPONSE_BYTES != 65536 or TIMEOUT_SECONDS != 15:
        raise ValueError("i1_candidate_bound_changed")
    candidate = _read("config/phase_i_i1_production_executor_candidate.json")
    if (candidate.get("candidate_status"), candidate.get("live_acceptance"), candidate.get("production_route_active"), candidate.get("active_source_count")) != ("OWNER_ACTIVATION_ACCEPTED", "ACCEPTED_PASS", True, 3):
        raise ValueError("i1_owner_accepted_activation_metadata_invalid")
    if candidate.get("final_owner_activation_acceptance") != "ACCEPTED" or candidate.get("merge_authorized") is not True or "merge" in candidate:
        raise ValueError("i1_final_acceptance_authority_invalid")
    entries = candidate.get("executor_metadata", {}).get("executors", [])
    if len(entries) != 2 or {item.get("market") for item in entries} != {"TWSE", "TPEX"}:
        raise ValueError("i1_candidate_market_routes_invalid")
    if any(item.get("executor_id") != EXECUTOR_ID or item.get("capability_id") != CAPABILITY_ID or item.get("expected_evidence_contract") != EVIDENCE_CONTRACT or item.get("timeout_seconds") != 15 or item.get("network_required") is not True or item.get("bounded_execution_supported") is not True or item.get("maximum_result_items") != 1 or item.get("output_policy") != "contained_artifact_only" for item in entries):
        raise ValueError("i1_candidate_executor_contract_invalid")
    if candidate.get("transport") != {"timeout_seconds": 15, "automatic_retry": 0, "maximum_response_bytes_per_get": 65536, "http_success_status": 200, "accepted_media_type": "application/json", "redirects": "rejected", "raw_payload_persistence": "forbidden", "encoding": ["utf-8", "utf-8-sig"]}:
        raise ValueError("i1_candidate_transport_contract_invalid")

    frozen_contract = _read("docs/governance/phase_i/PHASE_I_I1_MARKET_STATE_SOURCE_CONTRACT_2026-09-29_FROZEN.json")
    frozen_sources = {item["source_id"]: item for item in frozen_contract.get("sources", [])}
    expected_ids = {"I1-TWSE-FMTQIK-OPENAPI", "I1-TWSE-BREADTH-TWTAZU-OPENAPI", "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"}
    if set(frozen_sources) != expected_ids or set(SOURCE_DESCRIPTORS) != expected_ids:
        raise ValueError("i1_frozen_source_set_invalid")
    for source_id, descriptor in SOURCE_DESCRIPTORS.items():
        frozen = frozen_sources[source_id]
        if descriptor["url"] != frozen["surface"] or descriptor["source_contract_id"] != frozen["source_contract_id"]:
            raise ValueError(f"i1_candidate_source_drift:{source_id}")

    ledger_path = ROOT / "docs/governance/phase_i/PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-09-30.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if ledger.get("status") != "PASS" or ledger.get("network", {}).get("actual_get_count") != 3 or ledger.get("network", {}).get("retry_count") != 0:
        raise ValueError("i1_bounded_live_acceptance_not_accepted")
    projection = ledger.get("projection", {})
    zip_path = ROOT / projection.get("governed_evidence_package_path", "")
    zip_hash = hashlib.sha256(zip_path.read_bytes()).hexdigest() if zip_path.is_file() else None
    if zip_hash != EXPECTED["zip"] or projection.get("governed_evidence_package_sha256") != EXPECTED["zip"]:
        raise ValueError("i1_bounded_live_zip_hash_mismatch")
    if projection.get("result_v3", {}).get("sha256") != EXPECTED["result"] or projection.get("audit_v3", {}).get("sha256") != EXPECTED["audit"]:
        raise ValueError("i1_bounded_live_projection_hash_mismatch")

    activation = _read("docs/governance/phase_i/PHASE_I_I1_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-09-30.json")
    if activation.get("status") != "OWNER_ACTIVATION_ACCEPTED" or activation.get("owner_authority_reference") != "USER_CHAT_2026-09-30_PHASE_I_I1_FINAL_PRODUCTION_ACTIVATION_ACCEPTANCE":
        raise ValueError("i1_final_owner_acceptance_ledger_invalid")
    runtime = activation.get("runtime_authority", {})
    if runtime.get("active_source_count") != 3 or runtime.get("normal_production_registry_routes") != 2 or runtime.get("active_source_ids") != ["I1-TWSE-FMTQIK-OPENAPI", "I1-TWSE-BREADTH-TWTAZU-OPENAPI", "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"]:
        raise ValueError("i1_final_activation_source_authority_invalid")

    normal = build_production_runtime_adapter_registry().routes_for_executor(EXECUTOR_ID)
    candidate_registry = build_i1_candidate_runtime_adapter_registry()
    candidate_routes = candidate_registry.routes_for_executor(EXECUTOR_ID)
    if len(normal) != 2 or {item.market for item in normal} != {"TWSE", "TPEX"}:
        raise ValueError("i1_normal_production_routes_invalid")
    if len(candidate_routes) != 2 or {item.market for item in candidate_routes} != {"TWSE", "TPEX"}:
        raise ValueError("i1_candidate_registry_missing")
    if any(item.adapter is not production_operation_adapter_candidate or item.batch_adapter is not production_batch_operation_adapter_candidate or item.fake_adapter for item in normal):
        raise ValueError("i1_production_adapter_binding_invalid")
    if any(item.batch_adapter is not production_batch_operation_adapter_candidate for item in candidate_routes):
        raise ValueError("i1_candidate_batch_adapter_missing")
    print("Phase I I1 production candidate: PASS (Owner-accepted bounded implementation and evidence preserved)")


if __name__ == "__main__":
    validate()
