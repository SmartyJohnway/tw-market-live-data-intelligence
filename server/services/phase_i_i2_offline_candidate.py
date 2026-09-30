"""Isolated, injected-input-only Phase I2 A2 candidate executor.

This is deliberately not imported by the default production runtime registry.
It has no transport implementation: a caller must supply fixture bytes, and
all shared-target operations reuse one decoded source payload in memory.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from scripts.m8r_05b_03.canonical import canonical_json
from scripts.m8r_05c.citation_builder import _build_citation_id

from .phase_i_i2_index_futures_adapters import (
    CAPABILITY_ID,
    EVIDENCE_SCHEMA,
    MAX_RESPONSE_BYTES,
    decode_or_copy_rows,
    normalize_taifex_tx_payload,
)

EXECUTOR_ID = "phase_i_i2_index_futures_context_executor"


def build_i2_candidate_runtime_adapter_registry() -> dict[tuple[str, str], Any]:
    """Return isolated candidate identity only; never the production registry."""
    return {(EXECUTOR_ID, "TWSE"): run_i2_candidate_offline_batch}


def run_i2_candidate_offline_batch(
    targets: list[Mapping[str, Any]],
    *,
    source_payload: bytes,
    governed_retrieved_at: str,
    transport_retrieved_at: str,
    fmtqik_benchmark_date: str | None = None,
) -> dict[str, Any]:
    """Normalize one injected fixture and bind it to compatible TWSE targets.

    The function does not accept a URL/callable, make network requests, or
    persist source payload bytes. Returned artifact bytes contain normalized
    evidence only.
    """
    if not isinstance(source_payload, bytes) or len(source_payload) > MAX_RESPONSE_BYTES:
        raise ValueError("source_failed:payload_invalid_or_oversized")
    rows, error, byte_count, content_type = decode_or_copy_rows(source_payload)
    if error or rows is None:
        raise ValueError(error or "source_failed:payload_invalid")
    if not targets:
        raise ValueError("binding_failed:no_targets")
    if len(targets) > 50:
        raise ValueError("binding_failed:target_limit_exceeded")

    seen_operations: set[str] = set()
    prepared = []
    for target in targets:
        if (target.get("market"), target.get("instrument_family"), target.get("instrument_type")) != (
            "TWSE", "company_share", "common_share"
        ):
            raise ValueError("unsupported_target")
        target_id = target.get("canonical_target_id")
        operation_id = target.get("operation_id")
        request_id = target.get("execution_request_id")
        request_hash = target.get("execution_request_hash")
        if not all(isinstance(value, str) and value for value in (target_id, operation_id, request_id)):
            raise ValueError("binding_failed:target_identity_missing")
        if not target_id.startswith("TWSE:"):
            raise ValueError("unsupported_target")
        if operation_id in seen_operations:
            raise ValueError("binding_failed:duplicate_operation")
        seen_operations.add(operation_id)
        if not isinstance(request_hash, str) or len(request_hash) != 64:
            raise ValueError("binding_failed:execution_request_hash_invalid")
        execution_request = target.get("execution_request")
        if not isinstance(execution_request, dict):
            raise ValueError("binding_failed:execution_request_missing")
        schema_path = __import__("pathlib").Path(__file__).resolve().parents[2] / "schemas" / "unified_market_evidence_execution_request.v2.schema.json"
        request_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if list(Draft202012Validator(request_schema).iter_errors(execution_request)):
            raise ValueError("binding_failed:execution_request_v2_invalid")
        if (execution_request.get("capability_id"), execution_request.get("executor_id"),
                execution_request.get("network_authorized"), execution_request.get("operation_id"),
                execution_request.get("execution_request_id")) != (
            CAPABILITY_ID, EXECUTOR_ID, False, operation_id, request_id
        ):
            raise ValueError("binding_failed:offline_candidate_request_scope_invalid")
        if target_id not in execution_request.get("approved_security_identifiers", []):
            raise ValueError("binding_failed:request_target_mismatch")
        prepared.append((target, target_id, operation_id, request_id, request_hash))

    results = []
    artifacts: dict[str, bytes] = {}
    inventory = []
    for target, target_id, operation_id, request_id, request_hash in prepared:
        relative_path = f"evidence/phase_i/i2/{operation_id}.json"
        citation_id = _build_citation_id(operation_id, relative_path)
        transport = {
            "http_status": 200,
            "content_type": content_type or "application/octet-stream",
            "response_byte_count": byte_count,
            "response_sha256": hashlib.sha256(source_payload).hexdigest(),
            "retrieved_at": transport_retrieved_at,
            "get_count": 1,
            "retry_count": 0,
            "raw_payload_persisted": False,
        }
        evidence = normalize_taifex_tx_payload(
            rows,
            governed_retrieved_at=governed_retrieved_at,
            fmtqik_benchmark_date=fmtqik_benchmark_date,
            citation_ids=[citation_id],
            transport=transport,
        )
        evidence["caveats"].append("offline injected-fixture transport metadata; no market request occurred")
        failed = evidence["status"] in {"source_failed", "binding_failed"}
        evidence_bytes = canonical_json(evidence).encode("utf-8")
        artifacts[relative_path] = evidence_bytes
        metadata = {
            "relative_path": relative_path,
            "sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "schema_version": EVIDENCE_SCHEMA,
            "byte_size": len(evidence_bytes),
            "item_count": 1,
            "evidence_contract": EVIDENCE_SCHEMA,
            "artifact_role": "primary_evidence",
        }
        inventory.append(metadata)
        operation_result = {
            "schema_version": "unified_market_evidence_operation_result.v2",
            "operation_id": operation_id,
            "execution_request_id": request_id,
            "execution_request_hash": request_hash,
            "executor_id": EXECUTOR_ID,
            "capability_id": CAPABILITY_ID,
            "evidence_contract": EVIDENCE_SCHEMA,
            "status": "failed" if failed else "succeeded",
            "error_code": evidence["status"] if failed else None,
            "result_item_count": 1,
            "evidence_artifacts": [metadata],
            "warnings": list(evidence.get("caveats", [])),
        }
        results.append(operation_result)

    result_schema_path = __import__("pathlib").Path(__file__).resolve().parents[2] / "schemas" / "unified_market_evidence_operation_result.v2.schema.json"
    schema = json.loads(result_schema_path.read_text(encoding="utf-8"))
    for result in results:
        errors = list(Draft202012Validator(schema).iter_errors(result))
        if errors:
            raise ValueError("source_failed:operation_result_v2_invalid")
    return {
        "executor_id": EXECUTOR_ID,
        "capability_id": CAPABILITY_ID,
        "simulated_source_acquisition_count": 1,
        "network_calls": 0,
        "retry_count": 0,
        "artifact_bytes": artifacts,
        "artifact_inventory": inventory,
        "operation_results": results,
    }
