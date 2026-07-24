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
        ({"timeout_seconds": 0}, "executor_limits_invalid"),
        ({"maximum_result_items": 0}, "executor_limits_invalid"),
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
