"""Deterministic proof that 05B-03 source calls equal canonical batch accounting."""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from scripts.m8r_05b_01.canonical import sha256_json
from scripts.m8r_05b_01.models import PLANNER_VERSION
from scripts.m8r_05b_01.planner import HANDOFF_VERSION, ROUTING_VERSION, build_plan
from scripts.m8r_05b_03.dispatch import dispatch_prepared, prepare_dispatch
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_06_03_production_adapter import (
    build_production_runtime_adapter_registry,
    load_production_executor_metadata,
)
from tests.unit.m8r_05b_03_test_helpers import EVALUATION_TIMESTAMP, artifacts
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight


ROOT = Path(__file__).resolve().parents[2]
CATALOG = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json").read_text(encoding="utf-8"))
ROUTING = json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.json").read_text(encoding="utf-8"))
HANDOFF = json.loads((ROOT / "docs/data_capabilities/m8r_05b_orchestration_handoff_contract.json").read_text(encoding="utf-8"))
INVENTORY = json.loads((ROOT / "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json").read_text(encoding="utf-8"))


def _plan(targets: list[str], capabilities: list[str]) -> dict:
    target_results = []
    for index, target in enumerate(targets):
        market, code = target.split(":", 1)
        target_results.append({
            "target_index": index,
            "original_input": target,
            "resolution_requirement": "exact",
            "resolution_status": "resolved",
            "canonical_identity": {
                "canonical_target_id": target,
                "market": market,
                "security_code": code,
                "isin": "fixture",
                "security_name_zh": "fixture",
                "security_name_en": "fixture",
                "instrument_family": "company_share",
                "instrument_type": "common_share",
            },
        })
    validation = {
        "schema_version": "unified_market_evidence_request_validation.v1",
        "request_id": "m8r06-03-batch-runtime",
        "validation_status": "valid",
        "request_schema_status": "valid",
        "target_validation_status": "valid",
        "capability_validation_status": "valid",
        "normalized_request": {"data_needs": [{"type": item, "priority": "required", "parameters": {}} for item in capabilities]},
        "target_results": target_results,
        "capability_results": [
            {"data_need_index": index, "capability_id": item, "priority": "required", "status": "runtime_executable"}
            for index, item in enumerate(capabilities)
        ],
        "blocking_issues": [],
        "warnings": [],
        "limits": {"target_count": len(targets), "hard_target_limit": 50, "operation_count_computed": False, "operation_count": 0, "orchestrator_projection_required": True},
        "validation_metadata": {"offline": True, "deterministic": True, "allow_fixture_snapshot": True},
    }
    bindings = {
        "original_request_hash": "1" * 64,
        "normalized_request_hash": "2" * 64,
        "f3_validation_output_hash": sha256_json(validation),
        "security_master_evidence_references": ["master-a"],
        "security_master_artifact_hashes": ["a" * 64],
        "capability_catalog_hash": sha256_json(CATALOG),
        "planner_version": PLANNER_VERSION,
        "routing_matrix_version": ROUTING_VERSION,
        "routing_matrix_hash": sha256_json(ROUTING),
        "handoff_contract_version": HANDOFF_VERSION,
        "handoff_contract_hash": sha256_json(HANDOFF),
    }
    return build_plan(
        validation,
        capability_catalog=CATALOG,
        routing_matrix=ROUTING,
        handoff_contract=HANDOFF,
        executor_disposition=INVENTORY,
        input_bindings=bindings,
        planning_timestamp="2026-08-11T00:00:00Z",
    )


def _dispatch(plan: dict, tmp_path: Path, monkeypatch) -> tuple[list[dict], dict[str, int], dict]:
    calls = {"current": 0, "twse_eod": 0, "tpex_eod": 0}

    def current(watchlist, **kwargs):
        calls["current"] += 1
        assert kwargs["allow_individual_fallback"] is False
        return {"observations": [{"symbol": item["symbol"]} for item in watchlist["items"]]}

    def twse(symbols, *, timeout):
        calls["twse_eod"] += 1
        return {"source_id": "TWSE_OPENAPI", "observations": [{"symbol": symbol} for symbol in symbols]}

    def tpex(symbols, *, timeout):
        calls["tpex_eod"] += 1
        return {"source_id": "TPEX_OPENAPI", "observations": [{"symbol": symbol} for symbol in symbols]}

    monkeypatch.setattr("scripts.m8r_06_03_production_adapter.execute_live_observation", current)
    monkeypatch.setattr("scripts.m8r_06_03_production_adapter.execute_twse_official_eod_adapter", twse)
    monkeypatch.setattr("scripts.m8r_06_03_production_adapter.execute_tpex_official_eod_adapter", tpex)
    plan, authorization, binding, state = artifacts(plan)
    metadata = load_production_executor_metadata()
    preflight = build_orchestrator_preflight(
        plan, authorization, binding, supplied_consumption_state=state,
        evaluation_timestamp=EVALUATION_TIMESTAMP, executor_registry_metadata=metadata, output_root=str(tmp_path),
    )
    prepared = prepare_dispatch(
        preflight, ExecutorMetadataRegistry.from_json(metadata),
        build_production_runtime_adapter_registry(), mode="execute-approved",
    )
    outcomes = dispatch_prepared(
        prepared, governed_output_root=str(tmp_path), mode="execute-approved", accepted_preflight=preflight,
    )
    return outcomes, calls, preflight


@pytest.mark.parametrize(
    ("targets", "capabilities", "expected_batches", "expected_calls"),
    [
        (["TWSE:2330", "TWSE:2317"], ["current_observation"], 1, 1),
        (["TWSE:2330", "TWSE:2317"], ["official_eod_reference"], 1, 1),
        (["TWSE:2330", "TPEX:5227"], ["current_observation"], 2, 2),
        (["TWSE:2330", "TPEX:5227"], ["current_observation", "official_eod_reference"], 4, 4),
    ],
)
def test_production_batch_source_calls_equal_planner_network_estimate(
    tmp_path, monkeypatch, targets, capabilities, expected_batches, expected_calls
):
    plan = _plan(targets, capabilities)
    outcomes, calls, preflight = _dispatch(plan, tmp_path, monkeypatch)

    assert plan["accounting"]["batch_group_count"] == expected_batches
    assert plan["accounting"]["network_request_estimate"] == expected_calls
    assert sum(calls.values()) == plan["accounting"]["network_request_estimate"]
    assert len(outcomes) == plan["accounting"]["logical_operation_count"]
    assert all(item["status"] == "succeeded" for item in outcomes)
    assert len(preflight["resolved_batch_bindings"]) == expected_batches
    assert len(preflight["preflight_identity_scope"]["resolved_executor_route_keys"]) == expected_batches
