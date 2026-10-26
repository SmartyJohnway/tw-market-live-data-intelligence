"""R3 diagnostic fidelity from synthetic bytes only; no historical body reconstruction."""
from __future__ import annotations
import copy
import hashlib
import json
import socket
from types import SimpleNamespace

import pytest

from tests.unit.test_phase_i_i3_a4_candidate import _request, _bytes, _telemetry
from server.services.phase_i_i3_cash_institutional_flow_adapters import load_frozen_contract, prepare_market_source
from server.services.phase_i_i3_cash_institutional_flow_production_candidate import (
    production_operation_adapter_candidate, production_batch_operation_adapter_candidate,
)
from server.services.phase_i_i3_production_transport import Acquisition, AcquisitionError

PREFIX = "source preparation failed: "
PRIVATE = "SYNTHETIC_PROVIDER_TEXT_MUST_NOT_LEAK"


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*_args, **_kwargs):
        pytest.fail("R3 external network is forbidden")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


def encoded(value):
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def run(tmp_path, market, body, *, code=None, acquire=None):
    code = code or ("1101" if market == "TWSE" else "5347")
    calls = []
    def injected(requested_market, *, resolved_source_trade_date=None):
        calls.append((requested_market, resolved_source_trade_date))
        return Acquisition(body, _telemetry(market, body))
    result = production_operation_adapter_candidate(
        _request(market, code), SimpleNamespace(mode="execute-approved", governed_output_root=str(tmp_path)),
        acquire=acquire or injected,
    )
    artifact = tmp_path / result["evidence_artifacts"][0]["relative_path"]
    evidence = json.loads(artifact.read_text(encoding="utf-8"))
    assert evidence["transport"]["raw_payload_persisted"] is False
    assert list(tmp_path.rglob("*.*")) == [artifact]
    assert PRIVATE not in artifact.read_text(encoding="utf-8")
    return result, evidence, artifact, calls


def invalid_body(market, case):
    root = json.loads(_bytes(market))
    source = load_frozen_contract()["sources"][market]
    if case == "twse_root_invalid":
        return encoded({"stat": PRIVATE, "title": PRIVATE, "notes": PRIVATE})
    if case == "tpex_root_invalid":
        return encoded({"provider_notes": PRIVATE})
    if case == "duplicate_json_key":
        return b'{"date":"20260930","date":"20260930"}'
    if case == "twse_fields_invalid":
        root["fields"].append(root["fields"][0])
    elif case == "twse_row_width_invalid":
        root["data"][0].pop()
    elif case in {"required_security_code_missing", "required_source_fields_missing"}:
        key = source["code_field"] if case == "required_security_code_missing" else source["required_common_core"]["foreign_and_mainland_excluding_foreign_dealer"]["buy_shares"][0]
        index = root["fields"].index(key)
        root["fields"].pop(index)
        for row in root["data"]:
            row.pop(index)
    elif case == "twse_governed_source_date_mismatch":
        root["date"] = "20261001"
    elif case == "required_integer_invalid":
        key = source["required_common_core"]["foreign_and_mainland_excluding_foreign_dealer"]["buy_shares"][0]
        if market == "TWSE":
            root["data"][0][root["fields"].index(key)] = PRIVATE
        else:
            root[0][key] = PRIVATE
    return encoded(root)


@pytest.mark.parametrize("market,reason", [
    ("TWSE", "twse_root_invalid"), ("TWSE", "twse_fields_invalid"),
    ("TWSE", "twse_row_width_invalid"), ("TWSE", "required_security_code_missing"),
    ("TWSE", "required_source_fields_missing"), ("TWSE", "twse_governed_source_date_mismatch"),
    ("TWSE", "required_integer_invalid"), ("TWSE", "duplicate_json_key"),
    ("TPEX", "tpex_root_invalid"), ("TPEX", "required_integer_invalid"),
])
def test_canonical_normalization_reason_survives_in_caveat_and_warning(tmp_path, market, reason):
    body = invalid_body(market, reason)
    prepared = prepare_market_source(market, body, twse_governed_source_date="20260930" if market == "TWSE" else None, contract=load_frozen_contract())
    assert prepared.error_code == reason
    result, evidence, _, calls = run(tmp_path, market, body)
    diagnostic = PREFIX + reason
    assert result["status"] == "failed" and result["error_code"] == "source_failed"
    assert evidence["status"] == "source_failed" and evidence["error_code"] == "source_failed"
    assert evidence["caveats"] == ["publication finality and currentness are unknown", diagnostic]
    assert result["warnings"] == evidence["caveats"]
    assert calls == [(market, "2026-09-30" if market == "TWSE" else None)]


@pytest.mark.parametrize("market,baseline_sha,total", [
    ("TWSE", "a8aaa0c680aa76053fad5cc8b093ef0d2dbc44b2ba7c8b771807a9744d8d3bc2", 140),
    ("TPEX", "d33caa3093c2fa86874d8af306652dd255ecef5730b833a3f24e924c0e53521d", 120),
])
def test_success_bytes_numbers_and_citations_match_pre_repair_baseline(tmp_path, market, baseline_sha, total):
    result, evidence, artifact, _ = run(tmp_path, market, _bytes(market))
    # Hashes captured from exact pre-R3 implementation e98dba73 with these synthetic inputs.
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == baseline_sha
    assert result["status"] == "succeeded" and evidence["status"] == "complete"
    assert not any(c.startswith(PREFIX) for c in evidence["caveats"])
    assert evidence["institutional_total_net_shares"] == total
    assert evidence["foreign_and_mainland_excluding_foreign_dealer"] == {"buy_shares": 100, "sell_shares": 40, "net_shares": 60}
    assert evidence["citation_ids"] == ["cite-933378393d521610"]


@pytest.mark.parametrize("market", ["TWSE", "TPEX"])
@pytest.mark.parametrize("error", ["transport_error", "http_error", "unsupported_content_type", "response_read_failed", "response_byte_limit_exceeded"])
def test_acquisition_failure_keeps_telemetry_without_normalization_caveat(tmp_path, market, error):
    body = _bytes(market)
    telemetry = _telemetry(market, body)
    telemetry.update(complete_body_received=False, response_byte_count=0, response_sha256=None,
                     http_status=503 if error == "http_error" else None, error_code=error, failure_phase="acquisition")
    calls = []
    def fail(*args, **kwargs):
        calls.append(True)
        raise AcquisitionError(error, copy.deepcopy(telemetry))
    result, evidence, _, _ = run(tmp_path, market, body, acquire=fail)
    assert calls == [True]
    assert result["status"] == "failed" and evidence["status"] == "source_failed"
    assert result["error_code"] == evidence["error_code"] == error
    assert evidence["transport"] == {k: v for k, v in telemetry.items() if k not in {"retrieved_at", "resolved_source_trade_date"}}
    assert not any(c.startswith(PREFIX) for c in evidence["caveats"] + result["warnings"])


@pytest.mark.parametrize("market", ["TWSE", "TPEX"])
@pytest.mark.parametrize("matches", [0, 2])
def test_binding_failure_does_not_gain_normalization_caveat(tmp_path, market, matches):
    root = json.loads(_bytes(market))
    code = "1101" if market == "TWSE" else "5347"
    if matches == 0:
        code = "9999"
    elif market == "TWSE":
        index = root["fields"].index(load_frozen_contract()["sources"][market]["code_field"])
        root["data"].append(copy.deepcopy(next(row for row in root["data"] if row[index] == code)))
    else:
        key = load_frozen_contract()["sources"][market]["code_field"]
        root.append(copy.deepcopy(next(row for row in root if row[key] == code)))
    result, evidence, _, _ = run(tmp_path, market, encoded(root), code=code)
    assert result["status"] == "failed" and result["error_code"] == "binding_failed"
    assert evidence["status"] == evidence["error_code"] == "binding_failed"
    assert not any(c.startswith(PREFIX) for c in evidence["caveats"] + result["warnings"])


def test_same_market_batch_retains_reason_for_each_target_with_one_acquisition(tmp_path):
    body = invalid_body("TWSE", "twse_root_invalid")
    requests = [_request("TWSE", "1101", 1), _request("TWSE", "1102", 2)]
    requests[1]["batch_group_id"] = requests[0]["batch_group_id"]
    calls = []
    def acquire(*args, **kwargs):
        calls.append(True)
        return Acquisition(body, _telemetry("TWSE", body))
    results = production_batch_operation_adapter_candidate(requests, SimpleNamespace(mode="execute-approved", governed_output_root=str(tmp_path)), acquire=acquire)
    assert calls == [True] and len(results) == 2
    for result in results:
        evidence = json.loads((tmp_path/result["evidence_artifacts"][0]["relative_path"]).read_text(encoding="utf-8"))
        assert evidence["error_code"] == result["error_code"] == "source_failed"
        assert evidence["caveats"] == result["warnings"] == ["publication finality and currentness are unknown", PREFIX + "twse_root_invalid"]
