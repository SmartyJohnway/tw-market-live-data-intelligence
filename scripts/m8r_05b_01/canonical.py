"""Canonical identity functions for the non-authorizing plan artifact."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

MARKET_ORDER = {"TWSE": 0, "TPEX": 1, "TAIFEX": 2}
CROSS_MARKET_DERIVED_CAPABILITIES = frozenset({"source_currentness", "evidence_quality"})


def canonical_json(value: Any) -> str:
    """Return the mandated compact UTF-8 JSON semantic representation."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def canonical_target_ids(target_ids: Sequence[str]) -> list[str]:
    if not isinstance(target_ids, Sequence) or isinstance(target_ids, (str, bytes)):
        raise ValueError("canonical_target_ids_invalid")
    if not all(isinstance(target, str) and target for target in target_ids):
        raise ValueError("canonical_target_ids_invalid")
    if len(set(target_ids)) != len(target_ids):
        raise ValueError("canonical_target_ids_duplicate")
    return sorted(target_ids)


def canonical_warning_order(warnings: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Copy, canonicalize target lists, then order warnings without display text."""
    normalized: list[dict[str, Any]] = []
    for warning in warnings:
        if not isinstance(warning, Mapping):
            raise ValueError("canonical_warning_invalid")
        item = dict(warning)
        item["canonical_target_ids"] = canonical_target_ids(item.get("canonical_target_ids", []))
        normalized.append(item)
    return sorted(normalized, key=lambda warning: (
        warning.get("code", ""), warning.get("capability_id", ""),
        tuple(warning["canonical_target_ids"]), warning.get("severity", ""),
        warning.get("omission_reason", ""),
    ))


def _operation_key(
    operation: Mapping[str, Any], *, capability_order_by_id: Mapping[str, int],
    batch_key_by_operation_id: Mapping[str, str],
    cross_market_derived_capability_ids: frozenset[str],
) -> tuple[Any, ...]:
    operation_id_value = operation.get("operation_id")
    capability_id = operation.get("capability_id")
    if not isinstance(operation_id_value, str) or not operation_id_value:
        raise ValueError("operation_id_invalid")
    if capability_id not in capability_order_by_id:
        raise ValueError("capability_order_unknown")
    if operation_id_value not in batch_key_by_operation_id:
        raise ValueError("batch_key_unknown")
    market = operation.get("market")
    if market is None:
        if capability_id not in cross_market_derived_capability_ids:
            raise ValueError("cross_market_derived_rule_violation")
        market_order = len(MARKET_ORDER)
    elif market in MARKET_ORDER:
        market_order = MARKET_ORDER[market]
    else:
        raise ValueError("market_unknown")
    return (
        capability_order_by_id[capability_id], market_order,
        operation.get("executor_id") or "", tuple(canonical_target_ids(operation.get("canonical_target_ids", []))),
        canonical_json(operation.get("parameters", {})), batch_key_by_operation_id[operation_id_value], operation_id_value,
    )


def canonical_operation_order(
    operations: Sequence[Mapping[str, Any]], *, capability_order_by_id: Mapping[str, int],
    batch_key_by_operation_id: Mapping[str, str],
    cross_market_derived_capability_ids: frozenset[str] = CROSS_MARKET_DERIVED_CAPABILITIES,
) -> list[dict[str, Any]]:
    """Order schema-shaped operations using separate, non-emitted projection context."""
    copied = [dict(operation) for operation in operations]
    operation_ids = [operation.get("operation_id") for operation in copied]
    if len(operation_ids) != len(set(operation_ids)):
        raise ValueError("operation_id_duplicate")
    return sorted(copied, key=lambda operation: _operation_key(
        operation, capability_order_by_id=capability_order_by_id,
        batch_key_by_operation_id=batch_key_by_operation_id,
        cross_market_derived_capability_ids=cross_market_derived_capability_ids,
    ))


def operation_id(scope: Mapping[str, Any]) -> str:
    return "umeop-op-v1-" + sha256_json(scope)[:20]


def batch_group_id(scope: Mapping[str, Any]) -> str:
    return "umeop-batch-v1-" + sha256_json(scope)[:20]


def plan_hash_and_id(plan_identity_scope: Mapping[str, Any]) -> tuple[str, str]:
    digest = sha256_json(plan_identity_scope)
    return digest, "umeop-v1-" + digest[:20]
