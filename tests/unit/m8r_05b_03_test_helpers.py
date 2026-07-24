from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding


ROOT = Path(__file__).resolve().parents[2]
PLAN = json.loads((ROOT / "tests/fixtures/m8r_05b_01/golden/single_executable_plan.json").read_text(encoding="utf-8"))
EVALUATION_TIMESTAMP = "2026-07-23T00:30:00Z"


def artifacts(plan: dict | None = None, *, expires_at: str = "2026-07-23T01:00:00Z", decision: str = "approved"):
    selected_plan = deepcopy(plan or PLAN)
    operation_id = selected_plan["operations"][0]["operation_id"]
    authorization = build_execution_authorization(
        selected_plan,
        {
            "decision": decision,
            "decision_reason": "unit-test",
            "owner_identity_reference": "owner-test",
            "owner_review_reference": "review-test",
            "reviewed_at": "2026-07-23T00:00:00Z",
            "issued_at": "2026-07-23T00:00:00Z",
            "expires_at": expires_at,
            "single_use": True,
            "replay_policy": "deny_replay",
            "maximum_use_count": 1,
            "approval_scope_mode": "selected_operations",
            "approved_operation_ids": [operation_id],
            "approved_batch_group_ids": [],
            "approved_batch_membership": {},
        },
    )
    binding = build_consumption_binding(authorization)
    state = {
        "authorization_id": binding["authorization_id"],
        "authorization_hash": binding["authorization_hash"],
        "consumption_binding_id": binding["consumption_binding_id"],
        "consumption_binding_hash": binding["consumption_binding_hash"],
        "registry_contract_version": "m8r_05b_03.v1",
        "state": "unused",
    }
    return selected_plan, authorization, binding, state


def registry_metadata(plan: dict | None = None, **overrides):
    selected_plan = plan or PLAN
    operation = selected_plan["operations"][0]
    entry = {
        "executor_id": operation["executor_id"],
        "capability_id": operation["capability_id"],
        "market": operation["market"],
        "supported_security_types": sorted(operation["security_types"]),
        "expected_evidence_contract": operation["expected_evidence_contract"],
        "network_required": operation["network_required"],
        "bounded_execution_supported": True,
        "timeout_seconds": 15,
        "maximum_result_items": 50,
        "output_policy": "contained_artifact_only",
    }
    entry.update(overrides)
    return {"schema_version": "m8r_05b_03_executor_registry_metadata.v1", "executors": [entry]}


def build_valid_preflight(output_root: Path):
    from scripts.m8r_05b_03.preflight import build_orchestrator_preflight

    plan, authorization, binding, state = artifacts()
    return build_orchestrator_preflight(
        plan,
        authorization,
        binding,
        supplied_consumption_state=state,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        executor_registry_metadata=registry_metadata(plan),
        output_root=str(output_root),
    )
