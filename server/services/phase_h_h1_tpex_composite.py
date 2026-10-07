"""Production-neutral, fixed-source TPEx H1 composite execution core.

The caller supplies an already approved, exact target and execution context.
This module owns the fixed source set, bounded HTTPS transport, normalization,
source-local failure capture, artifact lineage, and Composite/OperationResult
construction. It has no routing or activation authority of its own.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any

from scripts.m8r_05b_03.canonical import canonical_json
from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext, request_identity
from scripts.m8r_05c.citation_builder import _build_citation_id
from scripts.m8r_05c.trading_status_composer import (
    build_component_record, compose_trading_status_context,
    validate_trading_status_context_composite,
)
from scripts.m8r_filesystem_safety import safe_destination
from scripts.ssl_policy import build_ssl_context
from .phase_h_trading_status_adapters import (
    H1NormalizationError, _tpex_attention_date_value, _tpex_cmode_date_value,
    _tpex_disposition_date_value, failed_source_result,
    normalize_representative_tpex_h1_component,
)

ROOT = Path(__file__).resolve().parents[2]
COMPOSITE_CONTRACT = "trading_status_context_composite.v1"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
TIMEOUT_SECONDS = 60
SOURCES: tuple[dict[str, Any], ...] = (
    {"source_id": "H1-TPEX-ATTENTION-OPENAPI", "source_family": "TPEX_ATTENTION_OPEN_DATA",
     "source_contract_id": "tpex_trading_warning_information",
     "endpoint": "https://www.tpex.org.tw/openapi/v1/tpex_trading_warning_information",
     "evidence_contract": "trading_status_context_evidence.v1",
     "required_fields": ("Date", "SecuritiesCompanyCode", "CompanyName", "TradingInformation", "ClosePrice", "PriceEarningRatio")},
    {"source_id": "H1-TPEX-DISPOSITION-OPENAPI", "source_family": "TPEX_DISPOSITION_OPEN_DATA",
     "source_contract_id": "tpex_disposal_information",
     "endpoint": "https://www.tpex.org.tw/openapi/v1/tpex_disposal_information",
     "evidence_contract": "trading_status_context_evidence.v1",
     "required_fields": ("Date", "SecuritiesCompanyCode", "CompanyName", "DispositionPeriod", "DispositionReasons", "DisposalCondition")},
    {"source_id": "H1-TPEX-CHANGED-TRADING-OPENAPI", "source_family": "TPEX_CHANGED_TRADING_OPEN_DATA",
     "source_contract_id": "tpex_cmode",
     "endpoint": "https://www.tpex.org.tw/openapi/v1/tpex_cmode",
     "evidence_contract": "trading_status_context_evidence.v2",
     "required_fields": ("Date", "SecuritiesCompanyCode", "CompanyName", "AlteredTrading", "PeriodicTrading", "ManagedStock", "MatchingFrequency", "SuspensionOfTrading", " FinancialAnnouncements")},
)
SOURCE_BY_ID = {source["source_id"]: source for source in SOURCES}


class H1CompositeSourceAttemptError(Exception):
    """An expected transport or source-payload failure for one fixed source."""


_SOURCE_LOCAL_NORMALIZATION_PREFIXES = (
    "source_failed:invalid_top_level_rows",
    "source_failed:missing_required_field:",
    "source_failed:invalid_required_field_type:",
    "source_failed:invalid_source_snapshot_date_type:",
    "source_failed:invalid_source_snapshot_date_calendar:",
    "source_failed:unresolved_source_record_date:",
    "source_failed:date_contract_drift:",
    "source_failed:empty_source_security_code",
    "binding_failed:ambiguous_exact_target_rows",
    "binding_failed:invalid_exact_target_security_code",
)


def _expected_normalization_failure_code(exc: H1NormalizationError) -> str:
    code = str(exc)
    if not any(code == prefix or (prefix.endswith(":") and code.startswith(prefix))
               for prefix in _SOURCE_LOCAL_NORMALIZATION_PREFIXES):
        raise exc
    return code


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def official_get(endpoint: str, *, timeout_seconds: int = TIMEOUT_SECONDS) -> dict[str, Any]:
    """Perform one verified HTTPS GET to a member of the fixed source set."""
    if endpoint not in {item["endpoint"] for item in SOURCES} or not 1 <= timeout_seconds <= TIMEOUT_SECONDS:
        raise ValueError("phase_h_composite_transport_authority_invalid")
    import ssl
    context = build_ssl_context("compatibility")
    if not isinstance(context, ssl.SSLContext) or context.verify_mode != ssl.CERT_REQUIRED or context.check_hostname is not True:
        raise ValueError("phase_h_composite_tls_verification_invalid")
    opener = urllib.request.build_opener(_NoRedirect(), urllib.request.HTTPSHandler(context=context))
    request = urllib.request.Request(endpoint, method="GET", headers={"Accept": "application/json"})
    try:
        response = opener.open(request, timeout=timeout_seconds)
    except urllib.error.HTTPError as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise H1CompositeSourceAttemptError("source_failed:response_ceiling_exceeded")
        return {"raw_bytes": raw, "status": int(response.code),
                "content_type": str(response.headers.get("Content-Type", "")),
                "effective_url": response.geturl(), "retrieved_at": _now(),
                "tls_policy": "compatibility", "redirect_count": 0}
    with response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise H1CompositeSourceAttemptError("source_failed:response_ceiling_exceeded")
        return {"raw_bytes": raw, "status": int(response.status),
                "content_type": str(response.headers.get("Content-Type", "")),
                "effective_url": response.geturl(), "retrieved_at": _now(),
                "tls_policy": "compatibility", "redirect_count": 0}


def _decode_payload(response: Mapping[str, Any]) -> list[dict[str, Any]]:
    if response.get("status") != 200 or "json" not in str(response.get("content_type", "")).lower():
        raise H1CompositeSourceAttemptError("source_failed:http_or_content_type")
    try:
        value = json.loads(response["raw_bytes"].decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise H1CompositeSourceAttemptError("source_failed:strict_json_decode") from exc
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise H1CompositeSourceAttemptError("source_failed:invalid_top_level_rows")
    return value


def _validate_source_rows(source: Mapping[str, Any], rows: list[dict[str, Any]], target: Mapping[str, str]) -> None:
    parsers = {"H1-TPEX-ATTENTION-OPENAPI": _tpex_attention_date_value,
               "H1-TPEX-DISPOSITION-OPENAPI": _tpex_disposition_date_value,
               "H1-TPEX-CHANGED-TRADING-OPENAPI": _tpex_cmode_date_value}
    for row in rows:
        missing = [field for field in source["required_fields"] if field not in row]
        if missing:
            raise H1NormalizationError(f"source_failed:missing_required_field:{missing[0]}")
        for field in source["required_fields"]:
            if not isinstance(row[field], str):
                raise H1NormalizationError(f"source_failed:invalid_required_field_type:{field}")
        try:
            parsed_date = parsers[source["source_id"]](row["Date"])
        except H1NormalizationError as exc:
            raise H1NormalizationError(f"source_failed:date_contract_drift:{exc}") from exc
        if parsed_date is None:
            raise H1NormalizationError("source_failed:date_contract_drift:unresolved_Date")
    matches = [row for row in rows if row.get("SecuritiesCompanyCode") == target["security_code"]]
    if source["source_id"] in {"H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI"} and len(matches) > 1:
        raise H1NormalizationError("binding_failed:ambiguous_exact_target_rows")


def _write_json(root: Path, relative_path: str, value: Mapping[str, Any]) -> bytes:
    content = (canonical_json(dict(value)) + "\n").encode("utf-8")
    safe_destination(str(root), relative_path, create_parent=True).path.write_bytes(content)
    return content


def _source_failure(source: Mapping[str, Any], target: Mapping[str, str], *, observed_at: str,
                    citation_id: str, code: str) -> dict[str, Any]:
    if source["source_id"] != "H1-TPEX-CHANGED-TRADING-OPENAPI":
        return failed_source_result(source["source_id"], target, observed_at=observed_at,
                                    diagnostic=code, citation_id=citation_id)
    descriptor = json.loads((ROOT / "config/phase_h_h1_dormant_source_descriptors.json").read_text(encoding="utf-8"))
    raw = next(item for item in descriptor["sources"] if item["source_id"] == source["source_id"])
    source_obj = {key: raw[key] for key in ("source_family", "source_contract_id", "transport", "license_authority", "source_role", "activation_state")}
    declared = ["attention", "disposition", "changed_trading_method", "suspension", "resumption"]
    return {"schema_version": "trading_status_context_evidence.v2", "status": "source_failed", "target": dict(target),
            "coverage": {"status": "source_failed", "declared_scope_complete": False, "retrieval_succeeded": False,
                         "source_contract_validated": False, "exact_target_search_succeeded": False,
                         "source_snapshot_date": None, "declared_status_types": declared,
                         "covered_status_types": [], "uncovered_status_types": declared,
                         "failed_source_families": [source_obj["source_family"]]},
            "source": source_obj, "observed_at": observed_at, "items": [], "caveats": [code],
            "citation_ids": [citation_id], "native_observation_count": 0, "native_observations": []}


def execute_composite_operation(
    request: dict[str, Any], context: DispatchRuntimeContext, *,
    target: Mapping[str, str], executor_id: str,
    response_provider: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    response_log: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute the fixed three-source semantic pipeline for an approved target."""
    if (request.get("executor_id") != executor_id or request.get("capability_id") != "trading_status_context"
            or request.get("market") != "TPEX" or request.get("approved_security_identifiers") != [target["canonical_target_id"]]
            or target.get("canonical_target_id") != f"TPEX:{target.get('security_code')}"
            or target.get("market") != "TPEX" or not isinstance(target.get("security_code"), str)
            or not target["security_code"] or request.get("approved_security_types") != ["equity"]):
        raise ValueError("phase_h_composite_execution_binding_mismatch")
    if context.mode != "execute-approved" or request.get("network_authorized") is not True:
        raise ValueError("network_required_not_authorized")
    operation_id = request["operation_id"]
    req_id, req_hash = request_identity(request)
    output_root = Path(context.governed_output_root)
    responses = response_log if response_log is not None else []
    components: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    sidecars: list[dict[str, Any]] = []
    for index, source in enumerate(SOURCES, start=1):
        citation_id = _build_citation_id(operation_id, f"evidence/phase_h/h1/composite/components/{index:02d}-{source['source_contract_id']}.json")
        source_meta: dict[str, Any] | None = None
        try:
            try:
                response = response_provider(source) if response_provider is not None else official_get(source["endpoint"], timeout_seconds=request.get("timeout_seconds", TIMEOUT_SECONDS))
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                raise H1CompositeSourceAttemptError("source_failed:transport_failure") from exc
            if response.get("effective_url") != source["endpoint"] or response.get("redirect_count") != 0:
                raise H1CompositeSourceAttemptError("source_failed:redirect_or_effective_url_mismatch")
            raw = response.get("raw_bytes")
            if not isinstance(raw, bytes):
                raise TypeError("phase_h_composite_response_bytes_invariant_invalid")
            if len(raw) > MAX_RESPONSE_BYTES:
                raise H1CompositeSourceAttemptError("source_failed:response_ceiling_exceeded")
            source_meta = {"request_ordinal": index, "method": "GET", "requested_url": source["endpoint"],
                           "effective_url": response["effective_url"], "http_status": response.get("status"),
                           "content_type": response.get("content_type", ""), "response_bytes": len(raw),
                           "response_sha256": _sha256(raw), "retrieved_at": response.get("retrieved_at", _now()),
                           "tls_policy": response.get("tls_policy", "compatibility"), "redirect_count": 0,
                           "attempt_number": 1}
            rows = _decode_payload(response)
            _validate_source_rows(source, rows, target)
            evidence = normalize_representative_tpex_h1_component(source["source_id"], rows, target,
                         observed_at=source_meta["retrieved_at"], citation_id=citation_id)
            outcome, failure_code, availability = "succeeded", None, "available"
        except (H1CompositeSourceAttemptError, H1NormalizationError) as exc:
            code = (_expected_normalization_failure_code(exc)
                    if isinstance(exc, H1NormalizationError) else str(exc))
            observed_at = _now()
            evidence = _source_failure(source, target, observed_at=observed_at, citation_id=citation_id, code=code)
            outcome, failure_code, availability = "failed", code, "unavailable"
            source_meta = {**(source_meta or {"request_ordinal": index, "method": "GET", "requested_url": source["endpoint"], "attempt_number": 1}),
                           "outcome": "failed", "failure_code": code}
        responses.append({**source_meta, "source_id": source["source_id"], "outcome": outcome, "failure_code": failure_code})
        relative_path = f"evidence/phase_h/h1/composite/components/{index:02d}-{source['source_contract_id']}.json"
        payload_bytes = _write_json(output_root, relative_path, evidence)
        comp_hash = _sha256(payload_bytes)
        components.append(build_component_record(target, source["source_id"], evidence,
                           {"relative_path": relative_path, "sha256": comp_hash}))
        artifacts.append({"relative_path": relative_path, "sha256": comp_hash, "schema_version": evidence["schema_version"],
                          "byte_size": len(payload_bytes), "item_count": len(evidence.get("items", [])),
                          "evidence_contract": evidence["schema_version"], "artifact_role": "component_evidence"})
        source_obj = evidence["source"]
        sidecar_path = f"evidence/phase_h/h1/composite/governance/{index:02d}-{source['source_contract_id']}.json"
        sidecar = {"schema_version": "phase_h_source_attempt_governance.v1", "evidence_artifact_reference": relative_path,
                   "canonical_target_id": target["canonical_target_id"], "capability_id": "trading_status_context",
                   "attempts": [{"source_family": source_obj["source_family"], "source_contract_id": source_obj["source_contract_id"],
                                 "source_role": source_obj["source_role"], "activation_state": source_obj["activation_state"],
                                 "provider_availability": availability, "license_authority": source_obj["license_authority"],
                                 "coverage_result": evidence["status"], "outcome": outcome, "failure_code": failure_code,
                                 "citation_ids": evidence.get("citation_ids", [])}]}
        sidecar_bytes = _write_json(output_root, sidecar_path, sidecar)
        sidecars.append({"relative_path": sidecar_path, "sha256": _sha256(sidecar_bytes),
                         "schema_version": sidecar["schema_version"], "byte_size": len(sidecar_bytes),
                         "item_count": 1, "evidence_contract": sidecar["schema_version"],
                         "artifact_role": "supporting_governance"})
    composite = compose_trading_status_context(target, components)
    validate_trading_status_context_composite(composite)
    composite_path = f"evidence/phase_h/h1/composite/{operation_id}.json"
    composite_bytes = _write_json(output_root, composite_path, composite)
    primary = {"relative_path": composite_path, "sha256": _sha256(composite_bytes),
               "schema_version": COMPOSITE_CONTRACT, "byte_size": len(composite_bytes),
               "item_count": composite["canonical_item_count"], "evidence_contract": COMPOSITE_CONTRACT,
               "artifact_role": "primary_evidence"}
    return {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": operation_id,
            "execution_request_id": req_id, "execution_request_hash": req_hash, "executor_id": executor_id,
            "capability_id": "trading_status_context", "evidence_contract": COMPOSITE_CONTRACT,
            "status": "succeeded", "error_code": None, "result_item_count": composite["canonical_item_count"],
            "evidence_artifacts": [primary, *artifacts, *sidecars], "warnings": []}


def production_composite_adapter(request: dict[str, Any], context: DispatchRuntimeContext) -> dict[str, Any]:
    """Production entry point; target is derived only from the approved request."""
    executor_id = "phase_h_h1_tpex_composite_executor"
    if request.get("executor_id") != executor_id or request.get("capability_id") != "trading_status_context" or request.get("market") != "TPEX":
        raise ValueError("phase_h_composite_execution_binding_mismatch")
    identifiers = request.get("approved_security_identifiers")
    if not isinstance(identifiers, list) or len(identifiers) != 1 or not isinstance(identifiers[0], str):
        raise ValueError("approved_target_count_invalid")
    target_id = identifiers[0]
    prefix, sep, code = target_id.partition(":")
    if not sep or prefix != "TPEX" or not code or code.strip() != code or any(ch.isspace() for ch in code):
        raise ValueError("approved_target_invalid")
    target = {"canonical_target_id": target_id, "market": "TPEX", "security_code": code}
    return execute_composite_operation(request, context, target=target, executor_id=executor_id)
