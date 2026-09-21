"""H-IMP-0: passive V3 validation and preview, without Phase H execution."""
from __future__ import annotations

import copy
import asyncio
import socket
import urllib.request

import pytest
import json
from pathlib import Path

from server.services.unified_mode_a import validate_mode_a_request
from server.services.unified_mode_b2 import ModeB2Error, build_local_operator_execution_ticket, build_mode_b2_authorization
from server.services.unified_local_operator_action import LocalOperatorActionError, fetch_market_evidence
from server.unified_mcp import tool_contracts
from server.unified_mcp.server import dispatch_safe_tool
from server.unified_mcp.tool_contracts import PREFERRED_REQUEST_SCHEMA_VERSION, ToolContractError, build_tool_contract_snapshot
from scripts.m8r_05b_01.models import PlanningError
from scripts.m8r_05b_01.planner import ALLOWED_CATALOG_ROUTING_VERSION_PAIRS, build_plan
from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package, build_planning_bindings, load_planning_authorities
from scripts.m8r_05a_f3.request_intake import _catalog_valid


FIXED_TIME = "2026-09-21T00:00:00Z"
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TOOLS = (
    "market_describe_capabilities",
    "market_validate_request",
    "market_preview_request",
    "market_read_result",
    "market_export_ai_handoff",
    "market_fetch_evidence",
)


class FakeSecurityMaster:
    pointer = {
        "index_path": "data/security_master/runtime_identity_indexes/sealed/index.json",
        "manifest_path": "data/security_master/runtime_identity_indexes/sealed/manifest.json",
        "compact_index_sha256": "a" * 64,
        "compact_manifest_sha256": "b" * 64,
    }


def request(version="unified_market_evidence_request.v3", needs=None, *, execution_mode="preview"):
    return {
        "schema_version": version,
        "request_id": "phase-h-imp-0",
        "execution_mode": execution_mode,
        "targets": [{"input": "2330", "market_hint": "TWSE"}],
        "data_needs": needs or [{"type": "current_observation", "priority": "required"}],
    }


def validation(req):
    return validate_mode_a_request(req, allow_fixture_snapshot=True)


def preview(req):
    return build_mode_b1_preview_package(
        req, validation(req), FakeSecurityMaster(), planning_timestamp=FIXED_TIME
    )


def test_explicit_v1_v2_v3_mode_a_dispatch_and_unknown_fail_closed():
    for version in ("unified_market_evidence_request.v1", "unified_market_evidence_request.v2"):
        assert validation(request(version))["validation_status"] == "valid"
    v3 = validation(request())
    assert v3["validation_status"] == "valid"
    assert v3["capability_results"][0]["capability_id"] == "current_observation"
    with pytest.raises(ValueError, match="unsupported_request_schema_version"):
        validation(request("unified_market_evidence_request.v4"))


def test_v3_unknown_data_need_and_schema_identity_mismatch_fail_closed(monkeypatch):
    malformed = request(needs=[{"type": "not_a_governed_capability", "priority": "required"}])
    assert validation(malformed)["validation_status"] == "invalid"
    monkeypatch.setitem(
        tool_contracts.REQUEST_SCHEMA_IDS,
        "unified_market_evidence_request.v3",
        "urn:tw-market-live-data-intelligence:unified_market_evidence_request:wrong",
    )
    with pytest.raises(ToolContractError, match="canonical_request_schema_identity_mismatch"):
        tool_contracts.load_unified_request_schema("unified_market_evidence_request.v3")


def test_frozen_catalog_v3_metadata_is_exact_and_mutations_reject():
    catalog = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8"))
    assert _catalog_valid(catalog)
    missing = copy.deepcopy(catalog)
    del missing["contract_versions"]["future_candidate_result_schema_version"]
    assert not _catalog_valid(missing)
    wrong = copy.deepcopy(catalog)
    wrong["contract_versions"]["future_candidate_result_schema_version"] = "unified_market_evidence_result.v2"
    assert not _catalog_valid(wrong)
    preferred_v3 = copy.deepcopy(catalog)
    preferred_v3["contract_versions"]["preferred_request_schema_version"] = "unified_market_evidence_request.v3"
    assert not _catalog_valid(preferred_v3)
    active = copy.deepcopy(catalog)
    active["contract_versions"]["v3_runtime_authority_status"] = "active"
    assert not _catalog_valid(active)


def test_mcp_passive_envelopes_accept_v3_but_execution_envelope_does_not():
    snapshot = build_tool_contract_snapshot()
    v3 = request()
    assert tuple(tool.name for tool in snapshot.tools) == EXPECTED_TOOLS
    assert PREFERRED_REQUEST_SCHEMA_VERSION == "unified_market_evidence_request.v2"
    assert snapshot.validate_arguments("market_validate_request", {"request": v3})
    assert snapshot.validate_arguments("market_preview_request", {"request": v3})
    assert not snapshot.validate_arguments("market_fetch_evidence", {"request": v3})


def test_mcp_dispatch_v3_validate_preview_and_fetch_barrier():
    class FakeClient:
        def __init__(self):
            self.validate_count = 0
            self.preview_count = 0
            self.fetch_count = 0

        async def validate_request(self, _args):
            self.validate_count += 1
            return {"validation_status": "valid"}

        async def preview_request(self, _args):
            self.preview_count += 1
            return {"status": "unsupported_capability"}

        async def fetch_evidence(self, _args):
            self.fetch_count += 1
            return {"unexpected": True}

    async def exercise():
        client = FakeClient()
        snapshot = build_tool_contract_snapshot()
        v3 = request()
        validated = await dispatch_safe_tool("market_validate_request", {"request": v3}, client=client, tool_contract_snapshot=snapshot)
        previewed = await dispatch_safe_tool("market_preview_request", {"request": v3}, client=client, tool_contract_snapshot=snapshot)
        rejected = await dispatch_safe_tool("market_fetch_evidence", {"request": request(execution_mode="execute")}, client=client, tool_contract_snapshot=snapshot)
        return client, validated, previewed, rejected

    client, validated, previewed, rejected = asyncio.run(exercise())
    assert validated.isError is False and client.validate_count == 1
    assert previewed.isError is False and client.preview_count == 1
    assert rejected.isError is True and client.fetch_count == 0


@pytest.mark.parametrize("capability", ["trading_status_context", "corporate_action_context"])
def test_v3_phase_h_capabilities_are_recognized_but_plan_only(capability):
    req = request(needs=[{"type": capability, "priority": "required", "parameters": {}}])
    result = preview(req)
    assert result["validation"]["validation_status"] == "valid"
    assert result["validation"]["capability_results"][0]["status"] == "contract_supported"
    assert result["preview"]["status"] == "unsupported_capability"
    operation = result["orchestration_plan"]["operations"][0]
    assert operation["operation_status"] == "plan_only_not_executable"
    assert operation["executor_id"] is None
    assert operation["network_required"] is False
    assert result["authorization_created"] is False
    assert result["network_executed"] is False


@pytest.mark.parametrize("lookback", [1, 5, 20])
def test_v3_h3_is_recognized_but_plan_only(lookback):
    req = request(needs=[{"type": "recent_performance", "priority": "required", "parameters": {"lookback_trading_days": lookback}}])
    result = preview(req)
    assert result["validation"]["capability_results"][0]["status"] == "contract_supported"
    assert result["orchestration_plan"]["plan_status"] in {"blocked", "plan_only_not_executable"}
    assert result["orchestration_plan"]["blocked_operations"][0]["capability_id"] == "recent_performance"


@pytest.mark.parametrize("parameters", [{"lookback_trading_days": 0}, {"lookback_trading_days": 21}, {}])
def test_v3_h3_invalid_lookback_remains_rejected(parameters):
    req = request(needs=[{"type": "recent_performance", "priority": "required", "parameters": parameters}])
    assert validation(req)["validation_status"] == "invalid"


def test_v3_mixed_preview_keeps_existing_executable_capability_and_phase_h_plan_only():
    req = request(needs=[
        {"type": "current_observation", "priority": "required"},
        {"type": "trading_status_context", "priority": "optional", "parameters": {}},
    ])
    result = preview(req)
    operations = {item["capability_id"]: item for item in result["orchestration_plan"]["operations"]}
    assert result["preview"]["status"] == "partial_possible"
    assert operations["current_observation"]["operation_status"] == "executable_pending_approval"
    assert operations["trading_status_context"]["operation_status"] == "plan_only_not_executable"
    assert operations["trading_status_context"]["executor_id"] is None


def test_planner_allows_only_matching_v2_or_v3_catalog_routing_pairs():
    assert ("unified_market_evidence_capability_catalog.v2", "m8r_05b_capability_to_executor_routing_matrix.v2") in ALLOWED_CATALOG_ROUTING_VERSION_PAIRS
    assert ("unified_market_evidence_capability_catalog.v3", "m8r_05b_capability_to_executor_routing_matrix.v3") in ALLOWED_CATALOG_ROUTING_VERSION_PAIRS
    req = request()
    f3 = validation(req)
    authorities = load_planning_authorities("unified_market_evidence_request.v3")
    bindings = build_planning_bindings(req, f3, FakeSecurityMaster(), capability_catalog=authorities["capability_catalog"], routing_matrix=authorities["routing_matrix"], handoff_contract=authorities["handoff_contract"])
    mixed = copy.deepcopy(authorities)
    mixed["routing_matrix"] = load_planning_authorities("unified_market_evidence_request.v2")["routing_matrix"]
    with pytest.raises(PlanningError, match="unsupported_contract_version"):
        build_plan(f3, capability_catalog=mixed["capability_catalog"], routing_matrix=mixed["routing_matrix"], handoff_contract=mixed["handoff_contract"], executor_disposition=mixed["executor_disposition"], input_bindings=bindings, planning_timestamp=FIXED_TIME)


def test_v3_execution_is_rejected_at_b2_and_local_operator_boundaries():
    execute_v3 = request(execution_mode="execute")
    with pytest.raises(ModeB2Error, match="phase_h_v3_execution_inactive"):
        build_local_operator_execution_ticket(execute_v3)
    with pytest.raises(ModeB2Error, match="phase_h_v3_execution_inactive"):
        build_mode_b2_authorization({"request": execute_v3, "confirm_authorization": True})
    with pytest.raises(LocalOperatorActionError, match="phase_h_v3_execution_inactive"):
        fetch_market_evidence({"request": execute_v3})


def test_v3_validation_and_preview_are_network_free(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("external network is forbidden in H-IMP-0")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    result = preview(request(needs=[{"type": "trading_status_context", "priority": "required", "parameters": {}}]))
    assert result["network_executed"] is False
    assert result["authorization_created"] is False
