"""Dormant A2.6 acceptance-only TPEx H1 composite execution candidate.

This module is deliberately not registered in the canonical executor registry.
Its only network path is the fixed, approval-bound three-source acceptance
plan described by ``ACCEPTANCE_AUTHORITY``.  Tests inject response bytes into
the same adapter path; production activation is outside this module.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any

from scripts.m8r_05b_01.canonical import plan_hash_and_id
from scripts.m8r_05b_01.planner import plan_identity_scope, PLAN_VALIDATOR
from scripts.m8r_05b_03.canonical import canonical_json
from scripts.m8r_05b_03.dispatch import request_identity
from scripts.ssl_policy import build_ssl_context
from scripts.m8r_05c.citation_builder import _build_citation_id
from scripts.m8r_05c.trading_status_composer import (
    build_component_record,
    compose_trading_status_context,
    validate_trading_status_context_composite,
)
from scripts.m8r_05c.errors import ProjectionError
from scripts.m8r_filesystem_safety import safe_destination
from .phase_h_trading_status_adapters import (
    H1NormalizationError,
    _tpex_attention_date_value,
    _tpex_cmode_date_value,
    _tpex_disposition_date_value,
    failed_source_result,
    normalize_representative_tpex_h1_component,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_EXECUTOR_ID = "phase_j_j_b03_tpex_trading_status_composite_candidate"
TARGET = {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488"}
COMPOSITE_CONTRACT = "trading_status_context_composite.v1"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
TIMEOUT_SECONDS = 60

SOURCE_PLAN = (
    {
        "source_id": "H1-TPEX-ATTENTION-OPENAPI",
        "source_family": "TPEX_ATTENTION_OPEN_DATA",
        "source_contract_id": "tpex_trading_warning_information",
        "endpoint": "https://www.tpex.org.tw/openapi/v1/tpex_trading_warning_information",
        "evidence_contract": "trading_status_context_evidence.v1",
        "required_fields": ("Date", "SecuritiesCompanyCode", "CompanyName", "TradingInformation", "ClosePrice", "PriceEarningRatio"),
    },
    {
        "source_id": "H1-TPEX-DISPOSITION-OPENAPI",
        "source_family": "TPEX_DISPOSITION_OPEN_DATA",
        "source_contract_id": "tpex_disposal_information",
        "endpoint": "https://www.tpex.org.tw/openapi/v1/tpex_disposal_information",
        "evidence_contract": "trading_status_context_evidence.v1",
        "required_fields": ("Date", "SecuritiesCompanyCode", "CompanyName", "DispositionPeriod", "DispositionReasons", "DisposalCondition"),
    },
    {
        "source_id": "H1-TPEX-CHANGED-TRADING-OPENAPI",
        "source_family": "TPEX_CHANGED_TRADING_OPEN_DATA",
        "source_contract_id": "tpex_cmode",
        "endpoint": "https://www.tpex.org.tw/openapi/v1/tpex_cmode",
        "evidence_contract": "trading_status_context_evidence.v2",
        "required_fields": ("Date", "SecuritiesCompanyCode", "CompanyName", "AlteredTrading", "PeriodicTrading", "ManagedStock", "MatchingFrequency", "SuspensionOfTrading", " FinancialAnnouncements"),
    },
)


def _source_overlay() -> list[dict[str, Any]]:
    return [{key: (list(value) if isinstance(value, tuple) else value) for key, value in source.items()}
            for source in SOURCE_PLAN]


ACCEPTANCE_AUTHORITY: dict[str, Any] = {
    "schema_version": "phase_j_b03_a2_6_acceptance_authority.v1",
    "authority_reference": "USER_CHAT_2026-10-07_J_B03_A2_6_REPRESENTATIVE_INTEGRATED_ACCEPTANCE_STAGE_A_AUTHORIZATION",
    "candidate_executor_id": CANDIDATE_EXECUTOR_ID,
    "capability_id": "trading_status_context",
    "target": deepcopy(TARGET),
    "ordered_sources": _source_overlay(),
    "composite_contract": COMPOSITE_CONTRACT,
    "transport": {
        "scheme": "https",
        "tls_policy": "compatibility",
        "certificate_verification": True,
        "hostname_verification": True,
        "timeout_seconds": TIMEOUT_SECONDS,
        "response_byte_ceiling": MAX_RESPONSE_BYTES,
        "retry": 0,
        "redirect_policy": "none",
        "fallback_policy": "none",
        "request_budget": {"GET": 3, "HEAD": 0, "POST": 0},
        "network_authorized": True,
    },
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def acceptance_authority_hash(authority: Mapping[str, Any] = ACCEPTANCE_AUTHORITY) -> str:
    return _sha256(canonical_json(dict(authority)).encode("utf-8"))


def validate_acceptance_authority(authority: Mapping[str, Any]) -> str:
    """Require byte-semantic equality with the candidate's fixed source plan."""
    if not isinstance(authority, Mapping) or dict(authority) != ACCEPTANCE_AUTHORITY:
        raise ValueError("a26_acceptance_authority_mismatch")
    if len(authority["ordered_sources"]) != 3:
        raise ValueError("a26_acceptance_authority_source_count_invalid")
    return acceptance_authority_hash(authority)


def bind_acceptance_authority_to_plan(plan: Mapping[str, Any], authority: Mapping[str, Any]) -> dict[str, Any]:
    """Create a single-operation candidate plan whose hash binds the overlay.

    The owner authorization and consumption binding then bind this plan hash;
    the execution request also carries that hash.  No request schema is changed.
    """
    overlay_hash = validate_acceptance_authority(authority)
    result = deepcopy(dict(plan))
    if len(result.get("operations", [])) != 1 or len(result.get("batch_groups", [])) != 1:
        raise ValueError("a26_candidate_requires_one_logical_operation")
    operation = result["operations"][0]
    batch = result["batch_groups"][0]
    if (operation.get("capability_id") != "trading_status_context"
            or operation.get("market") != "TPEX"
            or operation.get("canonical_target_ids") != [TARGET["canonical_target_id"]]
            or operation.get("operation_status") != "executable_pending_approval"):
        raise ValueError("a26_candidate_plan_target_or_capability_mismatch")
    old_operation_id = operation["operation_id"]
    operation_id = "umeop-op-v1-" + _sha256(f"{old_operation_id}:{overlay_hash}".encode("ascii"))[:20]
    batch_id = "umeop-batch-v1-" + _sha256(f"{operation_id}:{overlay_hash}".encode("ascii"))[:20]
    operation.update({
        "operation_id": operation_id,
        "executor_id": CANDIDATE_EXECUTOR_ID,
        "expected_evidence_contract": COMPOSITE_CONTRACT,
        "network_required": True,
        "parameters": {"acceptance_authority_sha256": overlay_hash},
        "batch_group_id": batch_id,
        "capability_requires_execution_approval": True,
    })
    batch.update({"batch_group_id": batch_id, "executor_id": CANDIDATE_EXECUTOR_ID,
                  "capability_id": "trading_status_context", "market": "TPEX",
                  "operation_ids": [operation_id], "network_required": True,
                  "capability_requires_execution_approval": True})
    result["accounting"]["network_request_estimate"] = 3
    result["input_bindings"]["planner_version"] = result["input_bindings"]["planner_version"]
    result["plan_hash"], result["plan_id"] = plan_hash_and_id(plan_identity_scope(result))
    errors = list(PLAN_VALIDATOR.iter_errors(result))
    if errors:
        raise ValueError("a26_candidate_plan_schema_invalid")
    return result


@dataclass(frozen=True)
class HTTPObservation:
    raw_bytes: bytes
    status: int
    content_type: str
    effective_url: str
    retrieved_at: str
    tls_policy: str
    redirect_count: int


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def official_get(endpoint: str, *, timeout_seconds: int = TIMEOUT_SECONDS,
                 byte_ceiling: int = MAX_RESPONSE_BYTES) -> HTTPObservation:
    """One verified HTTPS GET. Redirects and retries are disabled."""
    if (endpoint not in {source["endpoint"] for source in SOURCE_PLAN}
            or not endpoint.startswith("https://")
            or not 1 <= timeout_seconds <= 60
            or byte_ceiling != MAX_RESPONSE_BYTES):
        raise ValueError("a26_transport_authority_invalid")
    import ssl
    context = build_ssl_context("compatibility")
    if (not isinstance(context, ssl.SSLContext) or context.verify_mode != ssl.CERT_REQUIRED
            or context.check_hostname is not True):
        raise ValueError("a26_tls_verification_invalid")
    opener = urllib.request.build_opener(_NoRedirect(), urllib.request.HTTPSHandler(context=context))
    request = urllib.request.Request(endpoint, method="GET", headers={"Accept": "application/json"})
    try:
        response = opener.open(request, timeout=timeout_seconds)
    except urllib.error.HTTPError as response:
        # HTTP failures (including a blocked redirect) are still one completed
        # request and retain their status/headers without a second request.
        raw = response.read(byte_ceiling + 1)
        if len(raw) > byte_ceiling:
            raise ValueError("a26_response_byte_ceiling_exceeded")
        return HTTPObservation(
            raw_bytes=raw, status=int(response.code),
            content_type=str(response.headers.get("Content-Type", "")),
            effective_url=response.geturl(),
            retrieved_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            tls_policy="compatibility", redirect_count=0,
        )
    with response:
        raw = response.read(byte_ceiling + 1)
        if len(raw) > byte_ceiling:
            raise ValueError("a26_response_byte_ceiling_exceeded")
        return HTTPObservation(
            raw_bytes=raw,
            status=int(response.status),
            content_type=str(response.headers.get("Content-Type", "")),
            effective_url=response.geturl(),
            retrieved_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            tls_policy="compatibility",
            redirect_count=0,
        )


def _citation_for(operation_id: str, source_index: int, source_contract_id: str) -> str:
    return _build_citation_id(operation_id, f"evidence/phase_j/a26/components/{source_index:02d}-{source_contract_id}.json")


def _h1_failure(source: Mapping[str, Any], target: Mapping[str, str], *, observed_at: str,
                citation_id: str, code: str) -> dict[str, Any]:
    source_id = source["source_id"]
    if source_id != "H1-TPEX-CHANGED-TRADING-OPENAPI":
        return failed_source_result(source_id, target, observed_at=observed_at,
                                    diagnostic=code, citation_id=citation_id)
    descriptor = json.loads((ROOT / "config/phase_h_h1_dormant_source_descriptors.json").read_text(encoding="utf-8"))
    raw = next(item for item in descriptor["sources"] if item["source_id"] == source_id)
    source_obj = {key: raw[key] for key in ("source_family", "source_contract_id", "transport", "license_authority", "source_role", "activation_state")}
    declared = ["attention", "disposition", "changed_trading_method", "suspension", "resumption"]
    return {
        "schema_version": "trading_status_context_evidence.v2", "status": "source_failed",
        "target": dict(target), "coverage": {
            "status": "source_failed", "declared_scope_complete": False,
            "retrieval_succeeded": False, "source_contract_validated": False,
            "exact_target_search_succeeded": False, "source_snapshot_date": None,
            "declared_status_types": declared, "covered_status_types": [],
            "uncovered_status_types": declared, "failed_source_families": [source_obj["source_family"]],
        }, "source": source_obj, "observed_at": observed_at, "items": [],
        "caveats": [code], "citation_ids": [citation_id],
        "native_observation_count": 0, "native_observations": [],
    }


def _decode_payload(response: HTTPObservation) -> list[dict[str, Any]]:
    if response.status != 200 or "json" not in response.content_type.lower():
        raise ValueError("source_failed:http_or_content_type")
    try:
        value = json.loads(response.raw_bytes.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("source_failed:strict_json_decode") from exc
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise H1NormalizationError("source_failed:invalid_top_level_rows")
    return value


def _validate_source_rows(source: Mapping[str, Any], rows: list[dict[str, Any]], target: Mapping[str, str]) -> None:
    required = source["required_fields"]
    for row in rows:
        missing = [field for field in required if field not in row]
        if missing:
            raise H1NormalizationError(f"source_failed:missing_required_field:{missing[0]}")
        for field in required:
            if not isinstance(row[field], str):
                raise H1NormalizationError(f"source_failed:invalid_required_field_type:{field}")
        date_parsers = {
            "H1-TPEX-ATTENTION-OPENAPI": _tpex_attention_date_value,
            "H1-TPEX-DISPOSITION-OPENAPI": _tpex_disposition_date_value,
            "H1-TPEX-CHANGED-TRADING-OPENAPI": _tpex_cmode_date_value,
        }
        try:
            parsed_date = date_parsers[source["source_id"]](row["Date"])
        except H1NormalizationError as exc:
            raise H1NormalizationError(f"source_failed:date_contract_drift:{exc}") from exc
        if parsed_date is None:
            raise H1NormalizationError("source_failed:date_contract_drift:unresolved_Date")
    matches = [row for row in rows if row.get("SecuritiesCompanyCode") == target["security_code"]]
    if source["source_id"] == "H1-TPEX-ATTENTION-OPENAPI" and len(matches) > 1:
        raise H1NormalizationError("binding_failed:ambiguous_exact_target_rows")
    if source["source_id"] == "H1-TPEX-CHANGED-TRADING-OPENAPI" and len(matches) > 1:
        raise H1NormalizationError("binding_failed:ambiguous_exact_target_rows")


def _write_json(root: Path, relative_path: str, value: Mapping[str, Any]) -> bytes:
    content = (canonical_json(dict(value)) + "\n").encode("utf-8")
    destination = safe_destination(str(root), relative_path, create_parent=True).path
    destination.write_bytes(content)
    return content


def _artifact_record(root: Path, relative_path: str, value: Mapping[str, Any], role: str, item_count: int) -> dict[str, Any]:
    path = safe_destination(str(root), relative_path, create_parent=False).path
    content = path.read_bytes()
    return {"relative_path": relative_path, "sha256": _sha256(content),
            "schema_version": value["schema_version"], "byte_size": len(content),
            "item_count": item_count, "evidence_contract": value["schema_version"],
            "artifact_role": role}


def make_candidate_adapter(
    *, authority: Mapping[str, Any], bound_plan_hash: str,
    response_provider: Callable[[Mapping[str, Any]], HTTPObservation] | None = None,
    response_log: list[dict[str, Any]] | None = None,
) -> Callable[[dict[str, Any], Any], dict[str, Any]]:
    """Build a single-operation runtime callable, optionally with offline bytes."""
    authority_hash = validate_acceptance_authority(authority)
    observed_responses = response_log if response_log is not None else []

    def adapter(request: dict[str, Any], context: Any) -> dict[str, Any]:
        if (request.get("executor_id") != CANDIDATE_EXECUTOR_ID
                or request.get("capability_id") != "trading_status_context"
                or request.get("market") != "TPEX"
                or request.get("approved_security_identifiers") != [TARGET["canonical_target_id"]]
                or request.get("plan_hash") != bound_plan_hash):
            raise ValueError("a26_execution_binding_mismatch")
        if request.get("network_authorized") is not True:
            raise ValueError("a26_network_not_authorized")
        operation_id = request["operation_id"]
        req_id, req_hash = request_identity(request)
        output_root = Path(context.governed_output_root)
        components = []
        artifact_records: list[dict[str, Any]] = []
        sidecar_records: list[dict[str, Any]] = []
        for index, source in enumerate(SOURCE_PLAN, start=1):
            citation_id = _citation_for(operation_id, index, source["source_contract_id"])
            source_meta: dict[str, Any] | None = None
            try:
                response = (response_provider(source) if response_provider is not None
                            else official_get(source["endpoint"]))
                if response.effective_url != source["endpoint"] or response.redirect_count != 0:
                    raise ValueError("source_failed:redirect_or_effective_url_mismatch")
                source_meta = {
                    "request_ordinal": index, "method": "GET", "requested_url": source["endpoint"],
                    "effective_url": response.effective_url, "http_status": response.status,
                    "content_type": response.content_type, "response_bytes": len(response.raw_bytes),
                    "response_sha256": _sha256(response.raw_bytes), "retrieved_at": response.retrieved_at,
                    "tls_policy": response.tls_policy, "redirect_count": response.redirect_count,
                    "attempt_number": 1,
                }
                rows = _decode_payload(response)
                _validate_source_rows(source, rows, TARGET)
                evidence = normalize_representative_tpex_h1_component(
                    source["source_id"], rows, TARGET,
                    observed_at=response.retrieved_at, citation_id=citation_id,
                )
                attempt_outcome = "succeeded"
                failure_code = None
                provider_availability = "available"
            except Exception as exc:
                # Transport and source outcomes are source-local. The live
                # governance runner separately escalates source-contract drift.
                code = str(exc) if isinstance(exc, (ValueError, H1NormalizationError)) else f"source_failed:{type(exc).__name__}"
                observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                evidence = _h1_failure(source, TARGET, observed_at=observed_at,
                                       citation_id=citation_id, code=code)
                attempt_outcome = "failed"
                failure_code = code
                provider_availability = "unavailable"
                source_meta = {**(source_meta or {"request_ordinal": index, "method": "GET", "requested_url": source["endpoint"],
                               "attempt_number": 1}), "outcome": "failed", "failure_code": code}
            observed_responses.append({**source_meta, "source_id": source["source_id"],
                                       "outcome": attempt_outcome, "failure_code": failure_code})
            relative_path = f"evidence/phase_j/a26/components/{index:02d}-{source['source_contract_id']}.json"
            component_bytes = _write_json(output_root, relative_path, evidence)
            component_hash = _sha256(component_bytes)
            component = build_component_record(
                TARGET, source["source_id"], evidence,
                {"relative_path": relative_path, "sha256": component_hash},
            )
            components.append(component)
            item_count = len(evidence.get("items", []))
            artifact_records.append({"relative_path": relative_path, "sha256": component_hash,
                                     "schema_version": evidence["schema_version"], "byte_size": len(component_bytes),
                                     "item_count": item_count, "evidence_contract": evidence["schema_version"],
                                     "artifact_role": "component_evidence"})
            source_obj = evidence["source"]
            sidecar_path = f"evidence/phase_j/a26/governance/{index:02d}-{source['source_contract_id']}.json"
            sidecar = {"schema_version": "phase_h_source_attempt_governance.v1",
                       "evidence_artifact_reference": relative_path,
                       "canonical_target_id": TARGET["canonical_target_id"],
                       "capability_id": "trading_status_context", "attempts": [{
                           "source_family": source_obj["source_family"],
                           "source_contract_id": source_obj["source_contract_id"],
                           "source_role": source_obj["source_role"],
                           "activation_state": source_obj["activation_state"],
                           "provider_availability": provider_availability,
                           "license_authority": source_obj["license_authority"],
                           "coverage_result": evidence["status"],
                           "outcome": attempt_outcome, "failure_code": failure_code,
                           "citation_ids": evidence.get("citation_ids", []),
                       }]}
            sidecar_bytes = _write_json(output_root, sidecar_path, sidecar)
            sidecar_records.append({"relative_path": sidecar_path, "sha256": _sha256(sidecar_bytes),
                                    "schema_version": sidecar["schema_version"],
                                    "byte_size": len(sidecar_bytes), "item_count": 1,
                                    "evidence_contract": sidecar["schema_version"],
                                    "artifact_role": "supporting_governance"})

        composite = compose_trading_status_context(TARGET, components)
        validate_trading_status_context_composite(composite)
        composite_path = f"evidence/phase_j/a26/composite/{operation_id}.json"
        composite_bytes = _write_json(output_root, composite_path, composite)
        primary_record = {"relative_path": composite_path, "sha256": _sha256(composite_bytes),
                          "schema_version": COMPOSITE_CONTRACT, "byte_size": len(composite_bytes),
                          "item_count": composite["canonical_item_count"],
                          "evidence_contract": COMPOSITE_CONTRACT,
                          "artifact_role": "primary_evidence"}
        evidence_artifacts = [primary_record, *artifact_records, *sidecar_records]
        result = {
            "schema_version": "unified_market_evidence_operation_result.v2",
            "operation_id": operation_id, "execution_request_id": req_id,
            "execution_request_hash": req_hash, "executor_id": CANDIDATE_EXECUTOR_ID,
            "capability_id": "trading_status_context", "evidence_contract": COMPOSITE_CONTRACT,
            "status": "succeeded", "error_code": None,
            "result_item_count": composite["canonical_item_count"],
            "evidence_artifacts": evidence_artifacts, "warnings": [],
        }
        return result

    return adapter
