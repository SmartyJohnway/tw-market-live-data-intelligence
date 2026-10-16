from __future__ import annotations

import json
import ast
from pathlib import Path
import socket
from urllib.error import URLError

import pytest

from scripts.phase_l_a6_live_dispatch_guard import (
    AUTHORITY_ID,
    PHYSICAL_CEILING,
    A6DispatchController,
    DispatchBlocked,
    build_plan,
    contract_matrix,
    A6BootstrapBudgetAdapter,
    invoke_reserved_transport,
    plan_json,
    pre1_live_entrypoint,
    transport_observation,
)


HEAD = "a" * 40
TREE = "b" * 40


def _controller(tmp_path: Path, *, valid_reservation: bool = True) -> A6DispatchController:
    tmp_path.mkdir(parents=True, exist_ok=True)
    reservation = tmp_path / "authority_reservation.json"
    consumed = tmp_path / "authority_consumed.json"
    if valid_reservation:
        reservation.write_text(json.dumps({
            "authority_id": AUTHORITY_ID,
            "state": "RESERVED_NOT_CONSUMED",
            "pre_network_head": HEAD,
            "pre_network_tree": TREE,
        }), encoding="utf-8")
    return A6DispatchController(
        build_plan(), reservation_path=reservation, consumed_path=consumed,
        expected_head=HEAD, expected_tree=TREE, actual_head=HEAD, actual_tree=TREE,
        live_enabled=True,
    )


def _dispatch(controller: A6DispatchController, item, *, purpose="PRIMARY", delegate=None):
    _response, record = invoke_reserved_transport(
        controller,
        logical_sequence=item.logical_sequence,
        source_contract_id=item.source_contract_id,
        hostname=(item.hostname if purpose == "PRIMARY" else __import__("urllib.parse").parse.urlsplit(item.alternate_route).hostname),
        method=item.method,
        route_identity=item.route if purpose == "PRIMARY" else item.alternate_route,
        purpose=purpose,
        transport=(delegate or (lambda _record: None)),
    )
    return record


def test_plan_has_exact_23_logical_entries_and_27_maximum():
    plan = build_plan()
    assert len(plan) == 23
    assert [item.source_contract_id for item in plan] == [f"P{i:02d}" for i in range(1, 19)] + [f"B{i:02d}" for i in range(1, 6)]
    assert sum(item.maximum_physical_dispatches for item in plan) == 27
    assert sum(item.maximum_physical_dispatches - 1 for item in plan) == 4
    assert sum(item.maximum_physical_dispatches for item in plan) - 4 == 23
    assert [x.source_contract_id for x in plan if x.maximum_physical_dispatches == 2] == ["P04", "P05", "P06", "P07"]
    assert len(plan_json()) == len(contract_matrix()) == 23
    assert all(row["timeout_enforcement_expression"] and "inherited" not in row["timeout_enforcement_expression"] for row in contract_matrix())


def test_prepare_helper_binds_normalized_calendar_hash_and_frozen_p17_prerequisites():
    from scripts.run_phase_l_a6_pre1_prepare import verify_p0_r5_prerequisites

    facts = verify_p0_r5_prerequisites()
    assert facts["calendar_normalized_sha256"] == "28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8"
    assert facts["r4_daily_artifact_sha256"] == "059e9bbc5bc1c31d06a7d182c27c4dce4d0e01deef8a0a9b30b2cdf430b5574c"
    assert facts["r4_daily_response_sha256"] == "b1bdcdee51ae9513a094c5de4107c05f9fff2025cdd82a4052a7fbfd9c0c156e"
    assert facts["resolved_source_trade_date"] == "2026-10-15"
    assert facts["closure_scope"] == "complete_for_i3_resolution_window"


def test_baseline_and_all_four_governed_alternates_are_accounted(tmp_path):
    controller = _controller(tmp_path)
    for item in build_plan():
        controller.begin_logical(item.logical_sequence)
        _dispatch(controller, item)
        if item.source_contract_id in {"P04", "P05", "P06", "P07"}:
            _dispatch(controller, item, purpose="GOVERNED_ALTERNATE")
        controller.end_logical(verdict="CONFORMING")
    assert controller.physical_dispatch_count == 27
    assert sum(controller.per_source_dispatch_counts.values()) == 27
    assert all(controller.logical_results[x] == "CONFORMING" for x in controller.plan)


def test_physical_28th_and_source_overflow_are_blocked_before_delegate(tmp_path):
    controller = _controller(tmp_path)
    calls = []
    item = build_plan()[0]
    controller.begin_logical(1)
    _dispatch(controller, item, delegate=lambda _record: calls.append("first"))
    with pytest.raises(DispatchBlocked, match="per_source_dispatch_ceiling"):
        _dispatch(controller, item, delegate=lambda _record: calls.append("second"))
    assert calls == ["first"]
    controller.physical_dispatch_count = PHYSICAL_CEILING
    other = build_plan()[1]
    controller.end_logical(verdict="CONFORMING")
    controller.begin_logical(other.logical_sequence)
    with pytest.raises(DispatchBlocked, match="global_dispatch_ceiling"):
        _dispatch(controller, other, delegate=lambda _record: calls.append("overflow"))
    assert calls == ["first"]


@pytest.mark.parametrize("source_id,role", [("P01", "PRIMARY"), ("P04", "GOVERNED_ALTERNATE")])
def test_per_source_limits_reject_repeated_dispatch(tmp_path, source_id, role):
    controller = _controller(tmp_path)
    item = controller.plan[source_id]
    controller.begin_logical(item.logical_sequence)
    _dispatch(controller, item)
    if source_id == "P04":
        _dispatch(controller, item, purpose=role)
        with pytest.raises(DispatchBlocked, match="source_already_completed|per_source_dispatch_ceiling|primary_already_dispatched"):
            _dispatch(controller, item, purpose=role)
    else:
        with pytest.raises(DispatchBlocked):
            _dispatch(controller, item)


def test_authority_consumption_is_persisted_before_transport_and_crash_is_one_shot(tmp_path):
    controller = _controller(tmp_path)
    item = build_plan()[0]
    controller.begin_logical(1)
    consumed = tmp_path / "authority_consumed.json"

    def delegate(_record):
        receipt = json.loads(consumed.read_text(encoding="utf-8"))
        assert receipt["state"] == "CONSUMED"
        raise RuntimeError("simulated crash after latch")

    with pytest.raises(RuntimeError, match="simulated crash"):
        _dispatch(controller, item, delegate=delegate)
    second = _controller(tmp_path)
    second.begin_logical(1)
    with pytest.raises(DispatchBlocked, match="already_consumed"):
        _dispatch(second, item)


@pytest.mark.parametrize("reservation,head,tree,error", [
    (False, HEAD, TREE, "A6_LIVE_RESERVATION_NOT_FINALIZED"),
    (True, "c" * 40, TREE, "binding_invalid"),
    (True, HEAD, "d" * 40, "binding_invalid"),
])
def test_missing_or_mismatched_authority_fails_before_dispatch(tmp_path, reservation, head, tree, error):
    controller = _controller(tmp_path, valid_reservation=reservation)
    controller.actual_head, controller.actual_tree = head, tree
    item = build_plan()[0]
    controller.begin_logical(1)
    calls = []
    with pytest.raises(DispatchBlocked, match=error):
        _dispatch(controller, item, delegate=lambda _record: calls.append(1))
    assert calls == []
    assert controller.physical_dispatch_count == 0


def test_429_suppresses_only_later_exact_same_hostname_and_404_410_do_not(tmp_path):
    controller = _controller(tmp_path)
    plan = build_plan()
    p02, p11, p12 = plan[1], plan[10], plan[11]
    calls = []
    controller.begin_logical(p02.logical_sequence)
    record = _dispatch(controller, p02, delegate=lambda _r: calls.append("p02"))
    controller.observe_response(record, http_status=429, retry_after="120")
    controller.end_logical(verdict="TRANSPORT_OR_HTTP_DEGRADED")
    assert controller.skip_after_rate_limit(p11.logical_sequence) == "SKIPPED_AFTER_RATE_LIMIT"
    controller.begin_logical(p12.logical_sequence)
    other = _dispatch(controller, p12, delegate=lambda _r: calls.append("p12"))
    controller.observe_response(other, http_status=404)
    controller.end_logical(verdict="TRANSPORT_OR_HTTP_DEGRADED")
    assert calls == ["p02", "p12"]
    assert controller.suppressed_hosts == {p02.hostname}
    assert other["lifecycle_observation"] == "endpoint_not_found_observed"

    fresh = _controller(tmp_path / "fresh")
    x = build_plan()[1]
    fresh.begin_logical(x.logical_sequence)
    r = _dispatch(fresh, x)
    fresh.observe_response(r, http_status=410)
    assert fresh.suppressed_hosts == set()
    assert r["lifecycle_observation"] == "endpoint_gone_observed"


def test_probe_redirect_plan_is_zero_and_p01_fallback_disabled(tmp_path, monkeypatch):
    from scripts import m5k_common
    from urllib.request import OpenerDirector

    watchlist = {
        "schema_version": "m5n_watchlist.v1", "watchlist_id": "a6-offline-test",
        "items": [
            {"id": "TWSE:2330", "symbol": "2330", "display_name": "TWSE:2330", "market": "twse",
             "instrument_type": "listed_equity", "adapter": "twse_mis_equity_etf_quote", "category": "test",
             "enabled": True, "display_order": 1, "tags": [], "notes": "", "preferred_sources": ["twse_mis_equity_etf_quote"]},
            {"id": "TPEX:6488", "symbol": "6488", "display_name": "TPEX:6488", "market": "tpex",
             "instrument_type": "equity", "adapter": "twse_mis_equity_etf_quote", "category": "test",
             "enabled": True, "display_order": 2, "tags": [], "notes": "", "preferred_sources": ["twse_mis_equity_etf_quote"]},
        ],
    }
    calls = []

    def fail_once(_opener, *_args, **kwargs):
        calls.append(kwargs["timeout"])
        raise URLError("offline fake failure")

    monkeypatch.setattr(OpenerDirector, "open", fail_once)
    controller = _controller(tmp_path)
    item = controller.plan["P01"]
    controller.begin_logical(item.logical_sequence)
    with controller.production_source_scope(item.logical_sequence), controller.install_urllib_guard():
        result = m5k_common.execute_live_observation(watchlist, write_latest=False,
                 timeout=15, allow_individual_fallback=False)
    controller.end_logical(verdict="TRANSPORT_OR_HTTP_DEGRADED")
    assert len(calls) == 1
    assert calls == [15]
    assert controller.physical_dispatch_count == 1
    assert result["source_investigation_notes"][0]["fallback"] == "disabled_by_caller"
    matrix = contract_matrix()
    assert all(row["redirect_behavior"].startswith("follow_limit=0") for row in matrix if row["source_contract_id"].startswith("B"))
    assert all(row["maximum_physical_dispatches"] == 1 for row in matrix if row["source_contract_id"].startswith("B"))


def test_bootstrap_zero_redirect_is_rejected_before_second_dispatch(tmp_path, monkeypatch):
    import importlib.util
    from email.message import Message
    from urllib.request import OpenerDirector, Request
    path = Path("skills/tw-security-master-classifier/scripts/probe_sources.py").resolve()
    spec = importlib.util.spec_from_file_location("a6_pre1_probe_sources", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

    controller = _controller(tmp_path)
    item = controller.plan["B01"]
    budget = A6BootstrapBudgetAdapter(controller, logical_sequence=item.logical_sequence)
    handler = module.SafeRedirectHandler(
        [item.hostname], dispatch_budget=budget, max_followed_redirects=0,
    )
    request = Request(item.route)
    calls = []

    class FakeResponse:
        status = 200
        headers = Message()
        def getcode(self): return 200

    monkeypatch.setattr(OpenerDirector, "open", lambda *_a, **_k: calls.append(1) or FakeResponse())
    with controller.production_source_scope(item.logical_sequence):
        with controller.install_urllib_guard():
            assert budget.reserve_before_dispatch() == 1
            opener = OpenerDirector()
            opener.open(request, timeout=20)
            with pytest.raises(module.BootstrapRedirectLimitExceeded):
                handler.redirect_request(request, None, 302, "Found", {"Location": item.route + "&page=2"}, item.route + "&page=2")
    assert calls == [1]
    assert controller.physical_dispatch_count == 1
    assert budget.used_dispatches == 1


def test_p12_plan_is_exact_month_and_p17_date_is_frozen():
    plan = build_plan()
    assert plan[11].target_or_selector == "TWSE:2330;month=2026-10"
    assert plan[16].target_or_selector == "TWSE:2330;trade_date=2026-10-15"
    assert "format(date=\"20261015\")" in contract_matrix()[16]["production_transport"] or plan[16].route.endswith("date=20261015&selectType=ALLBUT0999&response=json")


def test_a5_adapter_preserves_rate_limit_lifecycle_facts():
    result = transport_observation(source_contract_id="P02", observed_at="2026-10-16T07:00:00Z",
        http_status=429, retry_after="60", contract_outcome="unknown", semantic_outcome="unknown")
    assert "rate_limit_observed" in result["drift_observations"]
    assert result["retry_after"]["delta_seconds"] == 60
    for status, expected in ((404, "endpoint_not_found_observed"), (410, "endpoint_gone_observed")):
        fact = transport_observation(source_contract_id="P02", observed_at="2026-10-16T07:00:00Z",
            http_status=status, contract_outcome="unknown")
        assert expected in fact["drift_observations"]
    valid = transport_observation(source_contract_id="P02", observed_at="2026-10-16T07:00:00Z",
        http_status=200, contract_outcome="valid", semantic_outcome="available")
    assert valid["adjudication"] == "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"
    drift = transport_observation(source_contract_id="P02", observed_at="2026-10-16T07:00:00Z",
        http_status=200, contract_outcome="invalid", semantic_outcome="source_failed")
    assert drift["adjudication"] == "CONTRACT_FAILURE_REPORTED"
    empty = transport_observation(source_contract_id="P02", observed_at="2026-10-16T07:00:00Z",
        http_status=200, contract_outcome="valid", semantic_outcome="no_evidence_in_covered_scope",
        response_form="empty_collection", empty_response_policy="allowed")
    assert empty["adjudication"] == "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"
    # A5 receives bounded facts only; arbitrary response text cannot assert deprecation.
    no_deprecation_inference = transport_observation(source_contract_id="P02",
        observed_at="2026-10-16T07:00:00Z", http_status=200,
        contract_outcome="valid", semantic_outcome="available")
    assert "explicit_deprecation_signal_observed" not in no_deprecation_inference["drift_observations"]


def test_urllib_hook_counts_actual_dispatch_and_attributes_h1_components(tmp_path, monkeypatch):
    from email.message import Message
    from urllib.request import OpenerDirector, Request

    controller = _controller(tmp_path)
    plan = build_plan()
    calls = []

    class FakeResponse:
        status = 200
        headers = Message()
        def getcode(self): return 200
        def read(self, *_args): return b"{}"
        def close(self): pass

    def fake_open(_opener, request, data=None, timeout=None):
        calls.append((request.full_url, request.get_method(), timeout))
        return FakeResponse()

    monkeypatch.setattr(OpenerDirector, "open", fake_open)
    with controller.production_source_scope(8, family_sequences=(9, 10)):
        with controller.install_urllib_guard():
            opener = OpenerDirector()
            for item in plan[7:10]:
                opener.open(Request(item.route, method=item.method), timeout=item.timeout_seconds)
    assert len(calls) == 3
    assert controller.physical_dispatch_count == 3
    assert [r["source_contract_id"] for r in controller.dispatch_ledger] == ["P08", "P09", "P10"]


def test_urllib_hook_rejects_unplanned_host_and_timeout_before_fake_transport(tmp_path, monkeypatch):
    from urllib.request import OpenerDirector, Request
    controller = _controller(tmp_path)
    item = build_plan()[1]
    calls = []
    monkeypatch.setattr(OpenerDirector, "open", lambda *_a, **_k: calls.append(1))
    with controller.production_source_scope(item.logical_sequence):
        with controller.install_urllib_guard():
            opener = OpenerDirector()
            with pytest.raises(DispatchBlocked, match="timeout_mismatch"):
                opener.open(Request(item.route), timeout=item.timeout_seconds + 1)
            with pytest.raises(DispatchBlocked, match="route_not_approved"):
                opener.open(Request("https://unplanned.example/data"), timeout=item.timeout_seconds)
    assert calls == []
    assert controller.physical_dispatch_count == 0


def test_urllib_hook_429_suppression_blocks_later_same_host_before_delegate(tmp_path, monkeypatch):
    from email.message import Message
    from urllib.error import HTTPError
    from urllib.request import OpenerDirector, Request

    controller = _controller(tmp_path)
    plan = build_plan()
    p02, p11 = plan[1], plan[10]
    calls = []
    headers = Message()
    headers["Retry-After"] = "25"

    def fake_open(_opener, request, data=None, timeout=None):
        calls.append(request.full_url)
        raise HTTPError(request.full_url, 429, "Too Many Requests", headers, None)

    monkeypatch.setattr(OpenerDirector, "open", fake_open)
    opener = OpenerDirector()
    with controller.production_source_scope(p02.logical_sequence):
        with controller.install_urllib_guard():
            with pytest.raises(HTTPError):
                opener.open(Request(p02.route), timeout=p02.timeout_seconds)
            assert controller.suppressed_hosts == {p02.hostname}
            with controller.production_source_scope(p11.logical_sequence):
                with pytest.raises(DispatchBlocked, match="hostname_suppressed"):
                    opener.open(Request(p11.route), timeout=p11.timeout_seconds)
    assert len(calls) == 1
    assert controller.physical_dispatch_count == 1
    assert controller.dispatch_ledger[0]["retry_after_raw"] == "25"


@pytest.mark.parametrize("status,retry_after,expected", [
    (200, None, "http_response"),
    (404, None, "http_response"),
    (410, None, "http_response"),
    (429, None, "http_response"),
    (429, "17", "http_response"),
    (429, "Wed, 21 Oct 2026 07:28:00 GMT", "http_response"),
    (500, None, "http_response"),
])
def test_fake_transport_http_cases_use_controller_before_delegate(tmp_path, status, retry_after, expected):
    controller = _controller(tmp_path)
    item = build_plan()[0]
    controller.begin_logical(1)
    ordering = []
    record = _dispatch(controller, item, delegate=lambda _r: ordering.append("delegate"))
    assert ordering == ["delegate"]
    controller.observe_response(record, http_status=status, retry_after=retry_after)
    assert record["transport_outcome"] == expected
    assert record["http_status"] == status
    assert record["retry_after_raw"] == retry_after
    assert controller.physical_dispatch_count == 1


@pytest.mark.parametrize("error", [TimeoutError("fake timeout"), ConnectionError("fake connection")])
def test_fake_transport_errors_are_counted_without_retry(tmp_path, error):
    controller = _controller(tmp_path)
    item = build_plan()[0]
    controller.begin_logical(1)
    calls = []
    with pytest.raises(type(error)):
        _dispatch(controller, item, delegate=lambda _r: calls.append("one") or (_ for _ in ()).throw(error))
    assert len(calls) == 1
    assert controller.physical_dispatch_count == 1
    record = controller.dispatch_ledger[-1]
    assert record["retry_count"] == 0
    assert record["transport_outcome"] == "transport_failure"


def test_p12_uses_one_exact_month_fetch_and_no_walker(monkeypatch):
    from server.services import phase_h_h3_twse_stock_day_adapter as adapter

    seen = []

    class Response:
        status = 200
        headers = {"Content-Type": "text/html; charset=utf-8"}
        def read(self, _limit): return b"not a real report, parser must fail closed"
        def close(self): pass
        def geturl(self): return "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?response=html&date=20261001&stockNo=2330"

    def fake_http_get(request, timeout):
        seen.append((request.full_url, timeout))
        return Response()

    result = adapter.fetch_twse_stock_day_month(
        target={"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"},
        instrument_family="company_share", instrument_type="common_share",
        requested_month="2026-10", retrieved_at="2026-10-16T07:00:00Z",
        timeout_seconds=15, max_response_bytes=1_000_000, http_get=fake_http_get,
    )
    assert result.status == "source_failed"
    assert len(seen) == 1
    assert "date=20261001" in seen[0][0]
    assert "stockNo=2330" in seen[0][0]
    assert seen[0][1] == 15


def test_pre1_live_cli_is_hard_disabled():
    with pytest.raises(DispatchBlocked, match="A6_LIVE_RESERVATION_NOT_FINALIZED"):
        pre1_live_entrypoint("--live")


def test_a6_controller_has_no_retry_sleep_or_scheduler_path():
    source = Path("scripts/phase_l_a6_live_dispatch_guard.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if name in {"sleep", "backoff", "schedule", "poll", "retry"}:
                forbidden_calls.append(name)
        if isinstance(node, ast.While):
            forbidden_calls.append("while_loop")
    assert forbidden_calls == []


def test_offline_tests_do_not_open_external_sockets(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("external socket attempted")
    monkeypatch.setattr(socket, "create_connection", fail)
