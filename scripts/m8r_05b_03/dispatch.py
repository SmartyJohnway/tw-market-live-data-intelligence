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
from .registry import ExecutorMetadata, ExecutorMetadataRegistry, executor_route_key


ROOT = Path(__file__).resolve().parents[2]
REQUEST_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_execution_request.v1.schema.json"
RESULT_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_operation_result.v1.schema.json"


@dataclass(frozen=True)
class DispatchRuntimeContext:
    governed_output_root: str
    mode: str


AdapterCallable = Callable[[dict, DispatchRuntimeContext], dict[str, Any]]
BatchAdapterCallable = Callable[[tuple[dict, ...], DispatchRuntimeContext], list[dict[str, Any]]]


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
    batch_adapter: BatchAdapterCallable | None = None
    fake_adapter: bool = False


class RuntimeAdapterRegistry:
    def __init__(self, registrations: list[RuntimeAdapterRegistration]):
        self._by_route: dict[str, RuntimeAdapterRegistration] = {}
        for registration in registrations:
            route_key = executor_route_key(
                registration.executor_id,
                registration.capability_id,
                registration.market,
            )
            if route_key in self._by_route:
                raise OrchestrationError("duplicate_runtime_adapter_route")
            self._by_route[route_key] = registration

    def get(self, executor_id: str) -> RuntimeAdapterRegistration | None:
        matches = [reg for reg in self._by_route.values() if reg.executor_id == executor_id]
        if len(matches) > 1:
            raise OrchestrationError("ambiguous_runtime_adapter_lookup")
        return matches[0] if matches else None

    def get_route(
        self, executor_id: str, capability_id: str, market: str
    ) -> RuntimeAdapterRegistration | None:
        return self._by_route.get(executor_route_key(executor_id, capability_id, market))

    def routes_for_executor(self, executor_id: str) -> tuple[RuntimeAdapterRegistration, ...]:
        return tuple(reg for reg in self._by_route.values() if reg.executor_id == executor_id)

    def resolve(
        self,
        request: dict,
        metadata: ExecutorMetadata,
        *,
        mode: str,
    ) -> RuntimeAdapterRegistration:
        registration = self.get_route(
            request["executor_id"], request["capability_id"], request["market"]
        )
        if registration is None:
            candidates = self.routes_for_executor(request["executor_id"])
            if any(item.capability_id == request["capability_id"] for item in candidates):
                raise OrchestrationError("market_mismatch")
            if any(item.market == request["market"] for item in candidates):
                raise OrchestrationError("capability_mismatch")
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
        metadata = metadata_registry.get_route(
            request["executor_id"], request["capability_id"], request["market"]
        )
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
    accepted_preflight: dict | None = None,
) -> list[dict]:
    context = DispatchRuntimeContext(governed_output_root=governed_output_root, mode=mode)
    outcomes: list[dict] = []
    result_schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(result_schema, format_checker=FormatChecker())

    by_batch: dict[str, list[PreparedDispatch]] = {}
    for item in prepared:
        by_batch.setdefault(item.request["batch_group_id"], []).append(item)

    def validate_result(item: PreparedDispatch, raw_result: dict) -> dict:
        validate_contained_relative_paths(
            governed_output_root,
            [item.request["relative_contained_output_path"]],
        )
        expected_req_id, expected_req_hash = request_identity(item.request)

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
            raise OrchestrationError("operation_result_identity_mismatch")

        if raw_result["status"] == "succeeded":
            artifact_total_items = sum(art["item_count"] for art in raw_result["evidence_artifacts"])
            if raw_result["result_item_count"] != artifact_total_items:
                raise OrchestrationError("operation_result_item_count_mismatch")
            _verify_evidence_artifacts(governed_output_root, raw_result["evidence_artifacts"], mode)
        return dict(raw_result)

    for batch_group_id, items in by_batch.items():
        first = items[0]
        route = (first.request["executor_id"], first.request["capability_id"], first.request["market"])
        if any((x.request["executor_id"], x.request["capability_id"], x.request["market"]) != route or x.registration != first.registration for x in items):
            raise OrchestrationError("batch_dispatch_binding_mismatch")
        if mode == "execute-approved" and len(items) > 1 and accepted_preflight is None:
            raise OrchestrationError("accepted_preflight_required_for_batch_dispatch")
        if accepted_preflight is not None:
            batch = accepted_preflight.get("resolved_batch_bindings", {}).get(batch_group_id)
            if not isinstance(batch, dict) or sorted(batch.get("operation_ids", [])) != sorted(x.request["operation_id"] for x in items) or (batch.get("executor_id"), batch.get("capability_id"), batch.get("market")) != route:
                raise OrchestrationError("batch_dispatch_binding_mismatch")
        try:
            if len(items) > 1:
                if first.registration.batch_adapter is None:
                    raise OrchestrationError("batch_runtime_adapter_required")
                raw_results = first.registration.batch_adapter(tuple(x.request for x in items), context)
                if not isinstance(raw_results, list) or len(raw_results) != len(items):
                    raise OrchestrationError("batch_operation_result_count_mismatch")
                by_operation = {item.get("operation_id"): item for item in raw_results if isinstance(item, dict)}
                if len(by_operation) != len(items) or set(by_operation) != {x.request["operation_id"] for x in items}:
                    raise OrchestrationError("batch_operation_result_membership_mismatch")
                outcomes.extend(validate_result(item, by_operation[item.request["operation_id"]]) for item in items)
            else:
                outcomes.append(validate_result(first, first.registration.adapter(first.request, context)))
        except OrchestrationError:
            raise
        except TimeoutError:
            for item in items:
                expected_req_id, expected_req_hash = request_identity(item.request)
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
                outcomes.append(outcome)
        except Exception:
            for item in items:
                expected_req_id, expected_req_hash = request_identity(item.request)
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
    order = {item.request["operation_id"]: index for index, item in enumerate(prepared)}
    return sorted(outcomes, key=lambda outcome: order[outcome["operation_id"]])
