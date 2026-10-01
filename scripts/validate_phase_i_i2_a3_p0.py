"""Validate and optionally record the disarmed I2-A3 P0 fake-runner candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_phase_i_i2_a3_bounded_live_acceptance import (
    EXECUTOR_ID, PRE_NETWORK_AUTHORITY, deterministic_fixture_payload,
    run_fake_governed_acceptance,
)
from server.services.phase_i_i2_index_futures_adapters import SOURCE_ENDPOINT

A1_SHA256 = "6d535e34defb1e82947f64ceec6df5e1859888fb3550e36e6ded1b6a7573d4fb"
STARTING_MAIN = "846c3f8f4c76862d8c76aeba3acdbf0f3dc44af1"
PRIOR_LIVE_AUTHORITY = "USER_CHAT_2026-10-01_PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE"
RECORD_PATH = ROOT / "docs/governance/phase_i/PHASE_I_I2_A3_PRE_NETWORK_GOVERNED_RUNNER_CANDIDATE_2026-10-01.json"


def _json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate(*, write_candidate_record: bool = False) -> dict:
    contract_path = ROOT / "docs/governance/phase_i/PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json"
    contract_sha = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    if contract_sha != A1_SHA256:
        raise ValueError("i2_a1_frozen_contract_hash_drift")
    catalog = _json("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _json("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    source = _json("docs/data_capabilities/phase_i_i2_source_authority.v1.json")
    i1_source = _json("docs/data_capabilities/phase_i_i1_source_authority.v1.json")
    cap = next(x for x in catalog["data_need_capabilities"] if x.get("capability_id") == "index_futures_context")
    route = next(x for x in routing["routes"] if x.get("capability_id") == "index_futures_context")
    if (cap.get("support_status"), cap.get("runtime_executable"), cap.get("phase_i_activation_state")) != ("contract_supported", False, "implementation_candidate_inactive"):
        raise ValueError("canonical_i2_catalog_not_dormant")
    if (route.get("routing_status"), route.get("runtime_executable"), route.get("selected_executor_id"), route.get("batching_scope")) != ("plan_only", False, None, "same_source"):
        raise ValueError("canonical_i2_route_not_dormant")
    if source.get("active_source_count") != 0 or source.get("runtime_executable") is not False or any(x.get("activation_state") != "inactive" for x in source.get("records", [])):
        raise ValueError("i2_source_authority_not_dormant")
    i1_count = sum(x.get("activation_state") == "active" and x.get("runtime_executable") is True for x in i1_source.get("records", []))
    if i1_source.get("active_source_count") != 3 or i1_count != 3:
        raise ValueError("i1_source_count_drift")
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    prod_registry = build_production_runtime_adapter_registry()
    if prod_registry.routes_for_executor(EXECUTOR_ID):
        raise ValueError("i2_executor_reachable_from_production_registry")
    if len(build_tool_contract_snapshot().tools) != 6:
        raise ValueError("mcp_surface_not_six")

    payload = deterministic_fixture_payload()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output_root = ROOT / "data" / "phase_i_i2_a3_p0" / run_id
    calls = []
    def fake_transport(url: str, timeout: int):
        from server.services.phase_i_i2_index_futures_adapters import SOURCE_ENDPOINT
        if calls or (url, timeout) != (SOURCE_ENDPOINT, 30):
            raise ValueError("p0_fake_transport_scope_or_count_invalid")
        calls.append((url, timeout))
        return 200, {"Content-Type": "application/octet-stream"}, payload

    def deny_socket(*args, **kwargs):
        raise AssertionError("external network forbidden during A3-P0")
    with patch("socket.socket.connect", deny_socket):
        outcome = run_fake_governed_acceptance(output_root=output_root, fake_transport=fake_transport)
    if calls != [("https://openapi.taifex.com.tw/v1/DailyMarketReportFut", 30)]:
        raise ValueError("fake_source_acquisition_count_not_one")
    if (outcome["simulated_source_acquisitions"], outcome["actual_external_market_calls"], outcome["raw_payload_persistence"], outcome["replay_denied_before_transport"]) != (1, 0, "NONE", True):
        raise ValueError("p0_execution_or_raw_persistence_proof_failed")
    if outcome["authorization"].get("owner_review_reference") != PRE_NETWORK_AUTHORITY:
        raise ValueError("p0_owner_authorization_binding_mismatch")
    if len(outcome["plan"].get("operations", [])) != 2 or len(outcome["plan"].get("batch_groups", [])) != 1 or outcome["plan"].get("accounting", {}).get("network_request_estimate") != 1:
        raise ValueError("p0_planner_scope_invalid")

    head = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    receipt = outcome["execution"]["execution_receipt"]
    bundle = outcome["execution"]["evidence_bundle"]
    acquisition = outcome["source_acquisition"]
    record = {
        "schema_version": "phase_i_i2_a3_pre_network_governed_runner_candidate.v1",
        "gate_id": "PHASE_I_I2_A3_PRE_NETWORK_GOVERNED_RUNNER_CLOSURE",
        "status": "PRE_NETWORK_GOVERNED_RUNNER_READY_FOR_INDEPENDENT_REVIEW",
        "starting_main": STARTING_MAIN,
        "review_candidate_head": head,
        "review_candidate_tree": tree,
        "prior_live_authority": PRIOR_LIVE_AUTHORITY,
        "prior_live_authority_consumed": False,
        "current_pre_network_authority": PRE_NETWORK_AUTHORITY,
        "live_execution_rearm_required": True,
        "frozen_a1_contract_sha256": contract_sha,
        "security_master": {
            "release_id": "security-master-20260926T151841Z",
            "release_index_sha256": "665d69e53588fa6cd723e434902946a43ac4f712920b0c4ec2adf91b556f4c10",
            "release_manifest_sha256": "18a10eb8927902d021d5e9023be4c9a6f28be50c9d02fa148e7a56780476a856",
            "selected_targets": outcome["selected_targets"],
        },
        "governed_execution": {
            "request_schema": "unified_market_evidence_request.v3",
            "execution_request_schema": "unified_market_evidence_execution_request.v2",
            "logical_operations": 2,
            "executable_operations": 2,
            "batch_group_count": 1,
            "network_request_estimate": 1,
            "executor_id": EXECUTOR_ID,
            "operation_ids": outcome["operation_ids"],
            "batch_group_ids": outcome["batch_group_ids"],
            "authorization_id": outcome["authorization"]["authorization_id"],
            "owner_review_reference": outcome["authorization"]["owner_review_reference"],
            "consumption_binding_id": outcome["consumption_binding"]["consumption_binding_id"],
            "preflight_id": outcome["preflight"]["preflight_id"],
            "execution_request_ids": [x["execution_request_id"] for x in outcome["preflight"]["bounded_execution_requests"]],
            "claim_id": outcome["execution"]["claim_record"]["claim_id"],
            "claim_state": outcome["execution"]["consumption_state"],
            "claim_attempt_count": outcome["execution"]["claim_record"]["attempt_count"],
            "receipt_id": receipt["execution_receipt_id"],
            "bundle_id": bundle["bundle_id"],
            "candidate_authority_overlay_sha256": outcome["overlay_sha256"],
        },
        "fake_source_acquisition": {
            "source_id": "I2-TAIFEX-DAILYMARKETREPORTFUT-OPENAPI",
            "endpoint": SOURCE_ENDPOINT,
            "simulated_acquisitions": outcome["simulated_source_acquisitions"],
            "actual_external_market_calls": outcome["actual_external_market_calls"],
            "retry_count": acquisition.retry_count,
            "http_status": acquisition.http_status,
            "content_type": acquisition.content_type,
            "response_byte_count": acquisition.response_byte_count,
            "response_sha256": acquisition.response_sha256,
            "retrieved_at": acquisition.retrieved_at,
            "selected_date": "2026-09-29",
            "selected_contract_period": "202610",
            "fixture_body_persisted": False,
        },
        "projection": {
            "operation_result_count": len(outcome["execution"]["dispatch_outcomes"]),
            "result_v3_sha256": outcome["result_v3_sha256"],
            "audit_v3_sha256": outcome["audit_v3_sha256"],
            "result_v3_schema": "PASS",
            "audit_v3_schema": "PASS",
            "result_replay": "PASS",
            "audit_replay": "PASS",
            "citation_lineage": "PASS",
            "artifact_lineage": "PASS",
            "raw_payload_persistence": "NONE",
            "generated_control_package": output_root.relative_to(ROOT).as_posix(),
        },
        "runtime_boundary": {
            "i2_active_sources": 0, "i2_production_routes": 0,
            "default_registry_i2_executor_present": False, "selected_production_executor": None,
            "i1_active_sources": 3, "mcp_tool_count": 6,
            "a3_live_acceptance": "NOT_YET_EXECUTED",
            "production_activation": "NOT_AUTHORIZED", "merge_authorized": False,
            "i3_started": False, "phase_j_started": False,
        },
        "network": {"market_network_calls": 0, "TAIFEX": 0, "TWSE": 0, "TPEx": 0,
                    "socket_connect_attempts": 0, "live_execution_rearm_required": True},
    }
    if write_candidate_record:
        RECORD_PATH.write_text(
            json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print("Phase I I2-A3-P0 governed runner: PASS (fake transport; market network=0)")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-candidate-record", action="store_true")
    args = parser.parse_args()
    validate(write_candidate_record=args.write_candidate_record)
