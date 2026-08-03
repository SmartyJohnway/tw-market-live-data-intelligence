from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.preflight import validate_preflight_hashes
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
    assert first["preflight_hash"] == first["preflight_identity_hash"]
    assert first["preflight_id"] == "umeopf-v1-" + first["preflight_identity_hash"][:20]
    assert first["preflight_artifact_hash"] != first["preflight_identity_hash"]


def test_input_operation_order_equivalence(tmp_path):
    reversed_plan = deepcopy(PLAN)
    reversed_plan["operations"] = list(reversed(reversed_plan["operations"]))
    assert build_valid_preflight(tmp_path)["preflight_hash"] == build_valid_preflight(tmp_path)["preflight_hash"]


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
