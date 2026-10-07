"""Offline validation of the Owner-authorized I3-A4 active runtime state."""
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
CAPABILITY = "cash_institutional_flow_context"
EXECUTOR = "phase_i_i3_cash_institutional_flow_context_executor"
ACTIVATION = "docs/governance/phase_i/PHASE_I_I3_A4_BOUNDED_PRODUCTION_ACTIVATION_2026-10-05.json"
PHASE_J_A2_6_BASELINE = "04af1d3ea63b058317facb8763a524c453bb9093"


def _json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def _historical_git_sha(relative: str, commit: str) -> str:
    """Hash an immutable prior authority snapshot without comparing it to current files."""
    payload = subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=ROOT)
    return hashlib.sha256(payload).hexdigest()


def validate() -> dict:
    def denied(*_args, **_kwargs):
        raise AssertionError("i3_a4_market_network_forbidden")

    with patch("socket.socket.connect", denied), patch("socket.create_connection", denied):
        record = _json(ACTIVATION)
        assert record["owner_authority"] == "USER_CHAT_2026-10-05_PHASE_I_I3_A4_BOUNDED_PRODUCTION_ACTIVATION_AUTHORIZATION"
        assert record["status"] == "I3_A4_BOUNDED_PRODUCTION_ACTIVATION_IMPLEMENTED_PENDING_INDEPENDENT_ACCEPTANCE"
        assert record["market_live_acquisition_authorized"] is False
        assert record["market_live_acquisition_performed"] is False
        assert record["merge_authorized"] is False and record["owner_final_A4_acceptance_recorded"] is False

        catalog = _json("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
        cap = [item for item in catalog["data_need_capabilities"] if item.get("capability_id") == CAPABILITY]
        assert len(cap) == 1 and cap[0]["support_status"] == "runtime_executable"
        assert cap[0]["runtime_executable"] is True and cap[0]["phase_i_activation_state"] == "selected_route_active"
        assert cap[0]["supported_markets"] == ["TWSE", "TPEX"]
        assert cap[0]["instrument_scope"] == {"instrument_families": ["company_share"], "instrument_types": ["common_share"]}
        assert cap[0]["output_evidence_contract"] == "cash_institutional_flow_context_evidence.v2"

        routing = _json("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
        routes = [item for item in routing["routes"] if item.get("capability_id") == CAPABILITY]
        assert len(routes) == 1 and routes[0]["runtime_executable"] is True
        assert routes[0]["routing_status"] == "resolved" and routes[0]["selected_executor_id"] == EXECUTOR
        assert routes[0]["supported_markets"] == ["TWSE", "TPEX"] and routes[0]["batching_scope"] == "same_market"
        assert routes[0]["output_evidence_contract"] == "cash_institutional_flow_context_evidence.v2"

        sources = _json("docs/data_capabilities/phase_i_i3_source_authority.v1.json")
        assert sources["activation_state"] == "active" and sources["runtime_executable"] is True
        assert sources["active_source_count"] == 2 and len(sources["sources"]) == 2
        assert {s["market"] for s in sources["sources"]} == {"TWSE", "TPEX"}
        policies = {s["market"]: s for s in sources["sources"]}
        assert policies["TWSE"]["source_id"] == "I3-TWSE-T86-INSTITUTIONAL-TRADING"
        assert policies["TWSE"]["endpoint"] == "https://www.twse.com.tw/rwd/zh/fund/T86"
        assert policies["TWSE"]["query_contract"] == {
            "date": "resolved_source_trade_date_as_YYYYMMDD", "selectType": "ALLBUT0999", "response": "json"}
        assert policies["TWSE"]["tls_policy"] == "compatibility_verified_tls"
        assert policies["TPEX"]["source_id"] == "I3-TPEX-3INSTI-DAILY-TRADING"
        assert policies["TPEX"]["endpoint"] == "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading"
        assert policies["TPEX"]["query_contract"]["requested_source_date_parameter"] is False
        assert policies["TPEX"]["tls_policy"] == "strict_verified_tls"
        assert all(s["activation_state"] == "active" and s["runtime_executable"] is True
                   and s["retry_count"] == 0 and s["maximum_dispatches_per_authorized_execution"] == 1
                   and s["timeout_seconds"] == 30 and s["maximum_response_bytes"] == 4194304
                   and s["accepted_mime"] == ["application/json"]
                   and s["redirect_policy"] == "reject" and s["fallback"] is False
                   and s["raw_persistence"] is False for s in sources["sources"])
        assert sources["authorization_boundary"]["production_activation_authorized"] is True
        assert sources["authorization_boundary"]["live_acquisition_authorized"] is False
        # This A4 record predates the separately authorized Phase J A2.6
        # additions to shared Phase-H catalog/routing/registry surfaces. Verify
        # its stored hashes against the then-current committed snapshot instead
        # of asserting that mutable current paths retain those historical bytes.
        historical_authorities = (
            ("docs/data_capabilities/phase_i_i3_source_authority.v1.json", "source_authority_sha256"),
            ("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json", "catalog_authority_sha256"),
            ("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json", "routing_authority_sha256"),
            ("config/m8r_06_03_executor_registry_metadata.json", "executor_metadata_sha256"),
            ("docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json", "orchestrator_disposition_sha256"),
        )
        for path, hash_key in historical_authorities:
            assert _historical_git_sha(path, PHASE_J_A2_6_BASELINE) == record["active_authority"][hash_key]

        from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
        from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
        from server.unified_mcp.tool_contracts import build_tool_specs
        metadata_raw = _json("config/m8r_06_03_executor_registry_metadata.json")
        metadata = ExecutorMetadataRegistry.from_json(metadata_raw)
        assert len(metadata.routes_for_executor(EXECUTOR)) == 2
        assert all(x.expected_evidence_contract == "cash_institutional_flow_context_evidence.v2"
                   and x.supported_security_types == ("equity",) and x.timeout_seconds == 30
                   and x.maximum_result_items == 50 for x in metadata.routes_for_executor(EXECUTOR))
        active = build_production_runtime_adapter_registry()
        registrations = active.routes_for_executor(EXECUTOR)
        assert len(registrations) == 2 and {x.market for x in registrations} == {"TWSE", "TPEX"}
        assert all(active.get_route(EXECUTOR, CAPABILITY, market) is not None for market in ("TWSE", "TPEX"))
        assert len(active.routes_for_executor("phase_i_i1_market_state_executor")) == 2
        assert len(active.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1
        assert len(build_tool_specs()) == 6

        request_schema = _json("schemas/unified_market_evidence_request.v3.schema.json")
        assert CAPABILITY in request_schema["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]
        result_schema = _json("schemas/unified_market_evidence_result.v3.schema.json")
        assert CAPABILITY in result_schema["definitions"]
        audit_schema = _json("schemas/unified_market_evidence_audit_package.v3.schema.json")
        refs = audit_schema["properties"]["phase_i_evidence"]["properties"]["evidence_artifact_references"]["items"]["oneOf"]
        assert any(ref.get("properties", {}).get("schema_version", {}).get("const") ==
                   "cash_institutional_flow_context_evidence.v2" for ref in refs)

        v1_sha = _sha("schemas/cash_institutional_flow_context_evidence.v1.schema.json")
        assert v1_sha == "3be9a0ca3cf0e0bb5badb427231d47ce86fdb604ae28cb31582b0f9612c76f7c"
        v2_sha = _sha("schemas/cash_institutional_flow_context_evidence.v2.schema.json")
        assert v2_sha == "caaf9deb00b6d711b92c8e9abc64e80c73be7f1186a414bd09cf7ce4ec716756"

        from scripts.phase_i_i3_a4_rollback_proof import prove_i3_rollback
        rollback = prove_i3_rollback()
        assert rollback["status"] == "PASS" and rollback["i3_active_sources"] == 0
        assert rollback["i3_routes"] == 0 and rollback["i3_executor_reachable"] is False
        assert rollback["i3_public_v3_support"] is False
        assert (rollback["i1_active_sources"], rollback["i1_routes"], rollback["i2_active_sources"],
                rollback["i2_routes"], rollback["mcp_tool_count"]) == (3, 2, 1, 1, 6)

        from scripts.phase_i_i3_a4_compat import assert_non_i3_authority_unchanged
        for path in (
            "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json",
            "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json",
            "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json",
            "config/m8r_06_03_executor_registry_metadata.json",
        ):
            assert_non_i3_authority_unchanged(path)
        return {"status": "PASS", "i3_active_sources": 2, "i3_logical_routes": 1,
                "i3_runtime_market_routes": 2, "i3_executor_reachable": True,
                "i3_public_v3_active": True, "production_evidence_contract": "cash_institutional_flow_context_evidence.v2",
                "rollback": "PASS", "i1_sources_routes": "3/2", "i2_sources_routes": "1/1",
                "mcp_tool_count": 6, "market_gets": 0, "merge_authorized": False}


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
