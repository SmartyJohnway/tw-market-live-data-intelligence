"""Dormant I3-A2 candidate: caller-supplied bytes only, no market transport.

This module is absent from the default production registry and public V3 path.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from scripts.m8r_05b_03.canonical import canonical_json
from scripts.m8r_05c.citation_builder import _build_citation_id

from .phase_i_i3_cash_institutional_flow_adapters import (
    CONTRACT_REL, CONTRACT_SHA256, EVIDENCE_SCHEMA, ROOT,
    load_frozen_contract, prepare_market_source, validate_evidence, validate_frozen_contract_object,
)

CAPABILITY_ID = "cash_institutional_flow_context"
EXECUTOR_ID = "phase_i_i3_cash_institutional_flow_context_executor"
_REQUEST_ID = re.compile(r"umereq-v[12]-[0-9a-f]{20}\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_OPERATION = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
_CODE = re.compile(r"[A-Za-z0-9]{1,20}\Z")


def build_i3_candidate_runtime_adapter_registry() -> dict[tuple[str, str], Any]:
    """Isolated candidate dispatch identity; never registered in production."""
    return {(EXECUTOR_ID, market): run_i3_candidate_offline_batch for market in ("TWSE", "TPEX")}


def _validate_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value or "T" not in value:
        raise ValueError("governed_retrieval_timestamp_required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("governed_retrieval_timestamp_invalid") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("governed_retrieval_timestamp_timezone_required")
    return value


def _validate_targets(targets: list[Mapping[str, Any]]) -> list[tuple[dict[str, Any], str]]:
    if not isinstance(targets, list) or not targets or len(targets) > 50:
        raise ValueError("candidate_target_count_invalid")
    result = []
    operations = set()
    for item in targets:
        if not isinstance(item, Mapping):
            raise ValueError("candidate_target_invalid")
        target = dict(item)
        market, code = target.get("market"), target.get("security_code")
        if market not in ("TWSE", "TPEX") or not isinstance(code, str) or not _CODE.fullmatch(code):
            raise ValueError("unsupported_target")
        if target.get("canonical_target_id") != f"{market}:{code}":
            raise ValueError("binding_failed:canonical_target_mismatch")
        if (target.get("instrument_family"), target.get("instrument_type")) != ("company_share", "common_share"):
            raise ValueError("unsupported_target")
        if target.get("execution_eligibility") != "allowed":
            raise ValueError("target_execution_not_eligible")
        operation = target.get("operation_id")
        if not isinstance(operation, str) or not _OPERATION.fullmatch(operation) or operation in operations:
            raise ValueError("operation_id_invalid_or_duplicate")
        operations.add(operation)
        if not isinstance(target.get("execution_request_id"), str) or not _REQUEST_ID.fullmatch(target["execution_request_id"]):
            raise ValueError("execution_request_id_invalid")
        if not isinstance(target.get("execution_request_hash"), str) or not _HEX.fullmatch(target["execution_request_hash"]):
            raise ValueError("execution_request_hash_invalid")
        result.append((target, market))
    return result


def run_i3_candidate_offline_batch(
    targets: list[Mapping[str, Any]],
    *,
    source_payloads: Mapping[str, bytes],
    retrieved_at_by_market: Mapping[str, str],
    twse_governed_source_date: str | None = None,
) -> dict[str, Any]:
    """Prepare each injected source once and project target-specific evidence."""
    scoped = _validate_targets(targets)
    requested = {market for _, market in scoped}
    if not isinstance(source_payloads, Mapping) or set(source_payloads) != requested:
        raise ValueError("injected_payload_market_scope_invalid")
    if not isinstance(retrieved_at_by_market, Mapping) or set(retrieved_at_by_market) != requested:
        raise ValueError("governed_retrieval_market_scope_invalid")
    timestamps = {market: _validate_timestamp(retrieved_at_by_market[market]) for market in requested}
    if "TWSE" not in requested and twse_governed_source_date is not None:
        raise ValueError("unexpected_twse_source_date")
    contract = load_frozen_contract()
    validate_frozen_contract_object(contract)
    prepared = {}
    transports = {}
    metrics = {}
    for market in sorted(requested):
        payload = source_payloads[market]
        if not isinstance(payload, bytes):
            raise ValueError("source_payload_must_be_bytes")
        prepared[market] = prepare_market_source(market, payload,
            twse_governed_source_date=twse_governed_source_date, contract=contract)
        transports[market] = {"mode": "offline_injected_fixture", "network_get_count": 0, "retry_count": 0,
            "response_byte_count": len(payload) if len(payload) <= 4 * 1024 * 1024 else 0,
            "response_sha256": hashlib.sha256(payload).hexdigest() if len(payload) <= 4 * 1024 * 1024 else None,
            "raw_payload_persisted": False}
        metrics[market] = {"decode_count": 1, "source_prepare_count": 1, "simulated_source_acquisition_count": 1,
                           "source_row_count": prepared[market].row_count}
    schema = json.loads((ROOT / "schemas/unified_market_evidence_operation_result.v2.schema.json").read_text(encoding="utf-8"))
    results = []
    artifacts = {}
    inventory = []
    evidence_objects = []
    for target, market in scoped:
        operation = target["operation_id"]
        relative_path = f"evidence/phase_i/i3/{operation}.json"
        citation_id = _build_citation_id(operation, relative_path)
        source = contract["sources"][market]
        common = {"schema_version": EVIDENCE_SCHEMA, "market": market, "security_code": target["security_code"],
            "canonical_target_id": target["canonical_target_id"], "retrieved_at": timestamps[market],
            "publication_finality": "unknown", "currentness_status": "unknown",
            "source": {"source_id": source["source_id"], "authority": "official", "market": market,
                       "source_contract_ref": CONTRACT_REL, "source_contract_sha256": CONTRACT_SHA256},
            "transport": transports[market], "citation_ids": [citation_id],
            "caveats": ["offline injected source fixture; no market request occurred",
                        "publication finality and currentness are unknown"]}
        state = prepared[market]
        if state.error_code:
            evidence = {**common, "status": "source_failed", "error_code": "source_failed"}
            evidence["caveats"].append(f"source preparation failed: {state.error_code}")
        else:
            matches = state.index.get(target["security_code"], [])
            common["source"]["trade_date"] = state.trade_date
            if len(matches) != 1:
                evidence = {**common, "status": "binding_failed", "error_code": "binding_failed"}
                evidence["caveats"].append(f"exact source-code matches: {len(matches)}")
            else:
                prepared_row = matches[0]
                evidence = {**common, "status": "complete", "trade_date": state.trade_date, "unit": "share",
                    **prepared_row.values}
                evidence["caveats"].extend(prepared_row.optional_caveats)
        validate_evidence(evidence)
        encoded = canonical_json(evidence).encode("utf-8")
        artifacts[relative_path] = encoded
        metadata = {"relative_path": relative_path, "sha256": hashlib.sha256(encoded).hexdigest(),
            "schema_version": EVIDENCE_SCHEMA, "byte_size": len(encoded), "item_count": 1,
            "evidence_contract": EVIDENCE_SCHEMA, "artifact_role": "primary_evidence"}
        inventory.append(metadata)
        failed = evidence["status"] in ("source_failed", "binding_failed")
        result = {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": operation,
            "execution_request_id": target["execution_request_id"], "execution_request_hash": target["execution_request_hash"],
            "executor_id": EXECUTOR_ID, "capability_id": CAPABILITY_ID, "evidence_contract": EVIDENCE_SCHEMA,
            "status": "failed" if failed else "succeeded", "error_code": evidence["status"] if failed else None,
            "result_item_count": 1, "evidence_artifacts": [metadata], "warnings": list(evidence["caveats"])}
        if list(Draft202012Validator(schema).iter_errors(result)):
            raise ValueError("operation_result_v2_invalid")
        results.append(result)
        evidence_objects.append(evidence)
    usable = {e["market"]: e["trade_date"] for e in evidence_objects if e["status"] == "complete"}
    if len(requested) == 2 and len(usable) == 2:
        alignment = "same_trade_date" if len(set(usable.values())) == 1 else "different_trade_date"
    else:
        alignment = "not_comparable"
    return {"executor_id": EXECUTOR_ID, "capability_id": CAPABILITY_ID,
            "simulated_source_acquisition_count": len(requested), "network_calls": 0, "retry_count": 0,
            "market_metrics": metrics, "alignment": {"status": alignment,
                "same_date_implies_simultaneous_publication": False,
                "numeric_same_session_interpretation_allowed": False},
            "artifact_bytes": artifacts, "artifact_inventory": inventory, "operation_results": results}
