"""PR-D D1 current-authority and compatibility acceptance."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from server.services.unified_local_service import describe_capabilities
from server.services.unified_mode_a import validate_mode_a_request
from server.services.unified_mode_c import build_mode_c_ai_handoff, build_mode_c_result_package
from server.unified_mcp import ADAPTER_VERSION, LOCAL_SERVICE_CONTRACT_VERSION
from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry


ROOT = Path(__file__).resolve().parents[2]
FROZEN_V1_SCHEMA_HASHES = {
    "unified_market_evidence_request.v1.schema.json": "6b2062151abdbb22f48b6b5e280636425b782c0e3c4e9c633ff552498607cc0b",
    "unified_market_evidence_result.v1.schema.json": "58fe88d33bbc5f53639cd3b9896ad0cf6106e00ec6e9f93630a45339c545f05f",
    "unified_market_evidence_audit_package.v1.schema.json": "5877ad564e488c6d4d4c5ef6b405e3b8dde60f056327cc1babf16a5ec2364198",
}
EXPECTED_TOOLS = (
    "market_describe_capabilities",
    "market_validate_request",
    "market_preview_request",
    "market_read_result",
    "market_export_ai_handoff",
    "market_fetch_evidence",
)


def _request(version: str) -> dict:
    base = {
        "schema_version": version,
        "request_id": f"phase-g-d1-{version[-2:]}",
        "execution_mode": "preview",
        "targets": [{"input": "2330", "market_hint": "TWSE"}],
        "data_needs": [{"type": "current_observation", "priority": "required"}],
    }
    if version.endswith("v2"):
        base["data_needs"].extend([
            {"type": "material_disclosures", "priority": "optional", "parameters": {}},
            {"type": "monthly_revenue", "priority": "optional", "parameters": {}},
        ])
    return base


def test_a09_a10_exact_six_mcp_tools_accept_v1_v2_and_reject_unknown():
    snapshot = build_tool_contract_snapshot()
    assert ADAPTER_VERSION == "unified_market_evidence_mcp_adapter.v2"
    assert LOCAL_SERVICE_CONTRACT_VERSION == "unified_market_evidence_local_service.v2"
    assert tuple(tool.name for tool in snapshot.tools) == EXPECTED_TOOLS
    for version in ("unified_market_evidence_request.v1", "unified_market_evidence_request.v2"):
        assert snapshot.validate_arguments("market_validate_request", {"request": _request(version)})
    assert not snapshot.validate_arguments(
        "market_validate_request",
        {"request": _request("unified_market_evidence_request.v999")},
    )


def test_a11_current_catalog_route_and_local_service_are_v2_and_truthful():
    payload = describe_capabilities()
    assert payload["service_contract_version"] == "unified_market_evidence_local_service.v2"
    assert payload["capability_catalog_schema_version"] == "unified_market_evidence_capability_catalog.v2"
    assert payload["routing_matrix_schema_version"] == "m8r_05b_capability_to_executor_routing_matrix.v2"
    assert payload["accepted_request_schema_versions"] == [
        "unified_market_evidence_request.v1",
        "unified_market_evidence_request.v2",
    ]
    assert payload["preferred_request_schema_version"] == "unified_market_evidence_request.v2"
    assert payload["emitted_result_schema_version"] == "unified_market_evidence_result.v2"
    by_id = {item["capability_id"]: item for item in payload["capabilities"]}
    for capability_id, coverage in (
        ("material_disclosures", "latest_completed_official_daily_batch"),
        ("monthly_revenue", "latest_available_reporting_period"),
    ):
        item = by_id[capability_id]
        assert item["routing_disposition"] == "resolved"
        assert item["selected_executor_id"] == "phase_g_official_research_executor"
        assert item["instrument_scope"] == {
            "instrument_families": ["company_share"],
            "instrument_types": ["common_share"],
        }
        assert item["coverage_modes"] == [coverage]
        assert item["historical_lookup_supported"] is False
        assert item["possible_fallbacks"] == ["official_json_openapi"]
        assert {entry["market"] for entry in item["markets"] if entry["disposition"] == "executable"} == {"TWSE", "TPEX"}


def test_mode_a_explicitly_accepts_v1_and_v2_and_fails_closed_on_unknown():
    for version in ("unified_market_evidence_request.v1", "unified_market_evidence_request.v2"):
        result = validate_mode_a_request(_request(version), allow_fixture_snapshot=True)
        assert result["validation_status"] == "valid"
    with pytest.raises(ValueError, match="unsupported_request_schema_version"):
        validate_mode_a_request(_request("unified_market_evidence_request.v999"), allow_fixture_snapshot=True)


def test_current_mode_c_defaults_to_v2_without_changing_internal_control_package_identity():
    assert inspect.signature(build_mode_c_result_package).parameters["output_schema_version"].default == "unified_market_evidence_result.v2"
    assert inspect.signature(build_mode_c_ai_handoff).parameters["output_schema_version"].default == "unified_market_evidence_result.v2"


def test_four_research_routes_are_registered_without_replacing_legacy_routes():
    registry = build_production_runtime_adapter_registry()
    for capability_id in ("material_disclosures", "monthly_revenue"):
        for market in ("TWSE", "TPEX"):
            route = registry.get_route("phase_g_official_research_executor", capability_id, market)
            assert route is not None and route.fake_adapter is False and route.network_required is True
    for capability_id in ("current_observation", "official_eod_reference"):
        for market in ("TWSE", "TPEX"):
            assert registry.get_route("m8r_03d_watchlist_controlled_executor_adapter", capability_id, market) is not None


def test_frozen_v1_request_result_and_audit_schema_bytes_are_unchanged():
    for name, expected in FROZEN_V1_SCHEMA_HASHES.items():
        assert hashlib.sha256((ROOT / "schemas" / name).read_bytes()).hexdigest() == expected


def test_e11_f08_f10_no_scheduler_polling_background_research_store_or_issuer_authority():
    paths = [
        ROOT / "scripts/phase_g/research_executor.py",
        ROOT / "scripts/phase_g/mops_material_disclosures.py",
        ROOT / "scripts/phase_g/mops_monthly_revenue.py",
        ROOT / "scripts/m8r_06_03_production_adapter.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    for forbidden in ("schedule.", "polling", "background_refresh", "research_database", "issuer_master"):
        assert forbidden not in combined


def test_activation_authorities_are_valid_json_and_hashable():
    for relative in (
        "docs/data_capabilities/unified_market_evidence_capability_catalog.v2.json",
        "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v2.json",
        "config/m8r_06_03_executor_registry_metadata.json",
    ):
        path = ROOT / relative
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)
        assert len(hashlib.sha256(path.read_bytes()).hexdigest()) == 64
