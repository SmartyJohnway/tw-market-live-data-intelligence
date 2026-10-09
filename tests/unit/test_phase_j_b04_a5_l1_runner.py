"""Network-denied deterministic tests for the A5 L1 runner control path."""
from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path

import pytest

from scripts.phase_j_b04_a5_bounded_live_acceptance import (
    A5Error, ENDPOINT, STARTING_MAIN, STAGE_WITNESS_POLICY,
    MAX_SESSION_GETS, BoundedSessionAuthority, expected_owner_statement,
    reserve_next_session_attempt, run_live_acceptance,
)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("network is forbidden in L1-P0 tests")
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


def row(code: str, *, day="2026-10-06", ex="除息", cash="1"):
    return {"Code": code, "Date": day, "Exdividend": ex, "StockDividendRatio": "0",
        "SubscriptionRatio": "0", "SubscriptionPricePerShare": "尚未公告", "CashDividend": cash}


TEST_SECRET = bytes(range(32))


def auth_file(tmp_path: Path, *, head="a" * 40, tree="b" * 40, environment="cloud_clean_source_acceptance",
              lease_sha256=None) -> Path:
    lease_sha256 = lease_sha256 or hashlib.sha256(TEST_SECRET).hexdigest()
    statement = expected_owner_statement(head, lease_sha256)
    record = {"gate": "J-B04-A5", "authorized_head_sha": head, "authorized_tree_sha": tree,
        "execution_environment_class": environment, "execution_instance_lease_sha256": lease_sha256,
        "max_market_gets": MAX_SESSION_GETS, "statement": statement,
        "statement_sha256": hashlib.sha256(statement.encode("utf-8")).hexdigest()}
    path = tmp_path / "owner-auth.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def kwargs_for(tmp_path: Path, response, calls: list):
    tmp_path.mkdir(parents=True, exist_ok=True)
    lease_path = tmp_path / "execution-instance.lease"
    lease_path.write_bytes(TEST_SECRET)
    return {"owner_authorization_path": auth_file(tmp_path),
        "execution_environment": "cloud_clean_source_acceptance",
        "execution_lease_file": lease_path,
        "get_once": lambda **kw: calls.append(kw) or response,
        "git_state_provider": lambda: ("a" * 40, "b" * 40, STARTING_MAIN),
        "dirty_check": lambda: False,
        "preflight_fn": lambda env: {"preflight_status": "J_B04_A5_P0_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW",
            "security_master_status": "NOT_INITIALIZED", "identity_assurance_level": "acceptance_only_predeclared_source_target",
            "production_identity_verified": False, "A6_identity_reverification_required": True,
            "H2_runtime": "INACTIVE", "selected_executor_id": None, "J-B04": "BLOCKING",
            "Phase J": "NOT_STARTED", "MCP": 6},
        "runtime_invariant_fn": lambda p: None,
        "acceptance_runs_root": tmp_path / "acceptance_runs",
        "now_fn": lambda: "2026-10-09T12:00:00Z"}


def response(rows):
    return {"raw_bytes": json.dumps(rows, ensure_ascii=False).encode(), "status": 200,
        "content_type": "application/json", "effective_url": ENDPOINT, "retrieved_at": "2026-10-09T11:00:00Z"}


def load_package(result, tmp_path):
    root = tmp_path / "acceptance_runs" / result["session_directory"] / result["run_directory"]
    return root, {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}


def test_fake_e2e_pass_reserves_attempt_replays_h2_h4_and_persists_no_raw(tmp_path):
    calls = []
    source = response([row("2330")])
    kwargs = kwargs_for(tmp_path, source, calls)
    owner_record = json.loads(kwargs["owner_authorization_path"].read_text())
    reserved_file = (tmp_path / "acceptance_runs" / f"j-b04-a5-session-{owner_record['statement_sha256'][:16]}"
        / "attempt-001" / "attempt_reserved.json")
    def check_reserved_before_fake_transport(**kw):
        assert reserved_file.is_file()
        reservation = json.loads(reserved_file.read_text())
        assert reservation["state"] == "RESERVED_BEFORE_TRANSPORT"
        assert reservation["attempt_number"] == 1
        calls.append(kw)
        return source
    kwargs["get_once"] = check_reserved_before_fake_transport
    result = run_live_acceptance(**kwargs)
    assert result["disposition"] == "J_B04_A5_BOUNDED_LIVE_SOURCE_ACCEPTANCE_PASS_AWAITING_INDEPENDENT_REVIEW"
    assert result["logical_get_attempts"] == 1 and len(calls) == 1
    assert result["http_dispatch_attempts"] == 0  # injected fake transport, no HTTP opener dispatch
    root, files = load_package(result, tmp_path)
    session_root = tmp_path / "acceptance_runs" / result["session_directory"]
    receipt = json.loads((session_root / "attempt-001" / "attempt_reserved.json").read_text())
    assert receipt["execution_instance_lease_sha256"] == hashlib.sha256(TEST_SECRET).hexdigest()
    summary = json.loads((root / "acceptance_summary.json").read_text())
    assert summary["raw_body_absence_verified"] is True
    assert summary["identity_assurance_level"] == "acceptance_only_predeclared_source_target"
    assert summary["production_identity_verified"] is False and summary["A6_identity_reverification_required"] is True
    assert summary["canonical_h2_runtime"] == "INACTIVE" and summary["selected_executor_id"] is None
    assert summary["J-B04"] == "BLOCKING" and summary["Phase J"] == "NOT_STARTED" and summary["MCP"] == 6
    attempt = json.loads((root / "transport_attempt.json").read_text())
    assert attempt["logical_get_attempts"] == 1 and attempt["retry_count"] == 0 and attempt["redirect_follow_count"] == 0
    h4 = json.loads((root / "h4_acceptance_replay.json").read_text())
    assert h4["state"] == "coverage_incomplete" and h4["ordinary_return_interpretation"] == "blocked"
    witness = json.loads((root / "stage_witness_summary.json").read_text())
    assert witness["source_evidence_stage"] == "preannouncement" and witness["event_lifecycle"] == "scheduled"
    assert witness["selection_rule"] == STAGE_WITNESS_POLICY
    h3_fixture = json.loads((root / "h3_acceptance_fixture_summary.json").read_text())
    assert h3_fixture["label"] == "TEST / ACCEPTANCE-ONLY; NOT LIVE H3 EVIDENCE; NOT SOURCE COMPLETENESS AUTHORITY"
    assert h3_fixture["requested_window"] == {"start": "2026-10-05", "end": "2026-10-06"}
    assert h3_fixture["live_h3_calls"] == 0 and h3_fixture["historical_source_completeness_authority"] is False
    telemetry = json.loads((root / "source_telemetry.json").read_text())
    assert not ({"raw_bytes", "rows", "rows_in_memory", "raw_payload"} & set(telemetry))
    assert all(source["raw_bytes"] not in p.read_bytes() for p in files.values())
    manifest = json.loads((root / "artifact_manifest.json").read_text())
    for artifact in manifest["artifacts"]:
        payload = (root / artifact["relative_path"]).read_bytes()
        assert len(payload) == artifact["byte_size"]
        assert hashlib.sha256(payload).hexdigest() == artifact["sha256"]
    assert result["raw_body_absence_verified"] is True
    with pytest.raises(A5Error, match="J_B04_A5_SESSION_TERMINAL"):
        run_live_acceptance(**kwargs)
    assert len(calls) == 1
    assert result["session_raw_body_absence_verified"] is True
    assert result["session_terminal"] is True and result["session_terminal_reason"] == "PASS"
    session_summary = json.loads((session_root / "session_summary.json").read_text())
    assert session_summary["max_market_gets"] == 10 and session_summary["attempts_reserved"] == 1
    assert session_summary["attempts_remaining"] == 9 and session_summary["successful_attempt_number"] == 1


def test_fake_zero_rows_is_not_historical_absence_and_stage_is_inconclusive(tmp_path):
    calls = []
    result = run_live_acceptance(**kwargs_for(tmp_path, response([]), calls))
    assert result["disposition"] == "J_B04_A5_INCONCLUSIVE_LIVE_STAGE_SAMPLE_UNAVAILABLE"
    root, _ = load_package(result, tmp_path)
    summary = json.loads((root / "primary_target_summary.json").read_text())
    assert summary["semantic"] == "no_evidence_in_retrieved_current_source_slice"
    assert summary["historical_absence_asserted"] is False
    assert not (root / "stage_witness_summary.json").exists()
    h4 = json.loads((root / "h4_acceptance_replay.json").read_text())
    assert h4["state"] == "coverage_incomplete" and h4["ordinary_return_interpretation"] == "blocked"
    assert len(calls) == 1


def test_primary_row_is_preferred_and_stage_lifecycle_are_preserved(tmp_path):
    calls = []
    result = run_live_acceptance(**kwargs_for(tmp_path, response([row("2330"), row("1101")]), calls))
    root, _ = load_package(result, tmp_path)
    witness = json.loads((root / "stage_witness_summary.json").read_text())
    assert witness["canonical_target_id"] == "TWSE:2330"
    assert witness["source_evidence_stage"] == "preannouncement" and witness["event_lifecycle"] == "scheduled"
    assert witness["product_scope_identity_verified"] is False and witness["source_stage_witness_only"] is True


def test_secondary_stage_witness_selection_is_deterministic_without_identity_claim(tmp_path):
    calls = []
    rows = [row("2330", cash="0"), row("1101", day="2026-10-08"), row("1216")]
    result = run_live_acceptance(**kwargs_for(tmp_path, response(rows), calls))
    root, _ = load_package(result, tmp_path)
    witness = json.loads((root / "stage_witness_summary.json").read_text())
    assert witness["canonical_target_id"] == "TWSE:1101"
    assert witness["selection_rule"] == "prefer normalizable TWSE:2330; otherwise lexicographically smallest (Code, Date, canonical raw-row SHA-256) among normalizable rows"
    assert witness["product_scope_identity_verified"] is False
    assert len(calls) == 1


def test_ambiguous_primary_rows_fail_binding_closed_and_h4_blocks(tmp_path):
    calls = []
    result = run_live_acceptance(**kwargs_for(tmp_path, response([row("2330"), row("2330"), row("1101")]), calls))
    root, _ = load_package(result, tmp_path)
    primary = json.loads((root / "primary_target_summary.json").read_text())
    assert primary["outcome"] == "multiple_exact_code_matches" and primary["h2_evidence_status"] == "binding_failed"
    h4 = json.loads((root / "h4_acceptance_replay.json").read_text())
    assert h4["state"] == "coverage_incomplete" and h4["ordinary_return_interpretation"] == "blocked"
    assert len(calls) == 1


def test_non_string_code_that_production_would_coerce_is_blocked(tmp_path):
    calls = []
    numeric_code = row("2330")
    numeric_code["Code"] = 2330
    result = run_live_acceptance(**kwargs_for(tmp_path, response([numeric_code]), calls))
    assert result["disposition"] == "J_B04_A5_BLOCKED_SOURCE_CONTRACT_OR_IMPLEMENTATION_REVIEW_REQUIRED"
    root, _ = load_package(result, tmp_path)
    summary = json.loads((root / "primary_target_summary.json").read_text())
    assert summary["outcome"] == "noncanonical_exact_code_type"
    assert not (root / "stage_witness_summary.json").exists()


def test_fake_transport_failure_keeps_same_session_eligible_for_next_invocation(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path, None, calls)
    def fail(**kw):
        calls.append(kw)
        raise OSError("private transport detail")
    kwargs["get_once"] = fail
    result = run_live_acceptance(**kwargs)
    assert result["disposition"] == "J_B04_A5_INCONCLUSIVE_TRANSIENT_SOURCE_FAILURE_NO_ACTIVATION"
    root, _ = load_package(result, tmp_path)
    attempt = json.loads((root / "transport_attempt.json").read_text())
    assert attempt["failure_class"] == "transport_failure" and attempt["retry_count"] == 0
    assert "private transport detail" not in (root / "transport_attempt.json").read_text()
    primary = json.loads((root / "primary_target_summary.json").read_text())
    assert primary["outcome"] == "not_observed_transport_failure" and primary["h2_evidence_status"] == "source_failed"
    h4 = json.loads((root / "h4_acceptance_replay.json").read_text())
    assert h4["state"] == "coverage_incomplete" and h4["ordinary_return_interpretation"] == "blocked"
    second = run_live_acceptance(**kwargs)
    assert second["attempt_number"] == 2 and second["session_terminal"] is False
    assert len(calls) == 2


def test_transient_attempt_one_then_pass_attempt_two_terminates_session(tmp_path):
    calls = []
    source = response([row("2330")])
    kwargs = kwargs_for(tmp_path, None, calls)
    def attempt(**kw):
        number = len(calls) + 1
        session = tmp_path / "acceptance_runs" / f"j-b04-a5-session-{json.loads(kwargs['owner_authorization_path'].read_text())['statement_sha256'][:16]}"
        reserved = session / f"attempt-{number:03d}" / "attempt_reserved.json"
        assert reserved.is_file()
        assert json.loads(reserved.read_text())["state"] == "RESERVED_BEFORE_TRANSPORT"
        calls.append(number)
        if number == 1:
            raise OSError("temporary unavailable")
        return source
    kwargs["get_once"] = attempt
    first = run_live_acceptance(**kwargs)
    second = run_live_acceptance(**kwargs)
    assert first["attempt_number"] == 1
    assert first["disposition"] == "J_B04_A5_INCONCLUSIVE_TRANSIENT_SOURCE_FAILURE_NO_ACTIVATION"
    assert second["attempt_number"] == 2
    assert second["disposition"] == "J_B04_A5_BOUNDED_LIVE_SOURCE_ACCEPTANCE_PASS_AWAITING_INDEPENDENT_REVIEW"
    assert second["session_terminal"] and second["session_terminal_reason"] == "PASS"
    with pytest.raises(A5Error, match="J_B04_A5_SESSION_TERMINAL"):
        run_live_acceptance(**kwargs)
    assert calls == [1, 2]


def test_ten_inconclusive_attempts_exhaust_budget_and_attempt_eleven_is_blocked(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path, response([]), calls)
    results = [run_live_acceptance(**kwargs) for _ in range(10)]
    assert [result["attempt_number"] for result in results] == list(range(1, 11))
    assert len(calls) == 10
    assert results[-1]["disposition"] == "J_B04_A5_SESSION_ATTEMPT_BUDGET_EXHAUSTED"
    assert results[-1]["attempts_remaining"] == 0
    assert results[-1]["session_terminal_reason"] == "BUDGET_EXHAUSTED"
    with pytest.raises(A5Error, match="J_B04_A5_SESSION_ATTEMPT_BUDGET_EXHAUSTED"):
        run_live_acceptance(**kwargs)
    assert len(calls) == 10


def test_hard_block_on_attempt_two_terminates_without_attempt_three(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path, None, calls)
    def attempt(**kw):
        calls.append(kw)
        if len(calls) == 1:
            raise OSError("temporary unavailable")
        return {"raw_bytes": b"not-json", "status": 200, "content_type": "application/json",
            "effective_url": ENDPOINT, "retrieved_at": "2026-10-09T11:00:00Z"}
    kwargs["get_once"] = attempt
    assert run_live_acceptance(**kwargs)["attempt_number"] == 1
    second = run_live_acceptance(**kwargs)
    assert second["attempt_number"] == 2
    assert second["disposition"] == "J_B04_A5_BLOCKED_SOURCE_CONTRACT_OR_IMPLEMENTATION_REVIEW_REQUIRED"
    assert second["session_terminal_reason"] == "HARD_BLOCK"
    with pytest.raises(A5Error, match="J_B04_A5_SESSION_TERMINAL"):
        run_live_acceptance(**kwargs)
    assert len(calls) == 2


def test_crash_after_reservation_counts_slot_and_next_invocation_uses_two(tmp_path):
    from scripts.phase_j_b04_a5_bounded_live_acceptance import ensure_session_authorization
    calls = []
    kwargs = kwargs_for(tmp_path, response([row("2330")]), calls)
    record = json.loads(kwargs["owner_authorization_path"].read_text())
    session_root = tmp_path / "acceptance_runs" / f"j-b04-a5-session-{record['statement_sha256'][:16]}"
    ensure_session_authorization(session_root, record)
    first_number, _ = reserve_next_session_attempt(session_root, record)
    assert first_number == 1  # simulated crash happens after this durable reservation
    result = run_live_acceptance(**kwargs)
    assert result["attempt_number"] == 2
    assert len(calls) == 1
    summary = json.loads((session_root / "session_summary.json").read_text())
    assert summary["attempts_reserved"] == 2 and summary["attempts_remaining"] == 8


def test_concurrent_attempt_reservations_allocate_distinct_slots(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from scripts.phase_j_b04_a5_bounded_live_acceptance import ensure_session_authorization
    calls = []
    kwargs = kwargs_for(tmp_path, response([]), calls)
    record = json.loads(kwargs["owner_authorization_path"].read_text())
    session_root = tmp_path / "acceptance_runs" / f"j-b04-a5-session-{record['statement_sha256'][:16]}"
    ensure_session_authorization(session_root, record)
    barrier = threading.Barrier(2)
    def reserve():
        barrier.wait()
        return reserve_next_session_attempt(session_root, record)[0]
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(reserve)
        second = pool.submit(reserve)
        numbers = sorted([first.result(), second.result()])
    assert numbers == [1, 2]
    assert len(list(session_root.glob("attempt-*/attempt_reserved.json"))) == 2


def test_git_change_after_first_attempt_terminalizes_session_before_next_get(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path, None, calls)
    kwargs["get_once"] = lambda **kw: calls.append(kw) or (_ for _ in ()).throw(OSError("temporary"))
    run_live_acceptance(**kwargs)
    kwargs["git_state_provider"] = lambda: ("c" * 40, "b" * 40, STARTING_MAIN)
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_STALE_HEAD"):
        run_live_acceptance(**kwargs)
    session_root = tmp_path / "acceptance_runs" / f"j-b04-a5-session-{json.loads(kwargs['owner_authorization_path'].read_text())['statement_sha256'][:16]}"
    terminal = json.loads((session_root / "session_terminal.json").read_text())
    assert terminal["terminal_reason"] == "HARD_BLOCK"
    assert len(calls) == 1


def test_session_authorization_cannot_be_rebound_to_different_tree(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path, None, calls)
    kwargs["get_once"] = lambda **kw: calls.append(kw) or (_ for _ in ()).throw(OSError("temporary"))
    run_live_acceptance(**kwargs)
    path = kwargs["owner_authorization_path"]
    record = json.loads(path.read_text())
    record["authorized_tree_sha"] = "d" * 40
    path.write_text(json.dumps(record))
    kwargs["git_state_provider"] = lambda: ("a" * 40, "d" * 40, STARTING_MAIN)
    with pytest.raises(A5Error, match="J_B04_A5_SESSION_AUTHORIZATION_MISMATCH"):
        run_live_acceptance(**kwargs)
    assert len(calls) == 1


def test_non_200_http_result_is_typed_failure_and_never_retried(tmp_path):
    calls = []
    failed_response = {"raw_bytes": b"service unavailable", "status": 503,
        "content_type": "text/plain", "effective_url": ENDPOINT, "retrieved_at": "2026-10-09T11:00:00Z"}
    result = run_live_acceptance(**kwargs_for(tmp_path, failed_response, calls))
    assert result["disposition"] == "J_B04_A5_INCONCLUSIVE_TRANSIENT_SOURCE_FAILURE_NO_ACTIVATION"
    root, _ = load_package(result, tmp_path)
    primary = json.loads((root / "primary_target_summary.json").read_text())
    assert primary["h2_evidence_status"] == "source_failed"
    h4 = json.loads((root / "h4_acceptance_replay.json").read_text())
    assert h4["state"] == "coverage_incomplete" and h4["ordinary_return_interpretation"] == "blocked"
    assert len(calls) == 1


def test_redirect_response_is_rejected_without_following(tmp_path):
    calls = []
    redirected = {"raw_bytes": b"", "status": 302, "content_type": "application/json",
        "effective_url": ENDPOINT, "retrieved_at": "2026-10-09T11:00:00Z"}
    result = run_live_acceptance(**kwargs_for(tmp_path, redirected, calls))
    assert result["disposition"] == "J_B04_A5_BLOCKED_SOURCE_CONTRACT_OR_IMPLEMENTATION_REVIEW_REQUIRED"
    root, _ = load_package(result, tmp_path)
    telemetry = json.loads((root / "source_telemetry.json").read_text())
    assert telemetry["redirect_result"] == "rejected_status_3xx"
    assert json.loads((root / "transport_attempt.json").read_text())["redirect_follow_count"] == 0
    assert len(calls) == 1


@pytest.mark.parametrize("state,expected", [
    (("c" * 40, "b" * 40, STARTING_MAIN), "STALE_HEAD"),
    (("a" * 40, "c" * 40, STARTING_MAIN), "STALE_TREE"),
    (("a" * 40, "b" * 40, "d" * 40), "MAIN_DRIFT"),
])
def test_stale_head_tree_or_main_rejected_before_consumption(tmp_path, state, expected):
    calls = []
    kwargs = kwargs_for(tmp_path, response([row("2330")]), calls)
    kwargs["git_state_provider"] = lambda: state
    with pytest.raises(A5Error, match=f"J_B04_A5_LIVE_.*{expected}"):
        run_live_acceptance(**kwargs)
    assert not (tmp_path / "acceptance_runs").exists()
    assert calls == []


def test_authorization_file_inside_repository_is_rejected():
    from scripts.phase_j_b04_a5_bounded_live_acceptance import PREFLIGHT_JSON, _strict_auth_json
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_INVALID"):
        _strict_auth_json(PREFLIGHT_JSON)


def test_non_exact_owner_statement_rejected_before_consumption(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path, response([row("2330")]), calls)
    auth_path = kwargs["owner_authorization_path"]
    record = json.loads(auth_path.read_text())
    record["statement"] = record["statement"].replace("up to 10 GET attempts total", "up to 9 GET attempts total")
    auth_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_INVALID"):
        run_live_acceptance(**kwargs)
    assert calls == [] and not (tmp_path / "acceptance_runs").exists()


def test_lease_preparation_creates_random_external_secret_without_changing_git(monkeypatch, capsys, tmp_path):
    import subprocess
    import scripts.phase_j_b04_a5_bounded_live_acceptance as runner
    before = (subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=runner.ROOT, text=True).strip(),
        subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=runner.ROOT, text=True).strip())
    lease_path = tmp_path / "new-instance.lease"
    code = runner.main(["--prepare-execution-lease", "--execution-environment", "cloud_clean_source_acceptance",
        "--execution-lease-file", str(lease_path)])
    assert code == 0
    output = capsys.readouterr().out
    metadata = json.loads(output)
    secret = lease_path.read_bytes()
    assert len(secret) >= 32 and metadata["execution_instance_lease_sha256"] == hashlib.sha256(secret).hexdigest()
    assert metadata["secret_disclosed"] is False
    assert secret.hex() not in output and __import__("base64").b64encode(secret).decode() not in output
    if hasattr(lease_path.stat(), "st_mode") and __import__("os").name == "posix":
        assert lease_path.stat().st_mode & 0o777 == 0o600
    after = (subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=runner.ROOT, text=True).strip(),
        subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=runner.ROOT, text=True).strip())
    assert before == after


def test_lease_prepare_never_overwrites_existing_secret(tmp_path):
    from scripts.phase_j_b04_a5_bounded_live_acceptance import prepare_execution_lease
    path = tmp_path / "existing.lease"
    path.write_bytes(b"original lease bytes" * 2)
    before = path.read_bytes()
    with pytest.raises(A5Error, match="J_B04_A5_EXECUTION_LEASE_INVALID"):
        prepare_execution_lease(path, "cloud_clean_source_acceptance")
    assert path.read_bytes() == before


def test_lease_paths_inside_repository_and_symlink_into_repository_rejected(tmp_path):
    from scripts.phase_j_b04_a5_bounded_live_acceptance import ROOT, load_execution_lease, prepare_execution_lease
    digest = hashlib.sha256(TEST_SECRET).hexdigest()
    with pytest.raises(A5Error, match="J_B04_A5_EXECUTION_LEASE_INVALID"):
        prepare_execution_lease(ROOT / "config" / "not-a-real-lease", "cloud_clean_source_acceptance")
    external_link = tmp_path / "repo-link.lease"
    external_link.symlink_to(ROOT / "config" / "phase_h_h2_dormant_source_descriptors.json")
    with pytest.raises(A5Error, match="J_B04_A5_EXECUTION_LEASE_INVALID"):
        load_execution_lease(external_link, digest)


def test_missing_wrong_and_truncated_lease_block_before_consumption(tmp_path):
    for case in ("missing", "wrong", "short"):
        calls = []
        kwargs = kwargs_for(tmp_path / case, response([row("2330")]), calls)
        lease = kwargs["execution_lease_file"]
        if case == "missing":
            lease.unlink()
            expected = "J_B04_A5_EXECUTION_LEASE_MISSING"
        elif case == "wrong":
            lease.write_bytes(b"x" * 32)
            expected = "J_B04_A5_EXECUTION_LEASE_HASH_MISMATCH"
        else:
            lease.write_bytes(b"short")
            expected = "J_B04_A5_EXECUTION_LEASE_INVALID"
        with pytest.raises(A5Error, match=expected):
            run_live_acceptance(**kwargs)
        assert calls == []
        consumed = list((tmp_path / case / "acceptance_runs").rglob("owner_authorization_consumed.json"))
        assert consumed == []


def test_cloud_workspace_loss_replay_requires_original_lease(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path / "workspace-a", response([row("2330")]), calls)
    result = run_live_acceptance(**kwargs)
    assert result["logical_get_attempts"] == 1 and len(calls) == 1
    # Workspace B has the same Git lease and external Owner authorization, but no local receipt or secret.
    kwargs["execution_lease_file"].unlink()
    kwargs["acceptance_runs_root"] = tmp_path / "workspace-b" / "acceptance_runs"
    with pytest.raises(A5Error, match="J_B04_A5_EXECUTION_LEASE_MISSING"):
        run_live_acceptance(**kwargs)
    assert len(calls) == 1


def test_cloud_workspace_loss_with_new_unrelated_lease_cannot_replay(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path / "workspace-a", response([row("2330")]), calls)
    run_live_acceptance(**kwargs)
    kwargs["execution_lease_file"].write_bytes(b"y" * 32)
    kwargs["acceptance_runs_root"] = tmp_path / "workspace-b" / "acceptance_runs"
    with pytest.raises(A5Error, match="J_B04_A5_EXECUTION_LEASE_HASH_MISMATCH"):
        run_live_acceptance(**kwargs)
    assert len(calls) == 1


def test_old_lease_free_owner_statement_and_malformed_lease_hash_are_rejected(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path, response([row("2330")]), calls)
    auth_path = kwargs["owner_authorization_path"]
    record = json.loads(auth_path.read_text())
    record["statement"] = record["statement"].replace("\nWITH EXECUTION LEASE " + record["execution_instance_lease_sha256"] + ":", ":")
    record["statement_sha256"] = hashlib.sha256(record["statement"].encode()).hexdigest()
    auth_path.write_text(json.dumps(record))
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_INVALID"):
        run_live_acceptance(**kwargs)
    record = json.loads(auth_file(tmp_path).read_text())
    record.pop("execution_instance_lease_sha256")
    auth_path.write_text(json.dumps(record))
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_INVALID"):
        run_live_acceptance(**kwargs)
    record = json.loads(auth_file(tmp_path).read_text())
    record["execution_instance_lease_sha256"] = "A" * 64
    auth_path.write_text(json.dumps(record))
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_INVALID"):
        run_live_acceptance(**kwargs)
    assert calls == []


def test_head_lease_is_rechecked_after_preflight_before_consumption(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path, response([row("2330")]), calls)
    owner_record = json.loads(kwargs["owner_authorization_path"].read_text())
    reserved_path = (tmp_path / "acceptance_runs" /
        f"j-b04-a5-session-{owner_record['statement_sha256'][:16]}" / "attempt-001" / "attempt_reserved.json")
    states = iter([("a" * 40, "b" * 40, STARTING_MAIN), ("c" * 40, "b" * 40, STARTING_MAIN)])
    kwargs["git_state_provider"] = lambda: next(states)
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_STALE_HEAD"):
        run_live_acceptance(**kwargs)
    assert calls == []
    assert not reserved_path.exists()


def test_invalid_security_master_blocks_before_consumption(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path, response([row("2330")]), calls)
    kwargs["preflight_fn"] = lambda env: {"preflight_status": "J_B04_A5_PREFLIGHT_BLOCKED_CANONICAL_SECURITY_MASTER_INVALID",
        "security_master_status": "INVALID"}
    kwargs.pop("runtime_invariant_fn")
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_PREFLIGHT_INVARIANT_FAILED"):
        run_live_acceptance(**kwargs)
    assert calls == [] and not (tmp_path / "acceptance_runs").exists()


def test_cloud_not_initialized_proceeds_but_preserves_a6_reverification(tmp_path):
    calls = []
    result = run_live_acceptance(**kwargs_for(tmp_path, response([row("2330")]), calls))
    root, _ = load_package(result, tmp_path)
    summary = json.loads((root / "acceptance_summary.json").read_text())
    assert summary["identity_assurance_level"] == "acceptance_only_predeclared_source_target"
    assert summary["production_identity_verified"] is False and summary["A6_identity_reverification_required"] is True


def test_raw_key_persistence_mutation_is_rejected(tmp_path):
    from scripts.phase_j_b04_a5_bounded_live_acceptance import _write_sanitized_json, _verify_sanitized_package
    with pytest.raises(A5Error, match="J_B04_A5_RAW_FIELD_PERSISTENCE_BLOCKED"):
        _write_sanitized_json(tmp_path, "bad.json", {"nested": [{"rows": [row("2330")]}]})


def test_package_body_byte_scan_rejects_raw_capture(tmp_path):
    from scripts.phase_j_b04_a5_bounded_live_acceptance import _verify_sanitized_package
    body = b'[{"Code":"2330","private":"raw"}]'
    (tmp_path / "leak.json").write_bytes(body)
    with pytest.raises(A5Error, match="J_B04_A5_RAW_BODY_PERSISTENCE_DETECTED"):
        _verify_sanitized_package(tmp_path, raw_bytes=body)


def test_l1_validator_contract_rejects_mutated_bounds():
    from copy import deepcopy
    from scripts.validate_phase_j_b04_a5_l1_p0_live_runner import validate_contract
    from scripts.validate_phase_j_b04_a5_l1_p0_live_runner import _strict, RECORD
    baseline = _strict(RECORD)
    assert validate_contract(baseline)["status"] == "PASS"
    mutations = [
        ("real_live_execution", True),
        ("owner_live_authorization", "PRESENT"),
        ("raw_payload_persistence", "PERSISTED"),
        ("stage_witness_selection_policy", "first row wins"),
    ]
    for key, value in mutations:
        changed = deepcopy(baseline)
        changed[key] = value
        with pytest.raises(AssertionError):
            validate_contract(changed)


@pytest.mark.parametrize("disposition,expected", [
    ("J_B04_A5_BOUNDED_LIVE_SOURCE_ACCEPTANCE_PASS_AWAITING_INDEPENDENT_REVIEW", 0),
    ("J_B04_A5_INCONCLUSIVE_LIVE_STAGE_SAMPLE_UNAVAILABLE", 2),
])
def test_live_cli_exit_codes_and_output_are_deterministic(monkeypatch, capsys, disposition, expected):
    import scripts.phase_j_b04_a5_bounded_live_acceptance as runner
    monkeypatch.setattr(runner, "run_live_acceptance", lambda *a, **k: {
        "disposition": disposition, "logical_get_attempts": 1, "http_dispatch_attempts": 0,
        "raw_body_absence_verified": True, "market_GET": 1, "market_HEAD": 0, "market_POST": 0})
    result = runner.main(["--live-acceptance", "--execution-environment", "cloud_clean_source_acceptance",
        "--owner-authorization-json", "/tmp/external-owner-auth.json", "--execution-lease-file",
        "/tmp/external-execution-lease"])
    assert result == expected
    output = capsys.readouterr().out
    assert disposition in output and "raw_bytes" not in output and "rows_in_memory" not in output

