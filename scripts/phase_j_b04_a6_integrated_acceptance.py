#!/usr/bin/env python3
"""J-B04-A6 exact-release preflight and bounded integrated acceptance runner.

The preflight is network-free. Live mode delegates exactly one governed
Local Service/MCP action to the existing production path; it never initializes
Security Master data.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import hashlib
import asyncio
import socket
import subprocess
import time
from datetime import datetime, timezone
import sys
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGET = "TWSE:2330"
STARTING_MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
AUTHORIZED_BASE = "67d1c703b20cd1e9925b7a9e794c96496c644fee"
AUTHORIZED_TREE = "ecde5491e00c004f1316fd163fb6f5212f1c1803"
H2_EXECUTOR = "phase_h_h2_twse_exright_pre_executor"
H3_EXECUTOR = "phase_h_h3_twse_recent_performance_executor"
IMPLEMENTATION_COMMIT_PREFIXES = ("feat(a6):", "fix(a6):", "test(a6):")
EXPECTED_RELEASE_ID = "security-master-20261010T112837Z"
EXPECTED_MANIFEST_SHA256 = "e23d5a60053aec9733764adc49908b3a238d2108cd70ac6e3965d99a1e2a26bc"
EXPECTED_INDEX_SHA256 = "3ac2b751ef96b7b488bbcba9c0e67980fdf13c7f22b33c41fb346fd6a6ceaae7"
EXPECTED_QUALIFICATION_SHA256 = "ecea8b143ecb2bd335ede982a29ce2e576162f8a1d0319c3d15bedd8b3be3238"
EXPECTED_ACTIVE_SHA256 = "25b24e55b188fc2fa08efbe227d98c5890b31f179168665bab8f1f413a55f0fc"
MCP_TOOLS = (
    "market_describe_capabilities",
    "market_validate_request",
    "market_preview_request",
    "market_read_result",
    "market_export_ai_handoff",
    "market_fetch_evidence",
)


def architecture_inventory() -> dict[str, Any]:
    """Describe the current implementation by reference, not by reimplementation."""
    return {
        "integrated_chain": [
            {
                "stage": "canonical_identity",
                "module": "scripts.m8r_06_01c2_mode_a_security_master_loader",
                "entrypoint": "get_production_mode_a_security_master",
                "contract": "ACTIVE, hash-verified qualified installation-local release; resolve exact listing ID TWSE:2330",
                "input": "canonical listing ID and TWSE market hint; no company-name or frozen descriptor fallback",
                "output": "resolved listing identity, durable ISIN, instrument classification, execution eligibility, release_id and manifest hash",
                "failure_semantics": "NOT_INITIALIZED, invalid release, unresolved, ambiguous, or out-of-scope identity blocks before plan execution",
                "network": False,
            },
            {
                "stage": "unified_request_plan_authorization_preflight",
                "module": "server.services.unified_mode_b2",
                "entrypoint": "build_local_operator_execution_ticket",
                "contract": "existing Unified Request -> F3 identity validation -> 05B plan -> explicit authorization/claim/preflight",
                "input": "Unified Market Evidence request for one exact target and recent_performance + corporate_action_context",
                "output": "F3 resolution, ordered operation graph, approval decision, claim authorization, preflight result",
                "failure_semantics": "identity/authorization/preflight errors stop before any executor call",
                "network": False,
            },
            {
                "stage": "H3",
                "module": "scripts.m8r_06_03_production_adapter",
                "entrypoint": "_phase_h_h3_twse_recent_performance",
                "executor": H3_EXECUTOR,
                "contract": "recent_performance_evidence.v1; lookback 1..20; H3 owns actual comparison window; max 3 unique TWSE STOCK_DAY months per operation",
                "input": "approved executable TWSE operation, exact target identity, lookback 1..20 and bounded timeout",
                "output": "normalized daily observations, source citation, actual baseline/comparison window, artifact hash and source-attempt outcome",
                "authorization_boundary": "approved operation and network authorization checked by production adapter/dispatcher",
                "audit_propagation": "operation result, artifact/citation lineage and coverage outcome enter bundle and Audit V3",
                "endpoint": "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=html&date=<YYYYMMDD>&stockNo=2330",
                "network_policy": "GET only; no retry; no redirect; 2 MiB response ceiling per month; verified TLS compatibility mode",
                "limitations": ["TPEx H3 remains blocked", "provider automation permission remains NOT_ESTABLISHED_TERMS_CONFLICTED", "partial/unavailable/source_failed remain distinct"],
            },
            {
                "stage": "H2",
                "module": "server.services.phase_h_h2_twse_exright_executor",
                "entrypoint": "execute_h2_twse_exright_pre",
                "executor": H2_EXECUTOR,
                "contract": "corporate_action_context_evidence.v1; consumes exact same-target H3 artifact/window; TWT48U preannouncement evidence only",
                "input": "approved H2 operation plus exactly one same-target successful H3 dependency artifact and its derived window",
                "output": "typed H2 evidence, exact requested-window binding, source citation, primary artifact and governed source-attempt sidecar",
                "status_semantics": "partial/no-evidence/succeeded remain distinct from typed source_failed or binding_failed; unexpected failures do not fabricate evidence",
                "authorization_boundary": "A6-authorized selected TWSE H2 route still requires existing per-request execution authorization",
                "audit_propagation": "H2 artifact and source governance metadata are projected to Audit V3; exact HTTP dispatch count is not in Audit V3",
                "endpoint": "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL",
                "network_policy": "one official GET per target operation; retry 0; no fallback; partial scope remains explicit",
                "activation": "only phase_h_h2_twse_exright_pre_executor is selected for the bounded TWSE TWT48U pre-announcement scope",
            },
            {
                "stage": "H4",
                "module": "server.services.phase_h_h2_twse_exright_executor",
                "entrypoint": "derive_h4_for_completed_plan -> server.services.phase_h_discontinuity_safety.derive_discontinuity_safety",
                "contract": "target-local exact H2/H3 artifacts; frozen discontinuity-safety derivation; partial coverage may produce coverage_incomplete / ordinary-return blocked",
                "input": "hash-verified exact-target H2 and its dependent H3 primary artifacts/window",
                "output": "one target-scoped H4 safety artifact, input references, state and interpretation guard",
                "status_semantics": "partial coverage remains coverage_incomplete and blocks ordinary-return interpretation",
                "audit_propagation": "H4 derivation inputs, target, state and guard are included in Audit V3",
                "network": False,
            },
            {
                "stage": "Result V3 and Audit V3",
                "module": "scripts.m8r_05c",
                "entrypoints": ["result_builder.build_result", "audit_package_builder.build_audit_package"],
                "contract": "existing Unified Result V3 and Audit V3; citations, target projection, partial/failure semantics, artifact hashes, operation lineage and H4 derivations",
                "input": "validated F3, request, plan, authorization, claim, receipt, bundle, evidence artifacts and citation index",
                "output": "schema-validated Result V3 plus Audit V3 with canonical identity and operation/artifact lineage",
                "network": False,
            },
            {
                "stage": "governed handoff",
                "module": "server.services.unified_mode_c",
                "entrypoints": ["build_mode_c_result_package", "build_mode_c_ai_handoff"],
                "contract": "verified Result/Audit package and guarded AI-ready Markdown handoff",
                "input": "verified stored Result V3 and Audit V3 package",
                "output": "target-specific guarded Markdown and structured package references",
                "status_semantics": "coverage_incomplete/blocked guard must remain visible through export",
                "network": False,
            },
            {
                "stage": "service, Workbench, MCP",
                "module": "server.services.unified_local_operator_action / server.unified_workbench_router / server.unified_mcp",
                "entrypoints": ["fetch_market_evidence", "POST /api/unified/fetch-evidence", "market_fetch_evidence / market_read_result / market_export_ai_handoff"],
                "contract": "same local-service governed execution and read/export boundaries; exactly six static MCP tools",
                "input": "request envelope through Local Service fetch; control package ID for result/audit/handoff read routes",
                "output": "execution outcome plus verified Result/Audit and AI-ready handoff",
                "status_semantics": "service errors are mapped to bounded conflict/validation responses; MCP has no generic executor selector",
                "network": "only the explicitly authorized bounded execution route can reach H3/H2 transport",
            },
        ],
        "execution_order": ["identity", "H3", "H2", "H4", "Result V3", "Audit V3", "handoff"],
        "activation_boundary": {
            "H2_runtime": "ACTIVE_FOR_BOUNDED_TWSE_ROUTE",
            "selected_executor_id": H2_EXECUTOR,
            "current_route": "resolved",
            "future_activation_mechanism": "none; current catalog and routing matrix are the canonical activation authority",
        },
        "handoff_coverage_matrix": [
            {"layer": "contract fixture", "status": "COVERED", "basis": "A3 frozen contracts and A6 target/inventory record"},
            {"layer": "deterministic unit", "status": "COVERED", "basis": "A3 H2/H3/H4 and V3 regression suites; A6 identity-gate tests"},
            {"layer": "integration", "status": "READY_FOR_A6", "basis": "A3 network-free production-chain E2E exists; A6 requires canonical identity and full governed rerun"},
            {"layer": "service API", "status": "READY_FOR_A6", "basis": "existing /api/unified/fetch-evidence and result-package routes"},
            {"layer": "Workbench", "status": "READY_FOR_A6", "basis": "existing Unified Workbench router consumes Local Service path"},
            {"layer": "MCP", "status": "READY_FOR_A6", "basis": "existing six-tool Local Service adapter; no seventh tool"},
            {"layer": "fresh-install", "status": "BLOCKED_WITH_REASON", "basis": "canonical Security Master is NOT_INITIALIZED; A6 must fail before H3/H2"},
            {"layer": "real bounded network", "status": "READY_AFTER_PRETRANSPORT_GATES", "basis": "Owner authorized one bounded A6 session; exact ACTIVE Security Master and selected H2 route are reverified before market transport"},
            {"layer": "real AI / agent", "status": "DEFERRED_TO_LATER_PHASE_J", "basis": "A6 scope is the bounded J-B04 product vertical, not full Phase J scenario closure"},
        ],
        "result_v3": {
            "schema": "schemas/unified_market_evidence_result.v3.schema.json",
            "projector": "scripts/m8r_05c/result_builder.py:build_result",
            "supports": ["canonical target identity", "recent_performance_v3 (H3)", "corporate_action_context (H2)", "discontinuity_safety (H4)", "source observation dates and currentness", "citations and lineage", "partial and failure states", "target coverage", "guarded Markdown via m8r_05c markdown renderer"],
            "authorization_and_bounded_execution_metadata": "authorization identity and bounded operation counts are carried by Audit V3 receipt/authorization identity, not by Result V3 evidence projection",
            "schema_change_required": False,
        },
        "audit_v3": {
            "schema": "schemas/unified_market_evidence_audit_package.v3.schema.json",
            "projector": "scripts/m8r_05c/audit_package_builder.py:build_audit_package",
            "supports": ["F3 identity validation hash", "Security Master artifact hashes/release ID/manifest hash when bound", "plan and authorization identity", "claim/receipt/bundle identity", "operation lineage and outcomes", "artifact/citation references and hashes", "Phase-H source family/contract/role/activation/provider/target/window/coverage/outcome/failure", "H4 derivation inputs/state/guard"],
            "gap": "Audit V3 does not record actual HTTP dispatch counts or an end-to-end network-call counter. Keep the frozen schema unchanged; A6 acceptance must retain a separate sanitized session-level transport ledger bound to the execution receipt/artifact hashes. Audit source_attempts alone cannot reconstruct redirects or actual dispatch count.",
            "schema_change_required": False,
        },
        "future_bounded_live_contract": {
            "designed_not_authorized": False,
            "owner_authorization_sha256": "4e43340f45f2eec12f0eefd38b8b0a2f4cd2f074b8fcc06be2500648d77a3c74",
            "authorized_integrated_attempts": 2,
            "target": TARGET,
            "sources": [
                {"executor": H3_EXECUTOR, "source": "H3-TWSE-DEFAULT-BOUNDED", "endpoint": "https://www.twse.com.tw/exchangeReport/STOCK_DAY", "method": "GET", "max_dispatches_per_integrated_attempt": 3, "retry": 0, "redirect_follow": 0, "response_ceiling_bytes_each": 2097152},
                {"executor": H2_EXECUTOR, "source": "H2-TWSE-EXRIGHT-PRE-OPENAPI", "endpoint": "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL", "method": "GET", "max_dispatches_per_integrated_attempt": 1, "retry": 0, "redirect_follow": 0, "response_ceiling_bytes_each": 4194304},
            ],
            "max_integrated_attempts": 2,
            "max_official_get_dispatches_per_session": 8,
            "contract_hard_ceiling_per_session": 10,
            "per_attempt_dispatch_maximum": 4,
            "stop_on": ["PASS", "hard block"],
            "eligible_continuation": ["transient source failure", "stage witness unavailable"],
            "prohibited": ["H3 TPEX", "TWT49U", "TPEx fallback", "TAIFEX", "browser", "unofficial APIs", "Security Master bootstrap during A6"],
            "note": "One integrated attempt may span up to three distinct H3 monthly requests plus one H2 TWT48U request. Two integrated attempts consume at most eight HTTP dispatches, below the ten-dispatch ceiling. No transport is run in P0.",
        },
        "no_trading_boundary": ["no orders", "no broker credentials", "no position mutation", "no trading action", "no recommendation engine", "no hidden scheduler"],
    }


def _identity_from_runtime(runtime: Any) -> dict[str, Any]:
    service = getattr(runtime, "identity_service", None)
    if service is None:
        return {"result": "invalid", "reason_code": "identity_service_missing"}
    try:
        resolution = service.resolve(TARGET, market_hint="TWSE")
    except Exception as exc:  # sanitized class only; no dataset content
        return {"result": "invalid", "reason_code": "identity_resolution_error", "exception_type": type(exc).__name__}
    reasons = list(getattr(resolution, "reason_codes", []) or [])
    selected = getattr(resolution, "selected", None)
    if getattr(resolution, "status", None) != "resolved" or not isinstance(selected, dict):
        return {"result": "unresolved", "resolution_status": getattr(resolution, "status", "unknown"), "resolution_reasons": reasons}
    classification = selected.get("classification") or {}
    identity = selected.get("identity") or {}
    eligibility = selected.get("execution_eligibility") or {}
    canonical = selected.get("canonical_target_id") or selected.get("listing_id")
    binding = {
        "canonical_target_id": canonical,
        "market": classification.get("market"),
        "security_code": identity.get("security_code"),
        "isin": identity.get("isin"),
        "instrument_family": classification.get("instrument_family"),
        "instrument_type": classification.get("instrument_type"),
        "execution_eligibility": eligibility.get("status"),
    }
    exact = (canonical == TARGET and "exact_listing_id" in reasons and binding["market"] == "TWSE"
             and binding["security_code"] == "2330" and binding["instrument_family"] == "company_share"
             and binding["isin"] == "TW0002330008" and binding["instrument_type"] == "common_share"
             and binding["execution_eligibility"] == "allowed")
    return {
        "result": "resolved" if exact else "scope_invalid",
        "resolution_status": getattr(resolution, "status", None),
        "resolution_reason": "exact_listing_id" if "exact_listing_id" in reasons else (reasons[0] if reasons else None),
        "target_binding": binding,
        "security_master_release_id": getattr(service, "release_id", None),
        "security_master_manifest_hash": getattr(service, "manifest_hash", None),
    }


def _validate_implementation_history(git: Callable[..., str]) -> list[str]:
    """Accept only a linear A6 implementation chain rooted at authorized HEAD."""
    commits = git("rev-list", "--first-parent", "--reverse", f"{AUTHORIZED_BASE}..HEAD").splitlines()
    if not commits:
        raise RuntimeError("A6_PRETRANSPORT_IMPLEMENTATION_COMMIT_MISSING")
    previous = AUTHORIZED_BASE
    for commit in commits:
        parents = git("rev-list", "--parents", "-n", "1", commit).split()
        subject = git("show", "-s", "--format=%s", commit)
        if len(parents) != 2 or parents[0] != commit or parents[1] != previous:
            raise RuntimeError("A6_PRETRANSPORT_IMPLEMENTATION_HISTORY_NOT_LINEAR")
        if not subject.startswith(IMPLEMENTATION_COMMIT_PREFIXES):
            raise RuntimeError("A6_PRETRANSPORT_UNRELATED_COMMIT_AFTER_BASELINE")
        previous = commit
    if previous != git("rev-parse", "HEAD"):
        raise RuntimeError("A6_PRETRANSPORT_IMPLEMENTATION_HEAD_MISMATCH")
    return commits


def run_preflight(loader: Callable[[], Any] | None = None) -> dict[str, Any]:
    """Check actual production identity authority; injectable only for tests."""
    if loader is None:
        from scripts.m8r_06_01c2_mode_a_security_master_loader import (
            ModeASecurityMasterUnavailable,
            get_production_mode_a_security_master,
        )
        loader = get_production_mode_a_security_master
    catalog = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8"))
    routing = json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(encoding="utf-8"))
    capability = next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == "corporate_action_context")
    route = next(item for item in routing["routes"] if item["capability_id"] == "corporate_action_context")
    h2_sources = [item for item in routing["phase_h_source_authority"]["records"] if item["source_id"].startswith("H2-") and item["activation_state"] == "active"]
    h2_active = (capability.get("runtime_executable") is True
                 and capability.get("phase_h_activation_state") == "selected_route_active"
                 and route.get("runtime_executable") is True
                 and route.get("routing_status") == "resolved"
                 and route.get("selected_executor_id") == H2_EXECUTOR
                 and route.get("candidate_executor_ids") == [H2_EXECUTOR]
                 and route.get("supported_markets") == ["TWSE"]
                 and len(h2_sources) == 1
                 and h2_sources[0].get("source_id") == "H2-TWSE-EXRIGHT-PRE-OPENAPI"
                 and h2_sources[0].get("source_contract") == "TWT48U_ALL"
                 and h2_sources[0].get("runtime_executable") is True)
    record: dict[str, Any] = {
        "schema_version": "phase_j_b04_a6_integrated_preflight.v1",
        "gate": "J-B04-A6",
        "starting_main": STARTING_MAIN,
        "target": TARGET,
        "production_identity_required": True,
        "acceptance_only_identity_fallback": False,
        "security_master_bootstrap_performed": False,
        "architecture_inventory_complete": True,
        "architecture": architecture_inventory(),
        "canonical_runtime_state": {
            "H2_runtime": "ACTIVE_FOR_BOUNDED_TWSE_ROUTE" if h2_active else "INVALID",
            "selected_executor_id": route.get("selected_executor_id"),
            "J-B04": "BLOCKING",
            "Phase J": "NOT_STARTED",
            "MCP": 6,
        },
        "network_counts": {"market_GET": 0, "market_HEAD": 0, "market_POST": 0, "Security_Master_live_acquisition": 0},
    }
    try:
        runtime = loader()
    except Exception as exc:
        reason = getattr(exc, "reason_code", None)
        if reason == "NOT_INITIALIZED":
            record.update({
                "disposition": "J_B04_A6_P0_BLOCKED_SECURITY_MASTER_NOT_INITIALIZED",
                "security_master_state": "NOT_INITIALIZED",
                "security_master_status": "NOT_INITIALIZED",
                "security_master_root_selection": "TW_MARKET_SECURITY_MASTER_ROOT" if os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT") else "canonical_installation_local_default",
                "security_master_release_id": None,
                "security_master_release_state": None,
                "security_master_qualification": None,
                "security_master_manifest_hash": None,
                "security_master_index_hash": None,
                "active_selector": "absent",
                "production_loader_result": "NOT_INITIALIZED",
                "production_identity_verified": False,
                "identity_resolution": {"result": "not_attempted", "reason_code": "NOT_INITIALIZED"},
                "execution_attempted": False,
            })
            return record
        record.update({
            "disposition": "J_B04_A6_P0_BLOCKED_SECURITY_MASTER_INVALID",
            "security_master_state": "INVALID",
            "security_master_status": "INVALID",
            "security_master_root_selection": "TW_MARKET_SECURITY_MASTER_ROOT" if os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT") else "canonical_installation_local_default",
            "security_master_private_reason_code": reason if isinstance(reason, str) else type(exc).__name__,
            "production_loader_result": "INVALID",
            "production_identity_verified": False,
            "identity_resolution": {"result": "not_attempted", "reason_code": "SECURITY_MASTER_INVALID"},
            "execution_attempted": False,
        })
        return record
    identity = _identity_from_runtime(runtime)
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    registry = build_production_runtime_adapter_registry()
    h2_regs = registry.routes_for_executor(H2_EXECUTOR)
    h3_regs = registry.routes_for_executor(H3_EXECUTOR)
    registration_ok = (len(h2_regs) == 1 and h2_regs[0].market == "TWSE"
                       and h2_regs[0].capability_id == "corporate_action_context"
                       and h2_regs[0].expected_evidence_contract == "corporate_action_context_evidence.v1"
                       and len(h3_regs) == 1 and h3_regs[0].market == "TWSE")
    root = Path(os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT", ROOT / "data/security_master")).resolve()
    active_path = root / "active.json"
    active_hash = hashlib.sha256(active_path.read_bytes()).hexdigest() if active_path.is_file() else None
    release_ok = (
        getattr(runtime.identity_service, "release_id", None) == EXPECTED_RELEASE_ID
        and getattr(runtime.identity_service, "manifest_hash", None) == EXPECTED_MANIFEST_SHA256
        and (runtime.manifest or {}).get("index_sha256") == EXPECTED_INDEX_SHA256
        and active_hash == EXPECTED_ACTIVE_SHA256
        and (root / "releases" / EXPECTED_RELEASE_ID / "qualification.json").is_file()
        and hashlib.sha256((root / "releases" / EXPECTED_RELEASE_ID / "qualification.json").read_bytes()).hexdigest() == EXPECTED_QUALIFICATION_SHA256
    )
    record.update({
        "security_master_state": "ACTIVE_QUALIFIED",
        "security_master_status": "ACTIVE",
        "security_master_root_selection": "TW_MARKET_SECURITY_MASTER_ROOT" if os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT") else "canonical_installation_local_default",
        "security_master_release_id": getattr(runtime.identity_service, "release_id", None),
        "security_master_release_state": "ACTIVE",
        "security_master_qualification": "QUALIFIED",
        "security_master_manifest_hash": getattr(runtime.identity_service, "manifest_hash", None),
        "security_master_index_hash": (runtime.manifest or {}).get("index_sha256"),
        "active_selector": "active.json",
        "production_loader_result": "ACTIVE_QUALIFIED",
        "production_identity_verified": identity.get("result") == "resolved",
        "identity_resolution": identity,
        "execution_attempted": False,
        "h2_activation_verified": h2_active,
        "executor_registration_verified": registration_ok,
        "active_selector_sha256": active_hash,
        "authorized_release_verified": release_ok,
    })
    if identity.get("result") == "resolved" and release_ok and h2_active and registration_ok:
        record["disposition"] = "J_B04_A6_READY_FOR_BOUNDED_LIVE_ACCEPTANCE"
    elif identity.get("result") == "resolved" and (not release_ok or not h2_active or not registration_ok):
        record["disposition"] = "J_B04_A6_PRETRANSPORT_SECURITY_MASTER_OR_ROUTE_MISMATCH"
    else:
        record["disposition"] = "J_B04_A6_P0_BLOCKED_IDENTITY_RESOLUTION"
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="inspect production authority and identity without network")
    parser.add_argument("--live", action="store_true", help="perform one authorized integrated acceptance attempt")
    args = parser.parse_args(argv)
    if args.preflight == args.live:
        parser.error("select exactly one of --preflight or --live")
    if args.preflight:
        print(json.dumps(run_preflight(), ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    return run_live_session()


def run_live_session() -> int:
    """Run one production Local Service/MCP action under durable A6 dispatch accounting."""
    import httpx
    from server.unified_mcp.local_service_client import UnifiedLocalServiceClient
    from server.unified_mcp.server import dispatch_safe_tool
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot

    session_root = Path(os.environ.get("A6_SESSION_ROOT", "/tmp/j-b04-a6")).resolve()
    session_root.mkdir(parents=True, exist_ok=True)
    auth_path = session_root / "owner-authorization.json"
    session_path = session_root / "session.json"
    if session_path.exists():
        raise RuntimeError("A6_PRETRANSPORT_SESSION_ALREADY_EXISTS")
    authorization = json.loads(auth_path.read_text(encoding="utf-8"))
    auth_hash = hashlib.sha256(authorization["statement"].encode("utf-8")).hexdigest()
    if (auth_hash != "4e43340f45f2eec12f0eefd38b8b0a2f4cd2f074b8fcc06be2500648d77a3c74"
            or authorization.get("authorized_head_sha") != AUTHORIZED_BASE
            or authorization.get("authorized_tree_sha") != AUTHORIZED_TREE
            or authorization.get("authorized_main_sha") != STARTING_MAIN
            or authorization.get("maximum_integrated_attempts") != 2
            or authorization.get("maximum_get_dispatches_per_attempt") != 4
            or authorization.get("maximum_h3_stock_day_gets_per_attempt") != 3
            or authorization.get("maximum_h2_twt48u_all_gets_per_attempt") != 1
            or authorization.get("maximum_official_market_get_dispatches") != 8
            or authorization.get("hard_ceiling_dispatches") != 10
            or authorization.get("automatic_retries") != 0
            or authorization.get("followed_redirects") != 0):
        raise RuntimeError("A6_PRETRANSPORT_AUTHORITY_MISMATCH")
    git = lambda *args: subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    if (git("branch", "--show-current") != "phase-j/j-b04-a5-bounded-live-source-acceptance"
            or git("rev-parse", "origin/main") != STARTING_MAIN
            or git("rev-parse", f"{AUTHORIZED_BASE}^{{tree}}") != AUTHORIZED_TREE
            or git("status", "--porcelain", "--untracked-files=no")):
        raise RuntimeError("A6_PRETRANSPORT_REPOSITORY_AUTHORITY_DRIFT")
    _validate_implementation_history(git)
    preflight = json.loads(subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--preflight"], cwd=ROOT,
        check=True, capture_output=True, text=True,
    ).stdout)
    if preflight.get("disposition") != "J_B04_A6_READY_FOR_BOUNDED_LIVE_ACCEPTANCE":
        raise RuntimeError("A6_PRETRANSPORT_PREFLIGHT_BLOCK")
    if (preflight.get("security_master_release_id") != EXPECTED_RELEASE_ID
            or preflight.get("security_master_manifest_hash") != EXPECTED_MANIFEST_SHA256
            or preflight.get("identity_resolution", {}).get("target_binding", {}).get("canonical_target_id") != TARGET
            or preflight.get("identity_resolution", {}).get("target_binding", {}).get("execution_eligibility") != "allowed"):
        raise RuntimeError("A6_PRETRANSPORT_IDENTITY_BLOCK")

    git = lambda *args: subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    session = {
        "schema_version": "j_b04_a6_live_session.v1", "network_enabled": True,
        "attempt_count": 1, "attempt_started_at": datetime.now(timezone.utc).isoformat(), "actual_dispatches": 0,
        "attempt_dispatches": {}, "attempt_h3": {}, "attempt_h2": {}, "reservations": [],
        "owner_authorization_sha256": auth_hash,
        "active_release_id": EXPECTED_RELEASE_ID,
        "active_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "implementation_head": git("rev-parse", "HEAD"),
        "implementation_tree": git("rev-parse", "HEAD^{tree}"),
        "active_h2_executor": H2_EXECUTOR,
        "active_h3_executor": H3_EXECUTOR,
        "mcp_tool_count": len(build_tool_contract_snapshot().tools),
        "authorized_dispatch_ceiling": 8,
        "preflight_sha256": hashlib.sha256(json.dumps(preflight, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    fd = os.open(session_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(session, stream, sort_keys=True); stream.flush(); os.fsync(stream.fileno())
    ledger = session_root / "transport-ledger.jsonl"
    if ledger.exists():
        raise RuntimeError("A6_PRETRANSPORT_LEDGER_COLLISION")
    ledger.touch(mode=0o600, exist_ok=False)

    with socket.socket() as temp_socket:
        temp_socket.bind(("127.0.0.1", 0))
        port = temp_socket.getsockname()[1]
    environment = os.environ.copy()
    environment.update({"A6_SESSION_ROOT": str(session_root), "A6_ATTEMPT": "1", "H3_LIVE_ACCEPTANCE_TELEMETRY": "YES"})
    server_log = session_root / "live-command.log"
    server_stream = server_log.open("xb")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, env=environment, stdout=server_stream, stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError("A6_LOCAL_SERVICE_START_FAILED")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.05)
        else:
            raise RuntimeError("A6_LOCAL_SERVICE_START_TIMEOUT")

        async def invoke() -> dict[str, Any]:
            client = UnifiedLocalServiceClient(base_url=base_url, timeout_seconds=145)
            tools = build_tool_contract_snapshot()
            request = {
                "schema_version": "unified_market_evidence_request.v3",
                "request_id": "j-b04-a6-twse-2330-live-acceptance",
                "execution_mode": "execute",
                "targets": [{"input": TARGET, "market_hint": "TWSE", "resolution_requirement": "exact"}],
                "data_needs": [
                    {"type": "recent_performance", "priority": "required", "parameters": {"lookback_trading_days": 20}},
                    {"type": "corporate_action_context", "priority": "required", "parameters": {}},
                ],
            }
            result = await dispatch_safe_tool("market_fetch_evidence", {"request": request}, client=client, tool_contract_snapshot=tools)
            if result.isError or not isinstance(result.structuredContent, dict):
                raise RuntimeError("A6_INTEGRATED_FETCH_FAILED")
            # The only market action is over. Persistently close the source gate
            # before any stored-result, Workbench, or MCP read/export operation.
            with session_path.open("r+", encoding="utf-8") as stream:
                live_state = json.load(stream); live_state["network_enabled"] = False
                live_state["attempt_count"] = 1; live_state["network_frozen_at"] = datetime.now(timezone.utc).isoformat()
                stream.seek(0); stream.truncate(); json.dump(live_state, stream, sort_keys=True); stream.flush(); os.fsync(stream.fileno())
            package_id = result.structuredContent.get("control_package_id")
            if not isinstance(package_id, str):
                raise RuntimeError("A6_CONTROL_PACKAGE_MISSING")
            read_result = await dispatch_safe_tool("market_read_result", {"control_package_id": package_id}, client=client, tool_contract_snapshot=tools)
            handoff_result = await dispatch_safe_tool("market_export_ai_handoff", {"control_package_id": package_id}, client=client, tool_contract_snapshot=tools)
            if read_result.isError or handoff_result.isError:
                raise RuntimeError("A6_MCP_STORED_RESULT_SURFACE_FAILED")
            async with httpx.AsyncClient(trust_env=False, follow_redirects=False, timeout=15) as workbench:
                response = await workbench.post(base_url + "/api/unified/result-package", json={"control_package_id": package_id})
                if response.status_code != 200:
                    raise RuntimeError("A6_WORKBENCH_RESULT_READ_FAILED")
                audit = await workbench.get(base_url + f"/api/unified/result-package/{package_id}/audit.json")
                if audit.status_code != 200:
                    raise RuntimeError("A6_WORKBENCH_AUDIT_READ_FAILED")
                wb_handoff = await workbench.get(base_url + f"/api/unified/result-package/{package_id}/handoff")
                if wb_handoff.status_code != 200:
                    raise RuntimeError("A6_WORKBENCH_HANDOFF_READ_FAILED")
            return {"fetch": result.structuredContent, "package": read_result.structuredContent,
                    "handoff": handoff_result.structuredContent,
                    "workbench_package": response.json(), "audit": audit.json(), "workbench_handoff": wb_handoff.json()}

        try:
            outcome = asyncio.run(invoke())
        except Exception as exc:
            outcome = {"terminal_error": type(exc).__name__, "terminal_reason": str(exc)[:160]}
    finally:
        # Freeze the production source gate before any result-only surfaces are revisited.
        with session_path.open("r+", encoding="utf-8") as stream:
            session = json.load(stream); session["network_enabled"] = False
            session["attempt_count"] = 1; session["network_frozen_at"] = datetime.now(timezone.utc).isoformat()
            stream.seek(0); stream.truncate(); json.dump(session, stream, sort_keys=True); stream.flush(); os.fsync(stream.fileno())
        server.terminate()
        try: server.wait(timeout=5)
        except subprocess.TimeoutExpired: server.kill(); server.wait(timeout=5)
        server_stream.close()

    output_path = session_root / "acceptance-result.json"
    with output_path.open("x", encoding="utf-8") as stream:
        json.dump(outcome, stream, ensure_ascii=False, sort_keys=True, indent=2); stream.flush(); os.fsync(stream.fileno())
    session = json.loads(session_path.read_text(encoding="utf-8"))
    session["terminal_output_sha256"] = hashlib.sha256(output_path.read_bytes()).hexdigest()
    session["result_package_id"] = outcome["fetch"].get("control_package_id")
    session["execution_outcome"] = outcome.get("fetch", {}).get("execution_outcome") if isinstance(outcome.get("fetch"), dict) else "FAILED"
    session["terminal_disposition"] = "J_B04_A6_INTEGRATED_LIVE_ACCEPTANCE_HARD_BLOCK" if "terminal_error" in outcome else "REQUIRES_SANITIZED_RESULT_REVIEW"
    session_path.write_text(json.dumps(session, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": session["terminal_disposition"],
                      "attempts": 1, "dispatches": session["actual_dispatches"],
                      "transport_ledger": str(ledger), "result_path": str(output_path),
                      "result_sha256": session["terminal_output_sha256"],
                      "control_package_id": session["result_package_id"],
                      "execution_outcome": session["execution_outcome"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
