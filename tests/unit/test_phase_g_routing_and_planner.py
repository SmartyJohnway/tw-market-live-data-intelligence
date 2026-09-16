"""A2 dormant routing and per-target applicability acceptance."""

from __future__ import annotations

import copy
import json
import socket
from pathlib import Path

import jsonschema

from scripts.m8r_05b_01.canonical import sha256_json
from scripts.m8r_05b_01.models import PLANNER_VERSION
from scripts.m8r_05b_01.planner import HANDOFF_VERSION, build_plan


ROOT = Path(__file__).resolve().parents[2]
CATALOG = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v2.json").read_text())
ROUTING = json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v2.json").read_text())
HANDOFF = json.loads((ROOT / "docs/data_capabilities/m8r_05b_orchestration_handoff_contract.json").read_text())
INVENTORY = json.loads((ROOT / "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json").read_text())
PLAN_SCHEMA = json.loads((ROOT / "schemas/unified_market_evidence_orchestration_plan.v1.schema.json").read_text())


def target(target_id: str, market: str, family: str, instrument_type: str) -> dict:
    return {
        "target_index": 0,
        "original_input": target_id,
        "resolution_requirement": "exact",
        "resolution_status": "resolved",
        "canonical_identity": {
            "canonical_target_id": target_id, "market": market,
            "security_code": target_id.rsplit(":", 1)[1], "isin": f"TW{target_id[-6:]:0>6}",
            "security_name_zh": "fixture", "security_name_en": "fixture",
            "instrument_family": family, "instrument_type": instrument_type,
        },
    }


def validation(targets: list[dict], needs: list[dict]) -> dict:
    return {
        "schema_version": "unified_market_evidence_request_validation.v1", "request_id": "phase-g-a2",
        "validation_status": "valid", "request_schema_status": "valid", "target_validation_status": "valid",
        "capability_validation_status": "valid", "normalized_request": {"data_needs": needs},
        "target_results": targets,
        "capability_results": [
            {"data_need_index": index, "capability_id": need["type"], "priority": need["priority"], "status": "runtime_executable"}
            for index, need in enumerate(needs)
        ],
        "blocking_issues": [], "warnings": [],
        "limits": {"target_count": len(targets), "hard_target_limit": 50, "operation_count_computed": False, "operation_count": 0, "orchestrator_projection_required": True},
        "validation_metadata": {"offline": True, "deterministic": True, "allow_fixture_snapshot": True},
    }


def bindings(value: dict) -> dict:
    return {
        "original_request_hash": "1" * 64, "normalized_request_hash": "2" * 64,
        "f3_validation_output_hash": sha256_json(value),
        "security_master_evidence_references": ["master-a"], "security_master_artifact_hashes": ["a" * 64],
        "capability_catalog_hash": sha256_json(CATALOG), "planner_version": PLANNER_VERSION,
        "routing_matrix_version": ROUTING["schema_version"], "routing_matrix_hash": sha256_json(ROUTING),
        "handoff_contract_version": HANDOFF_VERSION, "handoff_contract_hash": sha256_json(HANDOFF),
    }


def plan(value: dict) -> dict:
    return build_plan(value, capability_catalog=CATALOG, routing_matrix=ROUTING,
                      handoff_contract=HANDOFF, executor_disposition=INVENTORY,
                      input_bindings=bindings(value), planning_timestamp="2026-09-16T00:00:00Z")


def research_need(priority: str = "required", capability: str = "monthly_revenue") -> dict:
    return {"type": capability, "priority": priority, "parameters": {}}


def test_b01_b02_common_shares_are_dormant_research_eligible_by_market():
    for market, code in (("TWSE", "2330"), ("TPEX", "6488")):
        result = plan(validation([target(f"{market}:{code}", market, "company_share", "common_share")], [research_need()]))
        assert result["plan_status"] == "plan_only_not_executable"
        assert result["operations"][0]["capability_id"] == "monthly_revenue"
        assert result["operations"][0]["operation_status"] == "plan_only_not_executable"
        assert result["operations"][0]["network_required"] is False
        jsonschema.validate(result, PLAN_SCHEMA)


def test_b03_ky_eligibility_uses_security_master_classification_not_name():
    eligible = plan(validation([target("TWSE:KY01", "TWSE", "company_share", "common_share")], [research_need()]))
    ineligible = plan(validation([target("TWSE:KY01", "TWSE", "company_share", "preferred_share")], [research_need()]))
    assert eligible["plan_status"] == "plan_only_not_executable"
    assert ineligible["plan_status"] == "blocked"
    assert ineligible["blocked_operations"][0]["blocking_reason_codes"] == ["unsupported_instrument_scope"]


def test_b04_b05_b06_non_common_research_is_target_specific_and_optional_is_omitted():
    for family, instrument_type in (("company_share", "depositary_receipt"), ("fund_product", "etf"), ("company_share", "preferred_share"), ("derivative", "warrant"), ("debt", "bond")):
        result = plan(validation([target("TWSE:X", "TWSE", family, instrument_type)], [research_need("optional")]))
        assert result["plan_status"] == "plan_ready_with_warnings"
        assert result["omitted_optional_capabilities"][0]["reason_code"] == "unsupported_instrument_scope"
        assert not result["operations"] and not result["batch_groups"]


def test_b07_and_b10_planning_uses_canonical_market_code_and_preserves_full_scope():
    item = target("TPEX:6488", "TPEX", "company_share", "common_share")
    item["canonical_identity"]["security_name_zh"] = "arbitrary name cannot route evidence"
    result = plan(validation([item], [research_need()]))
    operation = result["operations"][0]
    assert operation["market"] == "TPEX"
    assert operation["canonical_target_ids"] == ["TPEX:6488"]
    assert operation["security_types"] == ["equity"]
    assert ROUTING["routes"][-1]["supported_instrument_families"] == ["company_share"]
    assert ROUTING["routes"][-1]["supported_instrument_types"] == ["common_share"]


def test_b10_frozen_result_contract_requires_resolved_identity_and_allows_unresolved_null():
    frozen = Path(r"D:\Codex-Workspace\docs\tw-market-live-data-intelligence\10_Phase_G_Authority\Phase_G_V2_Exact_Schema_Contract_FROZEN")
    result = json.loads((frozen / "example_unified_market_evidence_result.v2.json").read_text(encoding="utf-8"))
    identity = result["targets"][0]["canonical_identity"]
    assert set(("canonical_target_id", "isin", "market", "security_code", "instrument_family", "instrument_type")) <= set(identity)
    result["targets"][0]["resolution"]["status"] = "not_found"
    result["targets"][0]["canonical_identity"] = None
    jsonschema.validate(result, json.loads((ROOT / "schemas/unified_market_evidence_result.v2.schema.json").read_text()))


def test_mixed_targets_omit_only_noncommon_optional_research_without_network():
    common = target("TWSE:2330", "TWSE", "company_share", "common_share")
    etf = target("TWSE:0050", "TWSE", "fund_product", "etf")
    result = plan(validation([common, etf], [research_need("optional", "material_disclosures")]))
    assert result["plan_status"] == "plan_ready_with_warnings"
    assert [item["canonical_target_ids"] for item in result["operations"]] == [["TWSE:2330"]]
    assert result["omitted_optional_capabilities"][0]["canonical_target_ids"] == ["TWSE:0050"]
    assert result["accounting"]["network_request_estimate"] == 0


def test_e06_e07_e09_e12_dormant_routes_are_same_source_per_market_and_offline(monkeypatch):
    routes = {route["capability_id"]: route for route in ROUTING["routes"]}
    monthly = routes["monthly_revenue"]
    assert monthly["selected_executor_id"] == "phase_g_official_research_executor"
    assert monthly["batching_scope"] == "same_source"
    assert monthly["runtime_executable"] is False
    assert monthly["source_compatibility_key"] == "phase_g_official_research_executor:monthly_revenue"
    assert (monthly["source_compatibility_key"], "TWSE") == (monthly["source_compatibility_key"], "TWSE")
    assert (monthly["source_compatibility_key"], "TWSE") != (monthly["source_compatibility_key"], "TPEX")
    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network forbidden")))
    result = plan(validation([target("TWSE:2330", "TWSE", "company_share", "common_share")], [research_need()]))
    assert result["accounting"]["network_request_estimate"] == 0
    assert result["operations"][0]["executor_id"] is None
