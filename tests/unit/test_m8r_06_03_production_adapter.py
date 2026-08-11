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


def _request(capability_id: str, market: str) -> dict:
    return {
        "operation_id": "umeop-op-v1-00000000000000000000",
        "execution_request_id": "umereq-v1-00000000000000000000",
        "execution_request_hash": "0" * 64,
        "executor_id": "m8r_03d_watchlist_controlled_executor_adapter",
        "capability_id": capability_id,
        "market": market,
        "approved_security_identifiers": [f"{market}:2330"],
        "approved_security_types": ["equity"],
        "batch_group_id": "umeop-batch-v1-00000000000000000000",
        "network_authorized": True,
        "timeout_seconds": 15,
    }


def test_production_metadata_materializes_exactly_four_route_aware_adapters():
    metadata = load_production_executor_metadata()
    registry = build_production_runtime_adapter_registry()

    assert len(metadata["executors"]) == 4
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
