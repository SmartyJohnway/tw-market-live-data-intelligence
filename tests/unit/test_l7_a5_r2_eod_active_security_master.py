from __future__ import annotations

import copy
import json
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import m8r_06_03_production_adapter as adapter
from scripts import m8r_06_01c2_mode_a_security_master_loader as loader
from scripts import m8a_official_eod_instrument_classifier as classifier
from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_08g_identity_service import TaiwanMarketIdentityService


def record(market, code):
    return {
        "canonical_target_id": f"{market}:{code}",
        "identity": {"security_code": code, "isin": f"TW{code}".ljust(12, "0")},
        "classification": {"market": market, "instrument_family": "company_share", "instrument_type": "common_share"},
        "lifecycle": {"state": "listed", "resolution_status": "resolved", "events": []},
        "execution_eligibility": {"status": "allowed", "reason_codes": []},
    }


def runtime(records, release_id="synthetic-active-release", manifest_hash="a" * 64):
    return SimpleNamespace(
        identity_service=TaiwanMarketIdentityService(records, release_id=release_id, manifest_hash=manifest_hash),
        lookup={"not_a_legacy_classifier_lookup": True},
    )


def request(market, code, number=0):
    return {
        "operation_id": f"offline-operation-{number}",
        "execution_request_id": f"offline-request-{number}",
        "execution_request_hash": "b" * 64,
        "executor_id": adapter.EXECUTOR_ID,
        "capability_id": "official_eod_reference",
        "market": market,
        "batch_group_id": "offline-batch",
        "network_authorized": True,
        "approved_security_identifiers": [f"{market}:{code}"],
        "timeout_seconds": 15,
    }


@pytest.fixture(autouse=True)
def no_network_or_repository_seed(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("R2 attempted network or repository classification fallback")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(classifier, "build_security_master_lookup", forbidden)


def dispatch(market, codes, shape, tmp_path):
    registration = adapter.build_production_runtime_adapter_registry().get_route(
        adapter.EXECUTOR_ID, "official_eod_reference", market
    )
    requests = tuple(request(market, code, i) for i, code in enumerate(codes))
    context = DispatchRuntimeContext(str(tmp_path), "execute-approved")
    if shape == "single":
        return [registration.adapter(requests[0], context)]
    return registration.batch_adapter(requests, context)


@pytest.mark.parametrize("market,codes", [("TWSE", ["2330", "1101"]), ("TPEX", ["6488", "5347"])])
@pytest.mark.parametrize("shape", ["single", "batch"])
def test_registered_eod_routes_receive_target_bounded_active_projection(monkeypatch, tmp_path, market, codes, shape):
    selected = runtime([record(market, code) for code in [*codes, "9999"]])
    loads, calls = [], []
    def load():
        loads.append(True)
        return selected
    monkeypatch.setattr(loader, "get_production_mode_a_security_master", load)
    approved = codes[:1] if shape == "single" else codes
    legacy_market = classifier.normalize_market(market)
    def source(symbols, *, timeout, security_master):
        calls.append((symbols, timeout, security_master))
        assert set(security_master) == {(legacy_market, code) for code in approved}
        observations = []
        for code in symbols:
            classification = classifier.classify_official_eod_instrument(market, code, security_master)
            assert classification["instrument_type"] == "equity"
            assert classification["classification_status"] == "classified"
            assert classification["coverage_mode"] == "canonical_security_master"
            assert classification["production_classification_completeness"] == "complete"
            assert classification["canonical_instrument_family"] == "company_share"
            assert classification["canonical_instrument_type"] == "common_share"
            assert classification["canonical_target_id"] == f"{market}:{code}"
            assert classification["release_id"] == "synthetic-active-release"
            assert classification["release_manifest_sha256"] == "a" * 64
            assert classification["execution_eligibility"]["status"] == "allowed"
            observations.append({"symbol": code, "instrument_classification": classification})
        return {"source_id": market + "_OPENAPI", "observations": observations}
    monkeypatch.setattr(adapter, "execute_twse_official_eod_adapter" if market == "TWSE" else "execute_tpex_official_eod_adapter", source)
    results = dispatch(market, approved, shape, tmp_path)
    assert loads == [True]
    assert len(calls) == 1
    assert calls[0][:2] == (approved, 15)
    assert all(result["status"] == "succeeded" for result in results)
    for result in results:
        artifact = json.loads((tmp_path / result["evidence_artifacts"][0]["relative_path"]).read_text(encoding="utf-8"))
        assert artifact["records"][0]["instrument_classification"]["release_id"] == "synthetic-active-release"


@pytest.mark.parametrize("shape", ["single", "batch"])
@pytest.mark.parametrize("reason", ["NOT_INITIALIZED", "active_pointer_binding_mismatch", "release_integrity_invalid"])
def test_unavailable_active_authority_never_calls_source(monkeypatch, tmp_path, shape, reason):
    def unavailable():
        raise loader.ModeASecurityMasterUnavailable(reason)
    monkeypatch.setattr(loader, "get_production_mode_a_security_master", unavailable)
    calls = []
    monkeypatch.setattr(adapter, "execute_twse_official_eod_adapter", lambda *_args, **_kwargs: calls.append(True))
    with pytest.raises(OrchestrationError, match="official_eod_active_security_master_unavailable"):
        dispatch("TWSE", ["2330"], shape, tmp_path)
    assert calls == []


@pytest.mark.parametrize("shape", ["single", "batch"])
@pytest.mark.parametrize("failure", ["identity_service_absent", "not_found", "ambiguous", "canonical", "market", "code", "family", "type", "blocked", "manifest", "malformed_classification"])
def test_invalid_authority_fails_before_source(monkeypatch, tmp_path, shape, failure):
    selected = copy.deepcopy(record("TWSE", "2330"))
    result = SimpleNamespace(status="resolved", selected=selected)
    service = SimpleNamespace(release_id="synthetic-active-release", manifest_hash="a" * 64, resolve=lambda _target: result)
    if failure in {"not_found", "ambiguous"}:
        result.status, result.selected = failure, None
    elif failure == "canonical": selected["canonical_target_id"] = "TWSE:9999"
    elif failure == "market": selected["classification"]["market"] = "TPEX"
    elif failure == "code": selected["identity"]["security_code"] = "9999"
    elif failure == "family": selected["classification"]["instrument_family"] = "fund"
    elif failure == "type": selected["classification"]["instrument_type"] = "etf"
    elif failure == "blocked": selected["execution_eligibility"]["status"] = "blocked"
    elif failure == "manifest": service.manifest_hash = "invalid"
    elif failure == "malformed_classification": selected["classification"] = ["invalid"]
    active = SimpleNamespace(identity_service=None if failure == "identity_service_absent" else service)
    monkeypatch.setattr(loader, "get_production_mode_a_security_master", lambda: active)
    calls = []
    monkeypatch.setattr(adapter, "execute_twse_official_eod_adapter", lambda *_args, **_kwargs: calls.append(True))
    with pytest.raises(OrchestrationError, match="official_eod_"):
        dispatch("TWSE", ["2330"], shape, tmp_path)
    assert calls == []


def test_existing_process_lifetime_selection_is_preserved(monkeypatch):
    first = runtime([record("TWSE", "2330")], release_id="first-active")
    second = runtime([record("TWSE", "2330")], release_id="later-active")
    current, loads = [first], []
    def load(**_kwargs):
        loads.append(True)
        return current[0]
    loader.reset_production_mode_a_security_master_for_tests()
    monkeypatch.setattr(loader, "load_active_mode_a_security_master", load)
    try:
        a = adapter._official_eod_security_master_projection("TWSE", ["2330"])
        current[0] = second
        b = adapter._official_eod_security_master_projection("TWSE", ["2330"])
        assert a[("listed", "2330")]["release_id"] == b[("listed", "2330")]["release_id"] == "first-active"
        assert loads == [True]
    finally:
        loader.reset_production_mode_a_security_master_for_tests()


@pytest.mark.parametrize("market,codes", [("TWSE", ["2330", "1101"]), ("TPEX", ["6488", "5347"])])
def test_batch_validates_every_target_before_any_source_call(monkeypatch, tmp_path, market, codes):
    records = [record(market, code) for code in codes]
    records[1]["execution_eligibility"] = {"status": "blocked", "reason_codes": ["synthetic_block"]}
    active = runtime(records)
    monkeypatch.setattr(loader, "get_production_mode_a_security_master", lambda: active)
    calls = []
    name = "execute_twse_official_eod_adapter" if market == "TWSE" else "execute_tpex_official_eod_adapter"
    monkeypatch.setattr(adapter, name, lambda *_args, **_kwargs: calls.append(True))
    with pytest.raises(OrchestrationError, match="official_eod_execution_ineligible"):
        dispatch(market, codes, "batch", tmp_path)
    assert calls == []


@pytest.mark.parametrize("market,code,fixture_name,module_name,fetch_name", [
    ("TWSE", "2330", "twse_normal_rows.json", "scripts.m8a_twse_official_eod_adapter", "fetch_twse_official_eod_json"),
    ("TPEX", "8069", "tpex_normal_rows.json", "scripts.m8a_tpex_official_eod_adapter", "fetch_tpex_official_eod_json"),
])
def test_real_eod_parser_preserves_active_classification_provenance(
    monkeypatch, tmp_path, market, code, fixture_name, module_name, fetch_name
):
    import importlib
    source_module = importlib.import_module(module_name)
    active = runtime([record(market, code)])
    monkeypatch.setattr(loader, "get_production_mode_a_security_master", lambda: active)
    rows = json.loads((Path(__file__).resolve().parents[1] / "fixtures/m8a_official_eod" / fixture_name).read_text(encoding="utf-8"))
    calls = []
    def fetch(*, timeout):
        calls.append(timeout)
        return rows, 200, "application/json"
    monkeypatch.setattr(source_module, fetch_name, fetch)
    result = dispatch(market, [code], "single", tmp_path)[0]
    assert result["status"] == "succeeded"
    assert calls == [15]
    artifact = json.loads((tmp_path / result["evidence_artifacts"][0]["relative_path"]).read_text(encoding="utf-8"))
    classification = artifact["records"][0]["field_validation"]["instrument_classification"]
    assert classification["instrument_type"] == "equity"
    assert classification["release_id"] == "synthetic-active-release"
    assert classification["release_manifest_sha256"] == "a" * 64
    assert classification["coverage_mode"] == "canonical_security_master"
