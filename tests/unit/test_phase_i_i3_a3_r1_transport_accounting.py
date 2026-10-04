"""Offline R1 proof across canonical identity, reviewed transport, and dispatch."""
import hashlib
import io
import json
import socket
from urllib.error import URLError

import pytest

from scripts import phase_i_i3_a0_source_transport as transport
from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts.phase_i_i3_transport_mapping import transport_market_key

FIXTURES = a3.ROOT / "tests/fixtures/phase_i_i3_a0"


@pytest.fixture(autouse=True)
def deny_market_sockets(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("r1_external_socket_forbidden")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


class Response:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, body):
        self.stream = io.BytesIO(body)

    def read(self, limit):
        return self.stream.read(limit)

    def close(self):
        self.stream.close()


class Opener:
    def __init__(self, body=None, error=None):
        self.body = body
        self.error = error
        self.calls = []

    def open(self, request, *, timeout):
        self.calls.append((request, timeout))
        if self.error is not None:
            raise self.error
        return Response(self.body)


def fixture_bodies():
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


def test_exact_canonical_to_transport_mapping():
    assert transport_market_key("TWSE") == "TWSE"
    assert transport_market_key("TPEX") == "TPEx"
    for alias in ("TPEx", "tpex", "TAIFEX", "", None, 1):
        with pytest.raises(ValueError, match="unsupported_canonical_market"):
            transport_market_key(alias)


def test_canonical_tpex_reaches_reviewed_strict_transport_and_fake_open():
    payload = b'[]'
    opener = Opener(payload)
    dispatch = []
    telemetry, body = a3.acquire_reviewed_source("TPEX", on_http_dispatch=lambda: dispatch.append("TPEX"),
                                                  opener_factory=lambda *handlers: opener)
    assert dispatch == ["TPEX"] and len(opener.calls) == 1
    request, timeout = opener.calls[0]
    assert request.full_url == transport.URLS["TPEx"] and request.get_method() == "GET" and timeout == 30
    assert telemetry["market"] == "TPEx" and telemetry["ssl_policy"] == "strict"
    assert telemetry["http_status"] == 200 and telemetry["complete_body_received"] is True
    assert telemetry["response_sha256"] == hashlib.sha256(payload).hexdigest() and body == payload


def test_callback_attempt_and_dispatch_are_separate_on_pre_io_rejection(monkeypatch):
    bodies = fixture_bodies()
    dispatches = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}
    openers = {"TWSE": Opener(bodies["TWSE"]), "TPEX": Opener(bodies["TPEX"])}
    original = a3.transport_market_key

    def reject_tpex(market):
        if market == "TPEX":
            raise ValueError("unsupported_canonical_market")
        return original(market)
    monkeypatch.setattr(a3, "transport_market_key", reject_tpex)

    def acquire(market):
        return a3.acquire_reviewed_source(market,
            on_http_dispatch=lambda: dispatches.__setitem__(market, dispatches[market] + 1),
            opener_factory=lambda *handlers: openers[market])

    result, artifacts = a3.execute_with_acquirer(acquire, targets(), http_dispatch_count=dispatches)
    assert result["acquisition_callback_attempts"] == {"TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other": 0}
    assert result["http_dispatch_count"] == {"TWSE": 1, "TPEX": 0, "TAIFEX": 0, "other": 0}
    assert len(openers["TWSE"].calls) == 1 and openers["TPEX"].calls == []
    assert result["source_telemetry"].keys() == {"TWSE"}
    assert result["candidate"] is None and artifacts == {} and result["A3_decision"] == "HOLD"


def test_open_failure_counts_dispatch_but_not_response_or_body():
    bodies = fixture_bodies()
    dispatches = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}
    openers = {"TWSE": Opener(bodies["TWSE"]), "TPEX": Opener(error=URLError(ConnectionRefusedError(111, "refused")))}

    def acquire(market):
        return a3.acquire_reviewed_source(market,
            on_http_dispatch=lambda: dispatches.__setitem__(market, dispatches[market] + 1),
            opener_factory=lambda *handlers: openers[market])

    result, artifacts = a3.execute_with_acquirer(acquire, targets(), http_dispatch_count=dispatches)
    assert result["acquisition_callback_attempts"]["TPEX"] == 1
    assert result["http_dispatch_count"]["TPEX"] == 1 and len(openers["TPEX"].calls) == 1
    assert result["source_telemetry"]["TPEX"]["http_status"] is None
    assert result["source_telemetry"]["TPEX"]["complete_body_received"] is False
    assert result["A3_decision"] == "HOLD" and artifacts == {}


def test_two_fake_transport_dispatches_produce_complete_candidate_evidence():
    bodies = fixture_bodies()
    dispatches = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}
    openers = {market: Opener(body) for market, body in bodies.items()}

    def acquire(market):
        return a3.acquire_reviewed_source(market,
            on_http_dispatch=lambda: dispatches.__setitem__(market, dispatches[market] + 1),
            opener_factory=lambda *handlers: openers[market])

    result, artifacts = a3.execute_with_acquirer(acquire, targets(), http_dispatch_count=dispatches)
    assert result["acquisition_callback_attempts"] == result["http_dispatch_count"] == {
        "TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other": 0}
    assert all(len(opener.calls) == 1 for opener in openers.values())
    assert result["A3_decision"] == "PASS" and len(artifacts) == 2
    assert result["candidate"]["network_calls"] == 0
    assert all(result["evidence"][m]["status"] == "complete" for m in ("TWSE", "TPEX"))


def test_consumed_latch_precedes_candidate_drift_in_real_worktree(monkeypatch):
    original_git = a3.git
    monkeypatch.setattr(a3, "git", lambda *args: "?? data/" if args == ("status", "--porcelain") else original_git(*args))
    with pytest.raises(RuntimeError, match="single_use_latch_or_outcome_exists"):
        a3.final_pre_network_guard(original_git("rev-parse", "HEAD"))
