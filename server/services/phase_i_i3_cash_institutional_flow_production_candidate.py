"""Dormant I3-A4 V2 production executor candidate.

This module is intentionally absent from the default runtime registry. It uses
the frozen A1 parser and emits production-provenance V2 evidence separately
from the historical V1 offline-injected A2 candidate.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator

from scripts.m8r_05b_03.canonical import canonical_json
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_filesystem_safety import atomic_write_bytes
from scripts.m8r_05c.citation_builder import _build_citation_id
from .phase_i_i3_cash_institutional_flow_adapters import (
    CONTRACT_REL, CONTRACT_SHA256, ROOT, load_frozen_contract, prepare_market_source,
)
from .phase_i_i3_cash_institutional_flow_v2_evidence import validate_evidence_v2
from .phase_i_i3_production_transport import AcquisitionError, acquire_once

CAPABILITY_ID = "cash_institutional_flow_context"
EXECUTOR_ID = "phase_i_i3_cash_institutional_flow_context_executor"
EVIDENCE_SCHEMA = "cash_institutional_flow_context_evidence.v2"
MAX_BATCH_TARGETS = 50
_OPERATION = re.compile(r"umeop-op-v1-[0-9a-f]{20}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")


def build_i3_production_candidate_registry(*, acquire: Callable[..., Any] = acquire_once) -> dict[tuple[str, str], Any]:
    """Return isolated candidate registrations; never installs into default runtime."""
    return {(EXECUTOR_ID, market): lambda requests, context: production_batch_operation_adapter_candidate(
        requests, context, acquire=acquire
    ) for market in ("TWSE", "TPEX")}


def build_i3_production_candidate_registrations(*, acquire: Callable[..., Any] = acquire_once) -> list[Any]:
    """Build two dormant M8R runtime registrations without mutating its registry."""
    from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistration
    return [RuntimeAdapterRegistration(
        executor_id=EXECUTOR_ID, capability_id=CAPABILITY_ID, market=market,
        supported_security_types=("equity",), expected_evidence_contract=EVIDENCE_SCHEMA,
        network_required=True, bounded_execution_supported=True, timeout_seconds=30,
        maximum_result_items=50, output_policy="no_raw_payload_retention",
        adapter=lambda request, context, _acquire=acquire: production_operation_adapter_candidate(
            request, context, acquire=_acquire
        ),
        batch_adapter=lambda requests, context, _acquire=acquire: production_batch_operation_adapter_candidate(
            requests, context, acquire=_acquire
        ), fake_adapter=False,
    ) for market in ("TWSE", "TPEX")]


def _validate_batch(requests: tuple[dict[str, Any], ...], context: Any) -> tuple[str, str | None]:
    if getattr(context, "mode", None) != "execute-approved" or not 1 <= len(requests) <= MAX_BATCH_TARGETS:
        raise OrchestrationError("i3_approved_batch_required")
    first = requests[0]
    market = first.get("market")
    if market not in ("TWSE", "TPEX"):
        raise OrchestrationError("i3_market_unsupported")
    binding = (first.get("batch_group_id"), first.get("authorization_id"), first.get("authorization_hash"),
               first.get("plan_hash"))
    source_date: str | None = None
    if market == "TWSE":
        params = first.get("parameters")
        source_date = params.get("resolved_source_trade_date") if isinstance(params, dict) else None
        if not isinstance(source_date, str):
            raise OrchestrationError("i3_twse_date_binding_invalid")
    seen: set[str] = set()
    for request in requests:
        if (request.get("schema_version"), request.get("capability_id"), request.get("executor_id"),
            request.get("market"), request.get("network_authorized"), request.get("timeout_seconds"),
            request.get("maximum_records")) != (
            "unified_market_evidence_execution_request.v3", CAPABILITY_ID, EXECUTOR_ID, market, True, 30, 50
        ):
            raise OrchestrationError("i3_execution_request_scope_invalid")
        if not _HASH.fullmatch(str(request.get("execution_request_hash", ""))):
            raise OrchestrationError("i3_execution_request_hash_invalid")
        if not _OPERATION.fullmatch(str(request.get("operation_id", ""))) or request["operation_id"] in seen:
            raise OrchestrationError("i3_operation_id_invalid_or_duplicate")
        seen.add(request["operation_id"])
        targets = request.get("approved_security_identifiers")
        if not isinstance(targets, list) or len(targets) != 1 or not re.fullmatch(r"(?:TWSE|TPEX):[A-Za-z0-9]{1,20}", targets[0]):
            raise OrchestrationError("i3_target_binding_invalid")
        if targets[0].split(":", 1)[0] != market:
            raise OrchestrationError("i3_target_market_mismatch")
        if (request.get("batch_group_id"), request.get("authorization_id"), request.get("authorization_hash"),
            request.get("plan_hash")) != binding:
            raise OrchestrationError("i3_batch_binding_mismatch")
        params = request.get("parameters")
        if market == "TWSE":
            if not isinstance(params, dict) or set(params) != {"resolved_source_trade_date"}:
                raise OrchestrationError("i3_twse_date_binding_invalid")
            if params.get("resolved_source_trade_date") != source_date:
                raise OrchestrationError("i3_batch_binding_mismatch")
        if market == "TPEX" and params != {}:
            raise OrchestrationError("i3_tpex_query_date_forbidden")
    return market, source_date


def _failed_evidence(market: str, target_id: str, retrieved_at: str, transport: dict[str, Any], code: str) -> dict[str, Any]:
    source = load_frozen_contract()["sources"][market]
    return {
        "schema_version": EVIDENCE_SCHEMA, "status": "source_failed", "market": market,
        "security_code": target_id.split(":", 1)[1], "canonical_target_id": target_id,
        "trade_date": None, "resolved_source_trade_date": transport.get("resolved_source_trade_date"),
        "source_reported_trade_date": None, "retrieved_at": retrieved_at,
        "publication_finality": "unknown", "currentness_status": "unknown",
        "source": {"source_id": source["source_id"], "authority": "official", "market": market,
                   "source_contract_ref": CONTRACT_REL, "source_contract_sha256": CONTRACT_SHA256,
                   "source_reported_trade_date": None},
        "transport": {key: value for key, value in transport.items() if key != "resolved_source_trade_date"},
        "citation_ids": ["urn:tw-market:i3:source-failure"],
        "caveats": ["official source acquisition or normalization failed"], "error_code": code,
    }


def production_batch_operation_adapter_candidate(
    requests: tuple[dict[str, Any], ...] | list[dict[str, Any]], context: Any,
    *, acquire: Callable[..., Any] = acquire_once,
) -> list[dict[str, Any]]:
    """Acquire once for one approved same-market batch and persist V2 only."""
    batch = tuple(requests)
    market, source_date = _validate_batch(batch, context)
    try:
        acquired = acquire(market, resolved_source_trade_date=source_date)
        body, transport = acquired.body, dict(acquired.telemetry)
    except AcquisitionError as exc:
        transport = dict(exc.telemetry)
        transport["resolved_source_trade_date"] = source_date
        body = None
        code = exc.code
    else:
        code = None
    stamp = transport.get("retrieved_at")
    if not isinstance(stamp, str):
        raise OrchestrationError("i3_transport_retrieval_timestamp_missing")
    if source_date is not None:
        transport["resolved_source_trade_date"] = source_date
    prepared = None
    if body is not None:
        parser_date = source_date.replace("-", "") if source_date is not None else None
        prepared = prepare_market_source(market, body, twse_governed_source_date=parser_date,
                                        contract=load_frozen_contract())
        if prepared.error_code:
            code = "source_failed"
    outcomes: list[dict[str, Any]] = []
    schema = json.loads((ROOT / "schemas/unified_market_evidence_operation_result.v2.schema.json").read_text(encoding="utf-8"))
    source_contract = load_frozen_contract()["sources"][market]
    for request in batch:
        target_id = request["approved_security_identifiers"][0]
        code_value = target_id.split(":", 1)[1]
        relative_path = f"evidence/phase_i/i3/{request['operation_id']}.json"
        citation = _build_citation_id(request["operation_id"], relative_path)
        base_transport = {key: value for key, value in transport.items()
                          if key not in {"resolved_source_trade_date", "retrieved_at"}}
        base = {"schema_version": EVIDENCE_SCHEMA, "market": market, "security_code": code_value,
                "canonical_target_id": target_id, "retrieved_at": stamp,
                "resolved_source_trade_date": source_date, "source_reported_trade_date": None,
                "publication_finality": "unknown", "currentness_status": "unknown",
                "source": {"source_id": source_contract["source_id"], "authority": "official", "market": market,
                           "source_contract_ref": CONTRACT_REL, "source_contract_sha256": CONTRACT_SHA256,
                           "source_reported_trade_date": None},
                "transport": base_transport, "citation_ids": [citation],
                "caveats": ["publication finality and currentness are unknown"]}
        if code is not None or prepared is None:
            evidence = {**base, "status": "source_failed", "trade_date": None, "error_code": code or "source_failed"}
        else:
            base["source_reported_trade_date"] = prepared.trade_date
            base["source"]["source_reported_trade_date"] = prepared.trade_date
            matches = prepared.index.get(code_value, [])
            if len(matches) != 1:
                evidence = {**base, "status": "binding_failed", "trade_date": None, "error_code": "binding_failed",
                            "caveats": base["caveats"] + [f"exact source-code matches: {len(matches)}"]}
            else:
                row = matches[0]
                evidence = {**base, "status": "complete", "trade_date": prepared.trade_date, "unit": "share",
                            **copy.deepcopy(row.values), "caveats": base["caveats"] + list(row.optional_caveats)}
        validate_evidence_v2(evidence)
        content = (canonical_json(evidence) + "\n").encode("utf-8")
        atomic_write_bytes(context.governed_output_root, relative_path, content, allow_overwrite=False)
        artifact = {"relative_path": relative_path, "sha256": hashlib.sha256(content).hexdigest(),
                    "schema_version": EVIDENCE_SCHEMA, "byte_size": len(content), "item_count": 1,
                    "evidence_contract": EVIDENCE_SCHEMA, "artifact_role": "primary_evidence"}
        failed = evidence["status"] != "complete"
        result = {"schema_version": "unified_market_evidence_operation_result.v2",
                  "operation_id": request["operation_id"], "execution_request_id": request["execution_request_id"],
                  "execution_request_hash": request["execution_request_hash"], "executor_id": EXECUTOR_ID,
                  "capability_id": CAPABILITY_ID, "evidence_contract": EVIDENCE_SCHEMA,
                  "status": "failed" if failed else "succeeded", "error_code": evidence.get("error_code") if failed else None,
                  "result_item_count": 1, "evidence_artifacts": [artifact], "warnings": list(evidence["caveats"])}
        errors = list(Draft202012Validator(schema).iter_errors(result))
        if errors:
            raise OrchestrationError("i3_operation_result_invalid")
        outcomes.append(result)
    return outcomes


def production_operation_adapter_candidate(request: dict[str, Any], context: Any) -> dict[str, Any]:
    return production_batch_operation_adapter_candidate((request,), context)[0]
