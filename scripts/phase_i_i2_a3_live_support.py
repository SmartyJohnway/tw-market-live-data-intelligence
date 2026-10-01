"""Fresh-authority guards and durable packaging for one I2 A3 acquisition.

This module is acceptance CLI support only, never production dispatch wiring.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OWNER_AUTHORITY = "USER_CHAT_2026-10-01_PHASE_I_I2_A3_SINGLE_GET_LIVE_REARM"
SUPERSEDED_AUTHORITY = "USER_CHAT_2026-10-01_PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE"
REVIEWED_HEAD = "3739988994a25147e70180b471150a1cdebef016"
REVIEWED_TREE = "26b3d70777c10ac18cd87a7c6fe8c7725cf7bce0"
STARTING_MAIN = "846c3f8f4c76862d8c76aeba3acdbf0f3dc44af1"
GOVERNANCE = ROOT / "docs/governance/phase_i"
LEDGER_PATH = GOVERNANCE / "PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-10-01.json"
ATTEMPT_PATH = GOVERNANCE / "PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE_ATTEMPT_2026-10-01.json"
RESERVATION_PATH = GOVERNANCE / "acceptance_runs/i2-a3-single-get-authority-reservation.json"
A1_SHA = "6d535e34defb1e82947f64ceec6df5e1859888fb3550e36e6ded1b6a7573d4fb"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any) -> None:
    from scripts.m8r_filesystem_safety import atomic_write_bytes
    from scripts.m8r_05b_03.canonical import canonical_json
    atomic_write_bytes(path.parent, path.name, canonical_json(value).encode("utf-8"), allow_overwrite=False)


def dormant_authority() -> dict:
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    from scripts.run_phase_i_i2_a3_bounded_live_acceptance import EXECUTOR_ID
    catalog = _json(ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _json(ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    source = _json(ROOT / "docs/data_capabilities/phase_i_i2_source_authority.v1.json")
    i1 = _json(ROOT / "docs/data_capabilities/phase_i_i1_source_authority.v1.json")
    cap = next(x for x in catalog["data_need_capabilities"] if x["capability_id"] == "index_futures_context")
    route = next(x for x in routing["routes"] if x["capability_id"] == "index_futures_context")
    registry_routes = build_production_runtime_adapter_registry().routes_for_executor(EXECUTOR_ID)
    if (cap["support_status"], cap["runtime_executable"], cap["phase_i_activation_state"],
            route["routing_status"], route["runtime_executable"], route["selected_executor_id"],
            source["active_source_count"], source["runtime_executable"], i1["active_source_count"],
            len(registry_routes), len(build_tool_contract_snapshot().tools)) != (
            "contract_supported", False, "implementation_candidate_inactive", "plan_only", False, None,
            0, False, 3, 0, 6):
        raise ValueError("canonical_runtime_dormancy_failed")
    if any(x["activation_state"] != "inactive" or x["runtime_executable"] is not False for x in source["records"]):
        raise ValueError("i2_source_activation_drift")
    if sum(x["activation_state"] == "active" and x["runtime_executable"] is True for x in i1["records"]) != 3:
        raise ValueError("i1_active_sources_drift")
    return {"runtime_executable": False, "routing_status": "plan_only", "selected_executor_id": None,
        "i2_active_sources": 0, "i2_production_routes": 0, "default_production_i2_executor_present": False,
        "i1_active_sources": 3, "mcp_tool_count": 6, "i3_started": False, "phase_j_started": False}


def identity_preflight() -> dict:
    from scripts.m8r_06_01c2_mode_a_security_master_loader import load_active_mode_a_security_master
    runtime = load_active_mode_a_security_master(security_master_root=ROOT / "data/security_master")
    if runtime.validation.get("valid") is not True or runtime.pointer.get("release_id") != "security-master-20260926T151841Z":
        raise ValueError("security_master_release_or_validation_failed")
    if (runtime.pointer.get("release_index_sha256"), runtime.pointer.get("release_manifest_sha256")) != (
            "665d69e53588fa6cd723e434902946a43ac4f712920b0c4ec2adf91b556f4c10",
            "18a10eb8927902d021d5e9023be4c9a6f28be50c9d02fa148e7a56780476a856"):
        raise ValueError("security_master_reviewed_hash_drift")
    from scripts.run_phase_i_i2_a3_bounded_live_acceptance import _target_identity
    targets = []
    for target_id in ("TWSE:1101", "TWSE:1102"):
        record = runtime.lookup["by_canonical"][target_id]
        cls = record["classification"]
        if (cls.get("market"), cls.get("instrument_family"), cls.get("instrument_type"),
                record.get("execution_eligibility", {}).get("status")) != ("TWSE", "company_share", "common_share", "allowed"):
            raise ValueError("security_master_target_scope_failed")
        targets.append(_target_identity(record))
    return {"release_id": runtime.pointer["release_id"],
        "release_index_sha256": runtime.pointer["release_index_sha256"],
        "release_manifest_sha256": runtime.pointer["release_manifest_sha256"], "selected_targets": targets}


def require_rearm(*, authority: str | None, confirmed: bool, environment: str | None) -> None:
    if authority != OWNER_AUTHORITY or not confirmed or environment != "YES":
        raise ValueError("live_execution_not_rearmed")


def check_live_guards(args) -> None:
    require_rearm(authority=args.owner_authorization_reference,
        confirmed=args.confirm_single_taifex_get, environment=os.environ.get("PHASE_I_I2_A3_SINGLE_GET_LIVE_REARM"))
    if args.fake_preflight:
        raise ValueError("live_and_fake_modes_mutually_exclusive")
    if any(key.startswith("M8R_06_03_TEST_") for key in os.environ):
        raise ValueError("unexpected_test_transport_seam_present")
    head, tree = _git("rev-parse", "HEAD"), _git("rev-parse", "HEAD^{tree}")
    if not args.expected_live_runner_head or not args.expected_live_runner_tree or (
            head, tree) != (args.expected_live_runner_head, args.expected_live_runner_tree):
        raise ValueError("live_runner_head_tree_guard_failed")
    if _git("branch", "--show-current") != "phase-i/i2-a3-bounded-live-acceptance":
        raise ValueError("live_runner_branch_guard_failed")
    if _git("rev-parse", "origin/main") != STARTING_MAIN or _git("rev-parse", REVIEWED_HEAD + "^{tree}") != REVIEWED_TREE:
        raise ValueError("reviewed_baseline_drift")
    subprocess.run(["git", "merge-base", "--is-ancestor", REVIEWED_HEAD, head], cwd=ROOT, check=True)
    if _git("diff", "--name-only") or _git("diff", "--cached", "--name-only"):
        raise ValueError("tracked_worktree_drift")
    allowed = {"scripts/run_phase_i_i2_a3_bounded_live_acceptance.py", "scripts/phase_i_i2_a3_live_support.py",
        "scripts/validate_phase_i_i2_a3_live_acceptance.py", "tests/unit/test_phase_i_i2_a3_single_get_rearm.py"}
    if set(_git("diff", "--name-only", REVIEWED_HEAD, head).splitlines()) - allowed:
        raise ValueError("live_wiring_scope_drift")
    check_prior_attempts()
    contract = GOVERNANCE / "PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json"
    if _digest(contract) != A1_SHA:
        raise ValueError("frozen_a1_contract_drift")
    p0 = _json(GOVERNANCE / "PHASE_I_I2_A3_PRE_NETWORK_GOVERNED_RUNNER_CANDIDATE_2026-10-01.json")
    if p0["status"] != "PRE_NETWORK_GOVERNED_RUNNER_READY_FOR_INDEPENDENT_REVIEW" or p0["prior_live_authority_consumed"]:
        raise ValueError("p0_historical_authority_drift")
    dormant_authority()
    identity_preflight()
    # The accepted fake governed execution, including socket denial, must pass
    # before the real delegate can be constructed.
    from scripts.validate_phase_i_i2_a3_p0 import validate
    validate()


def check_prior_attempts() -> None:
    if LEDGER_PATH.exists() or ATTEMPT_PATH.exists() or RESERVATION_PATH.exists():
        raise ValueError("single_get_authority_already_recorded")
    for path in (GOVERNANCE / "acceptance_runs").glob("*/single-get-attempt.json"):
        if _json(path).get("owner_authorization_reference") == OWNER_AUTHORITY:
            raise ValueError("single_get_authority_already_consumed")


class SingleGetDelegate:
    """Counts before I/O and durably latches the attempt; never retries."""
    def __init__(self, delegate, marker_path: Path):
        self.delegate = delegate
        self.marker_path = marker_path
        self.calls = 0
        self.body: bytes | None = None
        self.telemetry: dict[str, Any] = {}

    def __call__(self, url, timeout):
        from server.services.phase_i_i2_index_futures_adapters import SOURCE_ENDPOINT
        if self.calls or url != SOURCE_ENDPOINT or timeout != 30:
            raise ValueError("single_get_scope_or_count_violation")
        _write(self.marker_path, {"owner_authorization_reference": OWNER_AUTHORITY,
            "get_authorization_consumed": True, "attempted_at": _utc(), "endpoint": url,
            "maximum_get_count": 1, "retry_count": 0, "timeout_seconds": timeout})
        self.calls = 1
        try:
            status, headers, body = self.delegate(url, timeout)
        except Exception as exc:
            self.telemetry = {"error_code": "source_failed:transport_exception", "exception_type": type(exc).__name__}
            raise
        self.body = body
        from server.services.phase_i_i2_live_acceptance_candidate import _base_media_type
        self.telemetry = {"http_status": status, "content_type": _base_media_type(headers),
            "response_byte_count": len(body), "response_sha256": hashlib.sha256(body).hexdigest(),
            "transport_observed_at": _utc(), "redirect": "rejected" if 300 <= status < 400 else "none"}
        return status, headers, body


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _source_summary(outcome: dict) -> dict:
    from server.services.phase_i_i2_index_futures_adapters import _parse_source_date
    rows = json.loads(outcome["source_acquisition"].body.decode("utf-8-sig"))
    dates = sorted({date.isoformat() for row in rows if (date := _parse_source_date(row.get("Date"))) is not None})
    status, period, selected_date, _ = outcome["source_selection"]
    eligible = [row["ContractMonth(Week)"] for row in rows
        if _parse_source_date(row.get("Date")) == selected_date and row.get("Contract") == "TX"
        and row.get("TradingSession") == "一般" and isinstance(row.get("ContractMonth(Week)"), str)
        and re.fullmatch(r"[0-9]{6}", row["ContractMonth(Week)"])
        and 1 <= int(row["ContractMonth(Week)"][4:6]) <= 12]
    source = outcome["source_acquisition"]
    return {"http_status": source.http_status, "content_type": source.content_type,
        "response_byte_count": source.response_byte_count, "response_sha256": source.response_sha256,
        "retrieved_at": source.retrieved_at, "json_root_type": "array", "root_row_count": len(rows),
        "unique_valid_official_dates": dates, "selected_maximum_official_date": selected_date.isoformat() if selected_date else None,
        "eligible_tx_regular_monthly_periods": sorted(set(eligible)), "eligible_candidate_count": len(eligible),
        "selected_contract_period": period, "selected_binding_count": eligible.count(period), "selection_status": status}


def execute_single_get_acceptance(*, transport_delegate=None, output_root: Path | None = None,
        write_governance: bool = True, guard_args=None) -> dict:
    """Only called after CLI guards; injected delegates support offline tests."""
    from scripts.run_phase_i_i2_a3_bounded_live_acceptance import _run_governed_acceptance
    from server.services.phase_i_i2_live_acceptance_candidate import _read_once
    if transport_delegate is None:
        if guard_args is None:
            raise ValueError("live_execution_not_rearmed")
        check_live_guards(guard_args)
    check_prior_attempts()
    runtime = dormant_authority()
    security = identity_preflight()
    timestamp = _utc()
    run_root = output_root or GOVERNANCE / "acceptance_runs" / (
        "i2-a3-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    run_root.mkdir(parents=True, exist_ok=False)
    # A durable reservation and attempt latch prevent cross-process reuse of
    # the same Owner authority, including after a crash.
    delegate = SingleGetDelegate(transport_delegate or _read_once, run_root / "single-get-attempt.json")
    snapshot = {"gate_id": "PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE", "owner_authorization_reference": OWNER_AUTHORITY,
        "superseded_authority": SUPERSEDED_AUTHORITY, "superseded_authority_consumed": False,
        "superseded_authority_operational_status": "superseded_without_use", "starting_main": STARTING_MAIN,
        "reviewed_p0_head": REVIEWED_HEAD, "reviewed_p0_tree": REVIEWED_TREE,
        "live_runner_commit": _git("rev-parse", "HEAD"), "live_runner_tree": _git("rev-parse", "HEAD^{tree}"),
        "acceptance_execution_timestamp": timestamp, "security_master": security,
        "normal_runtime_dormancy": runtime, "production_activation": "NOT_AUTHORIZED",
        "merge_authorized": False, "i3_started": False}
    if write_governance:
        RESERVATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        _write(RESERVATION_PATH, {"owner_authorization_reference": OWNER_AUTHORITY,
            "reserved_at": timestamp, "run_root": run_root.relative_to(ROOT).as_posix(),
            "retry_policy": "deny_reuse_even_after_process_failure"})
    _write(run_root / "execution-reference.json", snapshot)
    try:
        outcome = _run_governed_acceptance(output_root=run_root / "governed", fake_transport=delegate,
            owner_authority=OWNER_AUTHORITY, execution_timestamp=timestamp, live=True)
        _write(run_root / "operation-results.json", outcome["execution"]["dispatch_outcomes"])
        _write(run_root / "execution-requests.json", outcome["preflight"]["bounded_execution_requests"])
        evidences = outcome["evidence_objects"]
        if any(x["status"] not in {"complete", "partial"} for x in evidences):
            raise ValueError("live_evidence_not_acceptable:" + ",".join(x["status"] for x in evidences))
        shared = {(x["transport"]["response_sha256"], x["transport"]["response_byte_count"],
            x["transport"]["retrieved_at"], x["trade_date"], x["contract_period"], x["retrieved_at"]) for x in evidences}
        if delegate.calls != 1 or len(shared) != 1 or len(evidences) != 2:
            raise ValueError("live_same_source_reuse_failed")
        execution = outcome["execution"]
        if execution["consumption_state"] != "consumed_success" or execution["claim_record"]["attempt_count"] != 1:
            raise ValueError("live_claim_state_failed")
        if any(x["status"] != "succeeded" or x["error_code"] is not None for x in execution["dispatch_outcomes"]):
            raise ValueError("live_operation_status_failed")
        if dormant_authority() != runtime:
            raise ValueError("post_live_runtime_drift")
        raw_absent = all(delegate.body not in p.read_bytes() for p in run_root.rglob("*") if p.is_file())
        if not raw_absent:
            raise ValueError("raw_payload_persisted")
        record = {"schema_version": "phase_i_i2_a3_bounded_live_acceptance_ledger.v1", "status": "PASS", **snapshot,
            "get_authorization_consumed": True, "network": {"TAIFEX": delegate.calls, "TWSE": 0, "TPEx": 0,
                "maximum_get_count": 1, "retry_count": 0, "timeout_seconds": 30, "redirect_policy": "reject",
                "redirect_outcome": "none", "maximum_response_bytes": 2097152,
                "endpoint": "https://openapi.taifex.com.tw/v1/DailyMarketReportFut"},
            "source_telemetry": _source_summary(outcome),
            "normalized_evidence": [{key: x[key] for key in ("status", "trade_date", "contract_period", "retrieved_at",
                "market_data", "unit_metadata", "alignment_status", "currentness_status", "citation_ids", "caveats")}
                | ({"missing_fields": x["missing_fields"]} if "missing_fields" in x else {}) for x in evidences],
            "same_source_reuse": {"targets": 2, "logical_operations": 2, "batch_groups": 1,
                "source_acquisitions": 1, "per_target_refetch": 0, "shared_transport_and_series": True},
            "governed_execution": {"authorization_id": outcome["authorization"]["authorization_id"],
                "consumption_binding_id": outcome["consumption_binding"]["consumption_binding_id"],
                "preflight_id": outcome["preflight"]["preflight_id"], "claim_id": execution["claim_record"]["claim_id"],
                "claim_state": execution["consumption_state"], "claim_attempt_count": 1,
                "receipt_id": execution["execution_receipt"]["execution_receipt_id"],
                "bundle_id": execution["evidence_bundle"]["bundle_id"],
                "operation_ids": outcome["operation_ids"], "batch_group_ids": outcome["batch_group_ids"],
                "execution_request_ids": [x["execution_request_id"] for x in outcome["preflight"]["bounded_execution_requests"]],
                "operation_statuses": [x["status"] for x in execution["dispatch_outcomes"]],
                "artifact_inventory": execution["evidence_bundle"]["artifact_inventory"],
                "acceptance_only_overlay_sha256": outcome["overlay_sha256"]},
            "projection": {"result_v3": {"path": outcome["result_path"].relative_to(ROOT).as_posix() if output_root is None else outcome["result_path"].relative_to(run_root).as_posix(), "sha256": outcome["result_v3_sha256"], "schema_valid": True},
                "audit_v3": {"path": outcome["audit_path"].relative_to(ROOT).as_posix() if output_root is None else outcome["audit_path"].relative_to(run_root).as_posix(), "sha256": outcome["audit_v3_sha256"], "schema_valid": True},
                "result_replay": "PASS", "audit_replay": "PASS", "citation_lineage": "PASS", "artifact_lineage": "PASS"},
            "raw_payload_persistence": "NONE"}
        _write(run_root / "acceptance-summary.json", record)
        zip_path = run_root / "phase_i_i2_a3_bounded_live_acceptance_evidence.zip"
        with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(run_root.rglob("*")):
                if path.is_file() and path != zip_path:
                    archive.write(path, path.relative_to(run_root).as_posix())
        with zipfile.ZipFile(zip_path) as archive:
            if any(delegate.body in archive.read(name) for name in archive.namelist()):
                raise ValueError("raw_payload_in_zip")
        record["acceptance_package"] = {"path": zip_path.relative_to(ROOT).as_posix() if output_root is None else zip_path.name,
            "sha256": _digest(zip_path), "raw_body_absence_verified": True}
        _write(run_root / "acceptance-package-manifest.json", record)
        if write_governance:
            _write(LEDGER_PATH, record)
        delegate.body = None
        return record
    except Exception as exc:
        raw_absent = delegate.body is None or all(delegate.body not in p.read_bytes() for p in run_root.rglob("*") if p.is_file() and p.suffix != ".zip")
        record = {"schema_version": "phase_i_i2_a3_bounded_live_acceptance_attempt.v1", "status": "FAIL", **snapshot,
            "get_authorization_consumed": delegate.calls == 1, "error_code": str(exc),
            "network": {"TAIFEX": delegate.calls, "TWSE": 0, "TPEx": 0, "retry_count": 0, "timeout_seconds": 30},
            "source_telemetry": delegate.telemetry, "raw_payload_persistence": "NONE" if raw_absent else "DETECTED",
            "preserved_governed_artifacts": sorted(p.relative_to(run_root).as_posix() for p in run_root.rglob("*.json"))}
        _write(run_root / "bounded-attempt-summary.json", record)
        if write_governance:
            _write(ATTEMPT_PATH, record)
        delegate.body = None
        return record
