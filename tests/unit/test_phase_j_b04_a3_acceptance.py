from __future__ import annotations

import copy

import pytest

from scripts.validate_phase_j_b04_a3_network_free_implementation import (
    RECORD,
    _load,
    validate_contract,
)


def test_a3_acceptance_record_passes_machine_contract() -> None:
    record = _load(RECORD)
    assert validate_contract(record)["status"] == "PASS"


def test_a3_validator_rejects_head_only_failure_with_a_false_zero_delta() -> None:
    record = copy.deepcopy(_load(RECORD))
    baseline = record["baseline_comparison"]
    head = baseline["r1_head"]
    node = head["passed_nodes"].pop()
    head["passed_count"] -= 1
    head["failed_nodes"].append(node)
    head["failed_count"] += 1
    head["failure_codes"][node] = "fixture_hash_mismatch"
    with pytest.raises(AssertionError):
        validate_contract(record)


def test_a3_validator_computes_default_ci_new_failure_delta() -> None:
    record = copy.deepcopy(_load(RECORD))
    base = {
        "revision": "a833a5728501d99b942928fdebb790a993a5e838",
        "command": "python scripts/run_test_profile.py default-ci --json",
        "environment": {"python": "3.11.16", "security_master": "absent"},
        "failed_count": 1,
        "failed_nodes": ["tests/test_shared.py::test_environment_failure"],
        "failure_codes": {"tests/test_shared.py::test_environment_failure": "security_master_not_initialized"},
    }
    head = copy.deepcopy(base) | {"revision": "r2-implementation-sha"}
    record["default_ci_comparison"] = {
        "exact_base_revision": "a833a5728501d99b942928fdebb790a993a5e838",
        "r2_implementation_revision": "r2-implementation-sha",
        "head_revision": "r2-implementation-sha",
        "base": base,
        "head": head,
        "shared_failure_nodes": base["failed_nodes"],
        "new_failure_nodes": [],
        "resolved_failure_nodes": [],
        "default_ci_new_failure_delta": 0,
    }
    assert validate_contract(record)["status"] == "PASS"
    record["default_ci_comparison"]["new_failure_nodes"] = ["tests/test_new.py::test_regression"]
    record["default_ci_comparison"]["default_ci_new_failure_delta"] = 0
    with pytest.raises(AssertionError):
        validate_contract(record)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("canonical_h2_runtime", "ACTIVE"),
        ("canonical_h2_selected_executor", "phase_h_h2_twse_exright_pre_executor"),
        ("h2_max_gets", 2),
        ("h2_retry_count", 1),
        ("twt49u_required", True),
        ("h2_historical_completeness_claimed", True),
        ("no_row_proves_historical_no_event", True),
        ("scheduled_promoted_to_effective", True),
        ("local_reference_calculation_allowed", True),
        ("h3_dependency_required", False),
        ("cross_target_dependency_allowed", True),
        ("dependency_artifact_identity_required", False),
        ("hidden_h2_acquisition_allowed", True),
        ("h4_semantics_modified", True),
        ("result_v3_schema_changed", True),
        ("audit_v3_schema_changed", True),
        ("phase_j", "STARTED"),
        ("j_b04", "CLOSED"),
        ("mcp_tool_count", 7),
        ("market_GETs", 1),
        ("market_HEADs", 1),
        ("market_POSTs", 1),
        ("typed_h2_failure_h4_states", {"source_failed": "clear", "binding_failed": "clear"}),
        ("dependency_approval_closure", "all_plan_children"),
    ],
)
def test_a3_validator_rejects_unsafe_mutations(key: str, value: object) -> None:
    record = copy.deepcopy(_load(RECORD))
    record["machine_assertions"][key] = value
    with pytest.raises(AssertionError):
        validate_contract(record)
