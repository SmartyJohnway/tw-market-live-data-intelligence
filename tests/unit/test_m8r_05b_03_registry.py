from __future__ import annotations

import pytest

from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry, validate_executor_for_operation
from tests.unit.m8r_05b_03_test_helpers import artifacts, registry_metadata


def _operation_binding_registry(**registry_overrides):
    plan, authorization, _binding, _state = artifacts()
    operation = plan["operations"][0]
    binding = authorization["approved_operation_bindings"][0]
    registry = ExecutorMetadataRegistry.from_json(registry_metadata(plan, **registry_overrides))
    return operation, binding, registry


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"executor_id": "missing"}, "unknown_executor"),
        ({"capability_id": "other"}, "capability_mismatch"),
        ({"market": "TPEx"}, "market_mismatch"),
        ({"supported_security_types": ["warrant"]}, "unsupported_security_type"),
        ({"expected_evidence_contract": "other"}, "evidence_contract_mismatch"),
        ({"bounded_execution_supported": False}, "executor_not_bounded"),
    ],
)
def test_registry_rejects_invalid_executor_metadata(overrides, code):
    operation, binding, registry = _operation_binding_registry(**overrides)
    with pytest.raises(OrchestrationError, match=code):
        validate_executor_for_operation(operation, binding, registry, network_authorized=True)


def test_registry_rejects_network_required_without_authorization():
    operation, binding, registry = _operation_binding_registry(network_required=True)
    with pytest.raises(OrchestrationError, match="network_required_not_authorized"):
        validate_executor_for_operation(operation, binding, registry, network_authorized=False)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("timeout_seconds", "15"),
        ("timeout_seconds", 15.0),
        ("timeout_seconds", True),
        ("maximum_result_items", "50"),
        ("maximum_result_items", 50.0),
        ("maximum_result_items", False),
        ("network_required", "true"),
        ("bounded_execution_supported", "true"),
        ("executor_id", None),
        ("capability_id", ""),
        ("market", ""),
        ("expected_evidence_contract", ""),
        ("output_policy", ""),
        ("supported_security_types", ["equity", "equity"]),
        ("supported_security_types", [""]),
    ],
)
def test_registry_parser_rejects_coercible_or_empty_metadata(field, value):
    payload = registry_metadata()
    payload["executors"][0][field] = value
    with pytest.raises(OrchestrationError, match="executor_registry_schema_invalid"):
        ExecutorMetadataRegistry.from_json(payload)


def test_registry_schema_parser_accepts_exact_types():
    registry = ExecutorMetadataRegistry.from_json(registry_metadata())
    entry = registry.get(registry.ids()[0])
    assert type(entry.timeout_seconds) is int
    assert type(entry.maximum_result_items) is int
    assert type(entry.network_required) is bool
