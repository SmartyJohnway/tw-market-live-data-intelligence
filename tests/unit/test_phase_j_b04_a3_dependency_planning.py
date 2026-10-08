"""Network-free tests for the explicit same-target J-B04 H3 dependency."""
from __future__ import annotations

from copy import deepcopy

from tests.unit.test_phase_h_h3_activation_candidate_preview import (
    _production_preview,
    _request,
)
from scripts.m8r_05b_01.canonical import plan_hash_and_id
from scripts.m8r_05b_01.planner import plan_identity_scope


def _plan(needs: tuple[str, ...]):
    request = _request("TWSE", "1423")
    request["data_needs"] = [
        {"type": value, "priority": "required", **({"parameters": {"lookback_trading_days": 20}} if value == "recent_performance" else {})}
        for value in needs
    ]
    return _production_preview(request, "TWSE", "1423")["orchestration_plan"]


def test_explicit_h2_h3_request_binds_one_same_target_h3_dependency() -> None:
    plan = _plan(("corporate_action_context", "recent_performance"))
    h2 = next(item for item in plan["operations"] if item["capability_id"] == "corporate_action_context")
    h3 = next(item for item in plan["operations"] if item["capability_id"] == "recent_performance")
    assert h2["dependency_operation_ids"] == [h3["operation_id"]]
    assert h2["canonical_target_ids"] == h3["canonical_target_ids"] == ["TWSE:1423"]
    assert h2["executor_id"] is None
    assert h2["executor_invocation_eligible"] is False


def test_h2_alone_does_not_inject_h3_and_remains_non_executable() -> None:
    plan = _plan(("corporate_action_context",))
    h2 = next(item for item in plan["operations"] if item["capability_id"] == "corporate_action_context")
    assert h2["dependency_operation_ids"] == []
    assert h2["operation_status"] == "plan_only_not_executable"
    assert h2["executor_invocation_eligible"] is False


def test_h3_alone_does_not_inject_h2() -> None:
    plan = _plan(("recent_performance",))
    assert [item["capability_id"] for item in plan["operations"]] == ["recent_performance"]


def test_planning_repeats_with_deterministic_dependency_identity_and_hash() -> None:
    first = _plan(("corporate_action_context", "recent_performance"))
    second = _plan(("corporate_action_context", "recent_performance"))
    assert first["plan_id"] == second["plan_id"]
    assert first["plan_hash"] == second["plan_hash"]
    assert first["operations"] == second["operations"]


def test_dependency_is_in_operation_and_plan_hash_identity() -> None:
    plan = _plan(("corporate_action_context", "recent_performance"))
    changed = deepcopy(plan)
    h2 = next(item for item in changed["operations"] if item["capability_id"] == "corporate_action_context")
    h2["dependency_operation_ids"] = ["umeop-op-v1-00000000000000000000"]
    assert changed["operations"] != plan["operations"]
    changed_hash, _ = plan_hash_and_id(plan_identity_scope(changed))
    assert changed_hash != plan["plan_hash"]
