"""Canonical identity functions for the non-authorizing plan artifact."""
from __future__ import annotations
import hashlib
import json
from typing import Any, Mapping, Sequence

MARKET_ORDER = {"TWSE": 0, "TPEX": 1, "TAIFEX": 2}

def canonical_json(value: Any) -> str:
    """Return the mandated compact UTF-8 JSON semantic representation."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

def canonical_target_ids(target_ids: Sequence[str]) -> list[str]:
    if not all(isinstance(target, str) and target for target in target_ids):
        raise ValueError("canonical_target_ids_invalid")
    if len(set(target_ids)) != len(target_ids):
        raise ValueError("canonical_target_ids_duplicate")
    return sorted(target_ids)

def canonical_warning_order(warnings: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted((dict(warning) for warning in warnings), key=lambda warning: (
        warning.get("code", ""), warning.get("capability_id", ""),
        tuple(warning.get("canonical_target_ids", [])), warning.get("severity", ""),
        warning.get("omission_reason", ""),
    ))

def _operation_key(operation: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        int(operation.get("capability_order", 0)),
        MARKET_ORDER.get(operation.get("market"), len(MARKET_ORDER)),
        operation.get("executor_id") or "",
        tuple(operation.get("canonical_target_ids", [])),
        canonical_json(operation.get("parameters", {})),
        operation.get("batch_key") or "",
        operation.get("operation_id") or "",
    )

def canonical_operation_order(operations: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted((dict(operation) for operation in operations), key=_operation_key)

def operation_id(scope: Mapping[str, Any]) -> str:
    return "umeop-op-v1-" + sha256_json(scope)[:20]

def batch_group_id(scope: Mapping[str, Any]) -> str:
    return "umeop-batch-v1-" + sha256_json(scope)[:20]

def plan_hash_and_id(plan_identity_scope: Mapping[str, Any]) -> tuple[str, str]:
    digest = sha256_json(plan_identity_scope)
    return digest, "umeop-v1-" + digest[:20]
