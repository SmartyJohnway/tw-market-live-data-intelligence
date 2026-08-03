"""Closed runtime adapter boundary and sequential bounded dispatch."""
from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from jsonschema import Draft202012Validator

from .containment import validate_contained_relative_paths
from .errors import OrchestrationError
from .registry import ExecutorMetadata, ExecutorMetadataRegistry


ROOT = Path(__file__).resolve().parents[2]
REQUEST_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_execution_request.v1.schema.json"
AdapterCallable = Callable[[dict, "DispatchRuntimeContext"], dict]


@dataclass(frozen=True)
class DispatchRuntimeContext:
    governed_output_root: str
    mode: str


@dataclass(frozen=True)
class RuntimeAdapterRegistration:
    executor_id: str
    capability_id: str
    market: str
    supported_security_types: tuple[str, ...]
    expected_evidence_contract: str
    network_required: bool
    bounded_execution_supported: bool
    timeout_seconds: int
    maximum_result_items: int
    output_policy: str
    adapter: AdapterCallable
    fake_adapter: bool = False


class RuntimeAdapterRegistry:
    """Explicit code-constructed registry; never built from an input artifact."""

    def __init__(self, registrations: list[RuntimeAdapterRegistration]):
        entries: dict[str, RuntimeAdapterRegistration] = {}
        for registration in registrations:
            if not isinstance(registration, RuntimeAdapterRegistration) or not callable(registration.adapter):
                raise OrchestrationError("runtime_adapter_registration_invalid")
            if registration.executor_id in entries:
                raise OrchestrationError("duplicate_runtime_adapter")
            entries[registration.executor_id] = registration
        self._entries = entries

    def resolve(
        self,
        request: dict,
        metadata: ExecutorMetadata,
        *,
        mode: str,
    ) -> RuntimeAdapterRegistration:
        registration = self._entries.get(request["executor_id"])
        if registration is None:
            raise OrchestrationError("unknown_runtime_adapter")
        checks = (
            (registration.executor_id, metadata.executor_id, "executor_mismatch"),
            (registration.capability_id, metadata.capability_id, "capability_mismatch"),
            (registration.market, metadata.market, "market_mismatch"),
            (
                tuple(sorted(registration.supported_security_types)),
                metadata.supported_security_types,
                "unsupported_security_type",
            ),
            (
                registration.expected_evidence_contract,
                metadata.expected_evidence_contract,
                "evidence_contract_mismatch",
            ),
            (registration.network_required, metadata.network_required, "network_requirement_mismatch"),
            (
                registration.bounded_execution_supported,
                metadata.bounded_execution_supported,
                "bounded_support_mismatch",
            ),
            (registration.timeout_seconds, metadata.timeout_seconds, "timeout_limit_mismatch"),
            (
                registration.maximum_result_items,
                metadata.maximum_result_items,
                "record_limit_mismatch",
            ),
            (registration.output_policy, metadata.output_policy, "output_policy_mismatch"),
        )
        for actual, expected, code in checks:
            if actual != expected:
                raise OrchestrationError(code)
        if mode == "dry-run" and not registration.fake_adapter:
            raise OrchestrationError("dry_run_requires_fake_adapter")
        return registration


@dataclass(frozen=True)
class PreparedDispatch:
    request: dict
    metadata: ExecutorMetadata
    registration: RuntimeAdapterRegistration


def _validate_request_against_metadata(request: dict, metadata: ExecutorMetadata) -> None:
    if request["executor_id"] != metadata.executor_id:
        raise OrchestrationError("executor_mismatch")
    if request["capability_id"] != metadata.capability_id:
        raise OrchestrationError("capability_mismatch")
    if request["market"] != metadata.market:
        raise OrchestrationError("market_mismatch")
    if any(item not in metadata.supported_security_types for item in request["approved_security_types"]):
        raise OrchestrationError("unsupported_security_type")
    if request["timeout_seconds"] != metadata.timeout_seconds:
        raise OrchestrationError("timeout_limit_mismatch")
    if request["maximum_records"] != metadata.maximum_result_items:
        raise OrchestrationError("record_limit_mismatch")
    if request["network_authorized"] is not True and metadata.network_required:
        raise OrchestrationError("network_required_not_authorized")


def prepare_dispatch(
    preflight: dict,
    metadata_registry: ExecutorMetadataRegistry,
    runtime_registry: RuntimeAdapterRegistry,
    *,
    mode: str,
) -> tuple[PreparedDispatch, ...]:
    if mode not in {"dry-run", "execute-approved"}:
        raise OrchestrationError("execution_mode_invalid")
    schema = json.loads(REQUEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    requests = preflight.get("bounded_execution_requests")
    if not isinstance(requests, list):
        raise OrchestrationError("execution_request_schema_invalid")
    by_operation = {item.get("operation_id"): item for item in requests if isinstance(item, dict)}
    if list(by_operation) != preflight["approved_operation_order"]:
        raise OrchestrationError("dispatch_order_mismatch")
    prepared: list[PreparedDispatch] = []
    for operation_id in preflight["approved_operation_order"]:
        request = by_operation[operation_id]
        if list(Draft202012Validator(schema).iter_errors(request)):
            raise OrchestrationError("execution_request_schema_invalid")
        binding = preflight["resolved_operation_bindings"].get(operation_id)
        if not isinstance(binding, dict):
            raise OrchestrationError("approved_operation_binding_mismatch")
        metadata = metadata_registry.get(request["executor_id"])
        _validate_request_against_metadata(request, metadata)
        if (
            request["capability_id"] != binding["capability_id"]
            or request["market"] != binding["market"]
            or request["executor_id"] != binding["executor_id"]
            or sorted(request["approved_security_types"]) != sorted(binding["security_types"])
            or metadata.expected_evidence_contract != binding["expected_evidence_contract"]
        ):
            raise OrchestrationError("dispatch_binding_mismatch")
        registration = runtime_registry.resolve(request, metadata, mode=mode)
        prepared.append(PreparedDispatch(deepcopy(request), metadata, registration))
    return tuple(prepared)


def dispatch_prepared(
    prepared: tuple[PreparedDispatch, ...],
    *,
    governed_output_root: str,
    mode: str,
) -> list[dict]:
    context = DispatchRuntimeContext(governed_output_root=governed_output_root, mode=mode)
    outcomes: list[dict] = []
    for item in prepared:
        validate_contained_relative_paths(
            governed_output_root,
            [item.request["relative_contained_output_path"]],
        )
        try:
            result = item.registration.adapter(deepcopy(item.request), context)
            if not isinstance(result, dict) or set(result) - {"status", "error_code"}:
                raise ValueError("adapter_result_invalid")
            status = result.get("status")
            if status == "succeeded" and result.get("error_code") is None:
                outcome_status, error_code = "succeeded", None
            elif status in {"failed", "source_unavailable"} and isinstance(result.get("error_code"), str):
                outcome_status, error_code = "failed", result["error_code"]
            else:
                raise ValueError("adapter_result_invalid")
        except TimeoutError:
            outcome_status, error_code = "failed", "adapter_timeout"
        except Exception:
            outcome_status, error_code = "failed", "adapter_exception"
        outcomes.append(
            {
                "operation_id": item.request["operation_id"],
                "executor_id": item.request["executor_id"],
                "status": outcome_status,
                "error_code": error_code,
            }
        )
    return outcomes
