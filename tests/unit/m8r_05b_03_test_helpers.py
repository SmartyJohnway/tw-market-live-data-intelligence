from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding


ROOT = Path(__file__).resolve().parents[2]
PLAN = json.loads((ROOT / "tests/fixtures/m8r_05b_01/golden/single_executable_plan.json").read_text(encoding="utf-8"))
EVALUATION_TIMESTAMP = "2026-07-23T00:30:00Z"
CLAIM_TIMESTAMP = "2026-07-23T00:31:00Z"


def artifacts(plan: dict | None = None, *, expires_at: str = "2026-07-23T01:00:00Z", decision: str = "approved"):
    selected_plan = deepcopy(plan or PLAN)
    operation_ids = [item["operation_id"] for item in selected_plan["operations"]]
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
            "approved_operation_ids": operation_ids,
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


def default_mock_adapter(request, context):
    from scripts.m8r_05b_03.dispatch import request_identity

    req_id, req_hash = request_identity(request)
    contract = request.get("evidence_contract") or "bounded normalized source observation with source health/currentness"
    return {
        "schema_version": "unified_market_evidence_operation_result.v1",
        "operation_id": request["operation_id"],
        "execution_request_id": req_id,
        "execution_request_hash": req_hash,
        "executor_id": request["executor_id"],
        "capability_id": request["capability_id"],
        "evidence_contract": contract,
        "status": "succeeded",
        "error_code": None,
        "result_item_count": 0,
        "evidence_artifacts": [],
        "warnings": [],
    }


def runtime_registration(plan: dict | None = None, adapter=None, **overrides):
    from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistration

    entry = registry_metadata(plan)["executors"][0]
    values = {
        "executor_id": entry["executor_id"],
        "capability_id": entry["capability_id"],
        "market": entry["market"],
        "supported_security_types": tuple(entry["supported_security_types"]),
        "expected_evidence_contract": entry["expected_evidence_contract"],
        "network_required": entry["network_required"],
        "bounded_execution_supported": entry["bounded_execution_supported"],
        "timeout_seconds": entry["timeout_seconds"],
        "maximum_result_items": entry["maximum_result_items"],
        "output_policy": entry["output_policy"],
        "adapter": adapter or default_mock_adapter,
        "fake_adapter": True,
    }
    values.update(overrides)
    return RuntimeAdapterRegistration(**values)
