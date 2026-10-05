"""Offline-only production-evidence V2 and dormant I3 executor candidate tests."""
import hashlib
import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from server.services.phase_i_i3_cash_institutional_flow_adapters import ROOT, validate_evidence
from server.services.phase_i_i3_cash_institutional_flow_v2_evidence import validate_evidence_v2
from server.services.phase_i_i3_cash_institutional_flow_production_candidate import (
    EXECUTOR_ID, build_i3_production_candidate_registrations, production_batch_operation_adapter_candidate,
)
from server.services.phase_i_i3_production_transport import Acquisition, AcquisitionError, acquire_once, fixed_url

FIXTURES = ROOT / "tests/fixtures/phase_i_i3_a0"
V1_SCHEMA = json.loads((ROOT / "schemas/cash_institutional_flow_context_evidence.v1.schema.json").read_text())
V2_SCHEMA = json.loads((ROOT / "schemas/cash_institutional_flow_context_evidence.v2.schema.json").read_text())


@pytest.fixture(autouse=True)
def deny_external_sockets(monkeypatch):
    def denied(*_args, **_kwargs):
        raise AssertionError("i3_a4_market_network_forbidden_in_tests")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


def _request(market, code, number=1):
    params = {"resolved_source_trade_date": "2026-09-30"} if market == "TWSE" else {}
    return {
        "schema_version": "unified_market_evidence_execution_request.v3",
        "execution_request_id": "umereq-v3-" + f"{number:020x}",
        "execution_request_hash": f"{number:064x}",
        "operation_id": "umeop-op-v1-" + f"{number:020x}",
        "batch_group_id": "umeop-batch-v1-" + f"{number:020x}",
        "authorization_id": "auth", "authorization_hash": "a" * 64, "plan_hash": "b" * 64,
        "market": market, "capability_id": "cash_institutional_flow_context", "executor_id": EXECUTOR_ID,
        "network_authorized": True, "timeout_seconds": 30, "maximum_records": 50,
        "approved_security_identifiers": [f"{market}:{code}"], "parameters": params,
    }


def _bytes(market):
    if market == "TWSE":
        data = json.loads((FIXTURES / "twse_synthetic.json").read_text(encoding="utf-8"))
        return json.dumps(data, ensure_ascii=False).encode()
    data = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_a"]
    return json.dumps(data, ensure_ascii=False).encode()


def _telemetry(market, body):
    return {"mode": "official_https_live", "network_get_count": 1, "retry_count": 0,
            "http_status": 200, "content_type": "application/json", "complete_body_received": True,
            "response_byte_count": len(body), "partial_response_byte_count": 0,
            "response_sha256": hashlib.sha256(body).hexdigest(),
            "tls_policy": "compatibility" if market == "TWSE" else "strict",
            "redirect_policy": "reject", "raw_payload_persisted": False,
            "retrieved_at": "2026-10-04T12:00:00Z", "failure_phase": None, "error_code": None}


class _Response:
    status = 200
    def __init__(self, body, *, content_type="application/json", content_length=None):
        self.body = body
        self.offset = 0
        self.headers = {"Content-Type": content_type}
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)
    def getcode(self):
        return self.status
    def read(self, size):
        chunk = self.body[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk
    def close(self):
        pass


class _Opener:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.calls = response, error, []
    def open(self, request, timeout):
        self.calls.append((request.full_url, timeout))
        if self.error:
            raise self.error
        return self.response


def test_v1_is_immutable_historical_offline_contract():
    body = (ROOT / "schemas/cash_institutional_flow_context_evidence.v1.schema.json").read_bytes()
    assert hashlib.sha256(body).hexdigest() == "3be9a0ca3cf0e0bb5badb427231d47ce86fdb604ae28cb31582b0f9612c76f7c"
    # A real V1 fixture validates, but production transport is outside its schema.
    from server.services.phase_i_i3_cash_institutional_flow_offline_candidate import run_i3_candidate_offline_batch
    target = {"market": "TWSE", "security_code": "1101", "canonical_target_id": "TWSE:1101",
              "instrument_family": "company_share", "instrument_type": "common_share", "execution_eligibility": "allowed",
              "operation_id": "offline", "execution_request_id": "umereq-v2-" + "1" * 20, "execution_request_hash": "1" * 64}
    historical = run_i3_candidate_offline_batch([target], source_payloads={"TWSE": _bytes("TWSE")},
        retrieved_at_by_market={"TWSE": "2026-10-04T12:00:00Z"}, twse_governed_source_date="20260930")
    evidence = json.loads(next(iter(historical["artifact_bytes"].values())))
    assert not list(Draft202012Validator(V1_SCHEMA).iter_errors(evidence))
    productionized = dict(evidence)
    productionized["transport"] = {**evidence["transport"], "mode": "official_https_live", "network_get_count": 1}
    assert list(Draft202012Validator(V1_SCHEMA).iter_errors(productionized))


@pytest.mark.parametrize("market,code", [("TWSE", "1101"), ("TPEX", "5347")])
def test_v2_candidate_emits_live_provenance_without_market_io(tmp_path, market, code):
    body = _bytes(market)
    acquisition = Acquisition(body, _telemetry(market, body))
    calls = []
    def fake_acquire(got_market, *, resolved_source_trade_date=None):
        calls.append((got_market, resolved_source_trade_date))
        return acquisition
    req = _request(market, code)
    output = production_batch_operation_adapter_candidate([req], SimpleNamespace(mode="execute-approved", governed_output_root=str(tmp_path)), acquire=fake_acquire)
    assert calls == [(market, "2026-09-30" if market == "TWSE" else None)]
    result = output[0]
    assert (result["status"], result["evidence_contract"]) == ("succeeded", "cash_institutional_flow_context_evidence.v2")
    artifact_path = tmp_path / result["evidence_artifacts"][0]["relative_path"]
    evidence = json.loads(artifact_path.read_text(encoding="utf-8"))
    validate_evidence_v2(evidence)
    assert evidence["status"] == "complete"
    assert evidence["transport"]["network_get_count"] == 1
    assert evidence["transport"]["retry_count"] == 0
    assert evidence["transport"]["response_sha256"] == hashlib.sha256(body).hexdigest()
    assert evidence["transport"]["response_byte_count"] == len(body)
    assert evidence["transport"]["raw_payload_persisted"] is False
    assert evidence["unit"] == "share"
    assert evidence["publication_finality"] == evidence["currentness_status"] == "unknown"
    for key, value in (("mode", "offline_injected_fixture"), ("network_get_count", 0), ("raw_payload_persisted", True)):
        corrupted = json.loads(json.dumps(evidence))
        corrupted["transport"][key] = value
        with pytest.raises(ValueError):
            validate_evidence_v2(corrupted)
    corrupted = json.loads(json.dumps(evidence))
    corrupted["transport"]["complete_body_received"] = False
    with pytest.raises(ValueError):
        validate_evidence_v2(corrupted)
    corrupted = json.loads(json.dumps(evidence))
    corrupted["source_reported_trade_date"] = "2026-10-01"
    with pytest.raises(ValueError, match="lineage_mismatch|bound_date_mismatch"):
        validate_evidence_v2(corrupted)


def test_v2_rejects_offline_mode_zero_dispatch_and_date_mismatch():
    body = _bytes("TWSE")
    # Construct from the pure A2 result then prove it is not automatically a V2 artifact.
    from server.services.phase_i_i3_cash_institutional_flow_offline_candidate import run_i3_candidate_offline_batch
    target = {"market": "TWSE", "security_code": "1101", "canonical_target_id": "TWSE:1101",
              "instrument_family": "company_share", "instrument_type": "common_share", "execution_eligibility": "allowed",
              "operation_id": "offline", "execution_request_id": "umereq-v2-" + "1" * 20, "execution_request_hash": "1" * 64}
    v1 = run_i3_candidate_offline_batch([target], source_payloads={"TWSE": body},
        retrieved_at_by_market={"TWSE": "2026-10-04T12:00:00Z"}, twse_governed_source_date="20260930")
    offline = json.loads(next(iter(v1["artifact_bytes"].values())))
    with pytest.raises(ValueError):
        validate_evidence_v2(offline)


def test_transport_fixed_endpoints_and_single_dispatch_fake_opener():
    assert fixed_url("TWSE", "2026-09-30").endswith("date=20260930&selectType=ALLBUT0999&response=json")
    assert fixed_url("TPEX") == "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading"
    with pytest.raises(ValueError):
        fixed_url("TWSE")
    opener = _Opener(_Response(b"[]", content_length=2))
    result = acquire_once("TPEX", opener=opener, clock=lambda: datetime(2026, 10, 4, tzinfo=timezone.utc))
    assert len(opener.calls) == 1
    assert result.body == b"[]"
    assert result.telemetry["network_get_count"] == 1 and result.telemetry["retry_count"] == 0
    assert result.telemetry["complete_body_received"] is True


def test_candidate_registry_has_two_dormant_routes_default_registry_stays_zero():
    from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    candidate_registry = RuntimeAdapterRegistry(build_i3_production_candidate_registrations())
    assert len(candidate_registry.routes_for_executor(EXECUTOR_ID)) == 2
    assert not build_production_runtime_adapter_registry().routes_for_executor(EXECUTOR_ID)


def test_i3_roll_001_restores_baseline_without_disturbing_i1_i2_or_mcp():
    from scripts.phase_i_i3_a4_rollback_proof import prove_i3_rollback
    result = prove_i3_rollback()
    assert result["status"] == "PASS"
    assert (result["i3_active_sources"], result["i3_routes"], result["i3_executor_reachable"], result["i3_public_v3_support"]) == (0, 0, False, False)
    assert (result["i1_active_sources"], result["i1_routes"], result["i2_active_sources"], result["i2_routes"], result["mcp_tool_count"]) == (3, 2, 1, 1, 6)


def test_transport_rejects_partial_body_without_hash_or_retry():
    class ResetResponse(_Response):
        def read(self, size):
            if self.offset:
                raise ConnectionResetError("fixture")
            self.offset = 1
            return b"["
    opener = _Opener(ResetResponse(b"[]"))
    with pytest.raises(AcquisitionError) as caught:
        acquire_once("TPEX", opener=opener, clock=lambda: datetime(2026, 10, 4, tzinfo=timezone.utc))
    assert len(opener.calls) == 1
    assert caught.value.telemetry["complete_body_received"] is False
    assert caught.value.telemetry["response_byte_count"] == 0
    assert caught.value.telemetry["response_sha256"] is None
    assert caught.value.telemetry["partial_response_byte_count"] == 1
    assert caught.value.telemetry["retry_count"] == 0


def test_transport_rejects_declared_oversize_and_content_length_mismatch():
    oversized = _Opener(_Response(b"[]", content_length=4 * 1024 * 1024 + 1))
    with pytest.raises(AcquisitionError, match="response_byte_limit_exceeded"):
        acquire_once("TPEX", opener=oversized, clock=lambda: datetime(2026, 10, 4, tzinfo=timezone.utc))
    assert len(oversized.calls) == 1 and oversized.response.offset == 0
    mismatch = _Opener(_Response(b"[]", content_length=3))
    with pytest.raises(AcquisitionError, match="content_length_mismatch"):
        acquire_once("TPEX", opener=mismatch, clock=lambda: datetime(2026, 10, 4, tzinfo=timezone.utc))
    assert len(mismatch.calls) == 1
    assert mismatch.response.offset == 2


@pytest.mark.parametrize("failure,declared,partial,error", [
    ("response_headers", 4 * 1024 * 1024 + 777, 0, "response_byte_limit_exceeded"),
    ("response_body_read", None, 4 * 1024 * 1024 + 1, "response_byte_limit_exceeded"),
    ("response_body_read", 10, 7, "content_length_mismatch"),
])
def test_transport_failure_evidence_is_schema_valid_and_truthful(tmp_path, failure, declared, partial, error):
    body = _bytes("TPEX")
    telemetry = _telemetry("TPEX", body)
    telemetry.update(complete_body_received=False, response_byte_count=0, partial_response_byte_count=partial,
                     response_sha256=None, failure_phase=failure, error_code=error)
    telemetry["http_status"] = 200
    telemetry["content_type"] = "application/json"
    telemetry["declared_content_length"] = declared
    telemetry["retrieved_at"] = "2026-10-04T12:00:00Z"

    def fail_acquire(_market, *, resolved_source_trade_date=None):
        assert resolved_source_trade_date is None
        raise AcquisitionError(error, telemetry)

    request = _request("TPEX", "5347")
    results = production_batch_operation_adapter_candidate([request],
        SimpleNamespace(mode="execute-approved", governed_output_root=str(tmp_path)), acquire=fail_acquire)
    assert len(results) == 1 and results[0]["status"] == "failed"
    evidence_path = tmp_path / results[0]["evidence_artifacts"][0]["relative_path"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    validate_evidence_v2(evidence)
    assert evidence["status"] == "source_failed"
    transport = evidence["transport"]
    assert transport["network_get_count"] == 1 and transport["retry_count"] == 0
    assert transport["complete_body_received"] is False
    assert transport["declared_content_length"] == declared
    assert transport["response_byte_count"] == 0 and transport["response_sha256"] is None
    assert transport["partial_response_byte_count"] == partial
    assert transport["error_code"] == error and transport["raw_payload_persisted"] is False


def test_twse_batch_date_binding_uses_parameters_not_top_level_fields(tmp_path):
    from server.services.phase_i_i3_cash_institutional_flow_production_candidate import _validate_batch
    requests = [_request("TWSE", "1101", 1), _request("TWSE", "2330", 2)]
    shared = "umeop-batch-v1-" + "3" * 20
    for item in requests:
        item["batch_group_id"] = shared
        item["resolved_source_trade_date"] = "2099-12-31"  # ignored legacy/top-level field
    _validate_batch(requests, SimpleNamespace(mode="execute-approved"))
    observed = []
    body = _bytes("TWSE")
    acquisition = Acquisition(body, _telemetry("TWSE", body))
    outcomes = production_batch_operation_adapter_candidate(requests,
        SimpleNamespace(mode="execute-approved", governed_output_root=str(tmp_path)),
        acquire=lambda market, *, resolved_source_trade_date=None:
            observed.append((market, resolved_source_trade_date)) or acquisition)
    assert observed == [("TWSE", "2026-09-30")]
    assert len(outcomes) == 2
    requests[1]["parameters"]["resolved_source_trade_date"] = "2026-10-01"
    with pytest.raises(Exception, match="i3_batch_binding_mismatch"):
        _validate_batch(requests, SimpleNamespace(mode="execute-approved"))
