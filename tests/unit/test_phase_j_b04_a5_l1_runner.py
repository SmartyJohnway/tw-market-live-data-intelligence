"""Network-denied deterministic tests for the A5 L1 runner control path."""
from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path

import pytest

from scripts.phase_j_b04_a5_bounded_live_acceptance import (
    A5Error, ENDPOINT, STARTING_MAIN, STAGE_WITNESS_POLICY,
    expected_owner_statement, run_live_acceptance,
)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("network is forbidden in L1-P0 tests")
    monkeypatch.setattr(socket, "create_connection", denied)


def row(code: str, *, day="2026-10-06", ex="除息", cash="1"):
    return {"Code": code, "Date": day, "Exdividend": ex, "StockDividendRatio": "0",
        "SubscriptionRatio": "0", "SubscriptionPricePerShare": "尚未公告", "CashDividend": cash}


def auth_file(tmp_path: Path, *, head="a" * 40, tree="b" * 40, environment="cloud_clean_source_acceptance") -> Path:
    statement = expected_owner_statement(head)
    record = {"gate": "J-B04-A5", "authorized_head_sha": head, "authorized_tree_sha": tree,
        "execution_environment_class": environment, "statement": statement,
        "statement_sha256": hashlib.sha256(statement.encode("utf-8")).hexdigest(), "consumed": False}
    path = tmp_path / "owner-auth.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def kwargs_for(tmp_path: Path, response, calls: list):
    return {"owner_authorization_path": auth_file(tmp_path),
        "execution_environment": "cloud_clean_source_acceptance",
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
        "now_fn": iter(["2026-10-09T12:00:00Z", "2026-10-09T12:00:01Z", "2026-10-09T12:00:02Z", "2026-10-09T12:00:03Z"]).__next__}


def response(rows):
    return {"raw_bytes": json.dumps(rows, ensure_ascii=False).encode(), "status": 200,
        "content_type": "application/json", "effective_url": ENDPOINT, "retrieved_at": "2026-10-09T11:00:00Z"}


def load_package(result, tmp_path):
    root = tmp_path / "acceptance_runs" / result["run_directory"]
    return root, {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}


def test_fake_e2e_pass_consumes_once_replays_h2_h4_and_persists_no_raw(tmp_path):
    calls = []
    source = response([row("2330")])
    kwargs = kwargs_for(tmp_path, source, calls)
    owner_record = json.loads(kwargs["owner_authorization_path"].read_text())
    consumed_file = tmp_path / "acceptance_runs" / f"j-b04-a5-authority-{owner_record['statement_sha256'][:16]}" / "owner_authorization_consumed.json"
    def check_consumed_before_fake_transport(**kw):
        assert consumed_file.is_file()
        assert json.loads(consumed_file.read_text())["consumption_state"] == "CONSUMED_BEFORE_TRANSPORT"
        calls.append(kw)
        return source
    kwargs["get_once"] = check_consumed_before_fake_transport
    result = run_live_acceptance(**kwargs)
    assert result["disposition"] == "J_B04_A5_BOUNDED_LIVE_SOURCE_ACCEPTANCE_PASS_AWAITING_INDEPENDENT_REVIEW"
    assert result["logical_get_attempts"] == 1 and len(calls) == 1
    assert result["http_dispatch_attempts"] == 0  # injected fake transport, no HTTP opener dispatch
    root, files = load_package(result, tmp_path)
    assert (root / "owner_authorization_consumed.json").is_file()
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


def test_fake_transport_failure_receipt_and_same_authority_reuse_rejected(tmp_path):
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
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_ALREADY_CONSUMED"):
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
    record["statement"] = record["statement"].replace("retry 0", "retry 1")
    auth_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_INVALID"):
        run_live_acceptance(**kwargs)
    assert calls == [] and not (tmp_path / "acceptance_runs").exists()


def test_head_lease_is_rechecked_after_preflight_before_consumption(tmp_path):
    calls = []
    kwargs = kwargs_for(tmp_path, response([row("2330")]), calls)
    owner_record = json.loads(kwargs["owner_authorization_path"].read_text())
    consumed_path = (tmp_path / "acceptance_runs" /
        f"j-b04-a5-authority-{owner_record['statement_sha256'][:16]}" / "owner_authorization_consumed.json")
    states = iter([("a" * 40, "b" * 40, STARTING_MAIN), ("c" * 40, "b" * 40, STARTING_MAIN)])
    kwargs["git_state_provider"] = lambda: next(states)
    with pytest.raises(A5Error, match="J_B04_A5_LIVE_AUTHORIZATION_STALE_HEAD"):
        run_live_acceptance(**kwargs)
    assert calls == []
    assert not consumed_path.exists()


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
        "--owner-authorization-json", "/tmp/external-owner-auth.json"])
    assert result == expected
    output = capsys.readouterr().out
    assert disposition in output and "raw_bytes" not in output and "rows_in_memory" not in output

