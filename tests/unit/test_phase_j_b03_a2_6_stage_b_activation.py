from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from jsonschema import Draft202012Validator

from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext
from scripts.m8r_06_03_production_adapter import (
    PHASE_H_H1_COMPOSITE_EXECUTOR_ID, PHASE_H_H1_EXECUTOR_ID,
    build_production_runtime_adapter_registry, production_operation_adapter,
)
from scripts.m8r_05c.trading_status_composer import validate_trading_status_context_composite
from server.services import phase_h_h1_tpex_composite as shared
from tests.helpers.phase_j_b03_a2_6_integrated import fixture_responses
from tests.helpers.phase_j_b03_a2_6_stage_b import run_production_dispatch_fixture

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _composite(execution: dict) -> dict:
    primary = next(item for item in execution["outcomes"][0]["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    return json.loads((execution["root"] / primary["relative_path"]).read_text(encoding="utf-8"))


def test_stage_b_current_authority_selects_composite_and_activates_exact_three_h1_sources():
    catalog = _read("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _read("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    descriptors = _read("config/phase_h_h1_dormant_source_descriptors.json")
    route = next(item for item in routing["routes"] if item["capability_id"] == "trading_status_context")
    assert route["selected_executor_id"] == PHASE_H_H1_COMPOSITE_EXECUTOR_ID
    assert route["candidate_executor_ids"] == [PHASE_H_H1_COMPOSITE_EXECUTOR_ID]
    assert route["output_evidence_contract"] == "trading_status_context_composite.v1"
    assert route["estimated_network_requests_per_invocation"] == 3
    assert catalog["phase_h_contract"]["active_phase_h_source_count"] == 4
    assert routing["phase_h_source_authority"]["active_source_count"] == 4
    active = {item["source_id"] for item in routing["phase_h_source_authority"]["records"]
              if item["activation_state"] == "active" and item["runtime_executable"] is True}
    assert active == {"H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI",
                      "H1-TPEX-CHANGED-TRADING-OPENAPI", "H3-TWSE-DEFAULT-BOUNDED"}
    by_id = {item["source_id"]: item for item in descriptors["sources"]}
    for source_id in ("H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI"):
        assert (by_id[source_id]["activation_state"], by_id[source_id]["runtime_executable"]) == ("active", True)
    assert by_id["H1-TPEX-SUSPEND-TODAY-OPENAPI"]["activation_state"] == "inactive"
    assert by_id["H1-TPEX-SUSPEND-HISTORY-OPENAPI"]["activation_state"] == "eligible"
    registry = build_production_runtime_adapter_registry()
    assert registry.get_route(PHASE_H_H1_COMPOSITE_EXECUTOR_ID, "trading_status_context", "TPEX") is not None
    assert registry.get_route(PHASE_H_H1_EXECUTOR_ID, "trading_status_context", "TPEX") is not None
    assert len(registry.get_route(PHASE_H_H1_COMPOSITE_EXECUTOR_ID, "trading_status_context", "TPEX").adapter.__name__) > 0
    assert len(__import__("server.unified_mcp.tool_contracts", fromlist=["build_tool_specs"]).build_tool_specs()) == 6
    assert any("H0-SRC-02 prevents complete H1 coverage claims" in item for item in next(
        item for item in catalog["data_need_capabilities"] if item["capability_id"] == "trading_status_context"
    )["known_limitations"])


def test_stage_b_b_c1_b_c2_c12_canonical_production_dispatch_result_audit_handoff(tmp_path):
    execution = run_production_dispatch_fixture(tmp_path / "canonical")
    operation = execution["plan"]["operations"][0]
    outcome = execution["outcomes"][0]
    composite = _composite(execution)
    selected_route = next(item for item in _read("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")["routes"]
                          if item["capability_id"] == "trading_status_context")
    assert operation["executor_id"] == PHASE_H_H1_COMPOSITE_EXECUTOR_ID
    assert outcome["executor_id"] == selected_route["selected_executor_id"] == PHASE_H_H1_COMPOSITE_EXECUTOR_ID
    assert outcome["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert sum(item["artifact_role"] == "primary_evidence" for item in outcome["evidence_artifacts"]) == 1
    assert sum(item["artifact_role"] == "component_evidence" for item in outcome["evidence_artifacts"]) == 3
    assert composite["schema_version"] == "trading_status_context_composite.v1"
    assert [item["source_id"] for item in composite["components"]] == [
        "H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI"]
    assert composite["aggregate_coverage"]["covered_status_types"] == ["attention", "disposition"]
    assert composite["status"] == "partial"
    projected = execution["result"]["targets"][0]["evidence"]["trading_status_context"]
    assert projected == composite
    assert execution["audit"]["schema_version"] == "unified_market_evidence_audit_package.v3"
    assert all(name in execution["handoff_markdown"] for name in ("TPEx Attention", "TPEx Disposition", "TPEx Current Special-Status Native Evidence"))
    assert "Ｙ" in execution["handoff_markdown"] and "unresolved" in execution["handoff_markdown"]
    assert execution["result"]["schema_version"] == "unified_market_evidence_result.v3"
    assert execution["plan"]["accounting"]["network_request_estimate"] == 3


def test_stage_b_b_c3_same_production_core_binds_second_approved_target_not_6488(tmp_path):
    response_map = fixture_responses()
    for source_id, obs in list(response_map.items()):
        rows = json.loads(obs.raw_bytes.decode("utf-8"))
        changed = [{**row, "SecuritiesCompanyCode": "1234"} for row in rows]
        from dataclasses import replace
        response_map[source_id] = replace(obs, raw_bytes=json.dumps(changed, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    request = {"executor_id": PHASE_H_H1_COMPOSITE_EXECUTOR_ID, "capability_id": "trading_status_context",
               "market": "TPEX", "approved_security_identifiers": ["TPEX:1234"], "approved_security_types": ["equity"],
               "network_authorized": True, "timeout_seconds": 60, "operation_id": "umeop-op-v1-bbbbbbbbbbbbbbbbbbbb",
               "execution_request_id": "req-1234", "execution_request_hash": "a" * 64}
    calls = []

    def fake_get(endpoint: str, *, timeout_seconds: int = 60):
        source = next(item for item in shared.SOURCES if item["endpoint"] == endpoint)
        calls.append(endpoint)
        obs = response_map[source["source_id"]]
        return {"raw_bytes": obs.raw_bytes, "status": obs.status, "content_type": obs.content_type,
                "effective_url": obs.effective_url, "retrieved_at": obs.retrieved_at,
                "tls_policy": "fixture", "redirect_count": 0}

    with patch.object(shared, "official_get", fake_get):
        outcome = production_operation_adapter(request, DispatchRuntimeContext(str(tmp_path), "execute-approved"))
    primary = next(item for item in outcome["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    composite = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    assert calls == [item["endpoint"] for item in shared.SOURCES]
    assert all(item["evidence"]["target"]["canonical_target_id"] == "TPEX:1234" for item in composite["components"])
    assert all(item["evidence"]["target"]["security_code"] == "1234" for item in composite["components"])


@pytest.mark.parametrize("mutate", [
    lambda req: req.update(market="TWSE"),
    lambda req: req.update(approved_security_identifiers=["TPEX:6488", "TPEX:1234"]),
    lambda req: req.update(approved_security_identifiers=["TPEX:"]),
    lambda req: req.update(network_authorized=False),
])
def test_stage_b_b_c4_b_c5_reject_bad_authorization_binding_before_transport(tmp_path, mutate):
    request = {"executor_id": PHASE_H_H1_COMPOSITE_EXECUTOR_ID, "capability_id": "trading_status_context",
               "market": "TPEX", "approved_security_identifiers": ["TPEX:6488"], "approved_security_types": ["equity"],
               "network_authorized": True, "timeout_seconds": 60, "operation_id": "umeop-op-v1-cccccccccccccccccccc",
               "execution_request_id": "req", "execution_request_hash": "b" * 64}
    mutate(request)
    calls = []
    with patch.object(shared, "official_get", lambda *_a, **_k: calls.append("GET")):
        with pytest.raises(Exception):
            production_operation_adapter(request, DispatchRuntimeContext(str(tmp_path), "execute-approved"))
    assert calls == []


def test_stage_b_b_c6_sources_are_fixed_and_caller_url_fields_have_no_effect(tmp_path):
    request = {"executor_id": PHASE_H_H1_COMPOSITE_EXECUTOR_ID, "capability_id": "trading_status_context",
               "market": "TPEX", "approved_security_identifiers": ["TPEX:6488"], "approved_security_types": ["equity"],
               "network_authorized": True, "timeout_seconds": 60, "operation_id": "umeop-op-v1-dddddddddddddddddddd",
               "execution_request_id": "req", "execution_request_hash": "c" * 64,
               "endpoint": "https://example.invalid", "source_ids": ["caller-choice"]}
    observations = fixture_responses()
    seen = []
    def fake_get(endpoint: str, *, timeout_seconds: int = 60):
        seen.append(endpoint)
        source = next(item for item in shared.SOURCES if item["endpoint"] == endpoint)
        obs = observations[source["source_id"]]
        return {"raw_bytes": obs.raw_bytes, "status": obs.status, "content_type": obs.content_type,
                "effective_url": obs.effective_url, "retrieved_at": obs.retrieved_at,
                "tls_policy": "fixture", "redirect_count": 0}
    with patch.object(shared, "official_get", fake_get):
        production_operation_adapter(request, DispatchRuntimeContext(str(tmp_path), "execute-approved"))
    assert seen == [item["endpoint"] for item in shared.SOURCES]


def test_stage_b_b_c7_b_c8_b_c9_b_c10_semantics_remain_partial_and_unpromoted(tmp_path):
    execution = run_production_dispatch_fixture(tmp_path / "semantics")
    composite = _composite(execution)
    cmode = composite["components"][2]["evidence"]
    native = cmode["native_observations"][0]
    assert native["source_native_value"] == "Ｙ"
    assert [f"U+{ord(char):04X}" for char in native["source_native_value"]] == ["U+FF39"]
    assert native["semantic_status"] == "unresolved"
    assert "suspension" not in composite["aggregate_coverage"]["covered_status_types"]
    assert all(item["status_type"] != "suspension" for component in composite["components"] for item in component["evidence"]["items"])
    # A blank native value is evidence, not a negative status.
    blank = run_production_dispatch_fixture(tmp_path / "blank", responses=fixture_responses(cmode_value=""))
    blank_native = _composite(blank)["components"][2]["evidence"]["native_observations"][0]
    assert blank_native["source_native_value"] == "" and blank_native["semantic_status"] == "unresolved"
    # A successful exact-target no-match remains partial, with no canonical coverage.
    no_match_rows = [{"Date": "1151007", "SecuritiesCompanyCode": "9999", "CompanyName": "Other",
                      "AlteredTrading": "", "PeriodicTrading": "", "ManagedStock": "", "MatchingFrequency": "",
                      "SuspensionOfTrading": "", " FinancialAnnouncements": ""}]
    no_match = run_production_dispatch_fixture(tmp_path / "no-match", responses=fixture_responses(cmode_rows=no_match_rows))
    no_match_cmode = _composite(no_match)["components"][2]["evidence"]
    assert no_match_cmode["status"] == "partial" and no_match_cmode["native_observations"] == []
    assert no_match_cmode["coverage"]["covered_status_types"] == []
    assert _composite(no_match)["aggregate_coverage"]["covered_status_types"] == ["attention", "disposition"]


def test_stage_b_b_c11_source_failure_is_independent(tmp_path):
    execution = run_production_dispatch_fixture(tmp_path / "failure", failure_source_id="H1-TPEX-DISPOSITION-OPENAPI")
    composite = _composite(execution)
    assert execution["outcomes"][0]["status"] == "succeeded"
    assert [item["component_status"] for item in composite["components"]] == ["partial", "source_failed", "partial"]
    assert composite["aggregate_coverage"]["covered_status_types"] == ["attention"]
    assert composite["components"][2]["evidence"]["native_observation_count"] == 1


def test_stage_b_b_c14_rollback_copy_restores_pre_stage_b_two_source_topology():
    catalog = _read("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _read("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    descriptors = _read("config/phase_h_h1_dormant_source_descriptors.json")
    metadata = _read("config/m8r_06_03_executor_registry_metadata.json")
    rolled_catalog, rolled_routing, rolled_descriptors, rolled_metadata = map(deepcopy, (catalog, routing, descriptors, metadata))
    cap = next(item for item in rolled_catalog["data_need_capabilities"] if item["capability_id"] == "trading_status_context")
    cap.update(coverage_modes=["partial_attention_only"], known_limitations=["H0-SRC-02 prevents complete H1 coverage claims"])
    rolled_catalog["phase_h_contract"]["active_phase_h_source_count"] = 2
    route = next(item for item in rolled_routing["routes"] if item["capability_id"] == "trading_status_context")
    route.update(selected_executor_id=PHASE_H_H1_EXECUTOR_ID, candidate_executor_ids=[PHASE_H_H1_EXECUTOR_ID],
                 output_evidence_contract="trading_status_context_evidence.v1",
                 estimated_operation_rule="one logical operation and one bounded official TPEx OpenAPI request per exact approved target")
    route.pop("estimated_network_requests_per_invocation", None)
    source = next(item for item in rolled_routing["phase_h_source_authority"]["records"] if item["source_id"] == "H1-TPEX-DISPOSITION-OPENAPI")
    source.update(activation_state="eligible", runtime_executable=False)
    cmode = next(item for item in rolled_routing["phase_h_source_authority"]["records"] if item["source_id"] == "H1-TPEX-CHANGED-TRADING-OPENAPI")
    cmode.update(activation_state="eligible", runtime_executable=False)
    rolled_routing["phase_h_source_authority"]["active_source_count"] = 2
    rolled_routing["routing_scope"] = "rollback fixture: H1-TPEX-ATTENTION-OPENAPI and H3-TWSE-DEFAULT-BOUNDED are active"
    for item in rolled_descriptors["sources"]:
        if item["source_id"] in {"H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI"}:
            item.update(activation_state="eligible", runtime_executable=False)
    rolled_metadata["executors"] = [item for item in rolled_metadata["executors"] if item["executor_id"] != PHASE_H_H1_COMPOSITE_EXECUTOR_ID]
    registry = build_production_runtime_adapter_registry()
    legacy_registration = registry.get_route(PHASE_H_H1_EXECUTOR_ID, "trading_status_context", "TPEX")
    assert legacy_registration is not None and legacy_registration.network_required and not legacy_registration.fake_adapter
    assert next(item for item in rolled_catalog["data_need_capabilities"] if item["capability_id"] == "trading_status_context")["coverage_modes"] == ["partial_attention_only"]
    assert route["selected_executor_id"] == PHASE_H_H1_EXECUTOR_ID
    assert route["output_evidence_contract"] == "trading_status_context_evidence.v1"
    assert route["candidate_executor_ids"] == [PHASE_H_H1_EXECUTOR_ID]
    assert rolled_routing["phase_h_source_authority"]["active_source_count"] == 2
    rolled_active_sources = {item["source_id"] for item in rolled_routing["phase_h_source_authority"]["records"]
                             if item["activation_state"] == "active" and item["runtime_executable"] is True}
    assert rolled_active_sources == {"H1-TPEX-ATTENTION-OPENAPI", "H3-TWSE-DEFAULT-BOUNDED"}
    assert all(next(x for x in rolled_descriptors["sources"] if x["source_id"] == source_id)["runtime_executable"] is False
               for source_id in ("H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI"))
    assert any(item["executor_id"] == PHASE_H_H1_EXECUTOR_ID for item in rolled_metadata["executors"])
    assert all(item["executor_id"] != PHASE_H_H1_COMPOSITE_EXECUTOR_ID for item in rolled_metadata["executors"])
