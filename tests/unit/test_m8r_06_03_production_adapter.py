from __future__ import annotations

import json

from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext
from scripts.m8r_06_03_production_adapter import (
    build_production_runtime_adapter_registry,
    load_production_executor_metadata,
    production_batch_operation_adapter,
    production_executor_metadata_sha256,
    production_operation_adapter,
)


def _request(capability_id: str, market: str, *, executor_id: str = "m8r_03d_watchlist_controlled_executor_adapter", code: str = "2330") -> dict:
    return {
        "operation_id": "umeop-op-v1-00000000000000000000",
        "execution_request_id": "umereq-v1-00000000000000000000",
        "execution_request_hash": "0" * 64,
        "executor_id": executor_id,
        "capability_id": capability_id,
        "market": market,
        "approved_security_identifiers": [f"{market}:{code}"],
        "approved_security_types": ["equity"],
        "batch_group_id": "umeop-batch-v1-00000000000000000000",
        "network_authorized": True,
        "timeout_seconds": 15,
    }


def test_production_metadata_materializes_legacy_research_and_selected_h1_routes():
    metadata = load_production_executor_metadata()
    registry = build_production_runtime_adapter_registry()

    assert len(metadata["executors"]) == 9
    assert len(production_executor_metadata_sha256()) == 64
    for capability_id, market in (
        ("current_observation", "TWSE"),
        ("current_observation", "TPEX"),
        ("official_eod_reference", "TWSE"),
        ("official_eod_reference", "TPEX"),
    ):
        registration = registry.get_route("m8r_03d_watchlist_controlled_executor_adapter", capability_id, market)
        assert registration is not None
        assert registration.fake_adapter is False
    for capability_id, market in (
        ("material_disclosures", "TWSE"),
        ("material_disclosures", "TPEX"),
        ("monthly_revenue", "TWSE"),
        ("monthly_revenue", "TPEX"),
    ):
        registration = registry.get_route("phase_g_official_research_executor", capability_id, market)
        assert registration is not None
        assert registration.fake_adapter is False
    h1 = registry.get_route("phase_h_h1_tpex_attention_executor", "trading_status_context", "TPEX")
    assert h1 is not None
    assert h1.fake_adapter is False
    assert h1.network_required is True
    assert h1.batch_adapter is None


def test_selected_h1_tpex_attention_fetches_once_and_persists_only_target_bounded_artifacts(tmp_path, monkeypatch):
    rows = [
        {
            "Date": "2026-09-22",
            "SecuritiesCompanyCode": "6488",
            "CompanyName": "環球晶",
            "TradingInformation": "official attention entry",
            "ClosePrice": "100",
            "PriceEarningRatio": "20",
        },
        {
            "Date": "2026-09-22",
            "SecuritiesCompanyCode": "9999",
            "CompanyName": "other",
            "TradingInformation": "must not persist",
            "ClosePrice": "1",
            "PriceEarningRatio": "1",
        },
    ]
    calls = []
    def fake_fetch(url, *, timeout):
        calls.append((url, timeout))
        return json.dumps(rows, ensure_ascii=False).encode("utf-8")

    monkeypatch.setattr("scripts.m8r_06_03_production_adapter._fetch_official_payload", fake_fetch)
    request = _request(
        "trading_status_context", "TPEX",
        executor_id="phase_h_h1_tpex_attention_executor", code="6488"
    )
    result = production_operation_adapter(
        request, DispatchRuntimeContext(str(tmp_path), "execute-approved")
    )

    assert result["schema_version"] == "unified_market_evidence_operation_result.v2"
    assert result["status"] == "succeeded"
    assert calls == [("https://www.tpex.org.tw/openapi/v1/tpex_trading_warning_information", 15)]
    assert {item["artifact_role"] for item in result["evidence_artifacts"]} == {
        "primary_evidence", "supporting_governance"
    }
    primary = next(item for item in result["evidence_artifacts"] if item["artifact_role"] == "primary_evidence")
    evidence = json.loads((tmp_path / primary["relative_path"]).read_text(encoding="utf-8"))
    assert evidence["target"]["canonical_target_id"] == "TPEX:6488"
    assert evidence["source"]["activation_state"] == "active"
    assert evidence["status"] == "partial"
    assert evidence["coverage"]["covered_status_types"] == ["attention"]
    assert set(evidence["coverage"]["uncovered_status_types"]) == {
        "changed_trading_method", "disposition", "resumption", "suspension"
    }
    assert "must not persist" not in json.dumps(evidence, ensure_ascii=False)


def test_current_observation_adapter_uses_normalized_stub_and_writes_contained_artifact(tmp_path, monkeypatch):
    def fake_execute(_watchlist, **kwargs):
        assert kwargs["write_latest"] is False
        assert kwargs["allow_individual_fallback"] is False
        return {"observations": [{"schema_version": "m5k", "symbol": "2330"}]}

    monkeypatch.setattr("scripts.m8r_06_03_production_adapter.execute_live_observation", fake_execute)
    result = production_operation_adapter(
        _request("current_observation", "TWSE"),
        DispatchRuntimeContext(governed_output_root=str(tmp_path), mode="execute-approved"),
    )

    assert result["status"] == "succeeded"
    artifact = result["evidence_artifacts"][0]
    stored = json.loads((tmp_path / artifact["relative_path"]).read_text(encoding="utf-8"))
    assert stored["source_family"] == "TWSE_MIS"
    assert stored["records"] == [{"schema_version": "m5k", "symbol": "2330"}]


def test_official_eod_adapter_uses_exact_market_stub(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.m8r_06_03_production_adapter.execute_twse_official_eod_adapter",
        lambda symbols, *, timeout: {"source_id": "TWSE_OPENAPI", "observations": [{"symbol": symbols[0]}]},
    )
    result = production_operation_adapter(
        _request("official_eod_reference", "TWSE"),
        DispatchRuntimeContext(governed_output_root=str(tmp_path), mode="execute-approved"),
    )
    assert result["status"] == "succeeded"
    assert result["result_item_count"] == 1


def test_production_batch_current_observation_calls_source_once_and_fans_out(tmp_path, monkeypatch):
    calls = []

    def fake_execute(watchlist, **kwargs):
        calls.append(watchlist)
        assert kwargs["allow_individual_fallback"] is False
        return {"observations": [{"symbol": item["symbol"]} for item in watchlist["items"]]}

    monkeypatch.setattr("scripts.m8r_06_03_production_adapter.execute_live_observation", fake_execute)
    first, second = _request("current_observation", "TWSE"), _request("current_observation", "TWSE")
    second.update(operation_id="umeop-op-v1-00000000000000000001", execution_request_id="umereq-v1-00000000000000000001")
    second["approved_security_identifiers"] = ["TWSE:2317"]
    results = production_batch_operation_adapter((first, second), DispatchRuntimeContext(str(tmp_path), "execute-approved"))

    assert len(calls) == 1
    assert [item["status"] for item in results] == ["succeeded", "succeeded"]
    assert [item["result_item_count"] for item in results] == [1, 1]


def test_production_batch_partial_fanout_never_retries_missing_symbol(tmp_path, monkeypatch):
    calls = []

    def fake_execute(_watchlist, **_kwargs):
        calls.append(True)
        return {"observations": [{"symbol": "2330"}]}

    monkeypatch.setattr("scripts.m8r_06_03_production_adapter.execute_live_observation", fake_execute)
    first, second = _request("current_observation", "TWSE"), _request("current_observation", "TWSE")
    second.update(operation_id="umeop-op-v1-00000000000000000001", execution_request_id="umereq-v1-00000000000000000001")
    second["approved_security_identifiers"] = ["TWSE:2317"]
    result = production_batch_operation_adapter((first, second), DispatchRuntimeContext(str(tmp_path), "execute-approved"))
    assert calls == [True]
    assert [item["status"] for item in result] == ["succeeded", "failed"]


def test_production_batch_eod_uses_exact_market_once_and_fans_out(tmp_path, monkeypatch):
    calls = []

    def fake_execute(symbols, *, timeout):
        calls.append((symbols, timeout))
        return {"source_id": "TPEX_OPENAPI", "observations": [{"symbol": symbol} for symbol in symbols]}

    monkeypatch.setattr("scripts.m8r_06_03_production_adapter.execute_tpex_official_eod_adapter", fake_execute)
    first, second = _request("official_eod_reference", "TPEX"), _request("official_eod_reference", "TPEX")
    first["approved_security_identifiers"] = ["TPEX:5227"]
    second.update(operation_id="umeop-op-v1-00000000000000000001", execution_request_id="umereq-v1-00000000000000000001")
    second["approved_security_identifiers"] = ["TPEX:6488"]
    results = production_batch_operation_adapter((first, second), DispatchRuntimeContext(str(tmp_path), "execute-approved"))

    assert calls == [(["5227", "6488"], 15)]
    assert [item["status"] for item in results] == ["succeeded", "succeeded"]


def test_production_adapter_requires_execute_approved_and_network_authorization(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "scripts.m8r_06_03_production_adapter.execute_live_observation",
        lambda *_args, **_kwargs: calls.append(True),
    )
    request = _request("current_observation", "TWSE")

    import pytest
    from scripts.m8r_05b_03.errors import OrchestrationError

    with pytest.raises(OrchestrationError, match="production_execution_mode_required"):
        production_operation_adapter(request, DispatchRuntimeContext(str(tmp_path), "dry-run"))
    request["network_authorized"] = False
    with pytest.raises(OrchestrationError, match="network_required_not_authorized"):
        production_operation_adapter(request, DispatchRuntimeContext(str(tmp_path), "execute-approved"))
    assert calls == []


def test_research_material_disclosure_route_fetches_once_and_persists_only_target_evidence(tmp_path, monkeypatch):
    payload = (
        "出表日期,公司代號,公司名稱,發言日期,發言時間,主旨,符合條款,事實發生日,說明\n"
        "1150916,2330,台積電,1150915,065728,測試公告,1,1150914,內容\n"
        "1150916,2317,鴻海,1150915,065729,其他公告,1,1150914,不應保存\n"
    ).encode("utf-8")
    calls = []

    def fake_fetch(url, *, timeout):
        calls.append((url, timeout))
        return payload

    monkeypatch.setattr("scripts.m8r_06_03_production_adapter._fetch_official_payload", fake_fetch)
    request = _request("material_disclosures", "TWSE", executor_id="phase_g_official_research_executor")
    result = production_batch_operation_adapter(
        (request,), DispatchRuntimeContext(str(tmp_path), "execute-approved")
    )[0]

    assert result["status"] == "succeeded"
    assert len(calls) == 1
    evidence = json.loads((tmp_path / result["evidence_artifacts"][0]["relative_path"]).read_text(encoding="utf-8"))
    assert evidence["target"]["security_code"] == "2330"
    assert len(evidence["items"]) == 1
    assert "不應保存" not in json.dumps(evidence, ensure_ascii=False)


def test_research_monthly_revenue_route_uses_governed_json_fallback(tmp_path, monkeypatch):
    row = {
        "出表日期": "1150915", "資料年月": "11508", "公司代號": "6488", "公司名稱": "環球晶",
        "營業收入-當月營收": "100", "營業收入-上月營收": "90", "營業收入-去年當月營收": "80",
        "營業收入-上月比較增減(%)": "11.1", "營業收入-去年同月增減(%)": "25",
        "累計營業收入-當月累計營收": "800", "累計營業收入-去年累計營收": "700",
        "累計營業收入-前期比較增減(%)": "14.2", "備註": "官方備註",
    }
    calls = []

    def fake_fetch(url, *, timeout):
        calls.append((url, timeout))
        if url.endswith(".csv"):
            raise OSError("primary unavailable")
        return json.dumps([row], ensure_ascii=False).encode("utf-8")

    monkeypatch.setattr("scripts.m8r_06_03_production_adapter._fetch_official_payload", fake_fetch)
    request = _request(
        "monthly_revenue", "TPEX", executor_id="phase_g_official_research_executor", code="6488"
    )
    result = production_batch_operation_adapter(
        (request,), DispatchRuntimeContext(str(tmp_path), "execute-approved")
    )[0]

    assert result["status"] == "succeeded"
    assert len(calls) == 2
    evidence = json.loads((tmp_path / result["evidence_artifacts"][0]["relative_path"]).read_text(encoding="utf-8"))
    assert evidence["source"]["transport"] == "official_json_openapi"
    assert evidence["source"]["fallback_used"] is True
    assert evidence["value"]["currency"] == "TWD"


def test_research_adapter_fails_closed_before_network_for_route_target_market_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.m8r_06_03_production_adapter._fetch_official_payload",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network forbidden")),
    )
    request = _request("monthly_revenue", "TWSE", executor_id="phase_g_official_research_executor")
    request["approved_security_identifiers"] = ["TPEX:6488"]
    import pytest
    from scripts.m8r_05b_03.errors import OrchestrationError

    with pytest.raises(OrchestrationError, match="approved_target_market_mismatch"):
        production_batch_operation_adapter(
            (request,), DispatchRuntimeContext(str(tmp_path), "execute-approved")
        )
