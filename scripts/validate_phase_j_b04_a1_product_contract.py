"""Validate the J-B04-A1 product contract against current repository authority."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A1_REPRESENTATIVE_CONVERSATIONAL_CORRECTNESS_PRODUCT_CONTRACT_2026-10-08.json"
PREFLIGHT = ROOT / "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json"
CATALOG = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json"
ROUTING = ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json"
H2_SOURCES = ROOT / "config/phase_h_h2_dormant_source_descriptors.json"
H2_MANIFEST = ROOT / "docs/governance/phase_h/PHASE_H_H_IMP_3_ACCEPTANCE_MANIFEST.json"
H4_MANIFEST = ROOT / "docs/governance/phase_h/PHASE_H_H_IMP_1_ACCEPTANCE_MANIFEST.json"
H3_LEDGER = ROOT / "docs/governance/phase_h/PHASE_H_H_ACT_H3_TWSE_RECENT_PERFORMANCE_ACCEPTANCE_LEDGER.json"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _route(routes: list[dict[str, Any]], capability: str) -> dict[str, Any]:
    matches = [item for item in routes if item.get("capability_id") == capability]
    assert len(matches) == 1, f"expected exactly one {capability} route"
    return matches[0]


def validate_contract(record: dict[str, Any], *, check_repository: bool = False) -> dict[str, Any]:
    contract = record["product_exit_contract"]
    assert contract["exit_standard"] == "bounded_conversational_correctness"
    assert contract["complete_h2_required_for_j_b04_closure"] is False
    assert contract["representative_market"] == "TWSE"
    window = contract["comparison_window"]
    assert window["comparison_window_authority"] == "H3 available baseline"
    assert window["h2_self_defined_window"] == "prohibited"
    subtype = contract["subtype_boundaries"]
    assert subtype["capital_reduction_positive_runtime_evidence_required_for_j_entry"] is False
    assert subtype["capital_reduction_source_gap_closed"] is False
    safety = contract["event_and_coverage_semantics"]
    assert safety["unsupported_relevant_subtype_safe_outcome"] == "coverage_incomplete"
    assert safety["ordinary_return_interpretation_when_coverage_incomplete"] == "blocked"
    assert safety["final_reference_required_for_all_j_b04_closure_paths"] is False
    assert safety["local_adjustment_allowed"] is False
    future = record["future_j_b04_exit_criteria"]
    assert future["normal_governed_twse_h2_route_required"] is True
    assert future["explicit_activation_and_approval_bound_execution_required"] is True
    assert future["bounded_live_source_acceptance_required"] is True
    assert future["reference_available_state_may_be_proved_by_deterministic_fixture"] is True
    assert future["final_reference_live_evidence_required_for_j_b04_closure"] is False
    assert future["complete_h2_coverage_required"] is False
    assert future["phase_h_completion_implied"] is False
    machine = record["machine_assertions"]
    assert machine["exit_standard"] == "bounded_conversational_correctness"
    assert machine["complete_h2_required_for_j_b04_closure"] is False
    assert machine["representative_market"] == "TWSE"
    assert machine["comparison_window_authority"] == "H3 available baseline"
    assert machine["h2_self_defined_window"] == "prohibited"
    assert machine["capital_reduction_runtime_positive_evidence_required_for_j_entry"] is False
    assert machine["capital_reduction_source_gap_closed"] is False
    assert machine["unsupported_relevant_subtype_safe_outcome"] == "coverage_incomplete"
    assert machine["ordinary_return_interpretation_when_coverage_incomplete"] == "blocked"
    assert machine["final_reference_required_for_all_j_b04_closure_paths"] is False
    assert machine["local_adjustment_allowed"] is False
    assert machine["tpex_h3_activation_required"] is False
    assert machine["h2_runtime_after_a1"] == "inactive"
    assert machine["j_b04_after_a1"] == "BLOCKING"
    assert machine["phase_j_after_a1"] == "NOT_STARTED"
    assert machine["mcp_tool_count"] == 6
    assert machine["market_GETs"] == machine["market_HEADs"] == machine["market_POSTs"] == 0
    assert record["authority_reconciliation"]["contradiction_review"]["direct_same_or_higher_authority_conflict"] is False

    state = record["post_a1_state"]
    assert state["J-B04"] == "BLOCKING"
    assert state["Phase J"] == "NOT_STARTED"
    assert state["phase_j_implementation_authorized"] is False
    assert state["MCP"] == 6
    assert state["H2 runtime"] == "INACTIVE"
    scope = record["scope_and_network"]
    assert scope["market_GETs"] == scope["market_HEADs"] == scope["market_POSTs"] == 0
    assert scope["mcp_tool_count"] == 6
    assert scope["phase_j_started"] is False
    assert all(scope[key] is False for key in (
        "production_code_changed", "schema_changed", "routing_changed",
        "catalog_authority_changed", "source_authority_changed", "MCP_changed",
        "H3_activation_changed", "H4_implementation_changed",
    ))

    matrix = {item["scenario_id"]: item for item in record["scenario_acceptance_matrix"]}
    assert set(matrix) == {"J1-13", "J1-14", "J1-15", "J1-16"}
    assert "coverage_incomplete" in matrix["J1-13"]["safe_branch"]
    assert "coverage_incomplete" in matrix["J1-14"]["safe_branch"]
    assert "no capital reduction occurred" in matrix["J1-15"]["safe_branch"]
    assert "no_material_discontinuity_detected" in matrix["J1-16"]["reference_rule"]

    if check_repository:
        preflight = _load(PREFLIGHT)
        historical = {item["blocker_id"]: item for item in preflight["j_blockers"]}
        assert historical["J-B04"]["scenario_ids"] == ["J1-13", "J1-14", "J1-15", "J1-16"]
        assert historical["J-B04"]["network_proof_eventually_required"] is True

        catalog = _load(CATALOG)
        capabilities = {item["capability_id"]: item for item in catalog["data_need_capabilities"]}
        assert capabilities["recent_performance"]["runtime_executable"] is True
        assert "TWSE" in capabilities["recent_performance"]["supported_markets"]
        assert capabilities["corporate_action_context"]["runtime_executable"] is False

        routing = _load(ROUTING)
        routes = routing["routes"]
        h3 = _route(routes, "recent_performance")
        assert h3["runtime_executable"] is True
        assert h3["selected_executor_id"] == "phase_h_h3_twse_recent_performance_executor"
        assert h3["supported_markets"] == ["TWSE"]
        tpex_authority = [item for item in h3["source_authority_states"] if item.get("market") == "TPEX"]
        assert len(tpex_authority) == 1
        assert tpex_authority[0]["activation_state"] == "blocked"
        h2 = _route(routes, "corporate_action_context")
        assert h2["runtime_executable"] is False and h2["selected_executor_id"] is None
        h4 = routing["derived_contracts"]
        assert len(h4) == 1 and h4[0]["evidence_id"] == "discontinuity_safety"
        assert h4[0]["routing_status"] == "derived_zero_network"
        assert h4[0]["runtime_executable"] is False and h4[0]["selected_executor_id"] is None

        descriptor = _load(H2_SOURCES)
        sources = {item["source_id"]: item for item in descriptor["sources"]}
        assert sources["H2-TWSE-EXRIGHT-PRE-OPENAPI"]["activation_state"] == "eligible"
        assert sources["H2-TWSE-EXRIGHT-PRE-OPENAPI"]["runtime_executable"] is False
        twse_final = sources["H2-TWSE-EXRIGHT-FINAL-TWT49U"]
        assert twse_final["source_role"] == "optional_licensed_provider"
        assert twse_final["activation_state"] == "inactive"
        for source_id in ("H2-TWSE-CAPITAL-REDUCTION-WEB", "H2-TPEX-CAPITAL-REDUCTION-WEB"):
            assert sources[source_id]["source_role"] == "manual_verification"
            assert sources[source_id]["activation_state"] == "inactive"
        for source_id in ("H2-TWSE-PAR-SPLIT-CONSOLIDATION-GAP", "H2-TPEX-PAR-SPLIT-CONSOLIDATION-GAP"):
            assert sources[source_id]["source_role"] == "source_gap"
            assert sources[source_id]["activation_state"] == "blocked"
        assert sources["H2-TPEX-EXRIGHT-PRE-OPENAPI"]["activation_state"] == "eligible"
        assert sources["H2-TPEX-EXRIGHT-FINAL-OPENAPI"]["activation_state"] == "eligible"

        h2_manifest = _load(H2_MANIFEST)
        assert h2_manifest["component"]["runtime_wiring"] == "none"
        assert h2_manifest["component"]["production_executor_registration"] == "none"
        h4_manifest = _load(H4_MANIFEST)
        assert h4_manifest["component"]["component_mode"] == "dormant_pure_zero_network"
        assert h4_manifest["component"]["executor"] == "none"
        h3_ledger = _load(H3_LEDGER)
        assert h3_ledger["status"] == "OWNER_ACTIVATION_ACCEPTED"
        assert h3_ledger["selected_route"]["executor_id"] == "phase_h_h3_twse_recent_performance_executor"
        return {"status": "PASS", "contract": "J-B04-A1", "h2": "INACTIVE", "h3_twse": "ACTIVE", "h3_tpex": "BLOCKED", "market_requests": 0}

    return {"status": "PASS", "contract": "J-B04-A1", "repository_cross_check": False}


def validate() -> dict[str, Any]:
    return validate_contract(_load(RECORD), check_repository=True)


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
