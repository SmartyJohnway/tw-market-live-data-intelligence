from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight
from tests.unit.m8r_05b_03_test_helpers import EVALUATION_TIMESTAMP, artifacts, registry_metadata


def _assert_rejected(plan, authorization, binding, state, tmp_path, code):
    with pytest.raises(OrchestrationError, match=code):
        build_orchestrator_preflight(
            plan,
            authorization,
            binding,
            supplied_consumption_state=state,
            evaluation_timestamp=EVALUATION_TIMESTAMP,
            executor_registry_metadata=registry_metadata(plan),
            output_root=str(tmp_path),
        )


def test_rejected_authorization_fails_preflight(tmp_path):
    plan, authorization, binding, state = artifacts(decision="rejected")
    _assert_rejected(plan, authorization, binding, state, tmp_path, "authorization_rejected")


def test_expired_authorization_fails_preflight(tmp_path):
    plan, authorization, binding, state = artifacts(expires_at="2026-07-23T00:15:00Z")
    _assert_rejected(plan, authorization, binding, state, tmp_path, "authorization_expired")


def test_authorization_id_and_hash_drift_fail_preflight(tmp_path):
    plan, authorization, binding, state = artifacts()
    authorization = deepcopy(authorization)
    authorization["authorization_id"] = "umea-v1-00000000000000000000"
    _assert_rejected(plan, authorization, binding, state, tmp_path, "authorization_id_mismatch")

    plan, authorization, binding, state = artifacts()
    authorization = deepcopy(authorization)
    authorization["authorization_hash"] = "0" * 64
    _assert_rejected(plan, authorization, binding, state, tmp_path, "authorization_hash_mismatch")


def test_plan_and_scope_drift_fail_preflight(tmp_path):
    plan, authorization, binding, state = artifacts()
    drifted_plan = deepcopy(plan)
    drifted_plan["plan_hash"] = "0" * 64
    _assert_rejected(drifted_plan, authorization, binding, state, tmp_path, "plan_hash_mismatch")

    plan, authorization, binding, state = artifacts()
    authorization = deepcopy(authorization)
    authorization["scope_hash"] = "0" * 64
    _assert_rejected(plan, authorization, binding, state, tmp_path, "scope_hash_mismatch")


def test_consumption_binding_and_supplied_state_drift_fail_preflight(tmp_path):
    plan, authorization, binding, state = artifacts()
    binding = deepcopy(binding)
    binding["consumption_binding_hash"] = "0" * 64
    _assert_rejected(plan, authorization, binding, state, tmp_path, "consumption_binding_hash_mismatch")

    plan, authorization, binding, state = artifacts()
    state = deepcopy(state)
    state["authorization_hash"] = "0" * 64
    _assert_rejected(plan, authorization, binding, state, tmp_path, "consumption_authorization_mismatch")


def test_operation_set_and_batch_membership_drift_fail_preflight(tmp_path):
    plan, authorization, binding, state = artifacts()
    authorization = deepcopy(authorization)
    authorization["approved_operation_ids"] = []
    _assert_rejected(plan, authorization, binding, state, tmp_path, "authorization_schema_invalid")

    plan, authorization, binding, state = artifacts()
    binding = deepcopy(binding)
    binding["approved_batch_membership"] = {"umeop-batch-v1-00000000000000000000": ["umeop-op-v1-00000000000000000000"]}
    _assert_rejected(plan, authorization, binding, state, tmp_path, "batch_membership_mismatch")
