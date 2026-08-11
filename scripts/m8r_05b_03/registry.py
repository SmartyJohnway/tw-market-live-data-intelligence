"""Closed, strictly typed executor metadata registry."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from .errors import OrchestrationError


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_SCHEMA_PATH = ROOT / "schemas" / "unified_market_evidence_executor_registry_metadata.v1.schema.json"
SUPPORTED_OUTPUT_POLICIES = frozenset({"contained_artifact_only", "no_raw_payload_retention"})


def executor_route_key(executor_id: str, capability_id: str, market: str) -> str:
    """Return the canonical, collision-safe identity for an executor route.

    ``executor_id`` is intentionally not a route identity: one controlled
    executor can serve more than one approved capability and market.  The
    compact JSON representation is stable and can also be used as an object
    key in the persisted preflight artifact.
    """
    if not all(isinstance(value, str) and value for value in (executor_id, capability_id, market)):
        raise OrchestrationError("executor_registry_schema_invalid")
    return json.dumps([executor_id, capability_id, market], ensure_ascii=True, separators=(",", ":"))


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
    if not isinstance(raw, dict):
        raise OrchestrationError("executor_registry_schema_invalid")

    for str_field in ("executor_id", "capability_id", "market", "expected_evidence_contract", "output_policy"):
        val = raw.get(str_field)
        if not isinstance(val, str) or not val:
            raise OrchestrationError("executor_registry_schema_invalid")

    sec_types = raw.get("supported_security_types")
    if not isinstance(sec_types, list) or not sec_types or len(sec_types) != len(set(sec_types)):
        raise OrchestrationError("executor_registry_schema_invalid")
    for item in sec_types:
        if not isinstance(item, str) or not item:
            raise OrchestrationError("executor_registry_schema_invalid")

    for bool_field in ("network_required", "bounded_execution_supported"):
        val = raw.get(bool_field)
        if type(val) is not bool:
            raise OrchestrationError("executor_registry_schema_invalid")

    for int_field, min_val, max_val in (("timeout_seconds", 1, 60), ("maximum_result_items", 1, 500)):
        val = raw.get(int_field)
        if type(val) is not int or val < min_val or val > max_val:
            raise OrchestrationError("executor_registry_schema_invalid")

    if raw.get("output_policy") not in SUPPORTED_OUTPUT_POLICIES:
        raise OrchestrationError("executor_output_policy_invalid")

    return ExecutorMetadata(
        executor_id=raw["executor_id"],
        capability_id=raw["capability_id"],
        market=raw["market"],
        supported_security_types=tuple(sorted(raw["supported_security_types"])),
        expected_evidence_contract=raw["expected_evidence_contract"],
        network_required=raw["network_required"],
        bounded_execution_supported=raw["bounded_execution_supported"],
        timeout_seconds=raw["timeout_seconds"],
        maximum_result_items=raw["maximum_result_items"],
        output_policy=raw["output_policy"],
    )


class ExecutorMetadataRegistry:
    def __init__(self, entries: dict[str, ExecutorMetadata]):
        self._entries = dict(entries)

    @classmethod
    def from_json(cls, payload: dict) -> "ExecutorMetadataRegistry":
        schema = json.loads(REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or list(Draft202012Validator(schema).iter_errors(payload)):
            raise OrchestrationError("executor_registry_schema_invalid")
        entries: dict[str, ExecutorMetadata] = {}
        for raw in payload.get("executors", []):
            entry = _metadata_from_dict(raw)
            route_key = executor_route_key(entry.executor_id, entry.capability_id, entry.market)
            if route_key in entries:
                raise OrchestrationError("duplicate_executor_route")
            entries[route_key] = entry
        return cls(entries)

    def get(self, executor_id: str) -> ExecutorMetadata:
        matches = [entry for entry in self._entries.values() if entry.executor_id == executor_id]
        if not matches:
            raise OrchestrationError("unknown_executor")
        if len(matches) != 1:
            raise OrchestrationError("ambiguous_executor_lookup")
        return matches[0]

    def get_route(self, executor_id: str, capability_id: str, market: str) -> ExecutorMetadata:
        entry = self._entries.get(executor_route_key(executor_id, capability_id, market))
        if entry is None:
            raise OrchestrationError("unknown_executor_route")
        return entry

    def routes_for_executor(self, executor_id: str) -> tuple[ExecutorMetadata, ...]:
        return tuple(entry for entry in self._entries.values() if entry.executor_id == executor_id)

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted({entry.executor_id for entry in self._entries.values()}))

    def route_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))


def validate_executor_for_operation(
    operation: dict,
    binding: dict,
    registry: ExecutorMetadataRegistry,
    *,
    network_authorized: bool,
) -> ExecutorMetadata:
    executor_id = str(binding["executor_id"])
    capability_id = str(binding["capability_id"])
    market = str(binding["market"])
    try:
        entry = registry.get_route(executor_id, capability_id, market)
    except OrchestrationError as exc:
        if exc.code != "unknown_executor_route":
            raise
        candidates = registry.routes_for_executor(executor_id)
        if not candidates:
            raise OrchestrationError("unknown_executor") from exc
        if any(item.market == market for item in candidates):
            raise OrchestrationError("capability_mismatch") from exc
        if any(item.capability_id == capability_id for item in candidates):
            raise OrchestrationError("market_mismatch") from exc
        raise
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
    if entry.output_policy not in SUPPORTED_OUTPUT_POLICIES:
        raise OrchestrationError("executor_output_policy_invalid")
    return entry
