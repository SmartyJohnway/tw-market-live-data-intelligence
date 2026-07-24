from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
from scripts.m8r_05b_03.registry import ExecutorRegistry


ROOT = Path(__file__).resolve().parents[2]
PLAN = json.loads((ROOT / "tests/fixtures/m8r_05b_01/golden/single_executable_plan.json").read_text(encoding="utf-8"))
TIMESTAMP = "2026-07-23T00:30:00Z"


def _artifacts():
    operation_id = PLAN["operations"][0]["operation_id"]
    authorization = build_execution_authorization(PLAN, {
        "decision": "approved", "decision_reason": "test", "owner_identity_reference": "owner-test",
        "owner_review_reference": "review-test", "reviewed_at": "2026-07-23T00:00:00Z",
        "issued_at": "2026-07-23T00:00:00Z", "expires_at": "2026-07-23T01:00:00Z",
        "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1,
        "approval_scope_mode": "selected_operations", "approved_operation_ids": [operation_id],
        "approved_batch_group_ids": [], "approved_batch_membership": {},
    })
    binding = build_consumption_binding(authorization)
    state = {key: binding[key] for key in ("authorization_id", "authorization_hash", "consumption_binding_id", "consumption_binding_hash")}
    state.update({"registry_contract_version": "m8r_05b_03.v1", "state": "unused"})
    return authorization, binding, state


def _success(context):
    request = context.bounded_request
    return {"status": "success", "evidence_contract": request["expected_evidence_contract"], "evidence": {"source": "fixture", "operation_id": request["operation_id"]}}


def _run(tmp_path, adapter=_success):
    authorization, binding, state = _artifacts()
    registry = ExecutorRegistry({PLAN["operations"][0]["executor_id"]: adapter})
    return execute_controlled_plan(PLAN, authorization, binding, supplied_consumption_state=state, execution_timestamp=TIMESTAMP, output_root=tmp_path, executor_registry=registry), authorization, binding, state


def test_claims_once_writes_contained_bundle_and_schema_valid_receipt(tmp_path):
    result, authorization, binding, state = _run(tmp_path)
    receipt, bundle = result["execution_receipt"], result["evidence_bundle"]
    assert result["consumption_state"] == "consumed"
    assert receipt["execution_status"] == "complete"
    assert bundle["raw_payload_retained"] is False
    assert (tmp_path / "consumption" / f"{authorization['authorization_id']}.json").exists()
    for name, artifact in (("unified_market_evidence_execution_receipt.v1.schema.json", receipt), ("unified_market_evidence_bundle.v1.schema.json", bundle)):
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        assert not list(Draft202012Validator(schema).iter_errors(artifact))
    with pytest.raises(OrchestrationError, match="authorization_already_consumed"):
        execute_controlled_plan(PLAN, authorization, binding, supplied_consumption_state=state, execution_timestamp=TIMESTAMP, output_root=tmp_path, executor_registry=ExecutorRegistry({PLAN["operations"][0]["executor_id"]: _success}))


def test_unregistered_executor_is_audited_partial_and_consumed(tmp_path):
    result, authorization, _, _ = _run(tmp_path, adapter=None)
    assert result["execution_receipt"]["execution_status"] == "failed"
    assert result["execution_receipt"]["operation_results"][0]["omission_reason"] == "executor_not_registered"
    assert json.loads((tmp_path / "consumption" / f"{authorization['authorization_id']}.json").read_text())["state"] == "consumed"


def test_raw_payload_is_containment_failure_not_retained(tmp_path):
    def leaking(context):
        return {"status": "success", "evidence_contract": context.bounded_request["expected_evidence_contract"], "evidence": {"raw_payload": "forbidden"}}
    result, _, _, _ = _run(tmp_path, adapter=leaking)
    operation = result["execution_receipt"]["operation_results"][0]
    assert operation["status"] == "failed"
    assert operation["omission_reason"] == "evidence_containment_violation"


def test_drifted_supplied_state_fails_before_consumption(tmp_path):
    authorization, binding, state = _artifacts()
    state["authorization_hash"] = "0" * 64
    with pytest.raises(OrchestrationError, match="consumption_authorization_mismatch"):
        execute_controlled_plan(PLAN, authorization, binding, supplied_consumption_state=state, execution_timestamp=TIMESTAMP, output_root=tmp_path)
    assert not (tmp_path / "consumption").exists()
