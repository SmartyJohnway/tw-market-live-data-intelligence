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
POINTER = ROOT / "config/m8r_06_mode_a_security_master_pointer.json"


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
    """Resolve the fixed target only through the selected canonical runtime index."""
    try:
        pointer = json.loads(POINTER.read_text(encoding="utf-8"))
        index = ROOT / pointer["index_path"]
        manifest = ROOT / pointer["manifest_path"]
        if not index.is_file() or not manifest.is_file():
            raise A5Error("security_master_identity_unavailable")
        from scripts.m8r_06_01c2_mode_a_security_master_loader import load_active_mode_a_security_master
        runtime = load_active_mode_a_security_master(security_master_root=ROOT / "data/security_master")
        record = runtime.lookup["by_canonical"].get(TARGET_ID)
        if not record:
            raise A5Error("security_master_identity_unavailable")
        cls = record.get("classification", {})
        if (record.get("canonical_target_id"), cls.get("market"), cls.get("instrument_family"), cls.get("instrument_type")) != (
                TARGET_ID, "TWSE", "company_share", "common_share"):
            raise A5Error("security_master_target_scope_invalid")
        ident = record.get("identity", {})
        if ident.get("security_code") != "2330":
            raise A5Error("security_master_target_code_invalid")
        return {"canonical_target_id": TARGET_ID, "market": "TWSE", "security_code": "2330",
                "snapshot_id": runtime.snapshot.get("snapshot_id"), "record_id": record.get("record_id"),
                "record_hash": record.get("record_hash"), "instrument_family": cls["instrument_family"],
                "instrument_type": cls["instrument_type"]}
    except A5Error:
        raise
    except Exception as exc:
        raise A5Error("security_master_identity_unavailable") from exc


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
    identity_status = "resolved"
    try:
        identity = resolve_predeclared_target()
    except A5Error:
        identity_status = "J_B04_A5_PREFLIGHT_BLOCKED_SECURITY_MASTER_IDENTITY_UNAVAILABLE"
    return {"gate": "J-B04-A5", "preflight_status": identity_status,
        "starting_main": STARTING_MAIN, "observed_origin_main": main,
        "branch_head_sha": head, "tree_sha": tree, "target": TARGET_ID,
        "target_identity": identity, "endpoint": ENDPOINT, "method": "GET",
        "logical_get_maximum": 1, "http_dispatch_maximum": 1, "retry": 0,
        "redirect_policy": "reject", "timeout_seconds_maximum": TIMEOUT,
        "response_ceiling_bytes": MAX_BYTES, "H3_live_GETs": 0, "TPEx_GETs": 0,
        "TWT49U_GETs": 0, "browser_fallback": "prohibited",
        "raw_payload_persistence": "NONE", "H2_activation": "NOT_AUTHORIZED",
        "J-B04_closure": "NOT_AUTHORIZED", "Phase_J_start": "NOT_AUTHORIZED",
        "live_authorization": "NOT PRESENT; requires explicit Owner message naming exact current HEAD",
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
