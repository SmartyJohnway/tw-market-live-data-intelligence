"""Closed executor metadata registry for preflight validation only."""
from __future__ import annotations

from dataclasses import dataclass

from .errors import OrchestrationError


@dataclass(frozen=True)
class ExecutorMetadata:
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


def _metadata_from_dict(raw: dict) -> ExecutorMetadata:
    required = {
        "executor_id",
        "capability_id",
        "market",
        "supported_security_types",
        "expected_evidence_contract",
        "network_required",
        "bounded_execution_supported",
        "timeout_seconds",
        "maximum_result_items",
        "output_policy",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        raise OrchestrationError("executor_registry_schema_invalid")
    if not isinstance(raw["supported_security_types"], list) or not raw["supported_security_types"]:
        raise OrchestrationError("executor_registry_schema_invalid")
    try:
        timeout_seconds = int(raw["timeout_seconds"])
        maximum_result_items = int(raw["maximum_result_items"])
    except (TypeError, ValueError) as exc:
        raise OrchestrationError("executor_limits_invalid") from exc
    return ExecutorMetadata(
        executor_id=str(raw["executor_id"]),
        capability_id=str(raw["capability_id"]),
        market=str(raw["market"]),
        supported_security_types=tuple(sorted(str(item) for item in raw["supported_security_types"])),
        expected_evidence_contract=str(raw["expected_evidence_contract"]),
        network_required=raw["network_required"] is True,
        bounded_execution_supported=raw["bounded_execution_supported"] is True,
        timeout_seconds=timeout_seconds,
        maximum_result_items=maximum_result_items,
        output_policy=str(raw["output_policy"]),
    )


class ExecutorMetadataRegistry:
    def __init__(self, entries: dict[str, ExecutorMetadata]):
        self._entries = dict(entries)

    @classmethod
    def from_json(cls, payload: dict) -> "ExecutorMetadataRegistry":
        if not isinstance(payload, dict) or payload.get("schema_version") != "m8r_05b_03_executor_registry_metadata.v1":
            raise OrchestrationError("executor_registry_schema_invalid")
        executors = payload.get("executors")
        if not isinstance(executors, list) or not executors:
            raise OrchestrationError("executor_registry_schema_invalid")
        entries: dict[str, ExecutorMetadata] = {}
        for raw in executors:
            entry = _metadata_from_dict(raw)
            if entry.executor_id in entries:
                raise OrchestrationError("duplicate_executor_id")
            entries[entry.executor_id] = entry
        return cls(entries)

    def get(self, executor_id: str) -> ExecutorMetadata:
        entry = self._entries.get(executor_id)
        if entry is None:
            raise OrchestrationError("unknown_executor")
        return entry

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))


def validate_executor_for_operation(
    operation: dict,
    binding: dict,
    registry: ExecutorMetadataRegistry,
    *,
    network_authorized: bool,
) -> ExecutorMetadata:
    entry = registry.get(str(binding["executor_id"]))
    if entry.capability_id != binding["capability_id"] or entry.capability_id != operation.get("capability_id"):
        raise OrchestrationError("capability_mismatch")
    if entry.market != binding["market"] or entry.market != operation.get("market"):
        raise OrchestrationError("market_mismatch")
    if entry.expected_evidence_contract != binding["expected_evidence_contract"]:
        raise OrchestrationError("evidence_contract_mismatch")
    operation_security_types = tuple(sorted(str(item) for item in operation.get("security_types", [])))
    if any(item not in entry.supported_security_types for item in operation_security_types):
        raise OrchestrationError("unsupported_security_type")
    if entry.network_required and not network_authorized:
        raise OrchestrationError("network_required_not_authorized")
    if not entry.bounded_execution_supported:
        raise OrchestrationError("executor_not_bounded")
    if entry.timeout_seconds <= 0 or entry.timeout_seconds > 60 or entry.maximum_result_items <= 0 or entry.maximum_result_items > 500:
        raise OrchestrationError("executor_limits_invalid")
    if entry.output_policy not in {"contained_artifact_only", "no_raw_payload_retention"}:
        raise OrchestrationError("executor_output_policy_invalid")
    return entry
