from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.a6_session_transport import attempt_2_eligible, complete_dispatch, operation_context, reserve_dispatch
from scripts.phase_j_b04_a6_integrated_acceptance import (
    AUTHORIZED_BASE,
    AUTHORIZED_TREE,
    H2_EXECUTOR,
    H3_EXECUTOR,
    OWNER_AUTHORIZATION_SHA256,
    ROOT,
    _validate_fresh_session_repository,
    _validate_implementation_history,
    architecture_inventory,
)
from scripts.validate_phase_j_b04_a6_integrated_acceptance import validate_transport_events


def _session(root: Path, *, count: int = 0) -> None:
    root.mkdir()
    (root / "session.json").write_text(json.dumps({
        "network_enabled": True, "actual_dispatches": count, "attempt_count": 0,
        "attempt_dispatches": {}, "attempt_h3": {}, "attempt_h2": {}, "reservations": [],
    }), encoding="utf-8")


def test_canonical_activation_is_only_bounded_twse_h2_and_h3_route_remains_selected():
    inventory = architecture_inventory()
    assert inventory["activation_boundary"]["H2_runtime"] == "ACTIVE_FOR_BOUNDED_TWSE_ROUTE"
    assert inventory["activation_boundary"]["selected_executor_id"] == H2_EXECUTOR
    import json
    catalog = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text())
    routing = json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text())
    h2 = next(x for x in routing["routes"] if x["capability_id"] == "corporate_action_context")
    assert h2["selected_executor_id"] == H2_EXECUTOR and h2["supported_markets"] == ["TWSE"]
    assert next(x for x in routing["routes"] if x["capability_id"] == "recent_performance")["selected_executor_id"] == H3_EXECUTOR
    active_h2 = [x for x in routing["phase_h_source_authority"]["records"] if x["source_id"].startswith("H2-") and x["activation_state"] == "active"]
    assert [x["source_id"] for x in active_h2] == ["H2-TWSE-EXRIGHT-PRE-OPENAPI"]
    assert all(not x["runtime_executable"] for x in routing["phase_h_source_authority"]["records"] if x["source_id"].startswith("H2-") and x["source_id"] != "H2-TWSE-EXRIGHT-PRE-OPENAPI")
    assert len(__import__("server.unified_mcp.tool_contracts", fromlist=["build_tool_specs"]).build_tool_specs()) == 6


def test_implementation_history_accepts_only_linear_a6_commits_from_authorized_base():
    head = "a6-implementation-3"
    responses = {
        ("rev-list", "--first-parent", "--reverse", f"{AUTHORIZED_BASE}..HEAD"): "a6-implementation-1\na6-implementation-2\na6-implementation-3",
        ("rev-list", "--parents", "-n", "1", "a6-implementation-1"): f"a6-implementation-1 {AUTHORIZED_BASE}",
        ("show", "-s", "--format=%s", "a6-implementation-1"): "feat(a6): activate bounded H2",
        ("rev-list", "--parents", "-n", "1", "a6-implementation-2"): "a6-implementation-2 a6-implementation-1",
        ("show", "-s", "--format=%s", "a6-implementation-2"): "fix(a6): preserve historical checks",
        ("rev-list", "--parents", "-n", "1", "a6-implementation-3"): "a6-implementation-3 a6-implementation-2",
        ("show", "-s", "--format=%s", "a6-implementation-3"): "test(a6): enforce ledger pair validation",
        ("rev-parse", "HEAD"): head,
    }
    assert _validate_implementation_history(lambda *args: responses[args]) == ["a6-implementation-1", "a6-implementation-2", "a6-implementation-3"]

    responses[("show", "-s", "--format=%s", "a6-implementation-2")] = "docs: unrelated change"
    with pytest.raises(RuntimeError, match="UNRELATED_COMMIT"):
        _validate_implementation_history(lambda *args: responses[args])


def test_fresh_session_authority_uses_exact_r2_anchor_and_rejects_drift():
    assert AUTHORIZED_BASE == "8a56fcd3204fa852a7444363485bfc8af264e74c"
    assert AUTHORIZED_TREE == "c3e245b8a31a600e45c3552cd90a778baff6288e"
    assert OWNER_AUTHORIZATION_SHA256 == "a78b43ae8d251c96604820ac0e3f985eb5b92ea23d9020880ea0425cb8369252"
    values = {
        ("branch", "--show-current"): "phase-j/j-b04-a5-bounded-live-source-acceptance",
        ("rev-parse", "origin/main"): "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a",
        ("rev-parse", f"{AUTHORIZED_BASE}^{{tree}}"): AUTHORIZED_TREE,
    }
    _validate_fresh_session_repository(lambda *args: values[args], tracked_status="")
    for key, replacement in (
        (("rev-parse", f"{AUTHORIZED_BASE}^{{tree}}"), "0" * 40),
        (("branch", "--show-current"), "other-branch"),
        (("rev-parse", "origin/main"), "1" * 40),
    ):
        altered = dict(values); altered[key] = replacement
        with pytest.raises(RuntimeError, match="REPOSITORY_AUTHORITY_DRIFT"):
            _validate_fresh_session_repository(lambda *args: altered[args], tracked_status="")
    with pytest.raises(RuntimeError, match="REPOSITORY_AUTHORITY_DRIFT"):
        _validate_fresh_session_repository(lambda *args: values[args], tracked_status=" M tracked.py")


def test_consumed_a6_base_is_not_accepted_as_fresh_r2_implementation_base():
    consumed = "67d1c703b20cd1e9925b7a9e794c96496c644fee"
    assert AUTHORIZED_BASE != consumed
    requested_ranges = []

    def git(*args):
        if args[:3] == ("rev-list", "--first-parent", "--reverse"):
            requested_ranges.append(args[-1])
            return ""
        raise AssertionError(args)

    with pytest.raises(RuntimeError, match="IMPLEMENTATION_COMMIT_MISSING"):
        _validate_implementation_history(git)
    assert requested_ranges == [f"{AUTHORIZED_BASE}..HEAD"]


def _ledger_pair(*, completion_method: bool = True) -> list[dict]:
    reserved = {
        "event": "reserved", "reservation_id": "a6-01-test", "attempt": 1,
        "operation": "H3", "source_id": "H3-TWSE-DEFAULT-BOUNDED", "target": "TWSE:2330",
        "operation_id": "op-1", "dispatch_number": 1, "method": "GET",
        "url": "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=html&date=20261001&stockNo=2330",
        "redirects": 0, "retry_count": 0, "timestamp": "now",
    }
    completed = {
        "event": "completed", "reservation_id": "a6-01-test", "attempt": 1,
        "operation": "H3", "source_id": "H3-TWSE-DEFAULT-BOUNDED", "target": "TWSE:2330",
        "operation_id": "op-1", "dispatch_number": 1, "url": reserved["url"],
        "redirects": 0, "retry_count": 0, "status": 200, "final_url": reserved["url"],
        "content_type": "text/html", "byte_count": 1, "sha256": "0" * 64,
        "error": None, "timestamp": "now",
    }
    if completion_method:
        completed["method"] = "GET"
    return [reserved, completed]


def test_transport_ledger_accepts_new_and_frozen_legacy_completion_shapes():
    assert validate_transport_events(_ledger_pair(), expected_dispatches=1) == {
        "reservations": 1, "completions": 1, "legacy_completions_without_method": 0,
    }
    assert validate_transport_events(_ledger_pair(completion_method=False), expected_dispatches=1) == {
        "reservations": 1, "completions": 1, "legacy_completions_without_method": 1,
    }


@pytest.mark.parametrize("mutate, message", [
    (lambda e: e[1].update(method="POST"), "method_pair_mismatch"),
    (lambda e: e[1].update(operation="H2"), "operation_or_target_mismatch"),
    (lambda e: e[1].update(source_id="H2-TWSE-EXRIGHT-PRE-OPENAPI"), "pair_mismatch:source_id"),
    (lambda e: e[1].update(target="TWSE:2317"), "operation_or_target_mismatch"),
    (lambda e: e[1].update(url="https://example.test/"), "pair_mismatch:url"),
    (lambda e: e[1].update(dispatch_number=2), "pair_mismatch:dispatch_number"),
    (lambda e: e[1].update(operation_id="other"), "pair_mismatch:operation_id"),
    (lambda e: e[1].update(retry_count=1), "retry_or_redirect_forbidden"),
    (lambda e: e[0].update(retries=1), "retry_or_redirect_forbidden"),
    (lambda e: e[1].update(redirects=1), "retry_or_redirect_forbidden"),
    (lambda e: e.append(deepcopy(e[1])), "duplicate"),
    (lambda e: e.pop(), "pair_mismatch"),
    (lambda e: e.append(deepcopy(e[0])), "duplicate"),
])
def test_transport_ledger_rejects_pair_mismatches_and_unpaired_events(mutate, message):
    events = _ledger_pair()
    mutate(events)
    with pytest.raises(AssertionError, match=message):
        validate_transport_events(events)


def test_a6_dispatch_reserves_before_transport_and_caps_each_operation(tmp_path: Path, monkeypatch):
    root = tmp_path / "a6"
    _session(root)
    monkeypatch.setenv("A6_SESSION_ROOT", str(root))
    url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=html&date=20261001&stockNo=2330"
    for month in range(3):
        with operation_context(1, "H3", f"h3-{month}"):
            reservation = reserve_dispatch(method="GET", url=url.replace("20261001", f"20260{month + 1:02d}01"))
        assert reservation["dispatch_number"] == month + 1
        assert reservation["method"] == "GET"
        complete_dispatch(reservation, status=200, final_url=reservation["url"], content_type="text/html", body=b"bounded")
    with operation_context(1, "H3", "h3-fourth"):
        with pytest.raises(RuntimeError, match="budget_exhausted"):
            reserve_dispatch(method="GET", url=url)
    state = json.loads((root / "session.json").read_text())
    assert state["actual_dispatches"] == 3
    entries = [json.loads(line) for line in (root / "transport-ledger.jsonl").read_text().splitlines()]
    assert [item["event"] for item in entries].count("reserved") == 3
    assert all(item["method"] == "GET" for item in entries)
    assert all(item.get("retry_count", 0) == 0 and item.get("redirects", 0) == 0 for item in entries)


def test_a6_rejects_wrong_target_host_method_and_attempt_before_dispatch(tmp_path: Path, monkeypatch):
    root = tmp_path / "a6"
    _session(root)
    monkeypatch.setenv("A6_SESSION_ROOT", str(root))
    with operation_context(1, "H2", "h2-op"):
        for method, url in (
            ("POST", "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"),
            ("GET", "https://example.test/v1/exchangeReport/TWT48U_ALL"),
            ("GET", "http://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"),
        ):
            with pytest.raises(RuntimeError, match="contract_rejected"):
                reserve_dispatch(method=method, url=url)
    with operation_context(3, "H2", "h2-op"):
        with pytest.raises(RuntimeError, match="budget_exhausted"):
            reserve_dispatch(method="GET", url="https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL")
    assert json.loads((root / "session.json").read_text())["actual_dispatches"] == 0
    assert not (root / "transport-ledger.jsonl").exists()


def test_a6_session_ceiling_is_eight_and_h2_is_one_per_attempt(tmp_path: Path, monkeypatch):
    root = tmp_path / "a6"
    _session(root)
    monkeypatch.setenv("A6_SESSION_ROOT", str(root))
    for attempt in (1, 2):
        for month in range(3):
            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=html&date=20260{month + 1}01&stockNo=2330"
            with operation_context(attempt, "H3", f"h3-{attempt}-{month}"):
                reservation = reserve_dispatch(method="GET", url=url)
            complete_dispatch(reservation, status=200, final_url=url, content_type="text/html", body=b"x")
        h2_url = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
        with operation_context(attempt, "H2", f"h2-{attempt}"):
            reservation = reserve_dispatch(method="GET", url=h2_url)
        complete_dispatch(reservation, status=200, final_url=h2_url, content_type="application/json", body=b"[]")
        with operation_context(attempt, "H2", f"h2-repeat-{attempt}"):
            with pytest.raises(RuntimeError, match="budget_exhausted"):
                reserve_dispatch(method="GET", url=h2_url)
    with operation_context(1, "H2", "extra"):
        with pytest.raises(RuntimeError, match="budget_exhausted"):
            reserve_dispatch(method="GET", url="https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL")
    state = json.loads((root / "session.json").read_text())
    assert state["actual_dispatches"] == 8
    assert state["attempt_h3"] == {"1": 3, "2": 3}
    assert state["attempt_h2"] == {"1": 1, "2": 1}


def test_attempt_two_only_continues_eligible_nonterminal_failures():
    assert attempt_2_eligible(outcome="transient_source_failure", stage_witness_available=False)
    assert attempt_2_eligible(outcome="stage_witness_unavailable", stage_witness_available=False)
    for terminal in ("pass", "hard_block", "valid_no_evidence", "unsafe_interpretation_block"):
        assert not attempt_2_eligible(outcome=terminal, stage_witness_available=False)
    assert not attempt_2_eligible(outcome="transient_source_failure", stage_witness_available=True)
