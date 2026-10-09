#!/usr/bin/env python3
"""Network-free J-B04-A6 integrated acceptance preflight.

This command inventories the existing production path and verifies the
installation-local Security Master identity prerequisite. It never executes a
market adapter or initializes Security Master data.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGET = "TWSE:2330"
STARTING_MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
H2_EXECUTOR = "phase_h_h2_twse_exright_pre_executor"
H3_EXECUTOR = "phase_h_h3_twse_recent_performance_executor"
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
                "authorization_boundary": "canonical route is currently plan_only; H2 requires separately reviewed activation and existing execution authorization",
                "audit_propagation": "H2 artifact and source governance metadata are projected to Audit V3; exact HTTP dispatch count is not in Audit V3",
                "endpoint": "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL",
                "network_policy": "one official GET per target operation; retry 0; no fallback; partial scope remains explicit",
                "activation": "candidate is registered, canonical H2 route is plan_only with selected_executor_id=null; A6-P0 does not activate it",
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
            "H2_runtime": "INACTIVE",
            "selected_executor_id": None,
            "current_route": "plan_only",
            "future_activation_mechanism": "separately reviewed canonical capability-catalog activation plus routing-matrix selection of the already registered H2 candidate and any governed Phase-H activation authority; not performed by A6-P0",
        },
        "handoff_coverage_matrix": [
            {"layer": "contract fixture", "status": "COVERED", "basis": "A3 frozen contracts and A6 target/inventory record"},
            {"layer": "deterministic unit", "status": "COVERED", "basis": "A3 H2/H3/H4 and V3 regression suites; A6 identity-gate tests"},
            {"layer": "integration", "status": "READY_FOR_A6", "basis": "A3 network-free production-chain E2E exists; A6 requires canonical identity and full governed rerun"},
            {"layer": "service API", "status": "READY_FOR_A6", "basis": "existing /api/unified/fetch-evidence and result-package routes"},
            {"layer": "Workbench", "status": "READY_FOR_A6", "basis": "existing Unified Workbench router consumes Local Service path"},
            {"layer": "MCP", "status": "READY_FOR_A6", "basis": "existing six-tool Local Service adapter; no seventh tool"},
            {"layer": "fresh-install", "status": "BLOCKED_WITH_REASON", "basis": "canonical Security Master is NOT_INITIALIZED; A6 must fail before H3/H2"},
            {"layer": "real bounded network", "status": "BLOCKED_WITH_REASON", "basis": "identity not initialized and no A6 live authorization; P0 makes zero calls"},
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
            "designed_not_authorized": True,
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
             and binding["instrument_type"] == "common_share" and binding["execution_eligibility"] == "allowed")
    return {
        "result": "resolved" if exact else "scope_invalid",
        "resolution_status": getattr(resolution, "status", None),
        "resolution_reason": "exact_listing_id" if "exact_listing_id" in reasons else (reasons[0] if reasons else None),
        "target_binding": binding,
        "security_master_release_id": getattr(service, "release_id", None),
        "security_master_manifest_hash": getattr(service, "manifest_hash", None),
    }


def run_preflight(loader: Callable[[], Any] | None = None) -> dict[str, Any]:
    """Check actual production identity authority; injectable only for tests."""
    if loader is None:
        from scripts.m8r_06_01c2_mode_a_security_master_loader import (
            ModeASecurityMasterUnavailable,
            get_production_mode_a_security_master,
        )
        loader = get_production_mode_a_security_master
    record: dict[str, Any] = {
        "schema_version": "phase_j_j_b04_a6_p0_preflight.v1",
        "gate": "J-B04-A6-P0",
        "starting_main": STARTING_MAIN,
        "target": TARGET,
        "production_identity_required": True,
        "acceptance_only_identity_fallback": False,
        "security_master_bootstrap_performed": False,
        "architecture_inventory_complete": True,
        "architecture": architecture_inventory(),
        "canonical_runtime_state": {
            "H2_runtime": "INACTIVE",
            "selected_executor_id": None,
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
    })
    if identity.get("result") == "resolved":
        record["disposition"] = "J_B04_A6_P0_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW"
    else:
        record["disposition"] = "J_B04_A6_P0_BLOCKED_IDENTITY_RESOLUTION"
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="inspect production identity and print the network-free A6-P0 record")
    args = parser.parse_args(argv)
    if not args.preflight:
        parser.error("only --preflight is available in A6-P0")
    print(json.dumps(run_preflight(), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
