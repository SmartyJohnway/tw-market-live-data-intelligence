from __future__ import annotations

import json
import socket
from email.message import Message
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from scripts import run_phase_l_l3_a6_live_recertification as runner
from scripts.phase_l_a6_live_dispatch_guard import build_plan, contract_matrix, plan_json


def _run(tmp_path: Path, factory=None, name="run"):
    return runner.run(mode="offline", run_dir=tmp_path / name, response_factory=factory)


def _plan_for(url):
    return next(item for item in build_plan() if item.route == url or item.alternate_route == url)


def _research_json_success(url):
    from scripts.phase_g.research_executor import ROUTES, SOURCE_FIELD_MAPPINGS
    key, route = next((key, row) for key, row in ROUTES.items() if row["json_url"] == url)
    aliases = SOURCE_FIELD_MAPPINGS[(route["contract"], "official_json_openapi")]
    values = {"company_code": "2330" if key[1] == "TWSE" else "6488", "company_name": "fixture",
        "source_report_date": "2026/10/16", "publication_date": "2026/10/16",
        "publication_time": "12:00", "reporting_period": "2026/09"}
    row = {fields[0]: values.get(name, "0") for name, fields in aliases.items()}
    return 200, json.dumps([row], ensure_ascii=False).encode(), {"Content-Type": "application/json"}


def test_offline_baseline_uses_all_23_production_seams_without_sockets(tmp_path, monkeypatch):
    attempts = []
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: attempts.append("connect") or (_ for _ in ()).throw(AssertionError("network")))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: attempts.append("create_connection") or (_ for _ in ()).throw(AssertionError("network")))
    result = _run(tmp_path)
    assert result["logical_adjudicated"] == 23
    assert result["physical_dispatches"] == 23
    assert result["overall_disposition"] == "PASS"
    assert result["authority_consumed"] is False
    assert result["simulation_latch_exercised"] is True
    assert attempts == []


def test_all_four_governed_research_alternates_reach_exact_27(tmp_path):
    from scripts.phase_g.research_executor import ROUTES

    reverse = {item["csv_url"]: (key, item) for key, item in ROUTES.items()}

    def factory(url, method):
        if url.endswith(".csv"):
            return 500, b"offline primary failure", {"Content-Type": "text/plain"}
        if url in {row["json_url"] for row in ROUTES.values()}:
            return _research_json_success(url)
        return runner._default_offline_response(url, method)

    result = _run(tmp_path, factory, "max")
    assert result["logical_adjudicated"] == 23
    assert result["physical_dispatches"] == 27
    assert result["overall_disposition"] == "PARTIAL"
    assert all(row["bounded_detail"].get("fallback_attempted") is True for row in result["source_results"] if row["source_contract_id"] in {"P04", "P05", "P06", "P07"})
    assert all(row["dispatch_role"] in {"PRIMARY", "GOVERNED_ALTERNATE"} for row in json.loads((tmp_path / "max" / "dispatch_ledger.json").read_text())["entries"])


@pytest.mark.parametrize("primary", ["500", "404", "410", "timeout"])
def test_research_alternate_recovery_preserves_primary_degradation(tmp_path, primary):
    target = build_plan()[3]

    def factory(url, method):
        if url == target.route:
            if primary == "timeout":
                raise TimeoutError("offline timeout")
            return int(primary), b"", {"Content-Type": "text/plain"}
        if url == target.alternate_route:
            return _research_json_success(url)
        return runner._default_offline_response(url, method)

    result = _run(tmp_path, factory, f"recover-{primary}")
    p04 = next(row for row in result["source_results"] if row["source_contract_id"] == "P04")
    calls = [row for row in json.loads((tmp_path / f"recover-{primary}" / "dispatch_ledger.json").read_text())["entries"] if row["source_contract_id"] == "P04"]
    assert len(calls) == 2
    assert [row["dispatch_role"] for row in calls] == ["PRIMARY", "GOVERNED_ALTERNATE"]
    assert p04["verdict"] == "TRANSPORT_OR_HTTP_DEGRADED"
    assert p04["bounded_detail"]["alternate_dispatch_attempted"] is True
    assert p04["bounded_detail"]["primary_outcome"] in {"http_degraded", "transport_degraded"}
    assert result["overall_disposition"] == "PARTIAL"
    if primary == "404":
        assert calls[0]["lifecycle_observation"] == "endpoint_not_found_observed"
    if primary == "410":
        assert calls[0]["lifecycle_observation"] == "endpoint_gone_observed"


def test_research_429_never_uses_cross_host_alternate_and_skips_peer_primaries(tmp_path):
    target = build_plan()[3]

    def factory(url, method):
        if url == target.route:
            return 429, b"", {"Content-Type": "text/plain", "Retry-After": "120"}
        if url == target.alternate_route:
            return _research_json_success(url)
        return runner._default_offline_response(url, method)

    result = _run(tmp_path, factory, "research-429")
    by_id = {row["source_contract_id"]: row for row in result["source_results"]}
    ledger = json.loads((tmp_path / "research-429" / "dispatch_ledger.json").read_text())["entries"]
    p04 = [row for row in ledger if row["source_contract_id"] == "P04"]
    assert len(p04) == 1 and p04[0]["dispatch_role"] == "PRIMARY"
    assert p04[0]["retry_after_raw"] == "120"
    assert by_id["P04"]["verdict"] == "TRANSPORT_OR_HTTP_DEGRADED"
    assert by_id["P04"]["bounded_detail"]["alternate_dispatch_attempted"] is False
    for sid in ("P05", "P06", "P07"):
        assert by_id[sid]["verdict"] == "SKIPPED_AFTER_RATE_LIMIT"
        assert not [row for row in ledger if row["source_contract_id"] == sid]
    assert result["overall_disposition"] == "INCONCLUSIVE"


def test_primary_csv_contract_drift_survives_valid_governed_alternate(tmp_path):
    target = build_plan()[3]

    def factory(url, method):
        if url == target.route:
            return 200, b"a,b\n1,2,3\n", {"Content-Type": "text/csv; charset=utf-8"}
        if url == target.alternate_route:
            return _research_json_success(url)
        return runner._default_offline_response(url, method)

    result = _run(tmp_path, factory, "primary-drift")
    p04 = next(row for row in result["source_results"] if row["source_contract_id"] == "P04")
    assert p04["verdict"] == "CONTRACT_DRIFT_OBSERVED"
    assert p04["bounded_detail"]["alternate_dispatch_attempted"] is True
    assert p04["bounded_detail"]["primary_contract_drift"] is True
    assert result["overall_disposition"] == "SOURCE_CHANGED"


def test_429_suppresses_later_same_tpex_hostname_only(tmp_path):
    def factory(url, method):
        if url == build_plan()[2].route:
            return 429, b"", {"Content-Type": "application/json", "Retry-After": "120"}
        return runner._default_offline_response(url, method)

    result = _run(tmp_path, factory, "rate")
    by_id = {row["source_contract_id"]: row for row in result["source_results"]}
    assert result["overall_disposition"] == "INCONCLUSIVE"
    assert result["physical_dispatches"] == 17
    for sid in ("P08", "P09", "P10", "P15", "P18", "B04"):
        assert by_id[sid]["verdict"] == "SKIPPED_AFTER_RATE_LIMIT"
    assert by_id["P16"]["verdict"] != "SKIPPED_AFTER_RATE_LIMIT"
    ledger = json.loads((tmp_path / "rate" / "dispatch_ledger.json").read_text())["entries"]
    p03 = next(row for row in ledger if row["source_contract_id"] == "P03")
    assert p03["lifecycle_observation"] == "rate_limit_observed"
    assert p03["retry_after_raw"] == "120"


@pytest.mark.parametrize("status", [404, 410])
def test_404_410_are_observations_not_host_suppression(tmp_path, status):
    def factory(url, method):
        if url == build_plan()[1].route:
            return status, b"", {"Content-Type": "application/json"}
        return runner._default_offline_response(url, method)

    result = _run(tmp_path, factory, f"http-{status}")
    by_id = {row["source_contract_id"]: row for row in result["source_results"]}
    assert result["overall_disposition"] == "PARTIAL"
    assert result["physical_dispatches"] == 23
    assert by_id["P11"]["verdict"] != "SKIPPED_AFTER_RATE_LIMIT"
    ledger = json.loads((tmp_path / f"http-{status}" / "dispatch_ledger.json").read_text())["entries"]
    assert next(row for row in ledger if row["source_contract_id"] == "P02")["lifecycle_observation"] == ("endpoint_not_found_observed" if status == 404 else "endpoint_gone_observed")


def test_http_200_contract_drift_is_source_changed(tmp_path):
    def factory(url, method):
        if url == build_plan()[1].route:
            return 200, b'{"unexpected":true}', {"Content-Type": "application/json"}
        return runner._default_offline_response(url, method)

    result = _run(tmp_path, factory, "drift")
    by_id = {row["source_contract_id"]: row for row in result["source_results"]}
    assert by_id["P02"]["verdict"] == "CONTRACT_DRIFT_OBSERVED"
    assert result["overall_disposition"] == "SOURCE_CHANGED"


@pytest.mark.parametrize("failure,expected", [("timeout", "PARTIAL"), ("500", "PARTIAL")])
def test_transport_timeout_and_5xx_are_degraded_not_contract_drift(tmp_path, failure, expected):
    def factory(url, method):
        if url == build_plan()[1].route:
            if failure == "timeout":
                raise TimeoutError("offline timeout")
            return 500, b"", {"Content-Type": "application/json"}
        return runner._default_offline_response(url, method)

    result = _run(tmp_path, factory, failure)
    by_id = {row["source_contract_id"]: row for row in result["source_results"]}
    assert by_id["P02"]["verdict"] == "TRANSPORT_OR_HTTP_DEGRADED"
    assert result["overall_disposition"] == expected


def test_p12_uses_one_exact_month_and_p11_has_no_h3_dependency(tmp_path, monkeypatch):
    calls = {"month": 0, "walker": 0, "p11": 0}
    import server.services.phase_h_h3_twse_stock_day_adapter as h3
    original = h3.fetch_twse_stock_day_month

    def counted(*args, **kwargs):
        calls["month"] += 1
        assert kwargs["requested_month"] == "2026-10"
        return original(*args, **kwargs)

    monkeypatch.setattr(h3, "fetch_twse_stock_day_month", counted)
    result = _run(tmp_path)
    p12 = next(row for row in result["source_results"] if row["source_contract_id"] == "P12")
    assert calls["month"] == 1 and calls["walker"] == 0
    assert p12["bounded_detail"]["month"] == "2026-10"
    entries = json.loads((tmp_path / "run" / "dispatch_ledger.json").read_text())["entries"]
    assert len([row for row in entries if row["source_contract_id"] == "P11"]) == 1


def test_live_mode_without_final_reservation_fails_before_transport(tmp_path, monkeypatch):
    attempts = []
    monkeypatch.setattr(runner.OpenerDirector, "open", lambda *a, **k: attempts.append(1))
    with pytest.raises(runner.DispatchBlocked, match="A6_LIVE_RESERVATION_NOT_FINALIZED"):
        runner.run(mode="live", run_dir=tmp_path / "locked", reservation=None)
    assert attempts == []


def test_source_plan_and_matrix_are_exactly_frozen():
    ids = [item.source_contract_id for item in build_plan()]
    assert ids == [*(f"P{i:02d}" for i in range(1, 19)), *(f"B{i:02d}" for i in range(1, 6))]
    assert [item.logical_sequence for item in build_plan()] == list(range(1, 24))
    matrix = contract_matrix()
    assert len(matrix) == 23 and len({row["source_contract_id"] for row in matrix}) == 23
    assert all(row["timeout_seconds"] > 0 and row["retry_supported"] is False and row["a6_retry_allowed"] is False for row in matrix)
    assert sum(item.maximum_physical_dispatches for item in build_plan()) == 27
    assert len(plan_json()) == 23
