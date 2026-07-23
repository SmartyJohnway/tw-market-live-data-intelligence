"""Offline contract checks for the M8R-05B-00 preflight artifacts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def load(path): return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_handoff_contract_is_non_authorizing_and_immutably_bound():
    contract = load("docs/data_capabilities/m8r_05b_orchestration_handoff_contract.json")
    required = {"original_request_hash", "normalized_request_hash", "f3_validation_output_hash", "security_master_evidence_references", "security_master_artifact_hashes", "capability_catalog_hash", "planner_version", "routing_matrix_version", "routing_matrix_hash", "handoff_contract_version", "handoff_contract_hash"}
    assert required <= set(contract["input"]["immutable_bindings"])
    assert contract["input"]["f3_invariants_preserved"] == {"operation_count_computed": False, "operation_count": 0, "orchestrator_projection_required": True}
    assert "SHA-256" in contract["canonical_hash_rule"]["serialization"]
    assert "deterministic" in contract["canonical_hash_rule"]["operation_id"]
    assert "authorizes execution" in contract["operation_record_proposal"]["authorization_statement"]
    assert contract["planning_eligibility"]["session_status_policy"]
    assert "network invocations" in contract["planning_eligibility"]["derived_capability_policy"]

def test_routing_alias_and_route_safety_rules():
    routes = load("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.json")["routes"]
    for route in routes:
        assert route["approval_required"] is route["capability_requires_execution_approval"]
        if route["provisional"]:
            assert route["routing_status"] != "resolved"
        if route["capability_id"] in {"identity", "source_currentness", "evidence_quality"}:
            assert route["network_required"] is False
            assert route["selected_executor_id"] is None
    session = next(x for x in routes if x["capability_id"] == "session_status")
    assert session["routing_status"] == "blocked" and session["blocking_reasons"]

def test_phase_dependencies_and_execution_boundaries():
    phases = load("docs/data_capabilities/m8r_05b_implementation_plan.json")["phases"]
    by_id = {p["task_id"]: p for p in phases}
    first, second, third = (by_id[x] for x in ["M8R-05B-01-DETERMINISTIC-ORCHESTRATION-PLAN-PROJECTION", "M8R-05B-02-OWNER-APPROVAL-AND-EXECUTION-BINDING", "M8R-05B-03-CONTROLLED-UNIFIED-MARKET-EVIDENCE-ORCHESTRATOR"])
    assert first["network_allowed"] is False and first["execution_allowed"] is False
    assert second["execution_allowed"] is False and second["approval_allowed"] is True
    assert "M8R-05B-01-DETERMINISTIC-ORCHESTRATION-PLAN-PROJECTION" in third["dependencies"]
    assert "M8R-05B-02-OWNER-APPROVAL-AND-EXECUTION-BINDING" in third["dependencies"]
