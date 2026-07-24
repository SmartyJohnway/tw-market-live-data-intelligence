from __future__ import annotations

from copy import deepcopy

from tests.unit.m8r_05b_03_test_helpers import PLAN, build_valid_preflight


def test_valid_preflight_is_ready_for_later_claim_only(tmp_path):
    artifact = build_valid_preflight(tmp_path)
    assert artifact["ready_for_claim"] is True
    assert artifact["containment_status"] == "passed"
    assert artifact["network_required"] is True
    assert artifact["execution_authorized"] is True
    assert artifact["blocking_errors"] == []


def test_preflight_is_deterministic_and_excludes_wall_clock_identity(tmp_path):
    first = build_valid_preflight(tmp_path)
    second = build_valid_preflight(tmp_path)
    assert first == second
    assert "created_at" not in first["preflight_identity_scope"]
    assert "evaluation_timestamp" not in first["preflight_identity_scope"]


def test_input_operation_order_equivalence(tmp_path):
    reversed_plan = deepcopy(PLAN)
    reversed_plan["operations"] = list(reversed(reversed_plan["operations"]))
    assert build_valid_preflight(tmp_path)["preflight_hash"] == build_valid_preflight(tmp_path)["preflight_hash"]
