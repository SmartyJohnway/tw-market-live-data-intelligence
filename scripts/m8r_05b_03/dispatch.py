"""Controlled dispatch for preflight execution requests."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker

from scripts.m8r_filesystem_safety import (
    FilesystemSafetyError,
    safe_destination,
)

from .containment import validate_contained_relative_paths
from .errors import OrchestrationError
from .registry import ExecutorMetadata, ExecutorMetadataRegistry


ROOT = Path(__file__).resolve().parents[2]
REQUEST_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_execution_request.v1.schema.json"
RESULT_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_operation_result.v1.schema.json"


@dataclass(frozen=True)
class DispatchRuntimeContext:
    governed_output_root: str
    mode: str


AdapterCallable = Callable[[dict, DispatchRuntimeContext], dict[str, Any]]


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
    def __init__(self, registrations: list[RuntimeAdapterRegistration]):
        self._by_executor = {reg.executor_id: reg for reg in registrations}

    def get(self, executor_id: str) -> RuntimeAdapterRegistration | None:
        return self._by_executor.get(executor_id)

    def resolve(
        self,
        request: dict,
        metadata: ExecutorMetadata,
        *,
        mode: str,
    ) -> RuntimeAdapterRegistration:
        registration = self.get(request["executor_id"])
        if registration is None:
            raise OrchestrationError("unknown_runtime_adapter")
        checks = (
            (registration.executor_id, metadata.executor_id, "executor_mismatch"),
            (registration.capability_id, metadata.capability_id, "capability_mismatch"),
            (registration.market, metadata.market, "market_mismatch"),
            (
                sorted(registration.supported_security_types),
                sorted(metadata.supported_security_types),
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
                "bounded_execution_unsupported",
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
        if mode == "execute-approved" and registration.fake_adapter:
            raise OrchestrationError("execute_approved_rejects_fake_adapter")
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
        prepared.append(PreparedDispatch(request, metadata, registration))
    return tuple(prepared)


def _verify_evidence_artifacts(
    governed_output_root: str,
    artifacts: list[dict],
    mode: str,
) -> None:
    for art in artifacts:
        rel_path = art["relative_path"]
        try:
            dest = safe_destination(governed_output_root, rel_path, create_parent=False)
        except FilesystemSafetyError as exc:
            raise OrchestrationError(exc.code) from exc

        if mode == "execute-approved":
            if not dest.path.is_file():
                raise OrchestrationError("evidence_artifact_missing")
            content = dest.path.read_bytes()
            if len(content) != art["byte_size"]:
                raise OrchestrationError("evidence_artifact_size_mismatch")
            sha = hashlib.sha256(content).hexdigest()
            if sha != art["sha256"]:
                raise OrchestrationError("evidence_artifact_hash_mismatch")


def request_identity(request: dict) -> tuple[str, str]:
    return request["execution_request_id"], request["execution_request_hash"]


def dispatch_prepared(
    prepared: tuple[PreparedDispatch, ...],
    *,
    governed_output_root: str,
    mode: str,
) -> list[dict]:
    context = DispatchRuntimeContext(governed_output_root=governed_output_root, mode=mode)
    outcomes: list[dict] = []
    result_schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(result_schema, format_checker=FormatChecker())

    for item in prepared:
        validate_contained_relative_paths(
            governed_output_root,
            [item.request["relative_contained_output_path"]],
        )
        expected_req_id, expected_req_hash = request_identity(item.request)

        try:
            raw_result = item.registration.adapter(item.request, context)
            if list(validator.iter_errors(raw_result)):
                raise OrchestrationError("operation_result_schema_invalid")

            if (
                raw_result["operation_id"] != item.request["operation_id"]
                or raw_result["execution_request_id"] != expected_req_id
                or raw_result["execution_request_hash"] != expected_req_hash
                or raw_result["executor_id"] != item.request["executor_id"]
                or raw_result["capability_id"] != item.request["capability_id"]
                or raw_result["evidence_contract"] != item.metadata.expected_evidence_contract
            ):
                import sys
                sys.stderr.write(f"\nDETAILS:\n  op_id: {raw_result['operation_id']} vs {item.request['operation_id']}\n  req_id: {raw_result['execution_request_id']} vs {expected_req_id}\n  req_hash: {raw_result['execution_request_hash']} vs {expected_req_hash}\n  executor: {raw_result['executor_id']} vs {item.request['executor_id']}\n  cap: {raw_result['capability_id']} vs {item.request['capability_id']}\n  contract: {raw_result['evidence_contract']} vs {item.metadata.expected_evidence_contract}\n")
                raise OrchestrationError("operation_result_identity_mismatch")

            status = raw_result["status"]
            if status == "succeeded":
                _verify_evidence_artifacts(governed_output_root, raw_result["evidence_artifacts"], mode)
                outcome = dict(raw_result)
            else:
                outcome = dict(raw_result)
        except OrchestrationError:
            raise
        except TimeoutError:
            outcome = {
                "schema_version": "unified_market_evidence_operation_result.v1",
                "operation_id": item.request["operation_id"],
                "execution_request_id": expected_req_id,
                "execution_request_hash": expected_req_hash,
                "executor_id": item.request["executor_id"],
                "capability_id": item.request["capability_id"],
                "evidence_contract": item.metadata.expected_evidence_contract,
                "status": "failed",
                "error_code": "adapter_timeout",
                "result_item_count": 0,
                "evidence_artifacts": [],
                "warnings": [],
            }
        except Exception:
            outcome = {
                "schema_version": "unified_market_evidence_operation_result.v1",
                "operation_id": item.request["operation_id"],
                "execution_request_id": expected_req_id,
                "execution_request_hash": expected_req_hash,
                "executor_id": item.request["executor_id"],
                "capability_id": item.request["capability_id"],
                "evidence_contract": item.metadata.expected_evidence_contract,
                "status": "failed",
                "error_code": "adapter_exception",
                "result_item_count": 0,
                "evidence_artifacts": [],
                "warnings": [],
            }

        outcomes.append(outcome)
    return outcomes
