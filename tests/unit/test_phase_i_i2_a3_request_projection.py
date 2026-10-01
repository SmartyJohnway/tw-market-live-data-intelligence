from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.m8r_05b_03.request_projection import build_execution_request_projection
from scripts.m8r_05b_03.registry import ExecutorMetadata
from tests.unit.m8r_05b_03_test_helpers import artifacts

ROOT = Path(__file__).resolve().parents[2]


def _project(capability, *, executor_id=None, timeout=30, maximum=1, parameters=None):
    plan, authorization, binding, _ = artifacts()
    operation = dict(plan["operations"][0])
    operation["parameters"] = parameters or {}
    auth_binding = dict(authorization["approved_operation_bindings"][0])
    auth_binding["capability_id"] = capability
    executor = ExecutorMetadata(
        executor_id=executor_id or operation["executor_id"],
        capability_id=capability,
        market=auth_binding["market"],
        supported_security_types=("equity",),
        expected_evidence_contract=("index_futures_context_evidence.v1" if capability == "index_futures_context" else "recent_performance_evidence.v1" if capability == "recent_performance" else "unified_market_evidence_item.v1"),
        network_required=True,
        bounded_execution_supported=True,
        timeout_seconds=timeout,
        maximum_result_items=maximum,
        output_policy="contained_artifact_only",
    )
    return build_execution_request_projection(
        plan=plan, authorization=authorization, consumption_binding=binding,
        operation=operation, binding=auth_binding, executor=executor,
        network_authorized=True,
    )[0]


def test_i2_projects_valid_v2_with_empty_parameters_and_frozen_bounds():
    request = _project("index_futures_context", executor_id="phase_i_i2_index_futures_context_executor")
    schema = json.loads((ROOT / "schemas/unified_market_evidence_execution_request.v2.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(request)
    assert request["schema_version"] == "unified_market_evidence_execution_request.v2"
    assert request["parameters"] == {}
    assert request["timeout_seconds"] == 30
    assert request["maximum_records"] == 1
    assert request["network_authorized"] is True


def test_h3_recent_performance_stays_v2_and_keeps_lookback_binding():
    request = _project("recent_performance", timeout=15, maximum=1, parameters={"lookback_trading_days": 20})
    assert request["schema_version"] == "unified_market_evidence_execution_request.v2"
    assert request["parameters"] == {"lookback_trading_days": 20}
    assert request["timeout_seconds"] == 15


def test_existing_v1_capability_shape_is_unchanged():
    request = _project("official_eod_reference", timeout=15, maximum=1)
    schema = json.loads((ROOT / "schemas/unified_market_evidence_execution_request.v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(request)
    assert request["schema_version"] == "unified_market_evidence_execution_request.v1"
    assert "parameters" not in request
