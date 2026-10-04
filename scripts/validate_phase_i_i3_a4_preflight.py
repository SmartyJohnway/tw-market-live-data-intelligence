"""Offline I3-A4 production activation preflight validator.

This gate inventories the accepted A3 baseline and activation gaps. It must not
activate I3, expose I3 through public V3, or perform market network I/O.
"""
from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASELINE = "5c26e7b541bdb6c0d70a39c1e0eab8e129823373"
BASELINE_TREE = "ac72a639cba570d8a8cfc743934c6131f88fad42"
BRANCH = "phase-i/i3-a4-production-activation-preflight"
CAPABILITY = "cash_institutional_flow_context"
EXECUTOR = "phase_i_i3_cash_institutional_flow_context_executor"
PREFLIGHT = "docs/governance/phase_i/PHASE_I_I3_A4_PRODUCTION_ACTIVATION_PREFLIGHT_2026-10-04.json"

ACCEPTED = {
    "docs/governance/phase_i/PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_2026-10-03_FROZEN.json":
        "4f6c00f8c0ef61bd7c5c55daa81e23cf25ec6335c4fe99ef4c539572419f5428",
    "docs/governance/phase_i/PHASE_I_I3_A2_R1_OPTIONAL_SOURCE_NATIVE_FAILURE_SEMANTICS_CLOSURE_2026-10-03.json":
        "d4962eddf90fe2cf6e1ed3c231f66dc7e1332d9597c5e8fc886ca85e926b9b12",
    "docs/governance/phase_i/PHASE_I_I3_A3_OWNER_FINAL_ACCEPTANCE_CLOSURE_2026-10-04.json":
        "0cd51bc5b1b07098f0786ccbb4bd39d1ed3263fd6c9c898fc3c60be004c3101d",
    "docs/governance/phase_i/PHASE_I_I3_A3_FINAL_MERGE_AND_A4_PREFLIGHT_TRANSITION_2026-10-04.json":
        "5bd2dda1b50adb421369e2837f7e9a51968a821a3ab3a1e6f101dfbc4eb8e580",
}
PROTECTED = {
    "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json":
        "c245cc1bc28f12b3dcd087410ddc25f6e30861ec1ba34d1160d534a9c1661a83",
    "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json":
        "c2835ca9a41aaaf25547e239db8832a6ddadd06a9da7282a04c3022c1fc82251",
    "config/m8r_06_03_executor_registry_metadata.json":
        "518809f861cae1548122e1444f8de2702c50327161af6b4fdbacb477748d534c",
    "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json":
        "86da3a7febbb8f4d75ed041aefd9dc74b953df18c542ad327a806550f9161ca7",
    "schemas/unified_market_evidence_request.v3.schema.json":
        "e11807c2d43dfa91cae90e4b266cc450724301dea7152313fe0ef0afc883e348",
    "schemas/unified_market_evidence_result.v3.schema.json":
        "2c2092db493d183922b434e99922b2ed4409185ba67985f9b7fbb2639f21eb9b",
    "schemas/unified_market_evidence_audit_package.v3.schema.json":
        "08d90c8756503715a0174deda3eecc484ac21e97f542a23e1e7530a0939abadb",
    "schemas/unified_market_evidence_execution_request.v2.schema.json":
        "b527a40888ec1d17d1bf39684699e0d61701ce8abd71db2d331c2e9e3460b481",
    "scripts/m8r_05b_03/request_projection.py":
        "533de4bc06d51b13c977eb1e5d0b2d9bcc707911de2cea353244b00cd3e10559",
    "scripts/m8r_06_03_production_adapter.py":
        "4553292fc5a4a49b55c3169194ea738bc981d6703a49b03c4bed62a72ca48e65",
}


def sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def require(value: bool, code: str) -> None:
    if not value:
        raise ValueError(code)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
def validate() -> dict:
    def deny(*args, **kwargs):
        raise AssertionError("i3_a4_preflight_network_forbidden")

    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        require(git("branch", "--show-current") == BRANCH, "wrong_preflight_branch")
        require(git("merge-base", "HEAD", BASELINE) == BASELINE, "preflight_not_based_on_post_merge_main")
        require(git("rev-parse", "origin/main") == BASELINE, "origin_main_drift")
        require(git("show", "-s", "--format=%T", BASELINE) == BASELINE_TREE, "baseline_tree_drift")
        require({p: sha(p) for p in ACCEPTED} == ACCEPTED, "accepted_i3_authority_drift")
        require({p: sha(p) for p in PROTECTED} == PROTECTED, "production_or_public_authority_mutated")

        catalog = load("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
        routing = load("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
        metadata = load("config/m8r_06_03_executor_registry_metadata.json")
        disposition = load("docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json")
        require(all(x.get("capability_id") != CAPABILITY for x in catalog["data_need_capabilities"]),
                "i3_catalog_must_remain_absent")
        require(all(x.get("capability_id") != CAPABILITY for x in routing["routes"]),
                "i3_route_must_remain_absent")
        require(all(x.get("executor_id") != EXECUTOR for x in metadata["executors"]),
                "i3_metadata_must_remain_absent")
        require(all(x.get("surface_id") != EXECUTOR for x in disposition["surfaces"]),
                "i3_disposition_must_remain_absent")
        require(not (ROOT / "docs/data_capabilities/phase_i_i3_source_authority.v1.json").exists(),
                "i3_source_authority_must_remain_absent")
        from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
        from server.unified_mcp.tool_contracts import build_tool_specs
        registry = build_production_runtime_adapter_registry()
        require(not registry.routes_for_executor(EXECUTOR), "i3_executor_must_remain_unreachable")
        require(len(registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2,
                "i1_route_regression")
        require(len(registry.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1,
                "i2_route_regression")
        require(len(build_tool_specs()) == 6, "mcp_tool_count_drift")

        request = load("schemas/unified_market_evidence_request.v3.schema.json")
        need_enum = request["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]
        require(CAPABILITY not in need_enum, "i3_public_request_must_remain_absent")
        for rel in (
            "schemas/unified_market_evidence_result.v3.schema.json",
            "schemas/unified_market_evidence_audit_package.v3.schema.json",
            "schemas/unified_market_evidence_execution_request.v2.schema.json",
            "scripts/m8r_05b_03/request_projection.py",
        ):
            require(CAPABILITY.encode() not in (ROOT / rel).read_bytes(), f"i3_public_surface_changed:{rel}")

        contract = load("docs/governance/phase_i/PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_2026-10-03_FROZEN.json")
        twse, tpex = contract["sources"]["TWSE"], contract["sources"]["TPEX"]
        require(twse["parameters"]["date"] == "explicit_Gregorian_YYYYMMDD"
                and twse["automatic_previous_trading_day_fallback"] is False
                and twse["hidden_date_substitution"] is False
                and twse["calendar_today_implies_current"] is False,
                "twse_explicit_date_contract_drift")
        require(twse["transport"]["retry_count"] == 0 and tpex["transport"]["retry_count"] == 0,
                "production_retry_contract_drift")
        require(contract["batching"]["TWSE_max_acquisitions"] == 1
                and contract["batching"]["TPEX_max_acquisitions"] == 1
                and contract["batching"]["mixed_max_unique_acquisitions"] == 2,
                "i3_batching_contract_drift")
        record = load(PREFLIGHT)
        require(record["status"] == "PREFLIGHT_PASS_WITH_EXPLICIT_DESIGN_BLOCKERS",
                "preflight_status_invalid")
        require(record["baseline_main"] == BASELINE and record["baseline_tree"] == BASELINE_TREE,
                "preflight_baseline_invalid")
        require(record["current_state"] == {
            "i3_catalog_present": False,
            "i3_routing_present": False,
            "i3_executor_metadata_present": False,
            "i3_production_registry_routes": 0,
            "i3_active_sources": 0,
            "public_v3_request_supported": False,
            "public_v3_result_audit_supported": False,
            "mcp_tool_count": 6,
        }, "preflight_current_state_invalid")
        require(record["recommended_topology"]["batching_scope"] == "same_market"
                and record["recommended_topology"]["supported_markets"] == ["TWSE", "TPEX"]
                and record["recommended_topology"]["production_retry_count"] == 0
                and record["recommended_topology"]["maximum_unique_market_acquisitions"] == 2,
                "preflight_topology_invalid")
        require(record["blocking_decisions"] == [
            "PUBLIC_V3_INTEGRATION_REQUIRED_BUT_NOT_AUTHORIZED",
            "TWSE_EXPLICIT_SOURCE_DATE_BINDING_POLICY_UNRESOLVED",
            "PRODUCTION_EXECUTOR_TRANSPORT_NOT_IMPLEMENTED",
        ], "preflight_blocker_set_invalid")
        require(record["authorization_boundary"]["production_activation_authorized"] is False
                and record["authorization_boundary"]["source_or_route_activation_authorized"] is False
                and record["authorization_boundary"]["public_v3_integration_authorized"] is False
                and record["authorization_boundary"]["new_market_live_acquisition_authorized"] is False,
                "preflight_authorization_boundary_invalid")
        print("I3-A4 preflight PASS with explicit design blockers; market GETs=0; production remains 0/0; MCP=6")
        return record


if __name__ == "__main__":
    validate()
