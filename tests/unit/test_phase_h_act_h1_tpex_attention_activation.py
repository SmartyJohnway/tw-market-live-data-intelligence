"""H-ACT-H1 selected TPEx attention route activation acceptance (non-live layer)."""
from __future__ import annotations

import copy
import hashlib
import json
import socket
from pathlib import Path

import pytest

from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package
from scripts.m8r_06_03_production_adapter import (
    PHASE_H_H1_EXECUTOR_ID,
    build_production_runtime_adapter_registry,
)
from server.services.unified_mode_a import validate_mode_a_request
from server.services import unified_mode_b2
from server.services.unified_mode_b2 import ModeB2Error, build_mode_b2_authorization
from server.unified_mcp.tool_contracts import PREFERRED_REQUEST_SCHEMA_VERSION, build_tool_specs


ROOT = Path(__file__).resolve().parents[2]
FIXED_TIME = "2026-09-22T00:00:00Z"


class FakeSecurityMaster:
    pointer = {
        "index_path": "data/security_master/runtime_identity_indexes/sealed/index.json",
        "manifest_path": "data/security_master/runtime_identity_indexes/sealed/manifest.json",
        "compact_index_sha256": "a" * 64,
        "compact_manifest_sha256": "b" * 64,
    }


def _request(*, market: str = "TPEX", code: str = "6488", execution_mode: str = "preview") -> dict:
    return {
        "schema_version": "unified_market_evidence_request.v3",
        "request_id": f"h-act-h1-{market.lower()}-{code}",
        "execution_mode": execution_mode,
        "targets": [{"input": code, "market_hint": market}],
        "data_needs": [{"type": "trading_status_context", "priority": "required", "parameters": {}}],
    }


def _preview(request: dict) -> dict:
    validation = validate_mode_a_request(request, allow_fixture_snapshot=True)
    return build_mode_b1_preview_package(
        request,
        validation,
        FakeSecurityMaster(),
        planning_timestamp=FIXED_TIME,
    )


def test_h_act_h1_exact_route_scope_is_preserved_after_v3_promotion() -> None:
    catalog = json.loads(
        (ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8")
    )
    routing = json.loads(
        (ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(encoding="utf-8")
    )
    descriptors = json.loads(
        (ROOT / "config/phase_h_h1_dormant_source_descriptors.json").read_text(encoding="utf-8")
    )
    capability = next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == "trading_status_context")
    route = next(item for item in routing["routes"] if item["capability_id"] == "trading_status_context")
    active_records = [
        item for item in routing["phase_h_source_authority"]["records"]
        if item["activation_state"] == "active"
    ]
    active_descriptors = [
        item for item in descriptors["sources"]
        if item["activation_state"] == "active"
    ]

    assert catalog["contract_versions"]["preferred_request_schema_version"] == "unified_market_evidence_request.v3"
    assert catalog["contract_versions"]["emitted_result_schema_version"] == "unified_market_evidence_result.v3"
    assert catalog["contract_versions"]["v3_runtime_authority_status"] == "v3_preferred_selected_routes_active"
    assert catalog["phase_h_contract"]["active_phase_h_source_count"] == 1
    assert capability["support_status"] == "runtime_executable"
    assert capability["phase_h_activation_state"] == "selected_route_active"

    assert route["routing_status"] == "resolved"
    assert route["supported_markets"] == ["TPEX"]
    assert route["selected_executor_id"] == PHASE_H_H1_EXECUTOR_ID
    assert route["network_required"] is True
    assert route["batching_scope"] == "none"
    assert route["output_evidence_contract"] == "trading_status_context_evidence.v1"

    assert [(item["source_id"], item["runtime_executable"]) for item in active_records] == [
        ("H1-TPEX-ATTENTION-OPENAPI", True)
    ]
    assert [(item["source_id"], item["runtime_executable"]) for item in active_descriptors] == [
        ("H1-TPEX-ATTENTION-OPENAPI", True)
    ]
    assert PREFERRED_REQUEST_SCHEMA_VERSION == "unified_market_evidence_request.v3"
    assert [tool.name for tool in build_tool_specs()] == [
        "market_describe_capabilities",
        "market_validate_request",
        "market_preview_request",
        "market_read_result",
        "market_export_ai_handoff",
        "market_fetch_evidence",
    ]


def test_h_act_h1_preview_executes_only_tpex_selected_route() -> None:
    tpex = _preview(_request())
    assert tpex["validation"]["validation_status"] == "valid"
    assert tpex["validation"]["capability_results"][0]["status"] == "runtime_executable"
    assert tpex["preview"]["status"] == "ready_for_confirmation"
    assert tpex["preview"]["bounds"]["estimated_network_calls"] == 1
    operation = tpex["orchestration_plan"]["operations"][0]
    assert operation["market"] == "TPEX"
    assert operation["executor_id"] == PHASE_H_H1_EXECUTOR_ID
    assert operation["operation_status"] == "executable_pending_approval"
    assert operation["network_required"] is True

    twse = _preview(_request(market="TWSE", code="2330"))
    assert twse["validation"]["validation_status"] == "valid"
    assert twse["preview"]["status"] == "unsupported_capability"
    assert twse["orchestration_plan"]["blocked_operations"][0]["blocking_reason_codes"] == ["unsupported_market"]
    assert twse["orchestration_plan"]["accounting"]["network_request_estimate"] == 0


def test_h_act_h1_registry_materialization_has_no_startup_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "create_connection", lambda *_a, **_k: pytest.fail("startup network attempted"))
    monkeypatch.setattr(
        "scripts.m8r_06_03_production_adapter.urlopen",
        lambda *_a, **_k: pytest.fail("startup network attempted"),
    )
    registry = build_production_runtime_adapter_registry()
    selected = registry.get_route(PHASE_H_H1_EXECUTOR_ID, "trading_status_context", "TPEX")
    assert selected.fake_adapter is False
    assert selected.network_required is True
    assert selected.batch_adapter is None
    assert registry.get_route(PHASE_H_H1_EXECUTOR_ID, "trading_status_context", "TWSE") is None


def test_h_act_h1_workbench_b2_accepts_governed_v3_path_without_enabling_mcp_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request(execution_mode="execute")
    fake_preview = {
        "status": "ready_for_confirmation",
        "internal_execution_reference": {"preview_id": "preview-h-act-h1"},
    }
    fake_plan = {
        "plan_id": "plan-h-act-h1",
        "plan_hash": "a" * 64,
        "operations": [{
            "operation_status": "executable_pending_approval",
            "capability_id": "trading_status_context",
            "market": "TPEX",
            "executor_id": PHASE_H_H1_EXECUTOR_ID,
        }],
        "blocked_operations": [],
        "omitted_optional_capabilities": [],
    }

    monkeypatch.setattr(
        unified_mode_b2,
        "_authorizable_preview",
        lambda _request: (copy.deepcopy(fake_preview), copy.deepcopy(fake_plan)),
    )
    monkeypatch.setattr(
        unified_mode_b2,
        "_materialize_execution_ticket",
        lambda req, plan, decision: {
            "request_schema_version": req["schema_version"],
            "plan_id": plan["plan_id"],
            "decision": decision["decision"],
        },
    )
    result = build_mode_b2_authorization({
        "request": request,
        "confirm_authorization": True,
        "expected_preview_id": "preview-h-act-h1",
        "expected_plan_id": "plan-h-act-h1",
        "expected_plan_hash": "a" * 64,
    })
    assert result == {
        "request_schema_version": "unified_market_evidence_request.v3",
        "plan_id": "plan-h-act-h1",
        "decision": "approved",
    }

    snapshot = {tool.name: tool for tool in build_tool_specs()}
    assert snapshot["market_fetch_evidence"].inputSchema["properties"]["request"]["oneOf"]
    versions = {
        branch["properties"]["schema_version"]["const"]
        for branch in snapshot["market_fetch_evidence"].inputSchema["properties"]["request"]["oneOf"]
    }
    assert versions == {
        "unified_market_evidence_request.v1",
        "unified_market_evidence_request.v2",
        "unified_market_evidence_request.v3",
    }


@pytest.mark.parametrize(
    ("needs", "operation"),
    [
        (
            [{"type": "current_observation", "priority": "required", "parameters": {}}],
            {
                "operation_status": "executable_pending_approval",
                "capability_id": "current_observation",
                "market": "TPEX",
                "executor_id": "m8r_03d_watchlist_controlled_executor_adapter",
            },
        ),
        (
            [{"type": "material_disclosures", "priority": "required", "parameters": {}}],
            {
                "operation_status": "executable_pending_approval",
                "capability_id": "material_disclosures",
                "market": "TPEX",
                "executor_id": "phase_g_official_research_executor",
            },
        ),
        (
            [
                {"type": "trading_status_context", "priority": "required", "parameters": {}},
                {"type": "current_observation", "priority": "optional", "parameters": {}},
            ],
            {
                "operation_status": "executable_pending_approval",
                "capability_id": "trading_status_context",
                "market": "TPEX",
                "executor_id": PHASE_H_H1_EXECUTOR_ID,
            },
        ),
    ],
)
def test_h_act_v3_authorization_reuses_governed_resolved_routes(
    monkeypatch: pytest.MonkeyPatch, needs: list[dict], operation: dict
) -> None:
    request = _request(execution_mode="execute")
    request["data_needs"] = copy.deepcopy(needs)
    promoted_operation = {"operation_id": "op-promoted-v3", **copy.deepcopy(operation)}
    fake_preview = {
        "status": "ready_for_confirmation",
        "internal_execution_reference": {"preview_id": "preview-promoted-v3"},
    }
    fake_plan = {
        "plan_id": "plan-promoted-v3",
        "plan_hash": "b" * 64,
        "operations": [promoted_operation],
        "blocked_operations": [],
        "omitted_optional_capabilities": [],
    }
    captured = {}
    monkeypatch.setattr(
        unified_mode_b2,
        "_authorizable_preview",
        lambda _request: (copy.deepcopy(fake_preview), copy.deepcopy(fake_plan)),
    )
    monkeypatch.setattr(
        unified_mode_b2,
        "_materialize_execution_ticket",
        lambda request, plan, decision: captured.update(
            request=copy.deepcopy(request), plan=copy.deepcopy(plan), decision=copy.deepcopy(decision)
        ) or {
            "control_package_id": "umea-v1-" + "b" * 20,
            "execution_ready": True,
            "network_required": True,
        },
    )
    result = build_mode_b2_authorization({
        "request": request,
        "confirm_authorization": True,
        "expected_preview_id": "preview-promoted-v3",
        "expected_plan_id": "plan-promoted-v3",
        "expected_plan_hash": "b" * 64,
    })
    assert result["execution_ready"] is True
    assert captured["request"]["schema_version"] == "unified_market_evidence_request.v3"
    assert captured["plan"]["operations"][0]["executor_id"] == operation["executor_id"]
    assert captured["decision"]["single_use"] is True
    assert captured["decision"]["maximum_use_count"] == 1


def test_h0h_roll_001_single_route_rollback_model_preserves_artifact_bytes() -> None:
    paths = [
        ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json",
        ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json",
        ROOT / "config/phase_h_h1_dormant_source_descriptors.json",
    ]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    catalog, routing, descriptors = (json.loads(path.read_text(encoding="utf-8")) for path in paths)

    rollback_catalog = copy.deepcopy(catalog)
    rollback_routing = copy.deepcopy(routing)
    rollback_descriptors = copy.deepcopy(descriptors)

    cap = next(item for item in rollback_catalog["data_need_capabilities"] if item["capability_id"] == "trading_status_context")
    cap.update(
        support_status="contract_supported",
        runtime_executable=False,
        phase_h_activation_state="inactive",
    )
    # Source-route rollback is independent from preferred-version rollback.
    # V3 stays preferred while the selected H1 route alone returns to inactive.
    rollback_catalog["phase_h_contract"]["active_phase_h_source_count"] = 0

    route = next(item for item in rollback_routing["routes"] if item["capability_id"] == "trading_status_context")
    route.update(
        supported_markets=["TWSE", "TPEX"],
        runtime_executable=False,
        candidate_executor_ids=[],
        selected_executor_id=None,
        routing_status="plan_only",
        network_required=False,
        estimated_operation_rule="contract-only; no executor invocation",
    )
    route.pop("source_compatibility_key", None)
    rollback_routing["phase_h_source_authority"]["active_source_count"] = 0
    for item in rollback_routing["phase_h_source_authority"]["records"]:
        if item["source_id"] == "H1-TPEX-ATTENTION-OPENAPI":
            item["activation_state"] = "eligible"
            item["runtime_executable"] = False

    rollback_descriptors["status"] = "dormant_fixture_only"
    for item in rollback_descriptors["sources"]:
        if item["source_id"] == "H1-TPEX-ATTENTION-OPENAPI":
            item["activation_state"] = "eligible"
            item["runtime_executable"] = False

    assert rollback_catalog["phase_h_contract"]["active_phase_h_source_count"] == 0
    assert rollback_routing["phase_h_source_authority"]["active_source_count"] == 0
    assert not any(item["activation_state"] == "active" for item in rollback_routing["phase_h_source_authority"]["records"])
    assert not any(item["runtime_executable"] for item in rollback_descriptors["sources"])
    assert rollback_catalog["contract_versions"]["preferred_request_schema_version"] == "unified_market_evidence_request.v3"
    assert rollback_catalog["contract_versions"]["emitted_result_schema_version"] == "unified_market_evidence_result.v3"
    assert rollback_catalog["contract_versions"]["v3_runtime_authority_status"] == "v3_preferred_selected_routes_active"

    request = _request()
    validation = validate_mode_a_request(request, allow_fixture_snapshot=True)
    authorities = {
        "capability_catalog": rollback_catalog,
        "routing_matrix": rollback_routing,
        "handoff_contract": json.loads(
            (ROOT / "docs/data_capabilities/m8r_05b_orchestration_handoff_contract.json").read_text(encoding="utf-8")
        ),
        "executor_disposition": json.loads(
            (ROOT / "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json").read_text(encoding="utf-8")
        ),
        "preview_schema": json.loads(
            (ROOT / "schemas/unified_market_evidence_preview_response.v1.schema.json").read_text(encoding="utf-8")
        ),
    }
    replay = build_mode_b1_preview_package(
        request,
        validation,
        FakeSecurityMaster(),
        planning_timestamp=FIXED_TIME,
        authorities=authorities,
    )
    assert replay["preview"]["status"] == "unsupported_capability"
    assert replay["preview"]["bounds"]["estimated_network_calls"] == 0
    assert replay["orchestration_plan"]["operations"][0]["operation_status"] == "plan_only_not_executable"

    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
