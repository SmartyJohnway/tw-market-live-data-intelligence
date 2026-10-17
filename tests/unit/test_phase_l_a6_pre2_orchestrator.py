from __future__ import annotations

import json
import hashlib
import os
import socket
import subprocess
import sys
from email.message import Message
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from scripts import run_phase_l_l3_a6_live_recertification as runner
from scripts import phase_l_a6_final_live_reservation as reservation_tool
from scripts.phase_l_a6_live_dispatch_guard import build_plan, contract_matrix, plan_json


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_help(args, *, cwd):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, *map(str, args), "--help"], cwd=cwd, env=env,
        capture_output=True, text=True, timeout=20,
    )


def test_reservation_creator_direct_script_help_from_repo_root():
    result = _run_help(["scripts/phase_l_a6_final_live_reservation.py"], cwd=REPO_ROOT)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
    assert "ModuleNotFoundError" not in result.stderr


def test_reservation_creator_direct_script_help_from_arbitrary_cwd(tmp_path):
    script = REPO_ROOT / "scripts/phase_l_a6_final_live_reservation.py"
    result = _run_help([script], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
    assert "ModuleNotFoundError" not in result.stderr


def test_reservation_creator_module_help_from_repo_root():
    result = _run_help(["-m", "scripts.phase_l_a6_final_live_reservation"], cwd=REPO_ROOT)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
    assert "ModuleNotFoundError" not in result.stderr


def test_live_runner_direct_script_help_from_arbitrary_cwd(tmp_path):
    script = REPO_ROOT / "scripts/run_phase_l_l3_a6_live_recertification.py"
    result = _run_help([script], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
    assert "ModuleNotFoundError" not in result.stderr


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


def test_p01_batch_failure_is_one_physical_dispatch_without_symbol_fallback(tmp_path):
    p01 = build_plan()[0]
    def factory(url, method):
        if url.startswith(p01.route):
            raise OSError("offline batch transport failure")
        return runner._default_offline_response(url, method)
    result = _run(tmp_path, factory, "p01-batch-failure")
    ledger = json.loads((tmp_path / "p01-batch-failure" / "dispatch_ledger.json").read_text())["entries"]
    p01_entries = [entry for entry in ledger if entry["source_contract_id"] == "P01"]
    assert len(p01_entries) == 1
    assert result["physical_dispatches"] == 23
    assert all(entry["source_contract_id"] != "P01" or "individual" not in entry["route_identity"] for entry in ledger)


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


def _canonical_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _reservation_bundle(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "a6-test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "A6 Offline Test"], cwd=repo, check=True)
    bundle = repo / "governance" / "pre2"
    bundle.mkdir(parents=True)
    source_rows = [item.__dict__.copy() for item in build_plan()]
    plan = {"sources": source_rows, "logical_count": 23, "physical_ceiling": 27, "P17_trade_date": "2026-10-15"}
    matrix = {"entries": contract_matrix()}
    plan_path = bundle / "a6_source_plan.json"
    matrix_path = bundle / "transport_contract_matrix.json"
    plan_path.write_text(json.dumps(plan, sort_keys=True), encoding="utf-8")
    matrix_path.write_text(json.dumps(matrix, sort_keys=True), encoding="utf-8")
    orchestration = bundle / "orchestration_contract.json"
    orchestration.write_text('{"mode":"PRE2_TEST"}\n', encoding="utf-8")
    files = []
    for artifact in (plan_path, matrix_path, orchestration):
        files.append({"path": artifact.name, "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()})
    manifest_value = {"files": files}
    manifest_value["manifest_sha256"] = _canonical_sha(manifest_value)
    manifest_path = bundle / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_value, sort_keys=True), encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "offline reservation fixture"], cwd=repo, check=True)
    live_dir = repo / "acceptance_runs" / "l3-a6-offline-live-test"
    reservation_path = live_dir / "authority_reservation.json"
    reservation = reservation_tool.create_reservation(repo=repo, plan_path=plan_path, matrix_path=matrix_path,
        pre2_manifest_path=manifest_path, output_path=reservation_path, planned_run_id=live_dir.name)
    return repo, bundle, live_dir, reservation_path, reservation


def test_reservation_creator_binds_actual_git_plan_matrix_manifest_and_run_id(tmp_path):
    repo, bundle, live_dir, path, reservation = _reservation_bundle(tmp_path)
    assert reservation["pre_network_head"] == subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    assert reservation["pre_network_tree"] == subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True).strip()
    assert reservation["source_plan_sha256"] == hashlib.sha256((bundle / "a6_source_plan.json").read_bytes()).hexdigest()
    assert reservation["transport_matrix_sha256"] == hashlib.sha256((bundle / "transport_contract_matrix.json").read_bytes()).hexdigest()
    assert reservation["planned_run_id"] == live_dir.name
    assert reservation["live_authority_consumed"] is False
    assert path.is_file()


def test_live_runner_validates_creator_reservation_without_dispatch(tmp_path, monkeypatch):
    repo, _bundle, live_dir, path, _reservation = _reservation_bundle(tmp_path)
    monkeypatch.setattr(runner, "_git", lambda *args: subprocess.check_output(["git", *args], cwd=repo, text=True).strip())
    transport_calls = []
    monkeypatch.setattr(runner.OpenerDirector, "open", lambda *a, **k: transport_calls.append(1))
    validated = runner._validate_reservation(path, repo=repo, run_dir=live_dir)
    assert validated["state"] == "RESERVED_NOT_CONSUMED"
    assert validated["planned_run_id"] == live_dir.name
    assert transport_calls == []


@pytest.mark.parametrize("field,value,error", [
    ("authority_id", "wrong", "a6_authority_reservation_binding_invalid"),
    ("pre_network_head", "wrong", "a6_authority_reservation_binding_invalid"),
    ("pre_network_tree", "wrong", "a6_authority_reservation_binding_invalid"),
    ("source_plan_sha256", "wrong", "a6_authority_reservation_artifact_binding_invalid"),
    ("transport_matrix_sha256", "wrong", "a6_authority_reservation_artifact_binding_invalid"),
    ("pre2_manifest_sha256", "wrong", "a6_authority_reservation_artifact_binding_invalid"),
    ("pre2_manifest_canonical_sha256", "wrong", "a6_authority_reservation_artifact_binding_invalid"),
    ("planned_run_id", "other-run", "a6_authority_reservation_binding_invalid"),
])
def test_invalid_reservation_binding_refuses_before_transport(tmp_path, monkeypatch, field, value, error):
    repo, _bundle, live_dir, path, reservation = _reservation_bundle(tmp_path)
    reservation[field] = value
    path.write_text(json.dumps(reservation), encoding="utf-8")
    monkeypatch.setattr(runner, "_git", lambda *args: subprocess.check_output(["git", *args], cwd=repo, text=True).strip())
    transport_calls = []
    monkeypatch.setattr(runner.OpenerDirector, "open", lambda *a, **k: transport_calls.append(1))
    with pytest.raises(runner.DispatchBlocked, match=error):
        runner._validate_reservation(path, repo=repo, run_dir=live_dir)
    assert transport_calls == []


def test_missing_or_consumed_reservation_refuses_before_transport(tmp_path, monkeypatch):
    repo, _bundle, live_dir, path, _reservation = _reservation_bundle(tmp_path)
    monkeypatch.setattr(runner, "_git", lambda *args: subprocess.check_output(["git", *args], cwd=repo, text=True).strip())
    transport_calls = []
    monkeypatch.setattr(runner.OpenerDirector, "open", lambda *a, **k: transport_calls.append(1))
    with pytest.raises(runner.DispatchBlocked, match="A6_LIVE_RESERVATION_NOT_FINALIZED"):
        runner._validate_reservation(None, repo=repo, run_dir=live_dir)
    (live_dir / "authority_consumed.json").write_text("{}", encoding="utf-8")
    with pytest.raises(runner.DispatchBlocked, match="a6_authority_already_consumed"):
        runner._validate_reservation(path, repo=repo, run_dir=live_dir)
    assert transport_calls == []


def test_pre2_orchestrator_crash_after_latch_rejects_second_execution(tmp_path, monkeypatch):
    run_dir = tmp_path / "l3-a6-crash-reuse"
    run_dir.mkdir()
    reservation_path = run_dir / "authority_reservation.json"
    head, tree = "offline-committed-head", "offline-committed-tree"
    reservation_path.write_text(json.dumps({
        "authority_id": "USER_CHAT_2026-10-16_PHASE_L_L3_A6_BOUNDED_LIVE_SOURCE_DRIFT_RECERTIFICATION_AUTHORIZATION",
        "state": "RESERVED_NOT_CONSUMED", "pre_network_head": head, "pre_network_tree": tree,
    }), encoding="utf-8")
    monkeypatch.setattr(runner, "_git", lambda *_args: head if _args[-1] == "HEAD" else tree)

    def validate(path, *, run_dir):
        consumed = run_dir / "authority_consumed.json"
        if consumed.exists():
            raise runner.DispatchBlocked("a6_authority_already_consumed")
        return json.loads(path.read_text(encoding="utf-8"))

    monkeypatch.setattr(runner, "_validate_reservation", validate)
    def dispatch_first_source(sequence, controller, _run_dir):
        from urllib.request import Request, urlopen
        url = build_plan()[sequence - 1].route + "?ex_ch=tse_2330.tw|otc_6488.tw&json=1&delay=0"
        with urlopen(Request(url), timeout=15):
            pass
        return "CONFORMING", {}
    monkeypatch.setattr(runner, "_invoke_source", dispatch_first_source)
    underlying_calls = []
    def crash_after_latch(*_args, **_kwargs):
        underlying_calls.append("entered_transport")
        raise SystemExit("simulated process crash after authority latch")
    monkeypatch.setattr(runner.OpenerDirector, "open", crash_after_latch)
    with pytest.raises(SystemExit, match="simulated process crash"):
        runner.run(mode="live", run_dir=run_dir, reservation=reservation_path)
    receipt = json.loads((run_dir / "authority_consumed.json").read_text(encoding="utf-8"))
    assert receipt["state"] == "CONSUMED"
    assert underlying_calls == ["entered_transport"]
    with pytest.raises(runner.DispatchBlocked, match="a6_authority_already_consumed"):
        runner.run(mode="live", run_dir=run_dir, reservation=reservation_path)
    assert underlying_calls == ["entered_transport"]


@pytest.mark.parametrize("rate_limited_id,skipped_ids", [
    ("P08", ("P09", "P10")),
    ("P09", ("P10",)),
])
def test_h1_component_429_suppresses_only_later_same_host_components(tmp_path, rate_limited_id, skipped_ids):
    target = next(item for item in build_plan() if item.source_contract_id == rate_limited_id)
    def factory(url, method):
        if url == target.route:
            return 429, b"", {"Content-Type": "application/json", "Retry-After": "60"}
        return runner._default_offline_response(url, method)
    result = _run(tmp_path, factory, f"h1-429-{rate_limited_id}")
    by_id = {row["source_contract_id"]: row for row in result["source_results"]}
    ledger = json.loads((tmp_path / f"h1-429-{rate_limited_id}" / "dispatch_ledger.json").read_text())["entries"]
    for source_id in skipped_ids:
        assert by_id[source_id]["verdict"] == "SKIPPED_AFTER_RATE_LIMIT"
        assert not [entry for entry in ledger if entry["source_contract_id"] == source_id]
    assert len([entry for entry in ledger if entry["source_contract_id"] == rate_limited_id]) == 1
    assert result["overall_disposition"] == "INCONCLUSIVE"


def test_www_twse_rate_limit_suppresses_only_exact_host_not_twse_siblings(tmp_path):
    p12 = next(item for item in build_plan() if item.source_contract_id == "P12")
    def factory(url, method):
        if url.startswith(p12.route + "?"):
            return 429, b"", {"Content-Type": "text/html", "Retry-After": "60"}
        return runner._default_offline_response(url, method)
    result = _run(tmp_path, factory, "twse-host-429")
    by_id = {row["source_contract_id"]: row for row in result["source_results"]}
    assert by_id["P17"]["verdict"] == "SKIPPED_AFTER_RATE_LIMIT"
    for source_id in ("P11", "P13", "P14"):
        assert by_id[source_id]["verdict"] != "SKIPPED_AFTER_RATE_LIMIT"
    assert by_id["B03"]["verdict"] == "SKIPPED_AFTER_RATE_LIMIT"
    assert by_id["B05"]["verdict"] == "SKIPPED_AFTER_RATE_LIMIT"
    assert result["overall_disposition"] == "INCONCLUSIVE"
