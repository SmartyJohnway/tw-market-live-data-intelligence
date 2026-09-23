"""H-ACT-V3 preferred-authority promotion acceptance.

These tests are zero-network. Route-level and selected-product bounded-live
evidence remain governed by the accepted H-ACT-H1 / H-ACC-7L ledgers.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

from server.services.unified_contract_versions import (
    EXECUTION_REQUEST_SCHEMA_VERSIONS,
    PREFERRED_AUDIT_SCHEMA_VERSION,
    PREFERRED_REQUEST_SCHEMA_VERSION,
    PREFERRED_RESULT_SCHEMA_VERSION,
)
from server.services.unified_local_service import describe_capabilities
from server.services.unified_mode_c import (
    build_mode_c_ai_handoff,
    build_mode_c_result_package,
    read_mode_c_audit,
)
from server.unified_mcp.tool_contracts import build_tool_contract_snapshot, build_tool_specs


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TOOLS = [
    "market_describe_capabilities",
    "market_validate_request",
    "market_preview_request",
    "market_read_result",
    "market_export_ai_handoff",
    "market_fetch_evidence",
]


def _capability(payload: dict, capability_id: str) -> dict:
    return next(item for item in payload["capabilities"] if item["capability_id"] == capability_id)


def _market(capability: dict, market: str) -> dict:
    return next(item for item in capability["markets"] if item["market"] == market)


def test_h_act_v3_current_authority_is_promoted_without_expanding_active_source_set():
    catalog = json.loads(
        (ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(
            encoding="utf-8"
        )
    )
    routing = json.loads(
        (ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(
            encoding="utf-8"
        )
    )
    versions = catalog["contract_versions"]

    assert PREFERRED_REQUEST_SCHEMA_VERSION == "unified_market_evidence_request.v3"
    assert PREFERRED_RESULT_SCHEMA_VERSION == "unified_market_evidence_result.v3"
    assert PREFERRED_AUDIT_SCHEMA_VERSION == "unified_market_evidence_audit_package.v3"
    assert EXECUTION_REQUEST_SCHEMA_VERSIONS == frozenset(
        {
            "unified_market_evidence_request.v1",
            "unified_market_evidence_request.v2",
            "unified_market_evidence_request.v3",
        }
    )
    assert versions == {
        "accepted_request_schema_versions": [
            "unified_market_evidence_request.v1",
            "unified_market_evidence_request.v2",
            "unified_market_evidence_request.v3",
        ],
        "preferred_request_schema_version": "unified_market_evidence_request.v3",
        "emitted_result_schema_version": "unified_market_evidence_result.v3",
        "future_candidate_request_schema_version": None,
        "future_candidate_result_schema_version": None,
        "v3_runtime_authority_status": "v3_preferred_selected_routes_active",
    }
    assert catalog["phase_h_contract"]["active_phase_h_source_count"] == 1
    assert routing["phase_h_source_authority"]["active_source_count"] == 1
    active = [
        (item["source_id"], item["runtime_executable"])
        for item in routing["phase_h_source_authority"]["records"]
        if item["activation_state"] == "active"
    ]
    assert active == [("H1-TPEX-ATTENTION-OPENAPI", True)]


def test_h_act_v3_local_service_exposes_exact_route_truth_not_catalog_market_overclaim():
    described = describe_capabilities()
    assert described["capability_catalog_schema_version"] == "unified_market_evidence_capability_catalog.v3"
    assert described["routing_matrix_schema_version"] == "m8r_05b_capability_to_executor_routing_matrix.v3"
    assert described["accepted_request_schema_versions"] == [
        "unified_market_evidence_request.v1",
        "unified_market_evidence_request.v2",
        "unified_market_evidence_request.v3",
    ]
    assert described["preferred_request_schema_version"] == "unified_market_evidence_request.v3"
    assert described["emitted_result_schema_version"] == "unified_market_evidence_result.v3"

    h1 = _capability(described, "trading_status_context")
    assert h1["routing_disposition"] == "resolved"
    assert h1["selected_executor_id"] == "phase_h_h1_tpex_attention_executor"
    assert _market(h1, "TPEX") == {
        "market": "TPEX",
        "disposition": "executable",
        "production_executor_available": True,
    }
    assert _market(h1, "TWSE") == {
        "market": "TWSE",
        "disposition": "blocked",
        "production_executor_available": False,
    }

    h2 = _capability(described, "corporate_action_context")
    assert h2["routing_disposition"] == "plan_only"
    assert all(item["disposition"] != "executable" for item in h2["markets"])

    h3 = _capability(described, "recent_performance")
    assert h3["routing_disposition"] == "blocked"
    assert all(item["disposition"] != "executable" for item in h3["markets"])


def test_h_act_v3_mcp_keeps_six_tools_and_expands_existing_fetch_contract():
    snapshot = build_tool_contract_snapshot()
    assert [tool.name for tool in snapshot.tools] == EXPECTED_TOOLS
    assert [tool.name for tool in build_tool_specs()] == EXPECTED_TOOLS

    fetch = next(tool for tool in snapshot.tools if tool.name == "market_fetch_evidence")
    versions = {
        branch["properties"]["schema_version"]["const"]
        for branch in fetch.inputSchema["properties"]["request"]["oneOf"]
    }
    assert versions == {
        "unified_market_evidence_request.v1",
        "unified_market_evidence_request.v2",
        "unified_market_evidence_request.v3",
    }


def test_h_act_v3_mode_c_new_materialization_defaults_are_v3():
    assert inspect.signature(build_mode_c_result_package).parameters[
        "output_schema_version"
    ].default == "unified_market_evidence_result.v3"
    assert inspect.signature(read_mode_c_audit).parameters[
        "output_schema_version"
    ].default == "unified_market_evidence_result.v3"
    assert inspect.signature(build_mode_c_ai_handoff).parameters[
        "output_schema_version"
    ].default == "unified_market_evidence_result.v3"


def test_h_act_v3_workbench_primary_builder_is_v3_but_v1_v2_selection_contracts_remain():
    builder = (
        ROOT / "frontend/unified-workbench/watchlist-workbench.js"
    ).read_text(encoding="utf-8")
    assert "watchlist_evidence_selection_request.v3" in builder
    for name in (
        "watchlist_evidence_selection_request.v1.schema.json",
        "watchlist_evidence_selection_request.v2.schema.json",
        "watchlist_evidence_selection_request.v3.schema.json",
    ):
        assert (ROOT / "docs/contracts/schemas" / name).is_file()
