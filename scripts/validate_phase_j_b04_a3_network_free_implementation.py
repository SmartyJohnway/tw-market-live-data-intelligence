"""Validate the J-B04-A3 network-free implementation acceptance record."""
from __future__ import annotations

import hashlib
import ast
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A3_NETWORK_FREE_IMPLEMENTATION_ACCEPTANCE_2026-10-08.json"
BASELINE = "a833a5728501d99b942928fdebb790a993a5e838"
H4_BASELINE_SHA256 = "91163c3f1988c75c5f4b413d109e19d646b5ad9bfcb40e96a485a356f9180727"
FROZEN_SCHEMA_HASHES = {
    "schemas/corporate_action_context_evidence.v1.schema.json": "91f6613e595d030dbdc27fecd744f698de5cf5cb6bad68fd661bd5cbbfba93c2",
    "schemas/recent_performance_evidence.v1.schema.json": "b39708b3f8407f092037b133ecccae0452d80e68fba1221fc9afdd35a6a3390d",
    "schemas/discontinuity_safety_evidence.v1.schema.json": "98dad43636d977840cbcb1a4e4c4954c95cbefd9b1df09c6de4230c17326b018",
    "schemas/unified_market_evidence_result.v3.schema.json": "9269fc9e5e07884fa2de791eae902ee57b3d937dbb793318ca4aff1a93fc5bcb",
    "schemas/unified_market_evidence_audit_package.v3.schema.json": "94208ac6f4c13bcde294de1a8c7cf6be23245d738b5dcd36fffcac1ab134c4cc",
    "schemas/unified_market_evidence_execution_request.v1.schema.json": "0604c43f4b5c6292ffa2ad47318899196d32013fb4e7948f9198d7bbe20d5c46",
}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate_json_member:{key}")
        result[key] = value
    return result


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_contract(record: dict[str, Any], *, check_repository: bool = False) -> dict[str, Any]:
    expected = {
        "gate": "J-B04-A3",
        "baseline_main": BASELINE,
        "implementation_status": "NETWORK_FREE_IMPLEMENTED",
        "executor_id": "phase_h_h2_twse_exright_pre_executor",
        "source_id": "H2-TWSE-EXRIGHT-PRE-OPENAPI",
        "source_contract": "TWT48U_ALL",
        "representative_market": "TWSE",
        "source_stage": "preannouncement",
        "source_lifecycle": "scheduled",
        "h2_max_gets": 1,
        "h2_retry_count": 0,
        "h3_dependency_required": True,
        "dependency_target_match_required": True,
        "dependency_artifact_identity_required": True,
        "h3_window_is_h2_query_parameter": False,
        "h3_window_is_h2_assembly_binding": True,
        "twt48u_declared_scope_complete": False,
        "no_row_proves_historical_no_event": False,
        "h2_historical_completeness_claimed": False,
        "twt49u_required": False,
        "h4_semantics_modified": False,
        "h4_derived_zero_network": True,
        "h4_verified_artifact_path_implemented": True,
        "result_v3_schema_changed": False,
        "audit_v3_schema_changed": False,
        "h2_evidence_schema_changed": False,
        "h3_evidence_schema_changed": False,
        "h4_evidence_schema_changed": False,
        "scheduled_promoted_to_effective": False,
        "local_reference_calculation_allowed": False,
        "hidden_h2_acquisition_allowed": False,
        "cross_target_dependency_allowed": False,
        "canonical_h2_runtime": "INACTIVE",
        "canonical_h2_selected_executor": None,
        "j_b04": "BLOCKING",
        "phase_j": "NOT_STARTED",
        "mcp_tool_count": 6,
        "market_GETs": 0,
        "market_HEADs": 0,
        "market_POSTs": 0,
    }
    machine = record["machine_assertions"]
    for key, value in expected.items():
        assert machine.get(key) == value, f"machine_assertion_mismatch:{key}"
    assert record["disposition"] == "J_B04_A3_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_RE_REVIEW"
    assert record["disposition"] == machine["disposition"]
    assert machine["active_phase_h_source_count"] == 4
    assert machine["h3_twse"] == "ACTIVE" and machine["h3_tpex"] == "BLOCKED_NON_EXECUTABLE"
    assert machine["j_b01"] == machine["j_b02"] == machine["j_b03"] == "CLOSED"
    assert machine["j_b04_a3"] == "IMPLEMENTED_AWAITING_INDEPENDENT_REVIEW"
    assert machine["j_b04_a3_r1"] == "READY_FOR_EXACT_HEAD_INDEPENDENT_RE_REVIEW"
    assert machine["j_b04_a3_r2"] == "READY_FOR_EXACT_HEAD_INDEPENDENT_RE_REVIEW"
    assert machine["typed_h2_failure_h4_states"] == {
        "source_failed": "coverage_incomplete",
        "binding_failed": "coverage_incomplete",
    }
    assert machine["dependency_approval_closure"] == "approved_child_operations_only"
    assert machine["h2_source_activation_state"] == "eligible"
    assert machine["h2_source_runtime_executable"] is False
    assert machine["h4_implementation"] == "EXISTING_UNCHANGED_ZERO_NETWORK"

    baseline = record["baseline_comparison"]
    assert baseline["exact_baseline"] == BASELINE
    exact_base = baseline["exact_base"]
    r1_head = baseline["r1_head"]
    assert exact_base["revision"] == BASELINE
    assert r1_head["revision"] == baseline["tested_r1_head"]
    assert exact_base["command"] == r1_head["command"]
    assert exact_base["environment"] == r1_head["environment"]
    assert exact_base["fixture_manifest"] == r1_head["fixture_manifest"]
    assert exact_base["collected_nodes"] == r1_head["collected_nodes"]
    for result in (exact_base, r1_head):
        assert result["collected_count"] == len(result["collected_nodes"])
        assert result["passed_count"] == len(result["passed_nodes"])
        assert result["failed_count"] == len(result["failed_nodes"])
        assert result["skipped_count"] == len(result["skipped_nodes"])
        assert result["deselected_count"] == len(result["deselected_nodes"])
        assert set(result["passed_nodes"]).issubset(result["collected_nodes"])
        assert set(result["failed_nodes"]).issubset(result["collected_nodes"])
        assert set(result["skipped_nodes"]).issubset(result["collected_nodes"])
        assert set(result["deselected_nodes"]).isdisjoint(result["collected_nodes"])
        assert set(result["failure_codes"]) == set(result["failed_nodes"])
    computed_delta = sorted(set(r1_head["failed_nodes"]) - set(exact_base["failed_nodes"]))
    assert baseline["new_failure_nodes"] == computed_delta
    assert baseline["new_failure_delta"] == len(computed_delta)
    assert baseline["new_failure_delta"] == baseline["computed_new_failure_delta"]
    assert baseline["new_failure_delta"] == 0
    assert baseline["new_a3_owned_regression_failures"] == computed_delta
    assert baseline["exact_base"]["passed_count"] == 47
    assert baseline["r1_head"]["passed_count"] == 47
    assert baseline["exact_base"]["failed_count"] == baseline["r1_head"]["failed_count"] == 0
    r2_head = baseline["r2_head"]
    assert baseline["tested_r2_head"] == r2_head["revision"]
    assert r2_head["command"] == exact_base["command"]
    assert r2_head["environment"] == exact_base["environment"]
    assert r2_head["fixture_manifest"] == exact_base["fixture_manifest"]
    assert r2_head["collected_nodes"] == exact_base["collected_nodes"]
    assert r2_head["collected_count"] == len(r2_head["collected_nodes"]) == 47
    assert r2_head["passed_count"] == len(r2_head["passed_nodes"]) == 47
    assert r2_head["failed_count"] == len(r2_head["failed_nodes"]) == 0
    r2_delta = sorted(set(r2_head["failed_nodes"]) - set(exact_base["failed_nodes"]))
    assert baseline["r2_new_failure_nodes"] == r2_delta
    assert baseline["r2_new_failure_delta"] == len(r2_delta) == 0

    if "default_ci_comparison" in record:
        comparison = record["default_ci_comparison"]
        base_ci, head_ci = comparison["base"], comparison["head"]
        base_failed, head_failed = set(base_ci["failed_nodes"]), set(head_ci["failed_nodes"])
        new_failed = sorted(head_failed - base_failed)
        resolved = sorted(base_failed - head_failed)
        shared = sorted(base_failed & head_failed)
        assert comparison["exact_base_revision"] == BASELINE
        assert comparison["r2_implementation_revision"] == comparison["head_revision"]
        assert base_ci["revision"] == BASELINE
        assert head_ci["revision"] == comparison["r2_implementation_revision"]
        assert base_ci["command"] == head_ci["command"] == "python scripts/run_test_profile.py default-ci --json"
        assert base_ci["environment"] == head_ci["environment"]
        for result in (base_ci, head_ci):
            assert result["failed_count"] == len(result["failed_nodes"])
            assert set(result["failure_codes"]) == set(result["failed_nodes"])
            assert result["collected_count"] == result["selected_count"] + result["deselected_count"]
            assert result["selected_count"] == result["passed_count"] + result["failed_count"] + result["skipped_count"]
        assert comparison["shared_failure_nodes"] == shared
        assert comparison["new_failure_nodes"] == new_failed
        assert comparison["resolved_failure_nodes"] == resolved
        assert comparison["default_ci_new_failure_delta"] == len(new_failed)
        assert comparison["failure_codes_base"] == base_ci["failure_codes"]
        assert comparison["failure_codes_head"] == head_ci["failure_codes"]
        assert all(base_ci["failure_codes"][node] == head_ci["failure_codes"][node] for node in shared)
        if head_ci["failed_count"]:
            assert comparison["default_ci_new_failure_delta"] == 0

    checks = record["acceptance_evidence"]
    assert checks["h2_executor_tests"] == "PASS"
    assert checks["planner_dispatch_tests"] == "PASS"
    assert checks["clean_a3_projection"] == "PASS"
    assert checks["result_audit_handoff"] == "PASS"
    assert checks["real_partial_h4_state"] == "coverage_incomplete"
    assert checks["real_partial_ordinary_return_interpretation"] == "blocked"
    assert checks["fixture_reference_available"] == "PASS"
    assert checks["fixture_reference_unavailable"] == "PASS"
    assert checks["h3_unavailable_h2_calls"] == 0
    assert checks["h3_unavailable_h4_artifact"] is False
    assert checks["unexpected_internal_exception_propagates"] is True
    assert checks["network_isolation"] == "PASS"
    assert checks["multi_target_h3_h2_h4"].startswith("PASS:")
    assert checks["partial_multi_target_outcome"].startswith("PASS:")
    assert checks["dependency_preflight"].startswith("PASS:")
    assert checks["claim_before_dependency_failure"].startswith("PASS:")
    assert checks["typed_source_failed_h4"].startswith("PASS:")
    assert checks["typed_binding_failed_h4"].startswith("PASS:")
    assert checks["h3_unusable_h2_unattempted_no_h4"].startswith("PASS:")
    assert checks["unexpected_h2_failure_without_typed_evidence"].startswith("PASS:")
    assert checks["approval_closure_scoped_to_approved_child"].startswith("PASS:")
    assert record["validation"]["focused_tests"]["a3_owned_tests"]["passed"] == 55

    scope = record["scope_and_state"]
    assert scope["market_GETs"] == scope["market_HEADs"] == scope["market_POSTs"] == 0
    for key in ("schemas_changed", "source_activation_changed", "routing_activation_changed", "catalog_activation_changed", "h4_semantics_changed", "mcp_changed"):
        assert scope[key] is False, f"scope_changed:{key}"
    assert scope["h2_runtime"] == "INACTIVE"
    assert scope["j_b04"] == "BLOCKING" and scope["phase_j"] == "NOT_STARTED"
    assert scope["mcp_tool_count"] == 6
    assert record["network_audit"]["market_request_counts"] == {"GET": 0, "HEAD": 0, "POST": 0}

    if check_repository:
        descriptors = _load(ROOT / "config/phase_h_h2_dormant_source_descriptors.json")["sources"]
        descriptor = next(item for item in descriptors if item["source_id"] == machine["source_id"])
        assert descriptor["activation_state"] == "eligible" and descriptor["runtime_executable"] is False
        catalog = _load(ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
        capability = next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == "corporate_action_context")
        assert capability["runtime_executable"] is False
        routing = _load(ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
        route = next(item for item in routing["routes"] if item["capability_id"] == "corporate_action_context")
        assert route["runtime_executable"] is False and route["selected_executor_id"] is None
        assert route["routing_status"] == "plan_only"
        assert route["candidate_executor_ids"] == [machine["executor_id"]]
        registry = _load(ROOT / "config/m8r_06_03_executor_registry_metadata.json")
        candidate = [item for item in registry["executors"] if item["executor_id"] == machine["executor_id"]]
        assert len(candidate) == 1 and candidate[0]["network_required"] is True
        assert candidate[0]["expected_evidence_contract"] == "corporate_action_context_evidence.v1"
        h3 = next(item for item in routing["routes"] if item["capability_id"] == "recent_performance")
        assert h3["runtime_executable"] is True
        assert h3["selected_executor_id"] == "phase_h_h3_twse_recent_performance_executor"
        tpex = next(item for item in h3["source_authority_states"] if item.get("market") == "TPEX")
        assert tpex["activation_state"] == "blocked"
        assert (ROOT / "server/services/phase_h_h2_twse_exright_executor.py").is_file()
        assert _sha256(ROOT / "server/services/phase_h_discontinuity_safety.py") == H4_BASELINE_SHA256
        for rel, expected_sha in FROZEN_SCHEMA_HASHES.items():
            assert _sha256(ROOT / rel) == expected_sha, f"frozen_schema_changed:{rel}"
        tool_tree = ast.parse((ROOT / "server/unified_mcp/tool_contracts.py").read_text(encoding="utf-8"))
        tool_assignment = next(
            node for node in tool_tree.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
            and node.target.id == "TOOL_DESCRIPTIONS"
        )
        assert len(ast.literal_eval(tool_assignment.value)) == 6
        assert _sha256(ROOT / "skills/tw-market-evidence-agent/SKILL.md") == "72748e8f5c64784d316239a6cfab754cf522650de6dc07dd5d5ed7e3d55ecf52"
        assert record["protected_hashes"]["h4_sha256"] == H4_BASELINE_SHA256
        return {"status": "PASS", "gate": "J-B04-A3", "repository_cross_check": True, "mcp_tool_count": 6}
    return {"status": "PASS", "gate": "J-B04-A3", "repository_cross_check": False}


def validate() -> dict[str, Any]:
    return validate_contract(_load(RECORD), check_repository=True)


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
