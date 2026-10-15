import json
import socket
from pathlib import Path

import pytest

from scripts import m8r_03d_watchlist_controlled_executor as executor
from scripts.m8a_official_eod_observation import empty_adapter_result
from scripts.m8a_tpex_official_eod_adapter import parse_tpex_official_eod_rows
from scripts.m8a_twse_official_eod_adapter import parse_twse_official_eod_rows
from scripts.m8r_03d_watchlist_execution_plan import (
    AUTH_SCHEMA_VERSION,
    MAX_WATCHLIST_TARGETS,
    build_execution_plan,
    canonical_request_hash,
)


FIXTURES = Path("tests/fixtures/m8a_official_eod")
REQUEST = Path("tests/fixtures/m8r_03d/mixed_snapshot_request.json")
SM = {
    ("listed", "2330"): {"instrument_type": "equity", "name": "台積電", "listing_status": "active", "lifecycle_state": "active", "source": "test"},
    ("listed", "2317"): {"instrument_type": "equity", "name": "鴻海", "listing_status": "active", "lifecycle_state": "active", "source": "test"},
    ("tpex_otc", "6488"): {"instrument_type": "equity", "name": "環球晶", "listing_status": "active", "lifecycle_state": "active", "source": "test"},
}


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _authorization(request, plan, authorization_id="a2-test"):
    return {
        "schema_version": AUTH_SCHEMA_VERSION,
        "authorization_id": authorization_id,
        "one_shot_nonce": f"nonce-{authorization_id}",
        "issued_at_utc": "2026-10-15T00:00:00Z",
        "expires_at_utc": "2026-10-16T00:00:00Z",
        "authorized_request_hash": canonical_request_hash(request),
        "authorized_bundle_types": ["snapshot"],
        "authorized_source_families": sorted({g["source_family"] for g in plan["source_call_groups"]}),
        "authorized_target_ids": plan["target_order"],
        "max_target_count": MAX_WATCHLIST_TARGETS,
        "network_execution_allowed": True,
        "one_shot_only": True,
        "polling_allowed": False,
        "scheduler_allowed": False,
        "persistent_storage_allowed": False,
        "raw_payload_retention_allowed": False,
        "operator_approval": {"approved_by": "test"},
    }


def _run(request, tmp_path, monkeypatch, adapter_results, mis_targets=None):
    monkeypatch.setattr(executor, "AUTHORIZATION_CONSUMPTION_ROOT", tmp_path / "claims")
    plan = build_execution_plan(request, bundle_type="snapshot", generated_at_utc="2026-10-15T12:00:00Z", security_master=SM)
    assert not plan.get("issues")
    for family in ("TWSE_OPENAPI", "TPEX_OPENAPI"):
        if family not in adapter_results:
            continue
        prefix = "TWSE:" if family == "TWSE_OPENAPI" else "TPEX:"
        adapter_result = adapter_results[family]
        monkeypatch.setitem(
            executor.SOURCE_ADAPTERS,
            family,
            lambda p, request, g, result=adapter_result, prefix=prefix: executor._live_eod(p, g, lambda symbols: result, prefix),
        )
    out = executor.execute_watchlist(
        request,
        mode="execute",
        bundle_type="snapshot",
        authorization=_authorization(request, plan),
        artifact_root=str(tmp_path / "artifacts"),
        generated_at_utc="2026-10-15T12:00:00Z",
        executors={"TWSE_MIS": lambda *args, **kwargs: {"targets": mis_targets or {}}},
        security_master=SM,
    )
    return out


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("unexpected socket/network call in offline A2 test")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


def _twse(rows, symbols=("2330",)):
    return parse_twse_official_eod_rows(list(rows), requested_symbols=list(symbols), retrieved_at_utc="2026-10-15T12:00:00Z")


def _tpex(rows, symbols=("6488",)):
    return parse_tpex_official_eod_rows(list(rows), requested_symbols=list(symbols), retrieved_at_utc="2026-10-15T12:00:00Z")


def test_tpex_all_rejected_is_not_declared_clean_success():
    row = dict(_load(FIXTURES / "tpex_normal_rows.json")[0])
    row["CompanyName"] = None
    del row["Close"]
    result = _tpex([row])
    assert result["observations"] == []
    assert result["row_count_rejected"] == 1
    assert result["source_status"] == "success"
    assert result["batch_status"] == "source_error"


@pytest.mark.parametrize("source", ["twse", "tpex"])
def test_all_rejected_status_parity_for_both_openapi_adapters(source):
    if source == "twse":
        row = dict(_load(FIXTURES / "twse_normal_rows.json")[0])
        del row["ClosingPrice"]
        result = _twse([row])
    else:
        row = dict(_load(FIXTURES / "tpex_normal_rows.json")[0])
        del row["Close"]
        result = _tpex([row])
    assert result["observations"] == []
    assert result["row_count_rejected"] == 1
    assert result["source_status"] == "success"
    assert result["batch_status"] == "source_error"


def test_group_state_adjudication_keeps_existing_status_vocabulary_and_reason_detail():
    states = {
        "successful_eod_batch": ("success", None),
        "partial_source_success": ("success", "partial_source_success"),
        "date_mismatch": ("failed", "date_mismatch"),
        "empty_non_trading_day": ("success", "empty_non_trading_day"),
        "source_error": ("failed", "source_error"),
        "schema_drift": ("failed", "schema_drift"),
        "unknown_status": ("failed", "unknown_status"),
    }
    for batch_status, (expected_status, expected_reason) in states.items():
        source_status = "error" if batch_status in {"source_error", "schema_drift"} else "success"
        diagnostics = {"source_status": source_status, "batch_status": batch_status}
        assert executor._eod_group_status(diagnostics) == expected_status
        assert executor._eod_group_reason(diagnostics) == expected_reason


def test_partial_batch_retains_observation_and_diagnostics_without_clean_success(tmp_path, monkeypatch):
    rows = _load(FIXTURES / "twse_partial_rows.json")
    result = _twse(rows)
    assert result["batch_status"] == "successful_eod_batch" or result["batch_status"] == "partial_source_success"
    result["batch_status"] = "partial_source_success"
    result["row_count_rejected"] = max(1, result["row_count_rejected"])
    result["rejected_rows"] = [{"symbol": "2330", "reason_code": "missing_required_fields", "field_validation": {"missing": ["TradeValue"]}, "source_row": {"must_not_leak": "x"}}]
    request = _load(REQUEST)
    out = _run(request, tmp_path, monkeypatch, {"TWSE_OPENAPI": result})
    assert out["status"] == "success_with_partial_coverage"
    group = next(g for g in out["source_execution_summary"]["group_results"] if g["source_family"] == "TWSE_OPENAPI")
    assert group["status"] == "success"
    assert group["reason_code"] == "partial_source_success"
    assert group["adapter_diagnostics"]["rejection_reason_codes"] == ["missing_required_fields"]
    assert "source_row" not in json.dumps(out)
    target = next(t for t in out["target_results"] if t["target_id"] == "TWSE:2330" and t.get("source_family") == "TWSE_OPENAPI")
    assert target["source_diagnostics"]["batch_status"] == "partial_source_success"
    assert target["rejection_reason_codes"] == ["missing_required_fields"]
    assert target["fallback_used"] is True


def test_date_mismatch_observation_cannot_become_clean_success(tmp_path, monkeypatch):
    result = _twse(_load(FIXTURES / "twse_mixed_date.json"), symbols=("2330", "0050"))
    # Keep only the requested 2330 observation while retaining the source-wide conflicting dates.
    result["observations"] = [row for row in result["observations"] if row["symbol"] == "2330"]
    result["batch_status"] = "date_mismatch"
    request = _load(REQUEST)
    request["persistent_watchlist_reference"]["enabled_target_ids"] = ["TWSE:2330"]
    fixture = _load("tests/fixtures/m8r_03d/snapshot_source_data.json")
    mis_targets = {"TWSE:2330": {"TWSE_MIS": fixture["targets"]["TWSE:2330"]["TWSE_MIS"]}}
    out = _run(request, tmp_path, monkeypatch, {"TWSE_OPENAPI": result}, mis_targets)
    assert out["status"] == "success_with_partial_coverage"
    assert out["observation_count"] == 1
    group = next(g for g in out["source_execution_summary"]["group_results"] if g["source_family"] == "TWSE_OPENAPI")
    assert group["status"] == "failed"
    assert group["adapter_diagnostics"]["reported_trade_dates"] == ["2026-07-09", "2026-07-10"]
    assert any(issue["code"] == "date_mismatch" for issue in out["issues"])
    target = next(t for t in out["target_results"] if t.get("source_family") == "TWSE_OPENAPI")
    assert target["status"] == "failed" and target["reason_code"] == "date_mismatch"


def test_empty_non_trading_day_is_not_source_or_schema_failure(tmp_path, monkeypatch):
    result = empty_adapter_result("TWSE_OPENAPI", "twse_openapi_stock_day_all_v1", ["2330"], "2026-10-15T12:00:00Z")
    result.update(source_status="success", batch_status="empty_non_trading_day", http_status=200)
    request = _load(REQUEST)
    request["persistent_watchlist_reference"]["enabled_target_ids"] = ["TWSE:2330"]
    out = _run(request, tmp_path, monkeypatch, {"TWSE_OPENAPI": result})
    group = next(g for g in out["source_execution_summary"]["group_results"] if g["source_family"] == "TWSE_OPENAPI")
    assert group["status"] == "success"
    assert group["reason_code"] == "empty_non_trading_day"
    target = next(t for t in out["target_results"] if t.get("source_family") == "TWSE_OPENAPI")
    assert target["status"] == "source_unavailable"
    assert target["reason_code"] == "empty_non_trading_day"
    assert out["status"] != "source_execution_failed"
    assert out["observation_count"] == 0


def test_clean_batch_stays_clean_and_field_validation_survives(tmp_path, monkeypatch):
    result = _twse(_load(FIXTURES / "twse_invalid_numeric.json"))
    assert result["batch_status"] == "successful_eod_batch"
    assert result["observations"][0]["field_validation"]["ClosingPrice"]["valid"] is False
    request = _load(REQUEST)
    request["persistent_watchlist_reference"]["enabled_target_ids"] = ["TWSE:2330"]
    out = _run(request, tmp_path, monkeypatch, {"TWSE_OPENAPI": result})
    assert out["status"] == "success_with_partial_coverage"
    target = next(t for t in out["target_results"] if t.get("source_family") == "TWSE_OPENAPI")
    validation = target["field_validation_diagnostics"]
    assert {item["field"] for item in validation[0]["invalid_fields"]} >= {"ClosingPrice", "TradeVolume"}
    assert "ClosingPrice" not in json.dumps(validation) or "bad" not in json.dumps(validation)


def test_valid_clean_batch_preserves_existing_success(tmp_path, monkeypatch):
    result = _twse(_load(FIXTURES / "twse_normal_rows.json"))
    request = _load(REQUEST)
    request["persistent_watchlist_reference"]["enabled_target_ids"] = ["TWSE:2330"]
    fixture = _load("tests/fixtures/m8r_03d/snapshot_source_data.json")
    mis_targets = {"TWSE:2330": {"TWSE_MIS": fixture["targets"]["TWSE:2330"]["TWSE_MIS"]}}
    out = _run(request, tmp_path, monkeypatch, {"TWSE_OPENAPI": result}, mis_targets)
    group = next(g for g in out["source_execution_summary"]["group_results"] if g["source_family"] == "TWSE_OPENAPI")
    assert group["status"] == "success"
    assert out["status"] in {"success", "success_with_partial_coverage"}
    assert not any(issue.get("code") in {"partial_source_success", "date_mismatch", "schema_drift", "source_error"} for issue in out["issues"])


def test_all_rejected_tpex_reason_reaches_unified_target(tmp_path, monkeypatch):
    row = dict(_load(FIXTURES / "tpex_normal_rows.json")[0])
    row["SecuritiesCompanyCode"] = "6488"
    del row["Close"]
    result = _tpex([row])
    request = _load(REQUEST)
    request["persistent_watchlist_reference"]["enabled_target_ids"] = ["TPEX:6488"]
    out = _run(request, tmp_path, monkeypatch, {"TPEX_OPENAPI": result})
    assert out["status"] == "source_execution_failed"
    group = next(g for g in out["source_execution_summary"]["group_results"] if g["source_family"] == "TPEX_OPENAPI")
    assert group["status"] == "failed"
    target = next(t for t in out["target_results"] if t["target_id"] == "TPEX:6488" and t.get("source_family") == "TPEX_OPENAPI")
    assert target["reason_code"] == "missing_required_fields"
    assert target["rejection_reason_codes"] == ["missing_required_fields"]


def test_rejected_eod_reason_survives_when_current_mis_observation_exists(tmp_path, monkeypatch):
    row = dict(_load(FIXTURES / "twse_normal_rows.json")[0])
    del row["ClosingPrice"]
    result = _twse([row])
    request = _load(REQUEST)
    request["persistent_watchlist_reference"]["enabled_target_ids"] = ["TWSE:2330"]
    fixture = _load("tests/fixtures/m8r_03d/snapshot_source_data.json")
    mis_targets = {"TWSE:2330": {"TWSE_MIS": fixture["targets"]["TWSE:2330"]["TWSE_MIS"]}}
    out = _run(request, tmp_path, monkeypatch, {"TWSE_OPENAPI": result}, mis_targets)
    assert out["status"] == "success_with_partial_coverage"
    target = next(t for t in out["target_results"] if t.get("source_family") == "TWSE_OPENAPI")
    assert target["status"] == "failed"
    assert target["reason_code"] == "missing_required_fields"
    assert any(issue.get("code") == "source_error" for issue in out["issues"])


def test_mixed_market_batch_retains_valid_target_and_rejects_other_target(tmp_path, monkeypatch):
    twse = _twse(_load(FIXTURES / "twse_normal_rows.json"))
    tpex_row = dict(_load(FIXTURES / "tpex_normal_rows.json")[0])
    tpex_row["SecuritiesCompanyCode"] = "6488"
    del tpex_row["Close"]
    tpex = _tpex([tpex_row])
    out = _run(_load(REQUEST), tmp_path, monkeypatch, {"TWSE_OPENAPI": twse, "TPEX_OPENAPI": tpex})
    assert out["status"] == "success_with_partial_coverage"
    assert out["observation_count"] >= 1
    target = next(t for t in out["target_results"] if t["target_id"] == "TPEX:6488" and t.get("source_family") == "TPEX_OPENAPI")
    assert target["status"] == "failed"
    assert target["reason_code"] == "missing_required_fields"


def test_rejected_projection_and_diagnostics_are_bounded_and_raw_free():
    raw = {"symbol": "2330", "reason_code": "duplicate_identity", "field_validation": {}, "full_row": {"secret": "not-for-result"}}
    result = {
        "source_id": "TWSE_OPENAPI", "endpoint_contract_id": "twse_contract",
        "source_status": "success", "batch_status": "partial_source_success",
        "row_count_received": 2, "row_count_examined": 2, "row_count_retained": 1,
        "row_count_rejected": 1, "reported_trade_dates": ["2026-10-15"],
        "observations": [], "rejected_rows": [raw], "caveats": ["x"], "http_status": 200,
    }
    projected = executor._project_eod_diagnostics(result)
    assert projected["rejection_reason_codes"] == ["duplicate_identity"]
    assert projected["rejected_rows"] == [{"symbol": "2330", "reason_code": "duplicate_identity", "invalid_fields": []}]
    assert "full_row" not in json.dumps(projected)
