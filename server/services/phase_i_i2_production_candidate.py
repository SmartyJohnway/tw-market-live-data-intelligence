"""Approval-bound I2 A4 production surface; no acquisition at import/build time.

The accepted A3 fixed-endpoint transport and A2 normalizer remain unchanged.
Each fully validated same-source batch acquires and normalizes exactly once.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.m8r_05b_03.canonical import canonical_json
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_filesystem_safety import FilesystemSafetyError, atomic_write_bytes
from scripts.m8r_05c.citation_builder import _build_citation_id
from .phase_i_i2_index_futures_adapters import CAPABILITY_ID, EVIDENCE_SCHEMA, normalize_taifex_tx_payload
from .phase_i_i2_live_acceptance_candidate import A3TransportError, acquire_taifex_once, _read_once

EXECUTOR_ID = "phase_i_i2_index_futures_context_executor"
ROOT = Path(__file__).resolve().parents[2]
MAX_BATCH_TARGETS = 50


def _stamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_batch(requests, context):
    if context.mode != "execute-approved" or not 1 <= len(requests) <= MAX_BATCH_TARGETS:
        raise OrchestrationError("i2_approved_batch_required")
    schema = json.loads((ROOT / "schemas/unified_market_evidence_execution_request.v2.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    seen = set()
    binding = tuple(requests[0].get(k) for k in ("batch_group_id", "authorization_id"))
    for req in requests:
        if not validator.is_valid(req):
            raise OrchestrationError("i2_execution_request_invalid")
        if (req.get("schema_version"), req.get("executor_id"), req.get("capability_id"), req.get("market"),
                req.get("network_authorized"), req.get("timeout_seconds"), req.get("maximum_records"),
                req.get("parameters"), req.get("approved_security_types")) != (
                "unified_market_evidence_execution_request.v2", EXECUTOR_ID, CAPABILITY_ID, "TWSE",
                True, 30, 1, {}, ["equity"]):
            raise OrchestrationError("i2_execution_request_scope_invalid")
        targets = req.get("approved_security_identifiers", [])
        if len(targets) != 1 or not re.fullmatch(r"TWSE:[0-9]{4}", targets[0]):
            raise OrchestrationError("i2_approved_target_invalid")
        if tuple(req.get(k) for k in ("batch_group_id", "authorization_id")) != binding:
            raise OrchestrationError("i2_batch_binding_mismatch")
        if req["operation_id"] in seen:
            raise OrchestrationError("i2_duplicate_operation")
        seen.add(req["operation_id"])


def production_batch_operation_adapter_candidate(requests, context):
    _validate_batch(requests, context)
    governed_stamp = _stamp()
    # One execution-root-scoped reservation, latched before any delegate I/O.
    # It contains control metadata only, never source bytes or a reusable cache.
    try:
        atomic_write_bytes(context.governed_output_root, "source_acquisition/i2-single-get-claim.json",
            canonical_json({"capability_id": CAPABILITY_ID, "maximum_acquisitions": 1,
                            "retry_count": 0, "execution_reference_timestamp": governed_stamp}).encode("utf-8"),
            allow_overwrite=False)
    except FilesystemSafetyError as exc:
        raise OrchestrationError("i2_source_acquisition_reservation_failed") from exc
    try:
        acquired = acquire_taifex_once(transport=_read_once)
        transport = {"http_status": acquired.http_status, "content_type": acquired.content_type,
                     "response_byte_count": acquired.response_byte_count, "response_sha256": acquired.response_sha256,
                     "retrieved_at": acquired.retrieved_at, "get_count": 1, "retry_count": 0,
                     "raw_payload_persisted": False}
        payload = acquired.body
    except A3TransportError as exc:
        # Empty rows produce the frozen honest source_failed shape, not absent
        # evidence or fabricated observations. Keep bounded transport telemetry.
        payload = []
        transport = {"http_status": exc.status, "content_type": exc.content_type,
                     "response_byte_count": exc.byte_count, "response_sha256": exc.response_sha256,
                     "retrieved_at": _stamp(), "get_count": 1, "retry_count": 0,
                     "raw_payload_persisted": False, "error_code": exc.code}
    base = normalize_taifex_tx_payload(payload, governed_retrieved_at=governed_stamp,
            fmtqik_benchmark_date=None, citation_ids=["pending-operation-citation"], transport=transport)
    if "error_code" in transport:
        base["caveats"].append(transport["error_code"])
    results = []
    result_schema = json.loads((ROOT / "schemas/unified_market_evidence_operation_result.v2.schema.json").read_text(encoding="utf-8"))
    for req in requests:
        rel = f"evidence/phase_i/i2/{req['operation_id']}.json"
        evidence = copy.deepcopy(base)
        evidence["citation_ids"] = [_build_citation_id(req["operation_id"], rel)]
        body = canonical_json(evidence).encode("utf-8")
        atomic_write_bytes(context.governed_output_root, rel, body, allow_overwrite=False)
        artifact = {"relative_path": rel, "sha256": hashlib.sha256(body).hexdigest(),
                    "schema_version": EVIDENCE_SCHEMA, "byte_size": len(body), "item_count": 1,
                    "evidence_contract": EVIDENCE_SCHEMA, "artifact_role": "primary_evidence"}
        failed = evidence["status"] in {"source_failed", "binding_failed"}
        result = {"schema_version": "unified_market_evidence_operation_result.v2",
                  "operation_id": req["operation_id"], "execution_request_id": req["execution_request_id"],
                  "execution_request_hash": req["execution_request_hash"], "executor_id": EXECUTOR_ID,
                  "capability_id": CAPABILITY_ID, "evidence_contract": EVIDENCE_SCHEMA,
                  "status": "failed" if failed else "succeeded", "error_code": evidence["status"] if failed else None,
                  "result_item_count": 1, "evidence_artifacts": [artifact], "warnings": evidence["caveats"]}
        Draft202012Validator(result_schema).validate(result)
        results.append(result)
    return results


def production_operation_adapter_candidate(request, context):
    return production_batch_operation_adapter_candidate((request,), context)[0]
