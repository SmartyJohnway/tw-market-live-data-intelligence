from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from scripts.m8r_05b_03.consumption_claim import build_claim_record
from scripts.m8r_05b_03.request_projection import build_execution_request_projection
from tests.unit.m8r_05b_03_test_helpers import (
    CLAIM_TIMESTAMP,
    ROOT,
    artifacts,
    build_valid_preflight,
    registry_metadata,
)


def test_preflight_schema_accepts_valid_artifact(tmp_path):
    schema = json.loads((ROOT / "schemas/unified_market_evidence_orchestrator_preflight.v1.schema.json").read_text())
    valid = build_valid_preflight(tmp_path)
    assert not list(Draft202012Validator(schema).iter_errors(valid))


def test_execution_request_schema_accepts_valid_projection():
    schema = json.loads((ROOT / "schemas/unified_market_evidence_execution_request.v1.schema.json").read_text())
    plan, authorization, binding, _state = artifacts()
    from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry

    registry = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    executor_id = plan["operations"][0]["executor_id"]
    executor = registry.get(executor_id)
    op_binding = authorization["approved_operation_bindings"][0]
    projection, _warnings = build_execution_request_projection(
        plan=plan,
        authorization=authorization,
        consumption_binding=binding,
        operation=plan["operations"][0],
        binding=op_binding,
        executor=executor,
        network_authorized=True,
    )
    assert not list(Draft202012Validator(schema).iter_errors(projection))


def test_schemas_reject_invalid_payloads():
    schema = json.loads((ROOT / "schemas/unified_market_evidence_executor_registry_metadata.v1.schema.json").read_text())
    valid = registry_metadata()
    assert not list(Draft202012Validator(schema).iter_errors(valid))
    valid["executors"][0]["timeout_seconds"] = "15"
    assert list(Draft202012Validator(schema).iter_errors(valid))


def test_consumption_record_schema_accepts_claimed_record(tmp_path):
    schema = json.loads((ROOT / "schemas/unified_market_evidence_consumption_record.v1.schema.json").read_text())
    _plan, _authorization, _binding, state = artifacts()
    record = build_claim_record(
        build_valid_preflight(tmp_path),
        state,
        claim_created_at=CLAIM_TIMESTAMP,
        operator_confirmation_reference="op-ref-unit-test",
    )
    assert not list(Draft202012Validator(schema).iter_errors(record))
    record["state"] = "unknown"
    assert list(Draft202012Validator(schema).iter_errors(record))
