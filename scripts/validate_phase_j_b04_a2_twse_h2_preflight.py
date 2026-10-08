"""Validate the network-free J-B04-A2 TWSE H2 implementation preflight."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A2_TWSE_H2_PRODUCTION_IMPLEMENTATION_PREFLIGHT_2026-10-08.json"
SOURCES = ROOT / "docs/governance/phase_h/Phase_H_Official_Source_and_Automation_Authority_Matrix_FROZEN.json"
DESCRIPTORS = ROOT / "config/phase_h_h2_dormant_source_descriptors.json"
CATALOG = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json"
ROUTING = ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json"
REGISTRY = ROOT / "config/m8r_06_03_executor_registry_metadata.json"
H3_LEDGER = ROOT / "docs/governance/phase_h/PHASE_H_H_ACT_H3_TWSE_RECENT_PERFORMANCE_ACCEPTANCE_LEDGER.json"
H2_NORMALIZER = ROOT / "server/services/phase_h_corporate_action_adapters.py"
H4_IMPLEMENTATION = ROOT / "server/services/phase_h_discontinuity_safety.py"
RESULT_SCHEMA = ROOT / "schemas/unified_market_evidence_result.v3.schema.json"
AUDIT_SCHEMA = ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json"
EXECUTION_REQUEST_V1 = ROOT / "schemas/unified_market_evidence_execution_request.v1.schema.json"
EXECUTION_REQUEST_V2 = ROOT / "schemas/unified_market_evidence_execution_request.v2.schema.json"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_contract(record: dict[str, Any], *, check_repository: bool = False) -> dict[str, Any]:
    machine = record["machine_assertions"]
    expected = {
        "gate": "J-B04-A2",
        "baseline_main": "7c48336e78d7461a3a83ef599b945c7c65542ba8",
        "disposition": "J_B04_A2_READY_FOR_NETWORK_FREE_IMPLEMENTATION",
        "representative_market": "TWSE",
        "selected_h2_source": "H2-TWSE-EXRIGHT-PRE-OPENAPI",
        "source_contract": "TWT48U_ALL",
        "source_evidence_stage": "preannouncement",
        "production_route_semantics": "bounded_partial_fail_closed",
        "future_executor_id": "phase_h_h2_twse_exright_pre_executor",
        "comparison_window_authority": "H3_available_baseline",
        "h2_network_query_uses_h3_window": False,
        "h2_assembly_binds_h3_actual_window": True,
        "unsupported_temporal_completeness_may_be_claimed": False,
        "declared_scope_complete_for_twt48u_default": False,
        "no_row_proves_no_event_across_h3_window": False,
        "scheduled_may_be_promoted_to_effective": False,
        "final_reference_may_be_locally_calculated": False,
        "max_h2_market_gets_per_execution": 1,
        "h2_retry_count": 0,
        "hidden_h2_acquisition_allowed": False,
        "new_public_h2_window_parameter_required": False,
        "background_collection_allowed": False,
        "history_accumulation_allowed": False,
        "twt49u_activation_required": False,
        "capital_reduction_gap_closed": False,
        "tpex_h3_activation_required": False,
        "production_code_changed_in_a2": False,
        "routing_changed_in_a2": False,
        "source_activation_changed_in_a2": False,
        "h2_runtime_after_a2": "INACTIVE",
        "j_b04_after_a2": "BLOCKING",
        "phase_j_after_a2": "NOT_STARTED",
        "mcp_tool_count": 6,
        "market_GETs": 0,
        "market_HEADs": 0,
        "market_POSTs": 0,
        "source_cardinality_decision": "RETAIN_AMBIGUOUS_EXACT_TARGET_FAIL_CLOSED",
        "h3_unavailable_behavior": "SKIP_H2_AND_H4_NO_INVENTED_WINDOW",
        "h4_invocation_precondition": "EXACTLY_ONE_AVAILABLE_H3_BASELINE",
    }
    for key, value in expected.items():
        assert machine.get(key) == value, f"machine_assertion_mismatch:{key}"

    assert record["disposition"] == machine["disposition"]
    assert record["baseline_main"] == machine["baseline_main"]
    source = record["source_decision"]
    for key in ("representative_market", "source_id", "source_contract_id", "source_evidence_stage", "production_route_semantics", "future_executor_id"):
        machine_key = {"source_id": "selected_h2_source", "source_contract_id": "source_contract", "future_executor_id": "future_executor_id"}.get(key, key)
        assert source[key] == machine[machine_key], f"source_decision_mismatch:{key}"
    assert source["current_activation_state"] == "eligible"
    assert source["current_runtime_executable"] is False
    assert source["source_cardinality"]["decision"] == machine["source_cardinality_decision"]
    assert source["source_cardinality"]["uniqueness_proven_by_authority"] is False
    assert "ambiguous_exact_target_rows" in source["source_cardinality"]["current_normalizer_behavior"]

    temporal = record["temporal_coverage"]
    assert temporal["comparison_window_authority"] == "H3_available_baseline"
    assert temporal["h3_owns_window"] is True
    assert temporal["h2_network_query_uses_h3_window"] is False
    assert temporal["h2_assembly_binds_h3_actual_window"] is True
    assert temporal["binding_proves_source_temporal_completeness"] is False
    assert temporal["official_source_proves_arbitrary_historical_window_completeness"] is False
    assert temporal["unsupported_temporal_completeness_may_be_claimed"] is False
    assert temporal["declared_scope_complete_for_twt48u_default"] is False
    assert temporal["no_row_proves_no_event_across_h3_window"] is False
    assert set(temporal["prohibited_window_sources"]) == {
        "plan-time calendar guess", "H2 event-returned dates", "current date",
        "lookback count converted to calendar dates", "local cache accumulation",
        "background collection", "browser history",
    }

    execution = record["execution_contract"]
    assert execution["max_h2_market_gets_per_execution"] == 1
    assert execution["h2_retry_count"] == 0
    assert execution["hidden_h2_acquisition_allowed"] is False
    assert execution["new_public_h2_window_parameter_required"] is False
    assert execution["background_collection_allowed"] is False
    assert execution["history_accumulation_allowed"] is False
    assert execution["backfill"] is False
    assert execution["scheduler"] is False
    assert execution["polling"] is False
    assert "same-target H2 operation dependency on the H3 operation ID" in execution["dependency_binding"]
    assert "preview" in execution["preview_and_authorization"].lower()
    assert "one TWT48U_ALL GET" in execution["combined_network_budget"]

    preconditions = record["h3_preconditions"]
    assert machine["h4_invocation_precondition"] == "EXACTLY_ONE_AVAILABLE_H3_BASELINE"
    assert "Do not invent dates" in preconditions["no_usable_available_baseline"]["behavior"]
    assert "Do not select one arbitrarily" in preconditions["multiple_or_ambiguous_available_baselines"]["behavior"]

    h4 = record["h4_reconciliation"]
    assert h4["implementation"] == "server/services/phase_h_discontinuity_safety.py; pure deterministic zero-network derivation"
    assert h4["state_precedence"][0].startswith("failures or uncovered subtypes -> coverage_incomplete")
    assert "scheduled/preannouncement event" in h4["event_semantics"]
    assert "need not encounter an effective event" in h4["fixture_live_split"]

    projection = record["projection_wiring"]
    for section in ("h2_result_entry", "h3_result_entry", "h4_invocation", "h4_result_entry", "audit", "ai_handoff"):
        assert projection.get(section)
    assert "Not currently invoked by result_builder" in projection["h4_invocation"]
    assert "separate facts" in projection["raw_metric_vs_interpretation"]

    files = {item["path"]: item["classification"] for item in record["future_implementation_file_inventory"]}
    assert files["server/services/phase_h_h2_twse_exright_executor.py"] == "CREATE"
    for path in ("scripts/m8r_05b_01/planner.py", "scripts/m8r_05b_03/controlled_dispatch.py", "scripts/m8r_06_03_production_adapter.py"):
        assert files[path] == "MODIFY"
    for path in ("server/services/phase_h_discontinuity_safety.py", "schemas/corporate_action_context_evidence.v1.schema.json", "schemas/recent_performance_evidence.v1.schema.json", "schemas/discontinuity_safety_evidence.v1.schema.json", "schemas/unified_market_evidence_result.v3.schema.json", "schemas/unified_market_evidence_audit_package.v3.schema.json", "schemas/unified_market_evidence_execution_request.v1.schema.json"):
        assert files[path] == "MUST NOT MODIFY"
    assert [item["gate"] for item in record["future_gate_sequence"]] == ["J-B04-A3", "J-B04-A4", "J-B04-A5", "J-B04-A6"]

    validation = record["validation"]
    assert validation["a2_validator"] == "PASS"
    assert validation["a2_a1_phase_j_readiness_focused_tests"] == "61 passed"
    assert validation["phase_h_v3_contract_validator"] == "PASS"
    assert validation["phase_j_b04_a1_validator"] == "PASS"
    assert validation["phase_j_ghi_readiness_validator"] == "PASS"
    assert validation["portable_catalog_sync_validator"] == "PASS"
    assert validation["runtime_skill_guide_sync_validator"].startswith("PASS")
    assert validation["default_ci"] == "1282 passed, 1 skipped, 5 deselected; 0 failed"
    assert validation["live_market_tests"] == "NOT RUN"
    assert validation["network_get_head_post"] == "0/0/0"

    scope = record["scope_and_network"]
    assert scope["governance_only"] is True
    for key in ("production_code_changed", "schema_changed", "routing_changed", "catalog_changed", "source_authority_changed", "source_activation_changed", "executor_registry_changed", "MCP_changed"):
        assert scope[key] is False, f"scope_changed:{key}"
    assert scope["market_GETs"] == scope["market_HEADs"] == scope["market_POSTs"] == 0
    assert scope["mcp_tool_count"] == 6
    assert scope["h2_runtime_after_a2"] == "INACTIVE"
    assert scope["j_b04_after_a2"] == "BLOCKING"
    assert scope["phase_j_after_a2"] == "NOT_STARTED"

    if check_repository:
        descriptors = _load(DESCRIPTORS)
        descriptor = next(item for item in descriptors["sources"] if item["source_id"] == machine["selected_h2_source"])
        assert descriptor["source_contract_id"] == machine["source_contract"]
        assert descriptor["source_family"] == source["source_family"]
        assert descriptor["activation_state"] == "eligible" and descriptor["runtime_executable"] is False
        descriptor_map = {item["source_id"]: item for item in descriptors["sources"]}
        twt49u = descriptor_map["H2-TWSE-EXRIGHT-FINAL-TWT49U"]
        assert twt49u["source_role"] == "optional_licensed_provider" and twt49u["activation_state"] == "inactive"
        for source_id in ("H2-TWSE-CAPITAL-REDUCTION-WEB", "H2-TPEX-CAPITAL-REDUCTION-WEB"):
            assert descriptor_map[source_id]["source_role"] == "manual_verification"
            assert descriptor_map[source_id]["activation_state"] == "inactive"
        for source_id in ("H2-TWSE-PAR-SPLIT-CONSOLIDATION-GAP", "H2-TPEX-PAR-SPLIT-CONSOLIDATION-GAP"):
            assert descriptor_map[source_id]["source_role"] == "source_gap"
            assert descriptor_map[source_id]["activation_state"] == "blocked"

        authority = _load(SOURCES)
        official = next(item for item in authority["sources"] if item["source_id"] == machine["selected_h2_source"])
        assert official["endpoint_or_resource"] == source["endpoint"]
        assert official["event_stage"] == source["source_evidence_stage"]
        assert official["license_authority"].startswith("ODGL 1.0")
        assert "89748" in official["license_authority"]
        assert official["event_stage"] == "preannouncement"
        assert official["license_authority"].startswith("ODGL 1.0")
        assert official["historical_records_exist"] is False
        assert official["bounded_historical_retrieval_supported"] is False
        assert official["coverage_mode"] == "current preannouncement table"

        catalog = _load(CATALOG)
        capabilities = {item["capability_id"]: item for item in catalog["data_need_capabilities"]}
        assert capabilities["corporate_action_context"]["runtime_executable"] is False
        assert capabilities["recent_performance"]["runtime_executable"] is True
        routing = _load(ROUTING)
        routes = {item["capability_id"]: item for item in routing["routes"]}
        h3_route = routes["recent_performance"]
        assert h3_route["runtime_executable"] is True
        assert h3_route["selected_executor_id"] == "phase_h_h3_twse_recent_performance_executor"
        assert h3_route["supported_markets"] == ["TWSE"]
        assert "at most three unique official STOCK_DAY monthly GETs per execution; retry zero" in h3_route["estimated_operation_rule"]
        h3_tpex = next(item for item in h3_route["source_authority_states"] if item.get("market") == "TPEX")
        assert h3_tpex["activation_state"] == "blocked"
        h2_route = routes["corporate_action_context"]
        assert h2_route["runtime_executable"] is False and h2_route["selected_executor_id"] is None
        h4_routes = routing["derived_contracts"]
        assert len(h4_routes) == 1 and h4_routes[0]["routing_status"] == "derived_zero_network"
        assert h4_routes[0]["selected_executor_id"] is None
        registry = _load(REGISTRY)
        assert not any(item.get("executor_id") == machine["future_executor_id"] for item in registry["executors"])

        ledger = _load(H3_LEDGER)
        assert ledger["status"] == "OWNER_ACTIVATION_ACCEPTED"
        assert ledger["selected_route"]["executor_id"] == h3_route["selected_executor_id"]
        normalizer = H2_NORMALIZER.read_text(encoding="utf-8")
        assert "def normalize_twse_twt48u_all" in normalizer
        assert 'lifecycle="scheduled"' in normalizer and 'stage="preannouncement"' in normalizer
        assert "ambiguous_exact_target_rows" in normalizer
        h4_text = H4_IMPLEMENTATION.read_text(encoding="utf-8")
        assert "h3_requires_exactly_one_available_baseline" in h4_text
        assert 'state, guard = "coverage_incomplete"' in h4_text
        assert "uncovered" in h4_text and "declared_scope_complete" in h4_text
        result_schema = _load(RESULT_SCHEMA)
        result_evidence = result_schema["properties"]["targets"]["items"]["properties"]["evidence"]["properties"]
        assert {"corporate_action_context", "recent_performance", "discontinuity_safety"}.issubset(result_evidence)
        audit_schema = _load(AUDIT_SCHEMA)
        assert audit_schema["properties"].get("phase_h_governance") is not None
        request_v1 = _load(EXECUTION_REQUEST_V1)
        request_v2 = _load(EXECUTION_REQUEST_V2)
        assert "parameters" not in request_v1["properties"]
        assert "parameters" in request_v2["properties"]
        return {"status": "PASS", "gate": "J-B04-A2", "h2": "INACTIVE", "h3_twse": "ACTIVE", "market_requests": 0}
    return {"status": "PASS", "gate": "J-B04-A2", "repository_cross_check": False}


def validate() -> dict[str, Any]:
    return validate_contract(_load(RECORD), check_repository=True)


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
