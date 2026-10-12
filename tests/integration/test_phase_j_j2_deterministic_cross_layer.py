"""J2 acceptance over existing governed APIs and stored-result surfaces.

Synthetic source rows enter only through the existing test-only fixture executor.
The test then materializes and reads the actual Mode C Result/Audit/handoff via
the Local Service/Workbench router and actual MCP tool handlers. It never
patches those boundaries or calls an external market source.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.services import unified_mode_a
from server.services import unified_mode_c
from server.unified_mcp.local_service_client import UnifiedLocalServiceClient
from server.unified_mcp.server import dispatch_safe_tool
from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
from scripts.m8r_06_01c2_mode_a_security_master_loader import (
    reset_production_mode_a_security_master_for_tests,
)

from tests.helpers.phase_h_imp_7d_control_package import execute_fixture_package


@pytest.fixture(autouse=True)
def _isolate_process_security_master_cache():
    """Keep acceptance tests from leaking a process-lifetime loader snapshot."""
    reset_production_mode_a_security_master_for_tests()
    yield
    reset_production_mode_a_security_master_for_tests()


def _use_in_process_service_transport(monkeypatch):
    original_async_client = httpx.AsyncClient

    class InProcessServiceClient(original_async_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.ASGITransport(app=app)
            kwargs.setdefault("base_url", "http://127.0.0.1:8000")
            super().__init__(*args, **kwargs)

    monkeypatch.setattr("server.unified_mcp.local_service_client.httpx.AsyncClient", InProcessServiceClient)
    return UnifiedLocalServiceClient("http://127.0.0.1:8000"), build_tool_contract_snapshot()


@pytest.mark.parametrize(
    ("scenario_id", "malformed", "targets", "expected_status", "expected_execution"),
    [
        ("J1-11", False, ("6488",), "full_success", "succeeded"),
        ("J1-20", False, ("6488", "3333"), "partially_failed", "partial_success"),
        ("J1-23", True, ("6488",), "failed", "failed"),
    ],
)
def test_result_audit_workbench_and_mcp_reuse_one_fixture_execution(
    scenario_id, malformed, targets, expected_status, expected_execution,
    tmp_path: Path, monkeypatch,
):
    execution = execute_fixture_package(
        tmp_path / scenario_id, malformed=malformed, target_inputs=targets,
    )
    assert execution["invocations"]["count"] == len(targets)
    control_id = execution["authorization"]["authorization_id"]
    monkeypatch.setattr(unified_mode_c, "CONTROL_ROOT", execution["package"].parent)
    validate_fixture_request = unified_mode_a.validate_mode_a_request
    monkeypatch.setattr(
        unified_mode_c, "validate_mode_a_request",
        lambda request: validate_fixture_request(request, allow_fixture_snapshot=True),
    )

    client = TestClient(app)
    workbench = client.get("/workbench/")
    assert workbench.status_code == 200
    assert 'src="unified-workbench.js"' in workbench.text
    workbench_js = client.get("/workbench/unified-workbench.js")
    assert workbench_js.status_code == 200
    assert "currentModeCResult = data" in workbench_js.text

    service_result_response = client.post(
        "/api/unified/result-package", json={"control_package_id": control_id},
    )
    assert service_result_response.status_code == 200, service_result_response.text
    service_result = service_result_response.json()
    result = service_result["canonical_result"]
    assert result["schema_version"] == "unified_market_evidence_result.v3"
    assert service_result["result_status"] == expected_status
    assert result["status"] == expected_status
    assert service_result["external_market_network_executed"] is False

    service_audit_response = client.get(
        f"/api/unified/result-package/{control_id}/audit.json",
    )
    service_handoff_response = client.get(
        f"/api/unified/result-package/{control_id}/handoff",
    )
    assert service_audit_response.status_code == service_handoff_response.status_code == 200
    audit = service_audit_response.json()
    handoff = service_handoff_response.json()
    assert audit["schema_version"] == "unified_market_evidence_audit_package.v3"
    assert audit["result_id"] == result["result_id"]
    assert audit["audit_package_id"] == service_result["audit_package_id"]
    assert handoff["result_id"] == result["result_id"]
    assert handoff["execution_outcome"] == expected_execution
    assert handoff["additional_market_network_executed"] is False
    lowered_handoff = handoff["ai_ready_markdown"].casefold()
    assert not any(term in lowered_handoff for term in (
        "buy", "sell", "hold", "target price", "bullish", "bearish",
        "買進", "賣出", "持有", "目標價", "看多", "看空",
    ))
    assert result["targets"][0]["canonical_identity"]["canonical_target_id"] == "TPEX:6488"
    if scenario_id == "J1-20":
        assert handoff["execution_outcome"] == "partial_success"
        assert len(execution["outcomes"]) == 2
        assert {outcome["status"] for outcome in execution["outcomes"]} == {"succeeded", "failed"}
    if scenario_id == "J1-23":
        assert execution["outcomes"][0]["error_code"] == "source_failed"

    # Run the actual MCP dispatcher and Local Service client against the actual
    # FastAPI app through an in-process ASGI transport. Only the transport is
    # substituted; neither the handler nor service route is mocked.
    mcp_client, snapshot = _use_in_process_service_transport(monkeypatch)
    assert [tool.name for tool in snapshot.tools] == [
        "market_describe_capabilities", "market_validate_request", "market_preview_request",
        "market_read_result", "market_export_ai_handoff", "market_fetch_evidence",
    ]
    async def read_and_export():
        read = await dispatch_safe_tool(
            "market_read_result", {"control_package_id": control_id},
            client=mcp_client, tool_contract_snapshot=snapshot,
        )
        export = await dispatch_safe_tool(
            "market_export_ai_handoff", {"control_package_id": control_id},
            client=mcp_client, tool_contract_snapshot=snapshot,
        )
        return read, export

    mcp_read, mcp_export = asyncio.run(read_and_export())
    assert not mcp_read.isError and not mcp_export.isError
    assert mcp_read.structuredContent["canonical_result"]["result_id"] == result["result_id"]
    assert mcp_read.structuredContent["result_status"] == expected_status
    assert mcp_export.structuredContent["result_id"] == result["result_id"]
    assert mcp_export.structuredContent["execution_outcome"] == expected_execution
    assert mcp_export.structuredContent["ai_ready_markdown"] == handoff["ai_ready_markdown"]
    assert execution["invocations"]["count"] == len(targets)

    capture_path = os.environ.get("PHASE_J_J2_RUNTIME_CAPTURE")
    if capture_path:
        record = {
            "scenario_id": scenario_id,
            "control_package_id": control_id,
            "result_id": result["result_id"],
            "audit_package_id": audit["audit_package_id"],
            "handoff_result_id": handoff["result_id"],
            "execution_outcome": handoff["execution_outcome"],
            "additional_market_network_executed": handoff["additional_market_network_executed"],
        }
        with Path(capture_path).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")


def test_j1_10_financial_statements_fail_closed_through_local_service_and_mcp(monkeypatch):
    request = {
        "schema_version": "unified_market_evidence_request.v3",
        "request_id": "j2-j1-10-financial-statements",
        "targets": [{"input": "TWSE:2330", "market_hint": "TWSE", "resolution_requirement": "exact"}],
        "data_needs": [{"type": "financial_statements", "priority": "required", "parameters": {}}],
        "execution_mode": "preview",
    }
    client = TestClient(app)
    response = client.post("/api/unified/validate-request", json={"request": request})
    assert response.status_code == 200
    validation = response.json()
    assert validation["validation_status"] == "invalid"
    assert any(issue["code"] == "REQUEST_SCHEMA_INVALID" for issue in validation["blocking_issues"])
    assert validation["limits"]["operation_count_computed"] is False

    workbench = client.get("/workbench/")
    workbench_js = client.get("/workbench/unified-workbench.js")
    assert workbench.status_code == workbench_js.status_code == 200
    assert "renderValidationResult(data)" in workbench_js.text
    assert "res.blocking_issues" in workbench_js.text

    mcp_client, snapshot = _use_in_process_service_transport(monkeypatch)

    async def validate_via_mcp():
        return await dispatch_safe_tool(
            "market_validate_request", {"request": request},
            client=mcp_client, tool_contract_snapshot=snapshot,
        )

    mcp_validation = asyncio.run(validate_via_mcp())
    # The unchanged MCP input schema rejects this unsupported request before
    # reaching the Local Service. This is an observed bounded refusal, not a
    # fabricated service validation result.
    assert mcp_validation.isError
    assert mcp_validation.structuredContent == {"error": "invalid_tool_arguments"}
