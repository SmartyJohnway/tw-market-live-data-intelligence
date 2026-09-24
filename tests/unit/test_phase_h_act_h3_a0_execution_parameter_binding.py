from __future__ import annotations

import copy
import json

import pytest
from jsonschema import Draft202012Validator

from scripts.m8r_05b_03.canonical import sha256_json
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.request_projection import build_execution_request_projection
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from tests.unit.m8r_05b_03_test_helpers import ROOT, artifacts, registry_metadata


def _projection(lookback: object):
    plan, authorization, binding, _state = artifacts()
    operation = copy.deepcopy(plan["operations"][0])
    operation["parameters"] = {"lookback_trading_days": lookback}
    op_binding = copy.deepcopy(authorization["approved_operation_bindings"][0])
    op_binding["capability_id"] = "recent_performance"
    registry = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    executor = registry.get(operation["executor_id"])
    return build_execution_request_projection(
        plan=plan,
        authorization=authorization,
        consumption_binding=binding,
        operation=operation,
        binding=op_binding,
        executor=executor,
        network_authorized=True,
    )[0]


@pytest.mark.parametrize("lookback", [1, 5, 20])
def test_recent_performance_v2_binds_valid_lookback(lookback):
    request = _projection(lookback)
    schema = json.loads((ROOT / "schemas/unified_market_evidence_execution_request.v2.schema.json").read_text())
    assert not list(Draft202012Validator(schema).iter_errors(request))
    assert request["schema_version"] == "unified_market_evidence_execution_request.v2"
    assert request["execution_request_id"] == "umereq-v2-" + request["execution_request_hash"][:20]
    assert request["parameters"] == {"lookback_trading_days": lookback}
    identity = {key: value for key, value in request.items() if key not in {
        "schema_version", "execution_request_id", "execution_request_hash", "relative_contained_output_path"
    }}
    assert sha256_json(identity) == request["execution_request_hash"]


@pytest.mark.parametrize("parameters", [None, {}, {"lookback_trading_days": 0},
    {"lookback_trading_days": 21}, {"lookback_trading_days": "5"},
    {"lookback_trading_days": 5.0}, {"lookback_trading_days": True},
    {"lookback_trading_days": False}, {"lookback_trading_days": 5, "other": 1}])
def test_recent_performance_invalid_parameters_fail_closed(parameters):
    plan, authorization, binding, _state = artifacts()
    operation = copy.deepcopy(plan["operations"][0])
    operation["parameters"] = parameters
    op_binding = copy.deepcopy(authorization["approved_operation_bindings"][0])
    op_binding["capability_id"] = "recent_performance"
    registry = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    with pytest.raises(OrchestrationError, match="execution_request_parameters_invalid"):
        build_execution_request_projection(
            plan=plan, authorization=authorization, consumption_binding=binding,
            operation=operation, binding=op_binding,
            executor=registry.get(operation["executor_id"]), network_authorized=True,
        )


def test_five_and_twenty_day_parameters_change_authorized_identity():
    five = _projection(5)
    twenty = _projection(20)
    assert five["execution_request_hash"] != twenty["execution_request_hash"]
    assert five["execution_request_id"] != twenty["execution_request_id"]


def test_non_h3_projection_retains_v1_shape_and_identity():
    plan, authorization, binding, _state = artifacts()
    operation = plan["operations"][0]
    op_binding = authorization["approved_operation_bindings"][0]
    registry = ExecutorMetadataRegistry.from_json(registry_metadata(plan))
    request, _ = build_execution_request_projection(
        plan=plan, authorization=authorization, consumption_binding=binding,
        operation=operation, binding=op_binding,
        executor=registry.get(operation["executor_id"]), network_authorized=True,
    )
    schema = json.loads((ROOT / "schemas/unified_market_evidence_execution_request.v1.schema.json").read_text())
    assert not list(Draft202012Validator(schema).iter_errors(request))
    assert request["schema_version"] == "unified_market_evidence_execution_request.v1"
    assert request["execution_request_id"] == "umereq-v1-c41f6ec41025a13db140"
    assert request["execution_request_hash"] == "c41f6ec41025a13db140d1f793e98d3dcb3c09810cd10d073150a84f5d95f5ab"
    assert "parameters" not in request
    assert set(request) == set(schema["properties"])
    identity = {key: value for key, value in request.items() if key not in {
        "schema_version", "execution_request_id", "execution_request_hash", "relative_contained_output_path"
    }}
    assert sha256_json(identity) == request["execution_request_hash"]


def test_preflight_accepts_mixed_v1_v2_and_rejects_unknown_internal_version(tmp_path):
    plan = json.loads((ROOT / "tests/fixtures/m8r_05b_01/golden/batching_none_two_unique_batches.json").read_text())
    from tests.unit.m8r_05b_03_test_helpers import EVALUATION_TIMESTAMP, artifacts, registry_metadata
    from scripts.m8r_05b_03.preflight import build_orchestrator_preflight

    selected_plan, authorization, binding, state = artifacts(plan)
    preflight = build_orchestrator_preflight(
        selected_plan, authorization, binding, supplied_consumption_state=state,
        evaluation_timestamp=EVALUATION_TIMESTAMP,
        executor_registry_metadata=registry_metadata(selected_plan), output_root=str(tmp_path),
    )
    assert len(preflight["bounded_execution_requests"]) >= 2
    v2 = preflight["bounded_execution_requests"][0]
    v2.update({
        "schema_version": "unified_market_evidence_execution_request.v2",
        "execution_request_id": "umereq-v2-" + "a" * 20,
        "capability_id": "recent_performance",
        "parameters": {"lookback_trading_days": 5},
    })
    schema = json.loads((ROOT / "schemas/unified_market_evidence_orchestrator_preflight.v1.schema.json").read_text())
    assert not list(Draft202012Validator(schema).iter_errors(preflight))
    unknown = copy.deepcopy(preflight)
    unknown["bounded_execution_requests"][0]["schema_version"] = "unified_market_evidence_execution_request.v3"
    assert list(Draft202012Validator(schema).iter_errors(unknown))


def _result(version: int, request_id: str) -> dict:
    return {
        "schema_version": f"unified_market_evidence_operation_result.v{version}",
        "operation_id": "umeop-op-v1-" + "1" * 20,
        "execution_request_id": request_id,
        "execution_request_hash": "2" * 64,
        "executor_id": "fixture-executor",
        "capability_id": "recent_performance",
        "evidence_contract": "recent_performance_evidence.v1",
        "status": "failed",
        "error_code": "fixture_failure",
        "result_item_count": 0,
        "evidence_artifacts": [],
        "warnings": [],
    }


@pytest.mark.parametrize("version", [1, 2])
def test_operation_result_schemas_accept_only_authorized_v1_v2_request_ids(version):
    schema = json.loads((ROOT / f"schemas/unified_market_evidence_operation_result.v{version}.schema.json").read_text())
    validator = Draft202012Validator(schema)
    accepted_request_versions = (1,) if version == 1 else (1, 2)
    for request_version in accepted_request_versions:
        assert not list(validator.iter_errors(_result(version, f"umereq-v{request_version}-" + "a" * 20)))
    invalid_ids = ["umereq-v3-" + "a" * 20, "umereq-v2-short", "not-an-execution-request-id"]
    if version == 1:
        invalid_ids.append("umereq-v2-" + "a" * 20)
    for request_id in invalid_ids:
        assert list(validator.iter_errors(_result(version, request_id)))


def test_operation_result_v1_rejects_v2_execution_request_id():
    schema = json.loads((ROOT / "schemas/unified_market_evidence_operation_result.v1.schema.json").read_text())
    assert list(Draft202012Validator(schema).iter_errors(_result(1, "umereq-v2-" + "a" * 20)))
