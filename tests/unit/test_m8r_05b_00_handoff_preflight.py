"""Offline contract checks for the M8R-05B-00 preflight artifacts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def load(path): return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_handoff_contract_is_non_authorizing_and_immutably_bound():
    contract = load("docs/data_capabilities/m8r_05b_orchestration_handoff_contract.json")
    required = {"original_request_hash", "normalized_request_hash", "f3_validation_output_hash", "security_master_evidence_references", "security_master_artifact_hashes", "capability_catalog_hash", "planner_version", "routing_matrix_version", "routing_matrix_hash", "handoff_contract_version", "handoff_contract_hash"}
    assert contract["execution_authorized"] is False
    assert required <= set(contract["input"]["immutable_bindings"])
    assert contract["input"]["f3_invariants_preserved"] == {"operation_count_computed": False, "operation_count": 0, "orchestrator_projection_required": True}
    scope = contract["plan_identity_scope"]
    semantic = {"schema_version", "input_bindings", "plan_status", "operations", "canonical_operation_ordering", "batch_groups", "accounting", "blocked_operations", "omitted_optional_capabilities", "package_approval_requirements", "planner_version", "routing_matrix_version", "routing_matrix_hash", "handoff_contract_version", "handoff_contract_hash"}
    assert semantic <= set(scope["included_fields"])
    assert {"planning_timestamp", "warning_display_text", "human_readable_display_messages", "presentation_formatting"} <= set(scope["excluded_fields"])
    policy = scope["warning_and_omission_hash_policy"]
    assert policy["warning_display_text"] == "excluded"
    assert {"code", "capability_id", "canonical_target_ids", "severity", "omission_reason"} <= set(policy["included_machine_readable_warning_fields"])
    assert "omitted_optional_capabilities" in policy
    assert "exact plan_hash" in scope["plan_id_plan_hash_relationship"]

def test_operation_status_representation_and_planning_accounting_are_safe():
    contract = load("docs/data_capabilities/m8r_05b_orchestration_handoff_contract.json")
    representation = contract["operation_record_proposal"]["representation_by_status"]
    assert representation["executable_pending_approval"]["executor_id"] == "required non-null"
    assert representation["plan_only_not_executable"]["batch_group_id"] == "must be null"
    assert representation["plan_only_not_executable"]["executor_invocation_eligible"] is False
    assert representation["blocked"]["blocking_reason_codes"] == "required non-empty"
    assert representation["omitted_optional"]["collection"] == "omitted_optional_capabilities"
    assert representation["omitted_optional"]["operation_record"] == "forbidden"
    assert "Only executable_pending_approval" in contract["operation_record_proposal"]["batch_membership_guard"]
    accounting = contract["ordering_and_batching"]["accounting"]
    assert "planned_evidence_bundle_count" in accounting and "evidence_bundle_count" not in accounting
    assert "M8R-05B-03 execution receipt" in accounting["actual_evidence_bundle_count"]
    assert "non-authorizing" in accounting["network_request_estimate"]

def test_routing_alias_and_route_safety_rules():
    routes = load("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.json")["routes"]
    for route in routes:
        assert route["approval_required"] is route["capability_requires_execution_approval"]
        if route["provisional"]: assert route["routing_status"] != "resolved"
        if route["capability_id"] in {"identity", "source_currentness", "evidence_quality"}:
            assert route["network_required"] is False and route["selected_executor_id"] is None
    session = next(x for x in routes if x["capability_id"] == "session_status")
    assert session["routing_status"] == "blocked" and session["blocking_reasons"]

def test_phase_dependencies_and_execution_boundaries():
    phases = load("docs/data_capabilities/m8r_05b_implementation_plan.json")["phases"]; by_id = {p["task_id"]: p for p in phases}
    first, second, third = (by_id[x] for x in ["M8R-05B-01-DETERMINISTIC-ORCHESTRATION-PLAN-PROJECTION", "M8R-05B-02-OWNER-APPROVAL-AND-EXECUTION-BINDING", "M8R-05B-03-CONTROLLED-UNIFIED-MARKET-EVIDENCE-ORCHESTRATOR"])
    assert first["network_allowed"] is False and first["execution_allowed"] is False
    assert second["execution_allowed"] is False and second["approval_allowed"] is True
    assert "M8R-05B-01-DETERMINISTIC-ORCHESTRATION-PLAN-PROJECTION" in third["dependencies"]
    assert "M8R-05B-02-OWNER-APPROVAL-AND-EXECUTION-BINDING" in third["dependencies"]
