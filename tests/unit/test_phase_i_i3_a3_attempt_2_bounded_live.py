"""TPEx-first Attempt 2 pre-network proof, with all market sockets denied."""
import hashlib
import io
import json
import socket
from urllib.error import URLError

import pytest

from scripts import run_phase_i_i3_a3_attempt_2_bounded_live_acceptance as attempt2
from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts import validate_phase_i_i3_a3_r1 as r1
from scripts.phase_i_i3_transport_mapping import transport_market_key

FIXTURES = a3.ROOT / "tests/fixtures/phase_i_i3_a0"
ZERO = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}


@pytest.fixture(autouse=True)
def deny_sockets(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("attempt_2_external_socket_forbidden")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


class Response:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, body):
        self.stream = io.BytesIO(body)

    def read(self, size):
        return self.stream.read(size)

    def close(self):
        self.stream.close()


class Opener:
    def __init__(self, market, body, calls, error=None):
        self.market, self.body, self.calls, self.error = market, body, calls, error

    def open(self, request, *, timeout):
        self.calls.append((self.market, request.full_url, timeout))
        if self.error is not None:
            raise self.error
        return Response(self.body)


def bodies():
    twse = json.loads((FIXTURES / "twse_synthetic.json").read_text(encoding="utf-8"))
    tpex = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_a"]
    return {"TWSE": json.dumps(twse, ensure_ascii=False).encode(),
            "TPEX": json.dumps(tpex, ensure_ascii=False).encode()}


def targets():
    return {m: {"canonical_target_id": f"{m}:{code}", "market": m,
                "security_code": code, "instrument_family": "company_share",
                "instrument_type": "common_share", "execution_eligibility": "allowed",
                "isin": "synthetic-test-only"}
            for m, code in (("TWSE", "1101"), ("TPEX", "5347"))}


def run_fake(monkeypatch, *, fail_market=None, fail_stage=None):
    raw = bodies()
    calls, opens = [], []
    dispatch = dict(ZERO)
    mapping = a3.transport_market_key

    if fail_stage == "pre_dispatch":
        def maybe_reject(market):
            if market == fail_market:
                raise ValueError("injected_pre_dispatch_rejection")
            return mapping(market)
        monkeypatch.setattr(a3, "transport_market_key", maybe_reject)

    def acquire(market):
        calls.append(market)
        opener = Opener(market, raw[market], opens,
                        URLError(ConnectionRefusedError(111, "refused"))
                        if fail_market == market and fail_stage == "open" else None)
        return a3.acquire_reviewed_source(
            market,
            on_http_dispatch=lambda: dispatch.__setitem__(market, dispatch[market] + 1),
            opener_factory=lambda *handlers: opener,
        )

    result, artifacts = attempt2.execute_with_acquirer(acquire, targets(), http_dispatch_count=dispatch)
    return result, artifacts, calls, opens, raw


def test_tpex_first_fake_transport_and_candidate_complete(monkeypatch):
    result, artifacts, calls, opens, raw = run_fake(monkeypatch)
    assert calls == ["TPEX", "TWSE"]
    assert [item[0] for item in opens] == ["TPEX", "TWSE"]
    assert all(url.startswith("https://") and timeout == 30 for _, url, timeout in opens)
    assert result["acquisition_callback_attempts"] == result["http_dispatch_count"] == {
        "TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other": 0}
    assert result["A3_decision"] == "PASS" and result["retry_count"] == 0
    assert result["candidate"]["network_calls"] == 0 and len(artifacts) == 2
    assert all(result["evidence"][market]["status"] == "complete" for market in ("TPEX", "TWSE"))
    assert result["raw_payload_persistence"] == "NONE"
    serialized = a3.json_bytes(result) + b"".join(artifacts.values())
    assert all(payload not in serialized for payload in raw.values())


@pytest.mark.parametrize("stage,expected_dispatch", [("pre_dispatch", 0), ("open", 1)])
def test_tpex_failure_stops_before_twse(monkeypatch, stage, expected_dispatch):
    result, artifacts, calls, opens, _ = run_fake(monkeypatch, fail_market="TPEX", fail_stage=stage)
    assert calls == ["TPEX"] and len(opens) == expected_dispatch
    assert result["acquisition_callback_attempts"] == {"TWSE": 0, "TPEX": 1, "TAIFEX": 0, "other": 0}
    assert result["http_dispatch_count"] == {"TWSE": 0, "TPEX": expected_dispatch, "TAIFEX": 0, "other": 0}
    assert result["A3_decision"] == "HOLD" and result["candidate"] is None and artifacts == {}
    if stage == "open":
        assert result["source_telemetry"]["TPEX"]["http_status"] is None
        assert result["source_telemetry"]["TPEX"]["complete_body_received"] is False


@pytest.mark.parametrize("stage,expected_dispatch", [("pre_dispatch", 0), ("open", 1)])
def test_twse_failure_only_after_tpex_qualified(monkeypatch, stage, expected_dispatch):
    result, artifacts, calls, opens, _ = run_fake(monkeypatch, fail_market="TWSE", fail_stage=stage)
    assert calls == ["TPEX", "TWSE"] and len(opens) == 1 + expected_dispatch
    assert result["acquisition_callback_attempts"] == {"TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other": 0}
    assert result["http_dispatch_count"] == {"TWSE": expected_dispatch, "TPEX": 1, "TAIFEX": 0, "other": 0}
    assert result["source_telemetry"]["TPEX"]["complete_body_received"] is True
    assert result["candidate"] is None and result["A3_decision"] == "HOLD" and artifacts == {}


def test_old_owner_authority_rejected_and_no_new_authority_fabricated():
    for value in ("", "made-up", a3.OWNER):
        with pytest.raises(RuntimeError, match="fresh_separate_owner_authority_required"):
            attempt2.fresh_owner_reference(value)
    assert not hasattr(attempt2, "FRESH_OWNER")
    target = targets()["TPEX"]
    assert a3.target_request(target, 1)["execution_request_hash"] != a3.target_request(
        target, 1, request_authority=attempt2.OFFLINE_REQUEST_NAMESPACE)["execution_request_hash"]


def test_attempt2_latch_is_distinct_and_preexisting_consumed_latch_blocks(monkeypatch):
    assert attempt2.CONSUMED != a3.CONSUMED and attempt2.RESERVATION != a3.RESERVATION
    assert (a3.ROOT / a3.CONSUMED).is_file()
    monkeypatch.setattr(attempt2.Path, "exists", lambda path: str(path).endswith("i3-a3-attempt-2-live-authority-consumed.json"))
    with pytest.raises(RuntimeError, match="attempt_2_single_use_latch_or_outcome_exists"):
        attempt2.attempt2_artifacts_absent()


def test_exact_mapping_and_frozen_candidate_and_production_containment():
    assert transport_market_key("TWSE") == "TWSE" and transport_market_key("TPEX") == "TPEx"
    with pytest.raises(ValueError):
        transport_market_key("TPEx")
    assert a3.candidate_hashes() == r1.CANDIDATE_SHA
    assert a3.sha(a3.ROOT / r1.RECORD) == attempt2.R1_SHA256
    a3.production_containment()


def test_attempt2_artifact_lifecycle_is_consistent():
    paths = [a3.ROOT / path for path in (attempt2.RESERVATION, attempt2.CONSUMED, attempt2.OUTCOME, attempt2.HOLD)]
    existing = [path.exists() for path in paths]
    if not any(existing):
        assert existing == [False, False, False, False]
    else:
        assert existing[0] and existing[1]
        assert existing[2] != existing[3]
        consumed = json.loads(paths[1].read_text(encoding="utf-8"))
        assert consumed["consumed"] is True
        assert consumed["consumed_before_first_http_attempt"] is True
    assert attempt2.NETWORK_BUDGET == {"TPEX": 1, "TWSE": 1, "TAIFEX": 0, "other": 0, "retry": 0}
