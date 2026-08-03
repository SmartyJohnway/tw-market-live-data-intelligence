from __future__ import annotations

import json
from copy import deepcopy

import pytest

from scripts.m8r_05b_01.canonical import plan_hash_and_id
from scripts.m8r_05b_01.planner import plan_identity_scope
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight, validate_preflight_hashes
from tests.unit.m8r_05b_03_test_helpers import EVALUATION_TIMESTAMP, PLAN, ROOT, artifacts, build_valid_preflight, registry_metadata


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
    assert first["preflight_hash"] == first["preflight_identity_hash"]
    assert first["preflight_id"] == "umeopf-v1-" + first["preflight_identity_hash"][:20]
    assert first["preflight_artifact_hash"] != first["preflight_identity_hash"]


def test_input_operation_order_equivalence(tmp_path):
    multi_plan = json.loads((ROOT / "tests/fixtures/m8r_05b_01/golden/batching_none_two_unique_batches.json").read_text(encoding="utf-8"))
    orig_plan, authorization, binding, state = artifacts(multi_plan)

    reversed_plan = deepcopy(orig_plan)
    reversed_plan["operations"] = list(reversed(reversed_plan["operations"]))
    scope = plan_identity_scope(reversed_plan)
    h, i = plan_hash_and_id(scope)
    reversed_plan["plan_hash"] = h
    reversed_plan["plan_id"] = i

    rev_plan, rev_auth, rev_binding, rev_state = artifacts(reversed_plan)

    pf_orig = build_orchestrator_preflight(
        orig_plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        executor_registry_metadata=registry_metadata(orig_plan),
        output_root=str(tmp_path),
    )
    pf_rev = build_orchestrator_preflight(
        reversed_plan,
        rev_auth,
        rev_binding,
        supplied_consumption_state=rev_state,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        executor_registry_metadata=registry_metadata(reversed_plan),
        output_root=str(tmp_path),
    )

    assert pf_orig["approved_operation_order"] == pf_rev["approved_operation_order"]


def test_preflight_hash_validation_rejects_identity_and_artifact_drift(tmp_path):
    artifact = build_valid_preflight(tmp_path)
    identity_drift = deepcopy(artifact)
    identity_drift["preflight_identity_scope"]["plan_id"] = "drift"
    with pytest.raises(OrchestrationError, match="preflight_identity_mismatch"):
        validate_preflight_hashes(identity_drift)

    artifact_drift = deepcopy(artifact)
    artifact_drift["warnings"] = ["drift"]
    with pytest.raises(OrchestrationError, match="preflight_artifact_hash_mismatch"):
        validate_preflight_hashes(artifact_drift)
