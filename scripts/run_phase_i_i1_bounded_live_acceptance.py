"""One-shot, candidate-registry-only Phase I1 bounded live acceptance.

The normal Catalog, Routing, and executor registry remain dormant.  This
runner builds an acceptance-only in-memory planning overlay, then delegates
authorization, preflight, execute-once, receipt/bundle finalization, and V3
projection to the existing 05B/05C machinery.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import uuid
import urllib.error
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from jsonschema import Draft202012Validator, Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.m8r_05b_01.canonical import sha256_json
from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight, validate_preflight_hashes
from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry
from scripts.m8r_05c.artifact_loader import load_projection_inputs
from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.citation_builder import build_citation_index
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.result_builder import build_result
from scripts.m8r_05c.errors import ProjectionError
from scripts.m8r_06_01c2_mode_a_security_master_loader import get_production_mode_a_security_master
from scripts.m8r_08g_security_master_releases import load_active_identity_service
from server.services.phase_i_i1_production_candidate import (
    CAPABILITY_ID,
    EVIDENCE_CONTRACT,
    EXECUTOR_ID,
    MAX_RESPONSE_BYTES,
    SOURCE_DESCRIPTORS,
    TIMEOUT_SECONDS,
    _http_transport,
    build_i1_candidate_runtime_adapter_registry,
    production_batch_operation_adapter_candidate,
    production_operation_adapter_candidate,
)


OWNER_AUTHORITY_REFERENCE = "USER_CHAT_2026-09-30_PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE"
RESULT_V3 = "unified_market_evidence_result.v3"
AUDIT_V3 = "unified_market_evidence_audit_package.v3"
TOTAL_GET_LIMIT = 3
MARKET_TARGET_COUNT = 2
APPROVED_URLS = {item["url"]: source_id for source_id, item in SOURCE_DESCRIPTORS.items()}


class AcceptanceError(RuntimeError):
    def __init__(self, code: str, *, classification: str = "FAIL"):
        self.code = code
        self.classification = classification
        super().__init__(code)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _zulu(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AcceptanceError("authority_json_invalid")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _report_path(path: Path, package_root: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return "fixture-output/" + path.resolve().relative_to(package_root.resolve()).as_posix()


def classify_acceptance(*, transport_blocked: bool, network_bounds_proven: bool,
                        twse_status: str, tpex_status: str, result_valid: bool,
                        audit_valid: bool, citation_valid: bool, raw_payload_absent: bool,
                        runtime_dormant: bool) -> str:
    """Pure gate classification; external source refusal is BLOCKED, defects FAIL."""
    if transport_blocked or twse_status in {"unavailable", "source_failed", "binding_failed"} or tpex_status in {"unavailable", "source_failed", "binding_failed"}:
        return "BLOCKED"
    if not network_bounds_proven or twse_status not in {"complete", "partial"} or tpex_status != "complete":
        return "FAIL"
    if not (result_valid and audit_valid and citation_valid and raw_payload_absent and runtime_dormant):
        return "FAIL"
    return "PASS"


def select_targets(identity_runtime: Any) -> list[dict[str, Any]]:
    """Select the first two exact eligible common-share identities per market."""
    records = identity_runtime.lookup.get("by_canonical")
    if not isinstance(records, Mapping):
        raise AcceptanceError("security_master_lookup_invalid", classification="BLOCKED")
    selected: list[dict[str, Any]] = []
    for market in ("TWSE", "TPEX"):
        eligible = []
        for canonical, record in records.items():
            classification = record.get("classification") or {}
            if (
                classification.get("market") == market
                and classification.get("instrument_family") == "company_share"
                and classification.get("instrument_type") == "common_share"
                and (record.get("execution_eligibility") or {}).get("status") == "allowed"
                and record.get("canonical_target_id") == canonical
            ):
                eligible.append((canonical, record))
        eligible.sort(key=lambda item: item[0])
        if len(eligible) < MARKET_TARGET_COUNT:
            raise AcceptanceError("security_master_market_target_coverage_insufficient", classification="BLOCKED")
        for canonical, record in eligible[:MARKET_TARGET_COUNT]:
            identity = record.get("identity") or {}
            current_listing = record.get("current_listing") or {}
            if current_listing.get("market") != market or identity.get("security_code") != canonical.split(":", 1)[1]:
                raise AcceptanceError("security_master_canonical_listing_binding_invalid", classification="BLOCKED")
            selected.append({
                "canonical_target_id": canonical,
                "isin": identity.get("isin"),
                "market": market,
                "security_code": identity["security_code"],
                "instrument_family": "company_share",
                "instrument_type": "common_share",
                "security_master_record_hash": record.get("record_hash"),
            })
    return selected


def candidate_authorities() -> dict[str, dict[str, Any]]:
    """Return a private in-memory acceptance overlay; never touch canonical files."""
    from scripts.m8r_06_02_mode_b1_preview import load_planning_authorities

    authorities = load_planning_authorities("unified_market_evidence_request.v3")
    catalog = copy.deepcopy(authorities["capability_catalog"])
    routing = copy.deepcopy(authorities["routing_matrix"])
    cap = next((item for item in catalog["data_need_capabilities"] if item.get("capability_id") == CAPABILITY_ID), None)
    route = next((item for item in routing["routes"] if item.get("capability_id") == CAPABILITY_ID), None)
    if cap is None or route is None:
        raise AcceptanceError("i1_candidate_authority_missing")
    cap["support_status"] = "runtime_executable"
    cap["runtime_executable"] = True
    cap["phase_i_activation_state"] = "bounded_live_acceptance_only"
    route.update({
        "capability_status_source": "temporary acceptance-only projection of the reviewed I1 candidate; canonical route remains plan_only",
        "runtime_executable": True,
        "provisional": False,
        "candidate_executor_ids": [EXECUTOR_ID],
        "selected_executor_id": EXECUTOR_ID,
        "routing_status": "resolved",
        "network_required": True,
        "blocking_reasons": [],
        "estimated_operation_rule": "one shared official market context acquisition per same-market target group; no retry; total maximum three official GETs",
    })
    metadata = _read_json(ROOT / "config" / "phase_i_i1_production_executor_candidate.json")["executor_metadata"]
    surfaces = authorities["executor_disposition"].get("surfaces")
    if not isinstance(surfaces, list) or any(item.get("surface_id") == EXECUTOR_ID for item in surfaces if isinstance(item, dict)):
        raise AcceptanceError("i1_candidate_disposition_collision")
    surfaces.append({
        "surface_id": EXECUTOR_ID,
        "path": "server/services/phase_i_i1_production_candidate.py",
        "surface_type": "bounded_i1_acceptance_candidate_executor",
        "current_status": "explicit one-shot acceptance candidate only",
        "network_behavior": "fixed official endpoints, one GET each, no retry, three GET total maximum",
        "input_contract": "05B execution request v1 for market_state_context / one market / exact approved targets",
        "output_contract": EVIDENCE_CONTRACT,
        "approval_boundary": "05B plan-bound authorization, execute-once claim, and network confirmation",
        "authorization_binding": "05B operation, market, target set, executor, and evidence contract",
        "single_use_enforced": True,
        "supported_markets": ["TWSE", "TPEX"],
        "supported_security_types": ["equity"],
        "supported_capabilities": [CAPABILITY_ID],
        "batching_supported": True,
        "deterministic": False,
        "reusable_for_05b": True,
        "reuse_mode": "adapter_required",
        "disposition": "adapter_required",
        "blocking_gaps": [],
    })
    authorities.update({"capability_catalog": catalog, "routing_matrix": routing})
    authorities["executor_metadata"] = metadata
    return authorities


class BoundedTransport:
    """Count actual fixed-endpoint calls; reject repeat or fourth call pre-I/O."""
    def __init__(self, delegate: Callable[[str, int], tuple[int, Mapping[str, str], bytes]]):
        self.delegate = delegate
        self.calls: list[dict[str, Any]] = []
        self.bodies: list[bytes] = []
        self.by_url: dict[str, int] = {}
        self.failed = False

    def __call__(self, url: str, timeout_seconds: int) -> tuple[int, Mapping[str, str], bytes]:
        if self.failed:
            raise AcceptanceError("prior_source_attempt_failed", classification="BLOCKED")
        if url not in APPROVED_URLS:
            raise AcceptanceError("unapproved_source_endpoint")
        if timeout_seconds != TIMEOUT_SECONDS:
            raise AcceptanceError("transport_timeout_contract_mismatch")
        if len(self.calls) >= TOTAL_GET_LIMIT or self.by_url.get(url, 0) >= 1:
            raise AcceptanceError("live_get_budget_exceeded")
        self.by_url[url] = self.by_url.get(url, 0) + 1
        item: dict[str, Any] = {"source_id": APPROVED_URLS[url], "endpoint": url, "timeout_seconds": timeout_seconds}
        self.calls.append(item)
        try:
            status, headers, body = self.delegate(url, timeout_seconds)
        except urllib.error.HTTPError as exc:
            headers = dict(exc.headers.items()) if exc.headers else {}
            content_type = next((v for k, v in headers.items() if k.lower() == "content-type"), None)
            item.update({"http_status": int(exc.code), "content_type": content_type,
                         "response_byte_count": 0, "response_sha256": None,
                         "retrieved_at": _zulu(_now()), "transport_error": "HTTPError"})
            self.failed = True
            raise
        except Exception as exc:
            item.update({"http_status": None, "content_type": None, "response_byte_count": 0, "response_sha256": None, "transport_error": type(exc).__name__})
            self.failed = True
            raise
        body = body if isinstance(body, bytes) else b""
        self.bodies.append(body)
        content_type = next((v for k, v in headers.items() if k.lower() == "content-type"), None)
        item.update({
            "http_status": status if type(status) is int else None,
            "content_type": content_type,
            "response_byte_count": len(body),
            "response_sha256": hashlib.sha256(body).hexdigest(),
            "retrieved_at": _zulu(_now()),
        })
        try:
            payload = json.loads(body.decode("utf-8-sig"))
            item["json_root_type"] = type(payload).__name__
            item["row_count"] = len(payload) if isinstance(payload, list) else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            item["json_root_type"] = None
            item["row_count"] = None
        if APPROVED_URLS[url] == "I1-TWSE-FMTQIK-OPENAPI":
            try:
                from scripts.twse_trading_calendar import parse_twse_roc_date
                rows = json.loads(body.decode("utf-8-sig"))
                dates = [parse_twse_roc_date(row.get("Date")) for row in rows]
                selected_date = max(dates) if dates else None
                item["candidate_row_count"] = len(rows)
                item["selected_maximum_official_date"] = selected_date.isoformat() if selected_date else None
                item["rows_sharing_selected_maximum_date"] = sum(value == selected_date for value in dates) if selected_date else 0
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
                item.update({"candidate_row_count": None, "selected_maximum_official_date": None,
                             "rows_sharing_selected_maximum_date": None})
        if len(body) > MAX_RESPONSE_BYTES or status != 200 or not isinstance(content_type, str) or content_type.split(";", 1)[0].strip().lower() != "application/json":
            self.failed = True
            raise AcceptanceError("live_transport_contract_violation")
        return status, headers, body

    def raw_body_absent_from(self, root: Path) -> bool:
        files = [path for path in root.rglob("*") if path.is_file()]
        for body in self.bodies:
            if not body:
                continue
            for path in files:
                try:
                    if body in path.read_bytes():
                        return False
                except OSError:
                    return False
        return True


def _candidate_registry_with_transport(budget: BoundedTransport, execution_timestamp: str) -> RuntimeAdapterRegistry:
    from server.services.phase_i_i1_production_candidate import production_batch_operation_adapter_candidate, production_operation_adapter_candidate

    base = build_i1_candidate_runtime_adapter_registry()
    registrations = []
    for market in ("TWSE", "TPEX"):
        registration = base.get_route(EXECUTOR_ID, CAPABILITY_ID, market)
        registrations.append(replace(
            registration,
            adapter=lambda request, context, _adapter=production_operation_adapter_candidate: _adapter(
                request, context, transport=budget, retrieved_at=execution_timestamp
            ),
            batch_adapter=lambda requests, context, _adapter=production_batch_operation_adapter_candidate: _adapter(
                requests, context, transport=budget, retrieved_at=execution_timestamp
            ),
        ))
    registry = RuntimeAdapterRegistry(registrations)
    if {item.market for item in registry.routes_for_executor(EXECUTOR_ID)} != {"TWSE", "TPEX"}:
        raise AcceptanceError("candidate_registry_route_set_invalid")
    return registry


def _assert_dormant_authority() -> dict[str, Any]:
    catalog = _read_json(ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _read_json(ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    registry_json = _read_json(ROOT / "config/m8r_06_03_executor_registry_metadata.json")
    cap = next(item for item in catalog["data_need_capabilities"] if item.get("capability_id") == CAPABILITY_ID)
    route = next(item for item in routing["routes"] if item.get("capability_id") == CAPABILITY_ID)
    if (
        cap.get("support_status"), cap.get("runtime_executable"),
        route.get("runtime_executable"), route.get("routing_status"),
        route.get("selected_executor_id"), route.get("network_required"),
        route.get("batching_scope"),
    ) != ("contract_supported", False, False, "plan_only", None, False, "same_market"):
        raise AcceptanceError("normal_i1_authority_not_dormant")
    if any(item.get("capability_id") == CAPABILITY_ID for item in registry_json.get("executors", [])):
        raise AcceptanceError("normal_i1_registry_not_dormant")
    source_authority = _read_json(ROOT / "docs/data_capabilities/phase_i_i1_source_authority.v1.json")
    if source_authority.get("active_source_count") != 0:
        raise AcceptanceError("phase_i_source_authority_not_dormant")
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    normal_registry = build_production_runtime_adapter_registry()
    if normal_registry.routes_for_executor(EXECUTOR_ID):
        raise AcceptanceError("normal_i1_runtime_registry_not_dormant")
    candidate_registry = build_i1_candidate_runtime_adapter_registry()
    candidate_markets = {item.market for item in candidate_registry.routes_for_executor(EXECUTOR_ID)}
    if candidate_markets != {"TWSE", "TPEX"}:
        raise AcceptanceError("candidate_registry_route_set_invalid")
    if len(build_tool_contract_snapshot().tools) != 6:
        raise AcceptanceError("mcp_surface_changed")
    return {"support_status": "contract_supported", "runtime_executable": False,
            "routing_status": "plan_only", "selected_executor_id": None,
            "network_required": False, "batching_scope": "same_market",
            "active_source_count": 0, "normal_registry_i1_routes": 0,
            "candidate_registry_markets": sorted(candidate_markets), "mcp_tool_count": 6}


def _selected_date(evidence: Mapping[str, Any], key: str) -> str | None:
    component = (evidence.get("components") or {}).get(key) or {}
    return component.get("official_date") or evidence.get("trade_date")


def _verify_result_and_audit(package_root: Path, control_package_id: str, execution: dict[str, Any],
                             overlay_path: Path, overlay_hash: str) -> dict[str, Any]:
    import server.services.unified_mode_b2 as mode_b2
    import server.services.unified_mode_a as mode_a
    import server.services.unified_mode_c as mode_c
    from scripts.m8r_05c.evidence_projector import CURRENT_PROJECTOR_VERSION

    control_root = package_root / "control"
    old_root = mode_b2.CONTROL_ROOT
    mode_b2.CONTROL_ROOT = control_root.resolve()
    old_mode_c_root = mode_c.CONTROL_ROOT
    mode_c.CONTROL_ROOT = control_root.resolve()
    # The acceptance-only Catalog overlay is process-local and is used solely
    # to reproduce the exact F3 authority bound into the candidate plan.
    old_catalog_paths = mode_a.REQUEST_CAPABILITY_CATALOG_PATHS
    mode_a.REQUEST_CAPABILITY_CATALOG_PATHS = dict(old_catalog_paths)
    mode_a.REQUEST_CAPABILITY_CATALOG_PATHS["unified_market_evidence_request.v3"] = overlay_path
    try:
        package_id = control_package_id
        claim_path, claim = _find_control_artifact(control_root / package_id / "claims", "authorization_id", package_id)
        receipt_path, receipt = _find_control_artifact(control_root / package_id / "receipts", "execution_receipt_id", claim["execution_receipt_id"])
        bundle_path, bundle = _find_control_artifact(control_root / package_id / "bundles", "claim_id", claim["claim_id"])
        package = control_root / package_id
        f3_path = package / "mode_c" / "f3_validation.json"
        # Mode C reconstructs F3 using the temporary in-process Catalog override.
        # No ordinary Mode A or production registry authority is changed on disk.
        result_package = mode_c.build_mode_c_result_package({"control_package_id": package_id}, output_schema_version=RESULT_V3)
        audit = mode_c.read_mode_c_audit(package_id, output_schema_version=RESULT_V3)
        result = result_package["canonical_result"]
        result_path = package / result_package["canonical_result_reference"]
        audit_path = package / result_package["audit_reference"]
        result_schema = _read_json(ROOT / "schemas/unified_market_evidence_result.v3.schema.json")
        audit_schema = _read_json(ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json")
        Draft7Validator(result_schema, format_checker=FormatChecker()).validate(result)
        Draft7Validator(audit_schema, format_checker=FormatChecker()).validate(audit)
        inputs = load_projection_inputs(
            request_path=str(package / "control/request.json"),
            f3_validation_path=str(f3_path),
            plan_path=str(package / "control/plan.json"),
            authorization_path=str(package / "control/authorization.json"),
            consumption_binding_path=str(package / "control/consumption_binding.json"),
            claim_path=str(claim_path), receipt_path=str(receipt_path), bundle_path=str(bundle_path),
            artifact_root=str(package), calculated_at=receipt.get("finalized_at"),
            calculated_at_source="receipt.finalized_at",
        )
        lineage = build_lineage_map(inputs)
        citation_index = build_citation_index(lineage, inputs.bundle, RESULT_V3)
        if result_package["canonical_result"] != build_result(inputs, output_schema_version=RESULT_V3):
            raise AcceptanceError("result_v3_replay_mismatch")
        replay_audit = build_audit_package(
            result, inputs, citation_index, result_package["canonical_result_reference"],
            projector_version=CURRENT_PROJECTOR_VERSION, output_schema_version=AUDIT_V3,
        )
        if replay_audit != audit:
            raise AcceptanceError("audit_v3_replay_mismatch")
        expected_targets = {item["canonical_target_id"] for item in execution["selected_targets"]}
        result_targets = {
            item.get("canonical_identity", {}).get("canonical_target_id"): item
            for item in result.get("targets", [])
        }
        if set(result_targets) != expected_targets:
            raise AcceptanceError("result_target_set_mismatch")
        evidence_by_target = {}
        for target_id, target in result_targets.items():
            evidence = (target.get("evidence") or {}).get(CAPABILITY_ID)
            if not isinstance(evidence, dict) or evidence.get("market") != target_id.split(":", 1)[0]:
                raise AcceptanceError("result_market_state_evidence_missing_or_misbound")
            if not evidence.get("citation_ids"):
                raise AcceptanceError("result_citations_missing")
            if any(citation not in citation_index.all_citations for citation in evidence["citation_ids"]):
                raise AcceptanceError("result_citation_unresolved")
            if "causation" in evidence or "target_specific_causation" in evidence:
                raise AcceptanceError("target_specific_causation_claim_present")
            evidence_by_target[target_id] = evidence
        audit_phase_i_refs = (audit.get("phase_i_evidence") or {}).get("evidence_artifact_references") or []
        if len(audit_phase_i_refs) != 4 or any(item.get("capability_id") != CAPABILITY_ID for item in audit_phase_i_refs):
            raise AcceptanceError("audit_phase_i_evidence_references_invalid")
        if audit.get("authorization_identity", {}).get("authorization_id") != control_package_id:
            raise AcceptanceError("audit_authorization_lineage_invalid")
        if claim.get("attempt_count") != 1 or claim.get("state") not in {"consumed_success", "consumed_partial"}:
            raise AcceptanceError("claim_finalization_invalid")
        return {
            "result": result,
            "audit": audit,
            "result_path": result_path,
            "audit_path": audit_path,
            "result_sha256": _sha256(result_path),
            "audit_sha256": _sha256(audit_path),
            "claim": claim,
            "receipt": receipt,
            "receipt_path": receipt_path,
            "bundle": _read_json(bundle_path),
            "bundle_path": bundle_path,
            "evidence_by_target": evidence_by_target,
            "citation_lineage_valid": True,
            "lineage_valid": True,
            "overlay_sha256": overlay_hash,
        }
    except Exception as exc:
        if isinstance(exc, AcceptanceError):
            raise
        raise AcceptanceError("result_or_audit_projection_failed") from exc
    finally:
        mode_a.REQUEST_CAPABILITY_CATALOG_PATHS = old_catalog_paths
        mode_b2.CONTROL_ROOT = old_root
        mode_c.CONTROL_ROOT = old_mode_c_root


def _find_control_artifact(directory: Path, key: str, value: str) -> tuple[Path, dict[str, Any]]:
    found = []
    for path in directory.glob("*.json"):
        obj = _read_json(path)
        if obj.get(key) == value:
            found.append((path, obj))
    if len(found) != 1:
        raise AcceptanceError("control_lineage_artifact_missing_or_ambiguous")
    return found[0]


def run_acceptance(*, transport: Callable[[str, int], tuple[int, Mapping[str, str], bytes]] = _http_transport,
                   security_master_root: Path | None = None, output_root: Path | None = None,
                   execution_timestamp: str | None = None,
                   write_governance_ledger: bool = True) -> dict[str, Any]:
    """Run exactly one explicit bounded attempt; tests inject a deterministic transport."""
    _assert_dormant_authority()
    security_master_root = (security_master_root or ROOT / "data" / "security_master").resolve()
    output_root = (output_root or ROOT / "data" / "phase_i_i1_bounded_live_acceptance").resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    run_id = _now().strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_root = output_root / run_id
    run_root.mkdir(parents=False, exist_ok=False)
    control_root = run_root / "control"
    control_root.mkdir()
    execution_time = execution_timestamp or _zulu(_now())
    budget = BoundedTransport(transport)
    from scripts.m8r_08g_security_master_releases import load_active_identity_service
    from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package
    import server.services.unified_mode_a as mode_a
    import server.services.unified_mode_b2 as mode_b2
    import server.services.unified_mode_c as mode_c

    old_env_root = os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT")
    os.environ["TW_MARKET_SECURITY_MASTER_ROOT"] = str(security_master_root)
    old_control_root = mode_b2.CONTROL_ROOT
    mode_b2.CONTROL_ROOT = control_root.resolve()
    attempt_identity: dict[str, Any] = {"run_id": run_id, "execution_timestamp": execution_time}
    try:
        service, pointer, release, manifest = load_active_identity_service(root=security_master_root)
        identity_runtime = get_production_mode_a_security_master()
        if identity_runtime.validation.get("valid") is not True:
            raise AcceptanceError("security_master_validation_failed", classification="BLOCKED")
        targets = select_targets(identity_runtime)
        request = {
            "schema_version": "unified_market_evidence_request.v3",
            "request_id": "i1-bounded-live-" + uuid.uuid4().hex,
            "targets": [{"input": item["security_code"], "market_hint": item["market"], "resolution_requirement": "exact",
                         "client_target_reference": item["canonical_target_id"]} for item in targets],
            "data_needs": [{"type": CAPABILITY_ID, "priority": "required", "parameters": {}}],
            "execution_mode": "execute",
            "response_preferences": {"include_citations": True, "include_currentness": True, "include_caveats": True, "include_audit_reference": True},
        }
        overlay = copy.deepcopy(_read_json(ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json"))
        cap = next(item for item in overlay["data_need_capabilities"] if item.get("capability_id") == CAPABILITY_ID)
        cap.update({"support_status": "runtime_executable", "runtime_executable": True,
                    "phase_i_activation_state": "bounded_live_acceptance_only"})
        overlay_path = run_root / "acceptance_only_candidate_catalog.json"
        _write_json(overlay_path, overlay)
        overlay_hash = _sha256(overlay_path)
        prior_catalog_path = mode_a.REQUEST_CAPABILITY_CATALOG_PATHS[request["schema_version"]]
        mode_a.REQUEST_CAPABILITY_CATALOG_PATHS = dict(mode_a.REQUEST_CAPABILITY_CATALOG_PATHS)
        mode_a.REQUEST_CAPABILITY_CATALOG_PATHS[request["schema_version"]] = overlay_path
        try:
            from server.services.unified_mode_a import validate_mode_a_request
            f3 = validate_mode_a_request(request)
            if f3.get("validation_status") != "valid" or len(f3.get("target_results", [])) != 4:
                raise AcceptanceError("mode_a_candidate_validation_failed", classification="BLOCKED")
            authorities = candidate_authorities()
            authorities["capability_catalog"] = overlay
            preview_package = build_mode_b1_preview_package(
                request, f3, identity_runtime, planning_timestamp=execution_time, authorities=authorities,
            )
            preview, plan = preview_package.get("preview"), preview_package.get("orchestration_plan")
            if not isinstance(preview, dict) or preview.get("status") != "ready_for_confirmation" or not isinstance(plan, dict):
                raise AcceptanceError("i1_candidate_preview_not_ready", classification="BLOCKED")
            operations = plan.get("operations") or []
            batch_groups = plan.get("batch_groups") or []
            if len(operations) != 4 or len(batch_groups) != 2 or any(op.get("executor_id") != EXECUTOR_ID or op.get("operation_status") != "executable_pending_approval" for op in operations):
                raise AcceptanceError("i1_candidate_plan_bounds_invalid")
            if {item.get("market") for item in batch_groups} != {"TWSE", "TPEX"} or any(len(item.get("operation_ids", [])) != 2 for item in batch_groups):
                raise AcceptanceError("i1_candidate_same_market_batch_invalid")

            issued = _now()
            decision = {
                "decision": "approved", "decision_reason": "Owner-authorized Phase I I1 single bounded live acceptance",
                "owner_identity_reference": "USER_CHAT_OWNER", "owner_review_reference": OWNER_AUTHORITY_REFERENCE,
                "reviewed_at": _zulu(issued), "issued_at": _zulu(issued), "expires_at": _zulu(issued + timedelta(minutes=15)),
                "single_use": True, "replay_policy": "deny_replay", "maximum_use_count": 1,
                "approval_scope_mode": "whole_plan_executable_scope", "approved_operation_ids": [],
                "approved_batch_group_ids": [], "approved_batch_membership": {},
            }
            authorization = build_execution_authorization(plan, decision)
            attempt_identity.update({"authorization_id": authorization["authorization_id"],
                                     "owner_review_reference": authorization.get("owner_review_reference"),
                                     "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"]})
            binding = build_consumption_binding(authorization)
            attempt_identity.update({"consumption_binding_id": binding["consumption_binding_id"]})
            unused_state = {
                "authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
                "consumption_binding_id": binding["consumption_binding_id"], "consumption_binding_hash": binding["consumption_binding_hash"],
                "registry_contract_version": "m8r_05b_03.v1", "state": "unused",
            }
            package_root = control_root / authorization["authorization_id"]
            package_root.mkdir()
            metadata = authorities["executor_metadata"]
            preflight = build_orchestrator_preflight(
                plan, authorization, binding, supplied_consumption_state=unused_state,
                evaluation_timestamp=decision["issued_at"], executor_registry_metadata=metadata,
                output_root=str(package_root),
            )
            validate_preflight_hashes(preflight)
            attempt_identity.update({"preflight_id": preflight["preflight_id"],
                                     "operation_ids": [item["operation_id"] for item in operations],
                                     "execution_request_ids": [item["execution_request_id"] for item in preflight["bounded_execution_requests"]]})
            control_artifacts = {
                "request": request, "plan": plan, "authorization": authorization,
                "consumption_binding": binding, "unused_consumption_state": unused_state,
                "preflight": preflight,
            }
            manifest_info = mode_b2._write_control_package(package_root, control_artifacts)
            candidate_registry = _candidate_registry_with_transport(budget, execution_time)
            execution = execute_controlled_plan(
                plan, authorization, binding, supplied_consumption_state=unused_state,
                accepted_preflight=preflight, evaluation_timestamp=decision["issued_at"],
                claim_created_at=_zulu(_now()), finalized_at=_zulu(_now()),
                executor_registry_metadata=metadata, runtime_adapter_registry=candidate_registry,
                output_root=str(package_root), mode="execute-approved", confirm_execution=True,
                operator_confirmation_reference=OWNER_AUTHORITY_REFERENCE, confirm_network_execution=True,
            )
            package = package_root
            attempt_identity.update({
                "claim_id": (execution.get("claim_record") or {}).get("claim_id"),
                "claim_state": execution.get("consumption_state"),
                "attempt_count": (execution.get("claim_record") or {}).get("attempt_count"),
                "receipt_id": (execution.get("execution_receipt") or {}).get("execution_receipt_id"),
                "bundle_id": (execution.get("evidence_bundle") or {}).get("bundle_id"),
                "operation_statuses": [item.get("status") for item in execution.get("dispatch_outcomes", [])],
            })
            # Verify the current Mode C projection while the candidate Catalog
            # override remains bound in-process; do not change files in docs/.
            evidence_by_market: dict[str, dict[str, Any]] = {}
            for artifact_path in package.glob("evidence/phase_i/i1/*.json"):
                evidence = _read_json(artifact_path)
                market = evidence.get("market")
                if market in evidence_by_market and evidence_by_market[market] != evidence:
                    # Target-bound artifacts should be byte-equivalent market evidence,
                    # except citation IDs are operation-specific.
                    left = dict(evidence_by_market[market]); right = dict(evidence)
                    left.pop("citation_ids", None); right.pop("citation_ids", None)
                    if left != right:
                        raise AcceptanceError("same_market_evidence_reuse_mismatch")
                else:
                    evidence_by_market[market] = evidence
            actual_statuses = {
                market: evidence.get("status") for market, evidence in evidence_by_market.items()
            }
            if execution.get("consumption_state") not in {"consumed_success", "consumed_partial"} or execution.get("aggregation", {}).get("overall_status") not in {"succeeded", "partial_success"}:
                source_blocked = any(
                    item.get("transport_error")
                    or item.get("http_status") in {403, 429}
                    or item.get("http_status") != 200
                    for item in budget.calls
                ) or any(value in {"unavailable", "source_failed", "binding_failed"} for value in actual_statuses.values())
                summary = {
                    "schema_version": "phase_i_i1_bounded_live_acceptance_attempt.v1",
                    "gate_id": "PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE",
                    "owner_authorization_reference": OWNER_AUTHORITY_REFERENCE,
                    "status": "BLOCKED" if source_blocked else "FAIL",
                    "error_code": "bounded_source_execution_not_accepted",
                    **attempt_identity,
                    "network_get_count": len(budget.calls), "network_attempts": budget.calls,
                    "retry_count": 0, "raw_payload_persistence": "NONE" if budget.raw_body_absent_from(run_root) else "DETECTED",
                    "observed_market_statuses": actual_statuses,
                    "evidence_artifact_paths": [path.relative_to(package).as_posix() for path in package.glob("evidence/phase_i/i1/*.json")],
                }
                _write_json(run_root / "acceptance-attempt-summary.json", summary)
                return summary
            if actual_statuses.get("TWSE") not in {"complete", "partial"} or actual_statuses.get("TPEX") != "complete":
                raise AcceptanceError("required_live_source_semantics_not_met", classification="BLOCKED")
            if execution["consumption_state"] not in {"consumed_success", "consumed_partial"} or execution["aggregation"].get("overall_status") not in {"succeeded", "partial_success"}:
                raise AcceptanceError("controlled_execution_not_successful", classification="BLOCKED")
            if len(budget.calls) != 3 or set(budget.by_url.values()) != {1}:
                raise AcceptanceError("live_transport_call_count_invalid")
            raw_absent = budget.raw_body_absent_from(run_root)
            if not raw_absent:
                raise AcceptanceError("raw_source_payload_persisted")
            dormant = _assert_dormant_authority()
            projection = _verify_result_and_audit(run_root, authorization["authorization_id"], {
                "selected_targets": targets,
            }, overlay_path, overlay_hash)
            classification = classify_acceptance(
                transport_blocked=False, network_bounds_proven=len(budget.calls) <= TOTAL_GET_LIMIT and len(budget.by_url) == 3 and all(count == 1 for count in budget.by_url.values()),
                twse_status=actual_statuses.get("TWSE", "source_failed"), tpex_status=actual_statuses.get("TPEX", "source_failed"),
                result_valid=True, audit_valid=True,
                citation_valid=projection["citation_lineage_valid"] and projection["lineage_valid"],
                raw_payload_absent=raw_absent, runtime_dormant=dormant["runtime_executable"] is False and dormant["routing_status"] == "plan_only" and dormant["selected_executor_id"] is None,
            )
            if classification != "PASS":
                raise AcceptanceError("bounded_acceptance_gate_not_passed", classification=classification)
            transport_metadata = []
            evidence_components = {
                "TWSE": evidence_by_market.get("TWSE", {}).get("components", {}),
                "TPEX": evidence_by_market.get("TPEX", {}).get("components", {}),
            }
            for call in budget.calls:
                source_id = call["source_id"]
                source_evidence = evidence_by_market.get("TWSE" if "TWSE" in source_id else "TPEX", {})
                component_key = "fmtqik" if "FMTQIK" in source_id else "breadth" if "BREADTH" in source_id else "tpex_mainborad_highlight"
                component = (source_evidence.get("components") or {}).get(component_key, {})
                transport_metadata.append({
                    **call,
                    "source_family": SOURCE_DESCRIPTORS[source_id]["source_family"],
                    "source_contract_id": SOURCE_DESCRIPTORS[source_id]["source_contract_id"],
                    "selected_official_date": component.get("official_date") or source_evidence.get("trade_date"),
                    "semantic_component_status": component.get("status"),
                })
            result_rel = _report_path(projection["result_path"], run_root)
            audit_rel = _report_path(projection["audit_path"], run_root)
            ledger = {
                "schema_version": "phase_i_i1_bounded_live_acceptance_ledger.v1",
                "gate_id": "PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE",
                "owner_authorization_reference": OWNER_AUTHORITY_REFERENCE,
                "candidate_commit": "0f556ca79134fd8338406ba3299eea83deab3e88",
                "status": "PASS",
                "acceptance_execution_timestamp": execution_time,
                "security_master": {
                    "release_id": pointer.get("release_id"),
                    "release_index_sha256": pointer.get("release_index_sha256"),
                    "release_manifest_sha256": pointer.get("release_manifest_sha256"),
                    "selected_targets": targets,
                },
                "network": {
                    "actual_get_count": len(budget.calls), "maximum_get_count": TOTAL_GET_LIMIT,
                    "retry_count": 0, "timeout_seconds": TIMEOUT_SECONDS,
                    "maximum_response_bytes_per_get": MAX_RESPONSE_BYTES,
                    "raw_payload_persistence": "NONE",
                    "sources": transport_metadata,
                },
                "market_evidence": {
                    "TWSE": {"status": actual_statuses["TWSE"], "trade_date": evidence_by_market["TWSE"].get("trade_date"), "components": evidence_components["TWSE"], "caveats": evidence_by_market["TWSE"].get("caveats", [])},
                    "TPEX": {"status": actual_statuses["TPEX"], "trade_date": evidence_by_market["TPEX"].get("trade_date"), "components": evidence_components["TPEX"], "caveats": evidence_by_market["TPEX"].get("caveats", [])},
                    "same_market_reuse": {"TWSE_targets": 2, "TWSE_source_gets": 2, "TPEX_targets": 2, "TPEX_source_gets": 1},
                },
                "projection": {
                    "result_v3": {"path": result_rel, "sha256": projection["result_sha256"], "schema_valid": True},
                    "audit_v3": {"path": audit_rel, "sha256": projection["audit_sha256"], "schema_valid": True},
                    "citation_lineage_valid": True, "artifact_lineage_valid": True,
                    "claim_id": projection["claim"]["claim_id"], "claim_state": projection["claim"]["state"],
                    "attempt_count": projection["claim"]["attempt_count"],
                    "receipt_id": projection["receipt"]["execution_receipt_id"],
                    "bundle_id": projection["bundle"]["bundle_id"],
                    "candidate_authority_overlay_sha256": overlay_hash,
                    "candidate_authority_overlay": "acceptance-only in-memory projection; canonical Catalog/Routing/registry unchanged",
                },
                "normal_runtime_dormancy": dormant,
                "production_route_active": False,
                "phase_i_active_source_count": 0,
                "i2_started": False, "i3_started": False,
                "mcp_tool_count": 6,
                "controlled_execution": {
                    "authorization_id": authorization["authorization_id"],
                    "authorization_owner_review_reference": authorization.get("owner_review_reference"),
                    "preflight_id": preflight["preflight_id"],
                    "control_package_manifest_sha256": manifest_info["manifest_hash"],
                "operation_ids": [item["operation_id"] for item in operations],
                "execution_request_ids": [item["execution_request_id"] for item in preflight["bounded_execution_requests"]],
                "artifact_inventory": projection["bundle"].get("artifact_inventory", []),
                    "operation_statuses": [item["status"] for item in execution["dispatch_outcomes"]],
                    "aggregation_status": execution["aggregation"]["overall_status"],
                },
            }
            docs_ledger_path = ROOT / "docs/governance/phase_i/PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-09-30.json"
            if write_governance_ledger:
                if docs_ledger_path.exists():
                    raise AcceptanceError("acceptance_ledger_already_exists")
                _write_json(docs_ledger_path, ledger)
            _write_json(run_root / "acceptance-summary.json", ledger)
            return ledger
        finally:
            mode_a.REQUEST_CAPABILITY_CATALOG_PATHS[request["schema_version"]] = prior_catalog_path
    except AcceptanceError as exc:
        summary = {
            "schema_version": "phase_i_i1_bounded_live_acceptance_attempt.v1",
            "gate_id": "PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE",
            "owner_authorization_reference": OWNER_AUTHORITY_REFERENCE,
            "status": exc.classification,
            "error_code": exc.code,
            "network_get_count": len(budget.calls),
            "network_attempts": [{k: v for k, v in item.items() if k != "body"} for item in budget.calls],
            **attempt_identity,
            "retry_count": 0,
            "raw_payload_persistence": "NONE" if budget.raw_body_absent_from(run_root) else "DETECTED",
        }
        _write_json(run_root / "acceptance-attempt-summary.json", summary)
        raise
    except Exception as exc:
        summary = {
            "schema_version": "phase_i_i1_bounded_live_acceptance_attempt.v1",
            "gate_id": "PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE",
            "owner_authorization_reference": OWNER_AUTHORITY_REFERENCE,
            "status": "FAIL",
            "error_code": "unexpected_runner_exception",
            "exception_type": type(exc).__name__,
            "network_get_count": len(budget.calls),
            "network_attempts": [{k: v for k, v in item.items() if k != "body"} for item in budget.calls],
            **attempt_identity,
            "retry_count": 0,
            "raw_payload_persistence": "NONE" if budget.raw_body_absent_from(run_root) else "DETECTED",
        }
        _write_json(run_root / "acceptance-attempt-summary.json", summary)
        raise AcceptanceError("unexpected_runner_exception") from exc
    finally:
        mode_b2.CONTROL_ROOT = old_control_root
        if old_env_root is None:
            os.environ.pop("TW_MARKET_SECURITY_MASTER_ROOT", None)
        else:
            os.environ["TW_MARKET_SECURITY_MASTER_ROOT"] = old_env_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-bounded-live", action="store_true")
    parser.add_argument("--owner-authorization-reference", required=True)
    args = parser.parse_args(argv)
    if not args.confirm_bounded_live:
        raise SystemExit("Phase I I1 acceptance requires --confirm-bounded-live")
    if args.owner_authorization_reference != OWNER_AUTHORITY_REFERENCE:
        raise SystemExit("owner_authorization_reference_mismatch")
    if os.environ.get("PHASE_I_I1_OWNER_AUTHORIZED") != "YES":
        raise SystemExit("explicit_owner_authorization_environment_missing")
    test_seams = sorted(key for key in os.environ if key.startswith("M8R_06_03_TEST_"))
    if test_seams:
        raise SystemExit("test_transport_seam_present:" + ",".join(test_seams))
    result = run_acceptance()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
