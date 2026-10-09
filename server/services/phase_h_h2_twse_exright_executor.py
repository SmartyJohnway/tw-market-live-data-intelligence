"""Bounded, dependency-bound TWSE TWT48U H2 executor candidate.

This executor is intentionally not selected by canonical routing in A3.  It is
available to the approved orchestration path only when an explicit same-target
H3 dependency is present in the approved plan.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import socket
import urllib.error
import urllib.request
from typing import Any, Mapping

from jsonschema import Draft7Validator, Draft202012Validator, FormatChecker

from scripts.m8r_05b_03.canonical import canonical_json
from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_filesystem_safety import FilesystemSafetyError, atomic_write_bytes, safe_destination
from scripts.ssl_policy import build_ssl_context
from scripts.validate_phase_h_v3_contracts import validate_recent_performance_semantics
from .phase_h_corporate_action_adapters import (
    H2NormalizationError,
    assemble_corporate_action_context,
    failed_source_result,
    normalize_twse_twt48u_all,
)


ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_ID = "phase_h_h2_twse_exright_pre_executor"
SOURCE_ID = "H2-TWSE-EXRIGHT-PRE-OPENAPI"
SOURCE_FAMILY = "TWSE_EXRIGHT_PRE_OPEN_DATA"
SOURCE_CONTRACT_ID = "TWT48U_ALL"
ENDPOINT = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
TIMEOUT_SECONDS = 15


class H2SourceAttemptError(Exception):
    """Expected source-local HTTP, payload, or source-contract failure."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def official_get_once(*, timeout_seconds: int = TIMEOUT_SECONDS) -> dict[str, Any]:
    """Make exactly one fixed-endpoint TLS-verified request; never retry/redirect."""
    if not 1 <= timeout_seconds <= TIMEOUT_SECONDS:
        raise OrchestrationError("h2_transport_timeout_policy_invalid")
    context = build_ssl_context("compatibility")
    if not isinstance(context, ssl.SSLContext) or context.verify_mode != ssl.CERT_REQUIRED or context.check_hostname is not True:
        raise OrchestrationError("h2_transport_tls_policy_invalid")
    opener = urllib.request.build_opener(_NoRedirect(), urllib.request.HTTPSHandler(context=context))
    request = urllib.request.Request(ENDPOINT, method="GET", headers={"Accept": "application/json"})
    try:
        response = opener.open(request, timeout=timeout_seconds)
    except urllib.error.HTTPError as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        return {"raw_bytes": raw, "status": int(response.code), "content_type": str(response.headers.get("Content-Type", "")), "effective_url": response.geturl(), "retrieved_at": _now()}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        # OSError here is limited to urllib/socket transport.  Internal
        # normalization and invariant failures occur outside this boundary.
        raise H2SourceAttemptError("source_failed:transport_unavailable") from exc
    with response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        return {"raw_bytes": raw, "status": int(response.status), "content_type": str(response.headers.get("Content-Type", "")), "effective_url": response.geturl(), "retrieved_at": _now()}


def _decode_rows(response: Mapping[str, Any]) -> list[dict[str, Any]]:
    if response.get("effective_url") != ENDPOINT:
        raise H2SourceAttemptError("source_failed:effective_url_mismatch")
    if len(response.get("raw_bytes", b"")) > MAX_RESPONSE_BYTES:
        raise H2SourceAttemptError("source_failed:response_ceiling_exceeded")
    if response.get("status") != 200 or "json" not in str(response.get("content_type", "")).lower():
        raise H2SourceAttemptError("source_failed:http_or_content_type")
    try:
        value = json.loads(response["raw_bytes"].decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise H2SourceAttemptError("source_failed:strict_json_decode") from exc
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise H2SourceAttemptError("source_failed:invalid_top_level_rows")
    return value


def _target_from_request(request: Mapping[str, Any]) -> dict[str, str]:
    identifiers = request.get("approved_security_identifiers")
    if request.get("market") != "TWSE" or not isinstance(identifiers, list) or len(identifiers) != 1:
        raise OrchestrationError("h2_target_binding_invalid")
    identifier = identifiers[0]
    if not isinstance(identifier, str) or not identifier.startswith("TWSE:"):
        raise OrchestrationError("h2_target_binding_invalid")
    code = identifier.split(":", 1)[1]
    if not code or not code.isascii() or not code.isdigit():
        raise OrchestrationError("h2_target_binding_invalid")
    return {"canonical_target_id": identifier, "market": "TWSE", "security_code": code}


def _h3_dependency(request: Mapping[str, Any], context: DispatchRuntimeContext, target: Mapping[str, str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    dependency_context = context.dependency_context or {}
    dependencies = dependency_context.get("dependencies")
    if not isinstance(dependencies, list) or len(dependencies) != 1:
        raise OrchestrationError("h2_h3_dependency_missing_or_ambiguous")
    dependency = dependencies[0]
    operation = dependency.get("operation")
    result = dependency.get("result")
    expected_id = dependency.get("operation_id")
    if (not isinstance(operation, dict) or not isinstance(result, dict)
            or operation.get("operation_id") != expected_id
            or operation.get("capability_id") != "recent_performance"
            or operation.get("market") != "TWSE"
            or operation.get("executor_id") != "phase_h_h3_twse_recent_performance_executor"
            or operation.get("canonical_target_ids") != [target["canonical_target_id"]]
            or result.get("operation_id") != expected_id
            or result.get("status") != "succeeded"
            or result.get("capability_id") != "recent_performance"
            or result.get("executor_id") != "phase_h_h3_twse_recent_performance_executor"
            or result.get("evidence_contract") != "recent_performance_evidence.v1"):
        raise OrchestrationError("h2_h3_dependency_unusable")
    artifacts = [item for item in result.get("evidence_artifacts", [])
                 if isinstance(item, dict)
                 and item.get("artifact_role") == "primary_evidence"
                 and item.get("schema_version") == "recent_performance_evidence.v1"
                 and item.get("evidence_contract") == "recent_performance_evidence.v1"]
    if len(artifacts) != 1:
        raise OrchestrationError("h2_h3_artifact_missing_or_ambiguous")
    artifact = artifacts[0]
    relative_path = artifact.get("relative_path")
    expected_hash = artifact.get("sha256")
    expected_size = artifact.get("byte_size")
    if (not isinstance(relative_path, str) or not relative_path
            or not isinstance(expected_hash, str) or len(expected_hash) != 64
            or type(expected_size) is not int or expected_size < 0):
        raise OrchestrationError("h2_h3_artifact_reference_invalid")
    try:
        destination = safe_destination(context.governed_output_root, relative_path, create_parent=False)
    except FilesystemSafetyError as exc:
        raise OrchestrationError("h2_h3_artifact_path_invalid") from exc
    if not destination.path.is_file():
        raise OrchestrationError("h2_h3_artifact_missing")
    try:
        raw = destination.path.read_bytes()
    except OSError as exc:
        raise OrchestrationError("h2_h3_artifact_read_failed") from exc
    if len(raw) != expected_size or hashlib.sha256(raw).hexdigest() != expected_hash:
        raise OrchestrationError("h2_h3_artifact_integrity_mismatch")
    try:
        h3 = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OrchestrationError("h2_h3_artifact_decode_failed") from exc
    schema = json.loads((ROOT / "schemas" / "recent_performance_evidence.v1.schema.json").read_text(encoding="utf-8"))
    if list(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(h3)):
        raise OrchestrationError("h2_h3_artifact_schema_invalid")
    try:
        validate_recent_performance_semantics(h3)
    except (TypeError, ValueError) as exc:
        raise OrchestrationError("h2_h3_artifact_semantics_invalid") from exc
    h3_target = h3.get("target", {})
    if any(h3_target.get(key) != target.get(key) for key in ("canonical_target_id", "market", "security_code")):
        raise OrchestrationError("h2_h3_artifact_target_mismatch")
    available = [item for item in h3.get("baselines", []) if item.get("status") == "available"]
    if len(available) != 1:
        raise OrchestrationError("h2_h3_available_baseline_not_unique")
    baseline = available[0]
    window = {"start": baseline.get("start_observation_date"), "end": baseline.get("end_observation_date")}
    if not all(isinstance(value, str) and value for value in window.values()) or window["start"] >= window["end"]:
        raise OrchestrationError("h2_h3_comparison_window_invalid")
    ref = f"{relative_path}#{expected_hash}"
    return h3, window, {"operation_id": expected_id, "artifact": artifact, "evidence_reference": ref}


def _phase_h_artifact_record(context: DispatchRuntimeContext, *, relative_path: str, payload: dict[str, Any], role: str) -> dict[str, Any]:
    schema_version = payload.get("schema_version")
    schema_path = ROOT / "schemas" / f"{schema_version}.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema) if schema.get("$schema", "").endswith("2020-12/schema") else Draft7Validator(schema)
    if list(validator.iter_errors(payload)):
        raise OrchestrationError("phase_h_evidence_schema_invalid")
    content = (canonical_json(payload) + "\n").encode("utf-8")
    atomic_write_bytes(context.governed_output_root, relative_path, content)
    count = len(payload.get("items", [])) if isinstance(payload.get("items"), list) else 1
    return {"relative_path": relative_path, "sha256": hashlib.sha256(content).hexdigest(), "schema_version": schema_version,
            "byte_size": len(content), "item_count": count, "evidence_contract": schema_version, "artifact_role": role}


def _result_base(request: Mapping[str, Any], *, status: str, error_code: str | None) -> dict[str, Any]:
    return {"schema_version": "unified_market_evidence_operation_result.v2", "operation_id": request["operation_id"],
            "execution_request_id": request["execution_request_id"], "execution_request_hash": request["execution_request_hash"],
            "executor_id": EXECUTOR_ID, "capability_id": "corporate_action_context", "evidence_contract": "corporate_action_context_evidence.v1",
            "status": status, "error_code": error_code, "result_item_count": 0, "evidence_artifacts": [], "warnings": []}


def _materialize(request: Mapping[str, Any], context: DispatchRuntimeContext, *, target: dict[str, str], evidence: dict[str, Any], attempt_status: str, failure_code: str | None, provider_availability: str, warning: str | None = None) -> dict[str, Any]:
    evidence_path = f"evidence/phase_h/h2/{request['operation_id']}.json"
    sidecar_path = f"evidence/phase_h/governance/{request['operation_id']}.json"
    evidence_ref = _phase_h_artifact_record(context, relative_path=evidence_path, payload=evidence, role="primary_evidence")
    source = evidence["sources"][0]
    sidecar = {"schema_version": "phase_h_source_attempt_governance.v1", "evidence_artifact_reference": evidence_path,
               "canonical_target_id": target["canonical_target_id"], "capability_id": "corporate_action_context",
               "attempts": [{"source_family": source["source_family"], "source_contract_id": source["source_contract_id"],
                             "source_role": source["source_role"], "activation_state": source["activation_state"],
                             "provider_availability": provider_availability,
                             "license_authority": source["license_authority"], "coverage_result": evidence["status"],
                             "outcome": attempt_status, "failure_code": failure_code, "citation_ids": evidence["citation_ids"]}]}
    sidecar_ref = _phase_h_artifact_record(context, relative_path=sidecar_path, payload=sidecar, role="supporting_governance")
    failed = evidence["status"] in {"source_failed", "binding_failed"}
    result = _result_base(request, status="failed" if failed else "succeeded", error_code=evidence["status"] if failed else None)
    result["result_item_count"] = evidence_ref["item_count"]
    result["evidence_artifacts"] = [evidence_ref, sidecar_ref]
    result["warnings"] = [warning] if warning else list(evidence.get("caveats", []))
    return result


def execute_h2_twse_exright_pre(request: dict[str, Any], context: DispatchRuntimeContext, *, fetch_response=None) -> dict[str, Any]:
    """Run one approved TWT48U attempt using exact H3 dependency artifacts."""
    if (request.get("executor_id") != EXECUTOR_ID or request.get("capability_id") != "corporate_action_context"
            or request.get("market") != "TWSE" or request.get("schema_version") != "unified_market_evidence_execution_request.v1"):
        raise OrchestrationError("unsupported_h2_production_route")
    target = _target_from_request(request)
    try:
        h3, window, dependency = _h3_dependency(request, context, target)
    except OrchestrationError as exc:
        code = str(exc)
        if code.startswith(("h2_h3_dependency_", "h2_h3_artifact_", "h2_h3_available_baseline_", "h2_h3_comparison_window_")):
            blocked = _result_base(request, status="failed", error_code="h3_dependency_unusable")
            blocked["warnings"] = [
                "comparison_unavailable_h3_dependency_not_usable",
                f"dependency_failure:{code}",
                "h2_source_not_attempted",
                "h4_not_derived_no_clearance_implied",
            ]
            return blocked
        raise
    del h3  # validated exact input; only its baseline-derived dates bind H2 assembly.
    evidence_path = f"evidence/phase_h/h2/{request['operation_id']}.json"
    # Keep the M8R-05C projection dependency lazy: importing it here at module
    # load time creates a cycle through scripts.m8r_05b_03.__init__ →
    # orchestrator → this executor → citation_builder → M8R-05C canonical.
    from scripts.m8r_05c.citation_builder import _build_citation_id

    citation_id = _build_citation_id(request["operation_id"], evidence_path)
    observed_at = _now()
    source_fetch = official_get_once if fetch_response is None else fetch_response
    try:
        try:
            response = source_fetch(timeout_seconds=min(request.get("timeout_seconds", TIMEOUT_SECONDS), TIMEOUT_SECONDS))
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError) as exc:
            raise H2SourceAttemptError("source_failed:transport_unavailable") from exc
        observed_at = response.get("retrieved_at") if isinstance(response.get("retrieved_at"), str) else observed_at
        rows = _decode_rows(response)
        normalized = normalize_twse_twt48u_all(rows, target, observed_at=observed_at, citation_id=citation_id)
        evidence = assemble_corporate_action_context([normalized], target, observed_at=observed_at, requested_window=window)
        if evidence["coverage"]["requested_window"] != window:
            raise OrchestrationError("h2_window_binding_mismatch")
        result = _materialize(request, context, target=target, evidence=evidence,
                              attempt_status="failed" if evidence["status"] in {"source_failed", "binding_failed"} else "succeeded",
                              failure_code=evidence["status"] if evidence["status"] in {"source_failed", "binding_failed"} else None,
                              provider_availability="available")
        result["warnings"].append(f"h3_dependency_operation:{dependency['operation_id']}")
        return result
    except H2SourceAttemptError as exc:
        failed = failed_source_result(SOURCE_ID, str(exc), citation_id=citation_id)
        evidence = assemble_corporate_action_context([failed], target, observed_at=observed_at, requested_window=window)
        return _materialize(request, context, target=target, evidence=evidence, attempt_status="failed", failure_code=str(exc),
                            provider_availability="unavailable" if "transport_unavailable" in str(exc) else "unknown")
    except H2NormalizationError as exc:
        code = str(exc)
        binding_failed = code.startswith("binding_failed:")
        failed = failed_source_result(SOURCE_ID, code, binding_failed=binding_failed, citation_id=citation_id)
        evidence = assemble_corporate_action_context([failed], target, observed_at=observed_at, requested_window=window)
        return _materialize(request, context, target=target, evidence=evidence, attempt_status="failed", failure_code=str(exc),
                            provider_availability="available" if binding_failed else "unknown")


def derive_h4_for_completed_plan(plan: Mapping[str, Any], outcomes: list[dict[str, Any]], *, output_root: str) -> list[dict[str, Any]]:
    """Persist H4 only when the approved exact H2/H3 dependency chain is usable."""
    h2_ops = sorted(
        (op for op in plan.get("operations", [])
         if op.get("capability_id") == "corporate_action_context"
         and op.get("operation_status") == "executable_pending_approval"),
        key=lambda op: op.get("operation_id", ""),
    )
    outcome_by_id = {item.get("operation_id"): item for item in outcomes}
    operation_by_id = {item.get("operation_id"): item for item in plan.get("operations", [])}
    if len(outcome_by_id) != len(outcomes) or len(operation_by_id) != len(plan.get("operations", [])):
        raise OrchestrationError("h4_operation_identity_ambiguous")

    def load_primary(result: dict, contract: str) -> tuple[dict, dict]:
        matches = [item for item in result.get("evidence_artifacts", []) if item.get("artifact_role") == "primary_evidence" and item.get("evidence_contract") == contract and item.get("schema_version") == contract]
        if len(matches) != 1:
            raise OrchestrationError("h4_input_artifact_missing_or_ambiguous")
        item = matches[0]
        destination = safe_destination(output_root, item["relative_path"], create_parent=False)
        data = destination.path.read_bytes()
        if len(data) != item["byte_size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise OrchestrationError("h4_input_artifact_integrity_mismatch")
        value = json.loads(data.decode("utf-8", errors="strict"))
        return value, item

    def derive_one(h2_op: Mapping[str, Any]) -> dict[str, Any] | None:
        dependencies = h2_op.get("dependency_operation_ids")
        if not isinstance(dependencies, list) or len(dependencies) != 1:
            raise OrchestrationError("h2_dependency_graph_invalid")
        h3_id = dependencies[0]
        h3_op = operation_by_id.get(h3_id)
        if (h2_op.get("market") != "TWSE"
                or not isinstance(h3_op, dict)
                or h3_op.get("capability_id") != "recent_performance"
                or h3_op.get("market") != "TWSE"
                or h3_op.get("operation_status") != "executable_pending_approval"
                or h3_op.get("executor_invocation_eligible") is not True
                or h3_op.get("canonical_target_ids") != h2_op.get("canonical_target_ids")):
            raise OrchestrationError("h2_h3_dependency_binding_mismatch")
        h2_result = outcome_by_id.get(h2_op.get("operation_id"))
        h3_result = outcome_by_id.get(h3_id)
        if (not isinstance(h2_result, dict) or h2_result.get("status") != "succeeded"
                or h2_result.get("operation_id") != h2_op.get("operation_id")
                or h2_result.get("capability_id") != "corporate_action_context"
                or not isinstance(h3_result, dict) or h3_result.get("status") != "succeeded"
                or h3_result.get("operation_id") != h3_id
                or h3_result.get("capability_id") != "recent_performance"):
            return None
        h2, h2_ref = load_primary(h2_result, "corporate_action_context_evidence.v1")
        h3, h3_ref = load_primary(h3_result, "recent_performance_evidence.v1")
        target = h2.get("target", {})
        if (h2_op.get("canonical_target_ids") != [target.get("canonical_target_id")]
                or target != h3.get("target")):
            raise OrchestrationError("h4_input_target_mismatch")
        for contract, evidence in (("corporate_action_context_evidence.v1", h2), ("recent_performance_evidence.v1", h3)):
            schema = json.loads((ROOT / f"schemas/{contract}.schema.json").read_text(encoding="utf-8"))
            if list(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(evidence)):
                raise OrchestrationError("h4_input_artifact_schema_invalid")
        from .phase_h_discontinuity_safety import derive_discontinuity_safety
        event_refs = {index: h2_ref["relative_path"] for index in range(len(h2.get("events", [])))}
        official_refs = {index: h2_ref["relative_path"] for index, event in enumerate(h2.get("events", [])) if event.get("official_reference_price", {}).get("state") == "value"}
        h4 = derive_discontinuity_safety(h2_evidence=h2, h3_evidence=h3,
                                         h2_evidence_reference=f"{h2_ref['relative_path']}#{h2_ref['sha256']}",
                                         h3_evidence_reference=f"{h3_ref['relative_path']}#{h3_ref['sha256']}",
                                         event_evidence_references=event_refs,
                                         official_reference_evidence_references=official_refs)
        path = f"evidence/phase_h/h4/{h2_op['operation_id']}.json"
        schema = json.loads((ROOT / "schemas/discontinuity_safety_evidence.v1.schema.json").read_text(encoding="utf-8"))
        if list(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(h4)):
            raise OrchestrationError("h4_artifact_schema_invalid")
        content = (canonical_json(h4) + "\n").encode("utf-8")
        atomic_write_bytes(output_root, path, content)
        return {"relative_path": path, "sha256": hashlib.sha256(content).hexdigest(), "schema_version": "discontinuity_safety_evidence.v1",
                "byte_size": len(content), "item_count": 1, "evidence_contract": "discontinuity_safety_evidence.v1"}

    artifacts = [artifact for op in h2_ops if (artifact := derive_one(op)) is not None]
    return artifacts
