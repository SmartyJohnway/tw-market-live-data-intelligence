"""Offline fail-closed validator for the dormant I3-A4 technical candidate."""
from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASELINE = "5c26e7b541bdb6c0d70a39c1e0eab8e129823373"
BASELINE_TREE = "ac72a639cba570d8a8cfc743934c6131f88fad42"
CAPABILITY = "cash_institutional_flow_context"
EXECUTOR = "phase_i_i3_cash_institutional_flow_context_executor"
FROZEN = {
    "docs/governance/phase_i/PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_2026-10-03_FROZEN.json":
        "4f6c00f8c0ef61bd7c5c55daa81e23cf25ec6335c4fe99ef4c539572419f5428",
    "schemas/cash_institutional_flow_context_evidence.v1.schema.json":
        "3be9a0ca3cf0e0bb5badb427231d47ce86fdb604ae28cb31582b0f9612c76f7c",
    "docs/governance/phase_i/PHASE_I_I3_A2_DORMANT_OFFLINE_IMPLEMENTATION_CANDIDATE_2026-10-03.json":
        "122d3317d098bc602fe753b02837bf9b1b7133ba287c45cd8de73383d97300e1",
    "docs/governance/phase_i/PHASE_I_I3_A2_R1_OPTIONAL_SOURCE_NATIVE_FAILURE_SEMANTICS_CLOSURE_2026-10-03.json":
        "d4962eddf90fe2cf6e1ed3c231f66dc7e1332d9597c5e8fc886ca85e926b9b12",
}


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL).decode("utf-8").strip()


def validate() -> dict:
    def deny(*_args, **_kwargs):
        raise AssertionError("i3_a4_market_network_forbidden")

    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        _require(_git("show", "-s", "--format=%T", BASELINE) == BASELINE_TREE, "rollback_baseline_tree_mismatch")
        _require(all(_sha(path) == expected for path, expected in FROZEN.items()), "frozen_i3_authority_changed")

        v2_path = "schemas/cash_institutional_flow_context_evidence.v2.schema.json"
        v2_schema = _json(v2_path)
        Draft202012Validator.check_schema(v2_schema)
        _require(v2_schema["properties"]["schema_version"]["const"] == "cash_institutional_flow_context_evidence.v2",
                 "production_evidence_v2_contract_invalid")
        transport = v2_schema["properties"]["transport"]
        _require(transport["properties"]["mode"]["const"] == "official_https_live"
                 and transport["properties"]["network_get_count"]["const"] == 1
                 and transport["properties"]["retry_count"]["const"] == 0
                 and transport["properties"]["redirect_policy"]["const"] == "reject"
                 and transport["properties"]["raw_payload_persisted"]["const"] is False,
                 "production_v2_transport_contract_invalid")

        source_authority = _json("docs/data_capabilities/phase_i_i3_source_authority.v1.json")
        _require(source_authority["evidence_contract"] == "cash_institutional_flow_context_evidence.v2"
                 and len(source_authority["sources"]) == 2
                 and {item["market"] for item in source_authority["sources"]} == {"TWSE", "TPEX"},
                 "i3_source_authority_candidate_invalid")
        _require(all(item["retry_count"] == 0 and item["fallback"] is False
                     and item["maximum_dispatches_per_authorized_execution"] == 1
                     and item["raw_persistence"] is False for item in source_authority["sources"]),
                 "i3_source_policy_invalid")
        _require(source_authority["batching"]["mixed_market_max_dispatches"] == 2
                 and source_authority["batching"]["per_target_refetch"] is False,
                 "i3_batching_authority_invalid")

        evidence_decision = _json("docs/governance/phase_i/PHASE_I_I3_A4_PRODUCTION_EVIDENCE_V2_DECISION_2026-10-04.json")
        r1_record_path = "docs/governance/phase_i/PHASE_I_I3_A4_R1_INDEPENDENT_REVIEW_HARDENING_2026-10-05.json"
        has_r1 = (ROOT / r1_record_path).exists()
        expected_candidate_schema = (
            "b5c80c338be99ffa55d51c73e7909f2c0ba2908d8caecce0ac50a474738e2847"
            if has_r1 else _sha(v2_path)
        )
        _require(evidence_decision["owner_authority"] ==
                 "USER_CHAT_2026-10-04_PHASE_I_I3_A4_PRODUCTION_EVIDENCE_V2_AND_TECHNICAL_CANDIDATE_RESUME_AUTHORIZATION"
                 and evidence_decision["historical_contract"]["schema_sha256"] == FROZEN["schemas/cash_institutional_flow_context_evidence.v1.schema.json"]
                 and evidence_decision["historical_contract"]["bytes_changed"] is False
                 and evidence_decision["historical_contract"]["A1_changed"] is False
                 and evidence_decision["production_candidate_contract"]["schema_sha256"] == expected_candidate_schema
                 and evidence_decision["production_transport"]["retry_count"] == 0
                 and evidence_decision["acceptance_boundary"]["market_GETs_during_implementation"] ==
                 {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0},
                 "evidence_v2_governance_decision_invalid")

        catalog = _json("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
        route_matrix = _json("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
        catalog_candidates = [item for item in catalog["data_need_capabilities"] if item.get("capability_id") == CAPABILITY]
        routes = [item for item in route_matrix["routes"] if item.get("capability_id") == CAPABILITY]
        _require(len(catalog_candidates) == 1 and catalog_candidates[0].get("support_status") == "contract_supported",
                 "i3_catalog_candidate_invalid")
        _require(len(routes) == 1 and routes[0].get("routing_status") == "plan_only"
                 and routes[0].get("runtime_executable") is False
                 and routes[0].get("selected_executor_id") is None
                 and set(routes[0].get("supported_markets", [])) == {"TWSE", "TPEX"}
                 and routes[0].get("output_evidence_contract") == "cash_institutional_flow_context_evidence.v2",
                 "i3_route_must_remain_dormant_candidate")
        metadata_candidate = _json("docs/data_capabilities/phase_i_i3_executor_metadata_candidate.v1.json")
        _require(len(metadata_candidate["executors"]) == 2
                 and {item["market"] for item in metadata_candidate["executors"]} == {"TWSE", "TPEX"}
                 and all(item["expected_evidence_contract"] == "cash_institutional_flow_context_evidence.v2"
                         for item in metadata_candidate["executors"]), "i3_executor_metadata_candidate_invalid")

        from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
        from server.unified_mcp.tool_contracts import build_tool_specs
        active = build_production_runtime_adapter_registry()
        _require(len(active.routes_for_executor(EXECUTOR)) == 0, "i3_executor_reachable_from_default_runtime")
        _require(len(active.routes_for_executor("phase_i_i1_market_state_executor")) == 2, "i1_runtime_route_drift")
        _require(len(active.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1, "i2_runtime_route_drift")
        _require(len(build_tool_specs()) == 6, "mcp_tool_count_drift")

        request_schema = _json("schemas/unified_market_evidence_request.v3.schema.json")
        result_schema = _json("schemas/unified_market_evidence_result.v3.schema.json")
        audit_schema = _json("schemas/unified_market_evidence_audit_package.v3.schema.json")
        _require(CAPABILITY in request_schema["properties"]["data_needs"]["items"]["properties"]["type"]["enum"],
                 "i3_request_v3_support_missing")
        _require("cash_institutional_flow_context" in result_schema["definitions"], "i3_result_v3_projection_missing")
        audit_refs = audit_schema["properties"]["phase_i_evidence"]["properties"]["evidence_artifact_references"]["items"]["oneOf"]
        _require(any(any_of.get("properties", {}).get("schema_version", {}).get("const") == "cash_institutional_flow_context_evidence.v2"
                     for any_of in audit_refs), "i3_audit_v3_v2_reference_missing")
        execution_v3 = _json("schemas/unified_market_evidence_execution_request.v3.schema.json")
        _require("resolved_source_trade_date" in execution_v3["properties"]["parameters"]["properties"],
                 "i3_execution_request_v3_date_binding_missing")

        from scripts.phase_i_i3_a4_rollback_proof import prove_i3_rollback
        rollback = prove_i3_rollback()
        _require(rollback["status"] == "PASS" and rollback["i3_active_sources"] == 0
                 and rollback["i3_routes"] == 0 and rollback["i3_executor_reachable"] is False
                 and rollback["i3_public_v3_support"] is False and rollback["mcp_tool_count"] == 6,
                 "i3_roll_001_failed")

        candidate_record = _json("docs/governance/phase_i/PHASE_I_I3_A4_TECHNICAL_ACTIVATION_CANDIDATE_2026-10-04.json")
        if has_r1:
            # The original candidate record is a sealed pre-R1 snapshot. Its
            # V2 hash remains historical; the additive R1 record owns current
            # schema truth after the approved telemetry repair.
            r1_record = _json(r1_record_path)
            _require(candidate_record["candidate"]["V2_schema_sha256"] ==
                     "b5c80c338be99ffa55d51c73e7909f2c0ba2908d8caecce0ac50a474738e2847"
                     and r1_record["evidence_v2"]["schema_sha256_after"] == _sha(v2_path),
                     "i3_r1_historical_v2_schema_supersession_invalid")
        else:
            _require(candidate_record["candidate"]["V2_schema_sha256"] == _sha(v2_path),
                     "production_evidence_v2_schema_hash_mismatch")
        _require(candidate_record["final_disposition"] == "TECHNICAL_ACTIVATION_CANDIDATE_READY_FOR_OWNER_REVIEW"
                 and candidate_record["candidate"]["source_authority_count"] == 2
                 and candidate_record["rollback"]["status"] == "PASS"
                 and candidate_record["validation"]["default_ci"]["failed"] == 0
                 and candidate_record["validation"]["full_current"]["failed"] == 0
                 and candidate_record["runtime_containment"]["market_GETs_during_implementation"] ==
                 {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}
                 and candidate_record["authorization_boundary"]["production_activation_authorized"] is False
                 and candidate_record["authorization_boundary"]["merge_authorized"] is False,
                 "i3_candidate_governance_record_invalid")

        forbidden_live = [
            ROOT / "docs/governance/phase_i/acceptance_runs/i3-a4-authority-reservation.json",
            ROOT / "docs/governance/phase_i/acceptance_runs/i3-a4-authority-consumed.json",
        ]
        _require(not any(path.exists() for path in forbidden_live), "i3_a4_live_authority_artifact_exists")
        return {"status": "PASS", "v1_immutable": True, "v2_schema_sha256": _sha(v2_path),
                "i3_candidate_sources": 2, "i3_active_sources": 0, "i3_default_runtime_routes": 0,
                "i1_routes": 2, "i2_routes": 1, "mcp_tool_count": 6,
                "rollback_id": "I3-ROLL-001", "rollback_status": "PASS", "market_gets": 0,
                "production_activation_authorized": False, "merge_authorized": False}


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
