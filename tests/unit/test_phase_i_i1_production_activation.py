from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import zipfile

from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package, load_planning_authorities
from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
from scripts.validate_phase_i_i1_production_activation import validate
from server.services.phase_i_i1_production_candidate import (
    CAPABILITY_ID,
    EXECUTOR_ID,
    production_batch_operation_adapter_candidate,
)
from server.services.unified_mode_a import validate_mode_a_request
from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
from server.unified_mcp.server import build_unified_market_evidence_mcp_server
from server.services.unified_local_service import describe_capabilities

ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-09-30T02:00:00Z"
PHASE_H_ACTIVE = {"H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI", "H3-TWSE-DEFAULT-BOUNDED", "H2-TWSE-EXRIGHT-PRE-OPENAPI"}
I1_ACTIVE = {
    "I1-TWSE-FMTQIK-OPENAPI",
    "I1-TWSE-BREADTH-TWTAZU-OPENAPI",
    "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI",
}


class FixtureSecurityMaster:
    pointer = {
        "index_path": "data/security_master/runtime_identity_indexes/fixture/index.json",
        "manifest_path": "data/security_master/runtime_identity_indexes/fixture/manifest.json",
        "compact_index_sha256": "a" * 64,
        "compact_manifest_sha256": "b" * 64,
    }


def _read(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _request(targets):
    return {
        "schema_version": "unified_market_evidence_request.v3",
        "request_id": "i1-activation-offline-preview",
        "execution_mode": "preview",
        "targets": [
            {"input": code, "market_hint": market, "resolution_requirement": "exact"}
            for market, code in targets
        ],
        "data_needs": [{"type": CAPABILITY_ID, "priority": "required", "parameters": {}}],
    }


def _preview(targets, authorities=None):
    request = _request(targets)
    validation = validate_mode_a_request(request, allow_fixture_snapshot=True)
    return build_mode_b1_preview_package(
        request,
        validation,
        FixtureSecurityMaster(),
        planning_timestamp=NOW,
        authorities=authorities or load_planning_authorities(request["schema_version"]),
    )


def test_activation_validator_and_normal_registry_are_exactly_two_bounded_routes(monkeypatch):
    calls = []
    import server.services.phase_i_i1_production_candidate as candidate

    monkeypatch.setattr(candidate, "_http_transport", lambda *args, **kwargs: calls.append((args, kwargs)))
    validate()
    # These are construction and passive-read paths only: no startup, describe,
    # request validation, or preview path is allowed to acquire I1 sources.
    build_unified_market_evidence_mcp_server(
        client=object(), tool_contract_snapshot=build_tool_contract_snapshot()
    )
    description = describe_capabilities()
    assert any(item.get("capability_id") == CAPABILITY_ID for item in description["capabilities"])
    request = _request([("TWSE", "2330")])
    assert validate_mode_a_request(request, allow_fixture_snapshot=True)["validation_status"] == "valid"
    registry = build_production_runtime_adapter_registry()
    routes = registry.routes_for_executor(EXECUTOR_ID)
    assert len(routes) == 2
    assert {route.market for route in routes} == {"TWSE", "TPEX"}
    assert all(route.network_required and route.timeout_seconds == 15 and route.batch_adapter is production_batch_operation_adapter_candidate for route in routes)
    assert calls == []
    assert len(build_tool_contract_snapshot().tools) == 6


def test_normal_v3_preview_routes_twse_and_tpex_without_authorization_or_network(monkeypatch):
    import server.services.phase_i_i1_production_candidate as candidate

    calls = []
    monkeypatch.setattr(candidate, "_http_transport", lambda *args, **kwargs: calls.append((args, kwargs)))
    for market, code in (("TWSE", "2330"), ("TPEX", "6488")):
        result = _preview([(market, code)])
        assert result["validation"]["validation_status"] == "valid"
        assert result["validation"]["capability_results"][0]["status"] == "runtime_executable"
        assert result["preview"]["status"] == "ready_for_confirmation"
        assert result["authorization_created"] is False
        assert result["network_executed"] is False
        operation = result["orchestration_plan"]["operations"][0]
        assert operation["operation_status"] == "executable_pending_approval"
        assert operation["executor_id"] == EXECUTOR_ID
        assert operation["market"] == market
        assert operation["network_required"] is True
    assert calls == []


def test_normal_planner_groups_same_market_and_mixed_market_targets():
    twse = _preview([("TWSE", "2330"), ("TWSE", "2222")])
    assert len(twse["orchestration_plan"]["operations"]) == 2
    assert len(twse["orchestration_plan"]["batch_groups"]) == 1
    assert twse["orchestration_plan"]["batch_groups"][0]["market"] == "TWSE"

    tpex = _preview([("TPEX", "6488"), ("TPEX", "3333")])
    assert len(tpex["orchestration_plan"]["operations"]) == 2
    assert len(tpex["orchestration_plan"]["batch_groups"]) == 1
    assert tpex["orchestration_plan"]["batch_groups"][0]["market"] == "TPEX"

    mixed = _preview([("TWSE", "2330"), ("TWSE", "2222"), ("TPEX", "6488"), ("TPEX", "3333")])
    assert len(mixed["orchestration_plan"]["operations"]) == 4
    groups = mixed["orchestration_plan"]["batch_groups"]
    assert len(groups) == 2
    assert {group["market"] for group in groups} == {"TWSE", "TPEX"}
    assert all(len(group["operation_ids"]) == 2 for group in groups)
    assert all(operation["network_required"] is True for operation in mixed["orchestration_plan"]["operations"])


def test_i1_roll_001_in_memory_rollback_preserves_other_authorities_and_evidence():
    catalog = _read("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _read("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    source_authority = _read("docs/data_capabilities/phase_i_i1_source_authority.v1.json")
    descriptors = _read("config/phase_i_i1_dormant_source_descriptors.json")
    disposition = _read("docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json")
    registry_metadata = _read("config/m8r_06_03_executor_registry_metadata.json")
    active_registry = build_production_runtime_adapter_registry()

    cap_before = copy.deepcopy(next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == CAPABILITY_ID))
    route_before = copy.deepcopy(next(item for item in routing["routes"] if item["capability_id"] == CAPABILITY_ID))
    phase_h_before = copy.deepcopy(routing["phase_h_source_authority"])
    phase_h_active_before = {item["source_id"] for item in phase_h_before["records"] if item["activation_state"] == "active" and item["runtime_executable"] is True}
    h1_before = copy.deepcopy(next(item for item in routing["routes"] if item["capability_id"] == "trading_status_context"))
    h3_before = copy.deepcopy(next(item for item in routing["routes"] if item["capability_id"] == "recent_performance"))
    h2_before = copy.deepcopy([item for item in routing["routes"] if item["capability_id"] == "corporate_action_context"])

    ledger = _read("docs/governance/phase_i/PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-09-30.json")
    zip_path = ROOT / ledger["projection"]["governed_evidence_package_path"]
    evidence_before = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    with zipfile.ZipFile(zip_path) as archive:
        result_sha_before = hashlib.sha256(archive.read(ledger["projection"]["result_v3"]["archive_member"])).hexdigest()
        audit_sha_before = hashlib.sha256(archive.read(ledger["projection"]["audit_v3"]["archive_member"])).hexdigest()

    rolled_catalog = copy.deepcopy(catalog)
    rolled_routing = copy.deepcopy(routing)
    rolled_source_authority = copy.deepcopy(source_authority)
    rolled_descriptors = copy.deepcopy(descriptors)
    rolled_disposition = copy.deepcopy(disposition)
    rolled_registry_metadata = copy.deepcopy(registry_metadata)
    rolled_cap = next(item for item in rolled_catalog["data_need_capabilities"] if item["capability_id"] == CAPABILITY_ID)
    rolled_cap.update(support_status="contract_supported", runtime_executable=False, phase_i_activation_state="implementation_candidate_inactive")
    rolled_route = next(item for item in rolled_routing["routes"] if item["capability_id"] == CAPABILITY_ID)
    rolled_route.update(runtime_executable=False, candidate_executor_ids=[], selected_executor_id=None, routing_status="plan_only", network_required=False, blocking_reasons=["I1-ROLL-001 simulated dormant rollback"])
    rolled_source_authority.update(active_source_count=0, runtime_executable=False)
    for record in rolled_source_authority["records"]:
        record.update(activation_state="inactive", runtime_executable=False)
    rolled_descriptors.update(runtime_executable=False, network_enabled=False)
    for source in rolled_descriptors["sources"]:
        source.update(activation_state="inactive", runtime_executable=False)
    rolled_disposition["surfaces"] = [item for item in rolled_disposition["surfaces"] if item.get("surface_id") != EXECUTOR_ID]
    rolled_registry_metadata["executors"] = [item for item in rolled_registry_metadata["executors"] if item.get("capability_id") != CAPABILITY_ID]

    assert (cap_before["support_status"], cap_before["runtime_executable"], cap_before["phase_i_activation_state"]) == ("runtime_executable", True, "selected_route_active")
    assert (route_before["routing_status"], route_before["runtime_executable"], route_before["selected_executor_id"]) == ("resolved", True, EXECUTOR_ID)
    assert rolled_cap["support_status"] == "contract_supported" and rolled_cap["runtime_executable"] is False
    assert rolled_route["routing_status"] == "plan_only" and rolled_route["selected_executor_id"] is None and rolled_route["network_required"] is False
    assert rolled_source_authority["active_source_count"] == 0 and rolled_source_authority["runtime_executable"] is False
    assert all(item["activation_state"] == "inactive" and item["runtime_executable"] is False for item in rolled_source_authority["records"])
    assert rolled_descriptors["network_enabled"] is False
    assert not any(item.get("capability_id") == CAPABILITY_ID for item in rolled_registry_metadata["executors"])

    rollback_registry = RuntimeAdapterRegistry([item for item in active_registry._by_route.values() if item.executor_id != EXECUTOR_ID])
    assert rollback_registry.routes_for_executor(EXECUTOR_ID) == ()
    assert rollback_registry.get_route(h1_before["selected_executor_id"], "trading_status_context", "TPEX") == active_registry.get_route(h1_before["selected_executor_id"], "trading_status_context", "TPEX")
    assert rollback_registry.get_route(h3_before["selected_executor_id"], "recent_performance", "TWSE") == active_registry.get_route(h3_before["selected_executor_id"], "recent_performance", "TWSE")

    authorities = load_planning_authorities("unified_market_evidence_request.v3")
    authorities["capability_catalog"] = rolled_catalog
    authorities["routing_matrix"] = rolled_routing
    authorities["executor_disposition"] = rolled_disposition
    for market, code in (("TWSE", "2330"), ("TPEX", "6488")):
        preview = _preview([(market, code)], authorities)
        assert preview["preview"]["status"] != "ready_for_confirmation"
        assert preview["preview"]["bounds"]["estimated_network_calls"] == 0
        assert preview["authorization_created"] is False and preview["network_executed"] is False
        plan = preview["orchestration_plan"]
        assert all(item["operation_status"] != "executable_pending_approval" for item in plan["operations"])
        assert all(item.get("executor_id") is None for item in plan["operations"])
        assert all(item.get("network_required") is False for item in plan["operations"])
    assert phase_h_before["active_source_count"] == 5 and phase_h_active_before == PHASE_H_ACTIVE
    assert next(item for item in rolled_routing["routes"] if item["capability_id"] == "trading_status_context") == h1_before
    assert next(item for item in rolled_routing["routes"] if item["capability_id"] == "recent_performance") == h3_before
    assert [item for item in rolled_routing["routes"] if item["capability_id"] == "corporate_action_context"] == h2_before
    assert {item["source_id"] for item in rolled_routing["phase_h_source_authority"]["records"] if item["activation_state"] == "active" and item["runtime_executable"] is True} == PHASE_H_ACTIVE
    assert len(build_tool_contract_snapshot().tools) == 6
    assert hashlib.sha256(zip_path.read_bytes()).hexdigest() == evidence_before
    with zipfile.ZipFile(zip_path) as archive:
        assert hashlib.sha256(archive.read(ledger["projection"]["result_v3"]["archive_member"])).hexdigest() == result_sha_before
        assert hashlib.sha256(archive.read(ledger["projection"]["audit_v3"]["archive_member"])).hexdigest() == audit_sha_before
