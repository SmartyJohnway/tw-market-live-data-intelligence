"""Acceptance-only J-B04-A5 runner. No implicit or repeatable live access."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STARTING_MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
ENDPOINT = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
TARGET_ID = "TWSE:2330"
EXECUTOR_ID = "phase_h_h2_twse_exright_pre_executor"
SOURCE_ID = "H2-TWSE-EXRIGHT-PRE-OPENAPI"
CONTRACT = "TWT48U_ALL"
MAX_BYTES = 4 * 1024 * 1024
TIMEOUT = 15
PREFLIGHT_JSON = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_BOUNDED_LIVE_PREFLIGHT_2026-10-09.json"


class A5Error(RuntimeError):
    pass


class SingleUseAuthority:
    """A chat authorization must be recorded against the exact current commit."""
    def __init__(self, record: Mapping[str, Any], *, head: str):
        if record.get("gate") != "J-B04-A5" or record.get("authorized_head_sha") != head:
            raise A5Error("live_authorization_missing_or_stale_head")
        statement = record.get("statement", "")
        expected = (
            f"AUTHORIZE J-B04-A5 LIVE ON HEAD {head}:\nexactly 1 GET to\n{ENDPOINT},\n"
            "retry 0,\nno redirects,\ntarget TWSE:2330,\nno H3 live calls,\n"
            "no TWT49U/TPEx/browser fallback,\nno raw payload persistence,\n"
            "no H2 activation,\nno J-B04 closure,\nno Phase J start."
        )
        if statement != expected or record.get("statement_sha256") != hashlib.sha256(statement.encode()).hexdigest():
            raise A5Error("live_authorization_statement_invalid")
        if record.get("consumed") is True:
            raise A5Error("live_authorization_already_consumed")
        self.consumed = False

    def consume(self) -> None:
        if self.consumed:
            raise A5Error("single_use_live_authorization_consumed")
        self.consumed = True


def current_git_state() -> tuple[str, str, str]:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    return git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}"), git("rev-parse", "origin/main")


def resolve_predeclared_target() -> dict[str, Any]:
    """Resolve through the process-lifetime production Mode A identity service."""
    from scripts.m8r_06_01c2_mode_a_security_master_loader import (
        ModeASecurityMasterUnavailable,
        get_production_mode_a_security_master,
    )

    root_selected_by_env = bool(os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT"))
    try:
        runtime = get_production_mode_a_security_master()
    except ModeASecurityMasterUnavailable as exc:
        code = getattr(exc, "reason_code", "")
        disposition = ("J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_NOT_INITIALIZED"
                      if code == "NOT_INITIALIZED"
                      else "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID")
        raise A5Error(disposition) from exc
    except Exception as exc:
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID") from exc

    service = getattr(runtime, "identity_service", None)
    if service is None or not callable(getattr(service, "resolve", None)):
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID")
    try:
        resolution = service.resolve(TARGET_ID, market_hint="TWSE")
    except Exception as exc:
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID") from exc
    selected = getattr(resolution, "selected", None) or {}
    identity = selected.get("identity") or {}
    classification = selected.get("classification") or {}
    eligibility = selected.get("execution_eligibility") or {}
    if (getattr(resolution, "status", None), list(getattr(resolution, "reason_codes", []))) != (
            "resolved", ["exact_listing_id"]):
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_TARGET_IDENTITY_SCOPE_INVALID")
    if (selected.get("canonical_target_id"), identity.get("security_code"), classification.get("market"),
            classification.get("instrument_family"), classification.get("instrument_type"), eligibility.get("status")) != (
            TARGET_ID, "2330", "TWSE", "company_share", "common_share", "allowed"):
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_TARGET_IDENTITY_SCOPE_INVALID")

    pointer = runtime.pointer
    release_id = pointer.get("release_id")
    manifest_hash = pointer.get("release_manifest_sha256")
    index_hash = pointer.get("release_index_sha256")
    if not all(isinstance(value, str) and value for value in (release_id, manifest_hash, index_hash)):
        raise A5Error("J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID")
    return {
        "canonical_target_id": TARGET_ID,
        "market": "TWSE",
        "security_code": "2330",
        "isin": identity.get("isin"),
        "instrument_family": "company_share",
        "instrument_type": "common_share",
        "execution_eligibility": "allowed",
        "resolution_reason": "exact_listing_id",
        "security_master_release_id": release_id,
        "security_master_manifest_hash": manifest_hash,
        "security_master_release_index_sha256": index_hash,
        "canonical_identity_authority": "installation_local_security_master_release",
        "selected_root_class": "environment_selected_installation_local" if root_selected_by_env else "canonical_installation_local_default",
        "environment_root_selected": root_selected_by_env,
    }


def acceptance_h3_fixture(target: Mapping[str, str]) -> dict[str, Any]:
    """A deterministic date-window fixture, explicitly not live H3 evidence."""
    from server.services.phase_h_recent_performance import build_recent_performance_evidence
    schema = json.loads((ROOT / "schemas/recent_performance_evidence.v1.schema.json").read_text(encoding="utf-8"))
    start, end = "2026-10-05", "2026-10-06"
    def row(day: str, close: int) -> dict[str, Any]:
        return {**target, "trade_date": day, "close": close, "volume": 1000,
                "source_family": "TEST_ACCEPTANCE_ONLY_NOT_LIVE_H3",
                "source_contract_id": "J-B04-A5 deterministic window fixture",
                "retrieved_at": "2026-10-09T00:00:00Z", "citation_ids": [f"a5-fixture-{day}"]}
    evidence = build_recent_performance_evidence(target=target, observations=[row(start, 100)],
        governed_end_observation=row(end, 101), requested_observations=1, baseline_lookbacks=[1],
        current_volume_basis="completed_session", schema=schema)
    return evidence


def response_telemetry(response: Mapping[str, Any]) -> dict[str, Any]:
    raw = response.get("raw_bytes")
    if not isinstance(raw, bytes):
        raise A5Error("response_bytes_invalid")
    content_type = str(response.get("content_type", ""))
    if response.get("effective_url") != ENDPOINT:
        raise A5Error("effective_url_mismatch_or_redirect")
    if len(raw) > MAX_BYTES:
        raise A5Error("response_ceiling_exceeded")
    if response.get("status") != 200 or "json" not in content_type.casefold():
        raise A5Error("http_or_content_type_invalid")
    try:
        parsed = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise A5Error("json_invalid") from exc
    if not isinstance(parsed, list):
        raise A5Error("json_root_not_array")
    return {"http_status": 200, "content_type": content_type, "effective_url": ENDPOINT,
        "response_byte_count": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest(),
        "json_root_type": "array", "root_row_count": len(parsed), "rows_in_memory": parsed,
        "retrieved_at": response.get("retrieved_at")}


@contextmanager
def count_actual_dispatches(counter: dict[str, int]):
    """Count the production urllib opener dispatch without editing production code."""
    import urllib.request
    original = urllib.request.OpenerDirector.open
    def counted(opener, *args, **kwargs):
        counter["http_dispatch_attempts"] += 1
        if counter["http_dispatch_attempts"] > 1:
            raise A5Error("http_dispatch_limit_exceeded")
        return original(opener, *args, **kwargs)
    urllib.request.OpenerDirector.open = counted
    try:
        yield
    finally:
        urllib.request.OpenerDirector.open = original


def execute_single_authorized_get(authority: SingleUseAuthority, *, get_once=None) -> tuple[dict[str, Any], dict[str, int], dict[str, Any]]:
    """Invoke production transport once; keep exact response bytes only in memory."""
    from scripts.m8r_05b_03.canonical import canonical_json as _canonical_json  # primes the production import boundary
    del _canonical_json
    from server.services.phase_h_h2_twse_exright_executor import official_get_once
    authority.consume()  # Consumed on entering the one authorized transport attempt.
    counts = {"logical_get_attempts": 0, "http_dispatch_attempts": 0}
    transport = official_get_once if get_once is None else get_once
    counts["logical_get_attempts"] += 1
    if counts["logical_get_attempts"] != 1:
        raise A5Error("logical_get_limit_exceeded")
    with count_actual_dispatches(counts):
        response = transport(timeout_seconds=TIMEOUT)
    return response_telemetry(response), counts, response


def execute_primary_target(response: Mapping[str, Any], target: Mapping[str, str], output_root: Path) -> dict[str, Any]:
    """Replay the captured in-memory response through the unchanged H2 executor."""
    from scripts.m8r_05b_03.canonical import canonical_json
    from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext
    from scripts.m8r_filesystem_safety import atomic_write_bytes
    from server.services.phase_h_h2_twse_exright_executor import execute_h2_twse_exright_pre
    h3 = acceptance_h3_fixture(target)
    h3_path = "evidence/phase_h/h3/a5-acceptance-only-h3-fixture.json"
    h3_bytes = (canonical_json(h3) + "\n").encode("utf-8")
    atomic_write_bytes(str(output_root), h3_path, h3_bytes)
    h3_ref = {"relative_path": h3_path, "sha256": hashlib.sha256(h3_bytes).hexdigest(),
        "byte_size": len(h3_bytes), "schema_version": "recent_performance_evidence.v1",
        "evidence_contract": "recent_performance_evidence.v1", "artifact_role": "primary_evidence"}
    h3_op = {"operation_id": "a5-acceptance-only-h3-fixture", "capability_id": "recent_performance",
        "executor_id": "phase_h_h3_twse_recent_performance_executor", "market": "TWSE",
        "canonical_target_ids": [target["canonical_target_id"]], "dependency_operation_ids": []}
    dependency = {"operation_id": h3_op["operation_id"], "operation": h3_op, "result": {
        "operation_id": h3_op["operation_id"], "status": "succeeded", "capability_id": "recent_performance",
        "executor_id": h3_op["executor_id"], "evidence_contract": "recent_performance_evidence.v1",
        "evidence_artifacts": [h3_ref]}}
    request = {"schema_version": "unified_market_evidence_execution_request.v1",
        "operation_id": "a5-twse-2330-corporate-action", "execution_request_id": "a5-acceptance-only-request",
        "execution_request_hash": hashlib.sha256(b"J-B04-A5 acceptance-only request").hexdigest(),
        "executor_id": EXECUTOR_ID, "capability_id": "corporate_action_context", "market": "TWSE",
        "approved_security_identifiers": [target["canonical_target_id"]], "timeout_seconds": TIMEOUT}
    result = execute_h2_twse_exright_pre(request, DispatchRuntimeContext(str(output_root), "A5 acceptance-only", {"dependencies": [dependency]}),
        fetch_response=lambda **kwargs: dict(response))
    return {"operation_result": result, "h3_fixture_path": h3_path,
        "h3_fixture_label": "TEST / ACCEPTANCE-ONLY; NOT LIVE H3 EVIDENCE; NOT SOURCE COMPLETENESS AUTHORITY"}


def run_p0_preflight() -> dict[str, Any]:
    head, tree, main = current_git_state()
    identity = None
    identity_status = "J_B04_A5_P0_R1_READY_FOR_INDEPENDENT_REVIEW"
    identity_error = None
    try:
        identity = resolve_predeclared_target()
    except A5Error as exc:
        identity_status = str(exc)
        identity_error = str(exc)
    root_selected = bool(os.environ.get("TW_MARKET_SECURITY_MASTER_ROOT"))
    if identity is not None:
        security_master_status = "ACTIVE"
        identity_resolution = {
            "target": TARGET_ID, "authority": "installation-local Taiwan Market Identity Service",
            "result": "resolved", "resolution_status": "resolved", "resolution_reason": "exact_listing_id",
            "reason_code": None, "selected_root_class": identity["selected_root_class"],
            "TW_MARKET_SECURITY_MASTER_ROOT_selected": root_selected,
            "security_master_release_id": identity["security_master_release_id"],
            "security_master_manifest_hash": identity["security_master_manifest_hash"],
            "target_binding": {key: identity[key] for key in ("canonical_target_id", "market", "security_code", "isin",
                "instrument_family", "instrument_type", "execution_eligibility", "resolution_reason")},
        }
    else:
        security_master_status = ("NOT_INITIALIZED" if identity_error ==
            "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_NOT_INITIALIZED" else "INVALID"
            if identity_error == "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID" else "TARGET_SCOPE_INVALID")
        reason_code = "NOT_INITIALIZED" if security_master_status == "NOT_INITIALIZED" else identity_error
        identity_resolution = {
            "target": TARGET_ID, "authority": "installation-local Taiwan Market Identity Service",
            "result": "not_resolved", "reason_code": reason_code,
            "selected_root_class": "environment_selected_installation_local" if root_selected else "canonical_installation_local_default",
            "TW_MARKET_SECURITY_MASTER_ROOT_selected": root_selected,
            "security_master_release_id": None, "security_master_manifest_hash": None,
            "legacy_candidate_fallback": False, "fixture_identity_fallback": False,
            "company_name_fallback": False, "live_security_master_bootstrap_performed": False,
        }
    return {"gate": "J-B04-A5", "preflight_status": identity_status,
        "starting_main": STARTING_MAIN, "observed_origin_main": main,
        "branch_head_sha": head, "tree_sha": tree, "target": TARGET_ID,
        "target_identity": identity, "identity_resolution": identity_resolution,
        "security_master_status": security_master_status, "identity_error_code": identity_error,
        "canonical_identity_authority": "installation_local_security_master_release",
        "legacy_candidate_fallback": False, "fixture_identity_fallback": False,
        "company_name_fallback": False, "live_security_master_bootstrap_performed": False,
        "TW_MARKET_SECURITY_MASTER_ROOT_selected": root_selected,
        "endpoint": ENDPOINT, "method": "GET",
        "logical_get_maximum": 1, "http_dispatch_maximum": 1, "retry": 0,
        "redirect_policy": "reject", "timeout_seconds_maximum": TIMEOUT,
        "response_ceiling_bytes": MAX_BYTES, "H3_live_GETs": 0, "TPEx_GETs": 0,
        "TWT49U_GETs": 0, "browser_fallback": "prohibited",
        "raw_payload_persistence": "NONE", "H2_activation": "NOT_AUTHORIZED",
        "J-B04_closure": "NOT_AUTHORIZED", "Phase_J_start": "NOT_AUTHORIZED",
        "live_authorization": ("NOT PRESENT; not requested because P0 is blocked" if identity is None
                               else "NOT PRESENT; requires independent review before Owner authorization"),
        "network_calls_so_far": {"market_GET": 0, "market_HEAD": 0, "market_POST": 0}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true", help="run network-free A5 authority preflight")
    parser.add_argument("--live-acceptance", action="store_true", help="reserved for a later exact-head Owner authorization")
    parser.add_argument("--owner-authorization-json", type=Path)
    args = parser.parse_args(argv)
    if args.live_acceptance:
        raise SystemExit("A5-L1 is disabled in this P0 runner; exact-head Owner authorization is required after P0 review")
    if not args.preflight:
        parser.error("--preflight is required; no implicit network behavior")
    print(json.dumps(run_p0_preflight(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
