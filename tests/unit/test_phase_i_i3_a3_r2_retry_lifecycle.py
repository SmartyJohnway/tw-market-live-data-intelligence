"""R2 bounded retry and lifecycle tests; all external sockets denied."""
import io
import json
import socket
from urllib.error import HTTPError, URLError

import pytest

from scripts import phase_i_i3_a0_source_transport as transport
from scripts import run_phase_i_i3_a3_attempt_3_bounded_live_acceptance as attempt3
from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts.phase_i_i3_a3_retry_policy import (
    MAX_HTTP_DISPATCHES_PER_MARKET,
    MAX_RETRIES_PER_MARKET,
    retry_delay_seconds,
    retryable_transport_failure,
)

FIXTURES = a3.ROOT / "tests/fixtures/phase_i_i3_a0"
ZERO = {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0}


@pytest.fixture(autouse=True)
def deny_sockets(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("r2_external_socket_forbidden")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


class Response:
    status = 200

    def __init__(self, body: bytes, *, reset=False, content_type="application/json"):
        self.body = body
        self.reset = reset
        self.stream = io.BytesIO(body)
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}

    def read(self, size):
        if self.reset:
            self.reset = False
            raise ConnectionResetError(10054, "synthetic reset")
        return self.stream.read(size)

    def close(self):
        self.stream.close()

    def getcode(self):
        return self.status


class Opener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def open(self, request, *, timeout):
        if self.error is not None:
            raise self.error
        return self.response


class SequenceFactory:
    def __init__(self, openers):
        self.openers = list(openers)
        self.calls = 0

    def __call__(self, *handlers):
        opener = self.openers[self.calls]
        self.calls += 1
        return opener


def fixture_bodies():
    twse = json.loads((FIXTURES / "twse_synthetic.json").read_text(encoding="utf-8"))
    tpex = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(
        encoding="utf-8"))["unique_candidate_a"]
    return {
        "TWSE": json.dumps(twse, ensure_ascii=False).encode(),
        "TPEX": json.dumps(tpex, ensure_ascii=False).encode(),
    }


def targets():
    return {
        market: {
            "canonical_target_id": f"{market}:{code}",
            "market": market,
            "security_code": code,
            "instrument_family": "company_share",
            "instrument_type": "common_share",
            "execution_eligibility": "allowed",
            "isin": "synthetic-test-only",
        }
        for market, code in (("TWSE", "1101"), ("TPEX", "5347"))
    }


def test_retry_budget_is_ten_dispatches_per_market():
    assert MAX_HTTP_DISPATCHES_PER_MARKET == 10
    assert MAX_RETRIES_PER_MARKET == 9
    assert tuple(retry_delay_seconds(n) for n in range(2, 11)) == (1, 2, 4, 8, 10, 10, 10, 10, 10)
    with pytest.raises(ValueError):
        retry_delay_seconds(11)


def test_connection_reset_is_retryable_but_contract_failures_are_not():
    assert retryable_transport_failure({
        "complete_body_received": False,
        "error_code": "URLError",
        "reason_classification": "connection_reset",
        "failure_phase": "response_body_read",
        "http_status": 200,
    })
    assert retryable_transport_failure({
        "complete_body_received": False,
        "error_code": "http_status_not_200",
        "reason_classification": None,
        "http_status": 503,
    })
    for error in ("unsupported_content_type", "invalid_json_payload", "response_byte_limit_exceeded"):
        assert not retryable_transport_failure({
            "complete_body_received": False,
            "error_code": error,
            "reason_classification": None,
            "http_status": 200,
        })


def test_nine_resets_then_tenth_dispatch_can_succeed():
    body = fixture_bodies()["TPEX"]
    factory = SequenceFactory(
        [Opener(Response(body, reset=True)) for _ in range(9)]
        + [Opener(Response(body))]
    )
    dispatch = {"count": 0}
    history = {}
    sleeps = []
    observation, acquired = attempt3.acquire_with_retry(
        "TPEX",
        on_http_dispatch=lambda: dispatch.__setitem__("count", dispatch["count"] + 1),
        attempt_history=history,
        sleeper=sleeps.append,
        opener_factory=factory,
    )
    assert dispatch["count"] == 10
    assert factory.calls == 10
    assert len(history["TPEX"]) == 10
    assert sleeps == [1, 2, 4, 8, 10, 10, 10, 10, 10]
    assert observation["complete_body_received"] is True
    assert acquired == body


def test_ten_transient_failures_stop_without_eleventh_dispatch():
    body = fixture_bodies()["TPEX"]
    factory = SequenceFactory([Opener(Response(body, reset=True)) for _ in range(10)])
    dispatch = {"count": 0}
    history = {}
    observation, acquired = attempt3.acquire_with_retry(
        "TPEX",
        on_http_dispatch=lambda: dispatch.__setitem__("count", dispatch["count"] + 1),
        attempt_history=history,
        sleeper=lambda _: None,
        opener_factory=factory,
    )
    assert dispatch["count"] == 10
    assert factory.calls == 10
    assert len(history["TPEX"]) == 10
    assert acquired is None
    assert observation["reason_classification"] == "connection_reset"


def test_nonretryable_invalid_json_stops_after_first_dispatch():
    factory = SequenceFactory([Opener(Response(b"{not-json"))])
    dispatch = {"count": 0}
    history = {}
    observation, acquired = attempt3.acquire_with_retry(
        "TPEX",
        on_http_dispatch=lambda: dispatch.__setitem__("count", dispatch["count"] + 1),
        attempt_history=history,
        sleeper=lambda _: pytest.fail("nonretryable failure must not sleep"),
        opener_factory=factory,
    )
    assert dispatch["count"] == 1
    assert acquired is None
    assert observation["error_code"] == "invalid_json_payload"


def test_tpex_retries_then_twse_retries_and_candidate_can_pass():
    raw = fixture_bodies()
    factories = {
        "TPEX": SequenceFactory([
            Opener(Response(raw["TPEX"], reset=True)),
            Opener(Response(raw["TPEX"], reset=True)),
            Opener(Response(raw["TPEX"])),
        ]),
        "TWSE": SequenceFactory([
            Opener(Response(raw["TWSE"], reset=True)),
            Opener(Response(raw["TWSE"])),
        ]),
    }
    dispatches = dict(ZERO)
    histories = {}

    def acquire(market):
        return attempt3.acquire_with_retry(
            market,
            on_http_dispatch=lambda: dispatches.__setitem__(market, dispatches[market] + 1),
            attempt_history=histories,
            sleeper=lambda _: None,
            opener_factory=factories[market],
        )

    result, artifacts = a3.execute_with_acquirer(
        acquire,
        targets(),
        http_dispatch_count=dispatches,
        acquisition_order=attempt3.ACQUISITION_ORDER,
        operation_authority=attempt3.OFFLINE_REQUEST_NAMESPACE,
    )
    assert result["A3_decision"] == "PASS"
    assert result["acquisition_callback_attempts"] == {"TWSE": 1, "TPEX": 1, "TAIFEX": 0, "other": 0}
    assert dispatches == {"TWSE": 2, "TPEX": 3, "TAIFEX": 0, "other": 0}
    assert len(histories["TPEX"]) == 3 and len(histories["TWSE"]) == 2
    assert result["candidate"]["network_calls"] == 0
    assert len(artifacts) == 2


def test_tpex_tenth_failure_prevents_any_twse_attempt():
    raw = fixture_bodies()
    factory = SequenceFactory([Opener(Response(raw["TPEX"], reset=True)) for _ in range(10)])
    dispatches = dict(ZERO)
    histories = {}
    calls = []

    def acquire(market):
        calls.append(market)
        if market == "TWSE":
            pytest.fail("TWSE must not run after TPEX exhausts its bounded budget")
        return attempt3.acquire_with_retry(
            market,
            on_http_dispatch=lambda: dispatches.__setitem__(market, dispatches[market] + 1),
            attempt_history=histories,
            sleeper=lambda _: None,
            opener_factory=factory,
        )

    result, artifacts = a3.execute_with_acquirer(
        acquire,
        targets(),
        http_dispatch_count=dispatches,
        acquisition_order=attempt3.ACQUISITION_ORDER,
        operation_authority=attempt3.OFFLINE_REQUEST_NAMESPACE,
    )
    assert calls == ["TPEX"]
    assert dispatches == {"TWSE": 0, "TPEX": 10, "TAIFEX": 0, "other": 0}
    assert result["A3_decision"] == "HOLD"
    assert result["candidate"] is None and artifacts == {}


def test_previous_owner_authorities_are_rejected():
    for owner in ("", "made-up", a3.OWNER, attempt3.ATTEMPT2_OWNER):
        with pytest.raises(RuntimeError, match="fresh_separate_owner_authority_required"):
            attempt3.fresh_owner_reference(owner)


def test_attempt2_history_is_immutable_and_attempt3_lifecycle_is_consistent():
    attempt3.attempt2_history_intact()
    assert attempt3.RESERVATION.endswith("i3-a3-attempt-3-live-authority-reservation.json")
    assert attempt3.CONSUMED.endswith("i3-a3-attempt-3-live-authority-consumed.json")
    reservation = a3.ROOT / attempt3.RESERVATION
    consumed = a3.ROOT / attempt3.CONSUMED
    passed = a3.ROOT / attempt3.OUTCOME
    hold = a3.ROOT / attempt3.HOLD
    if not any(path.exists() for path in (reservation, consumed, passed, hold)):
        assert not reservation.exists() and not consumed.exists()
    else:
        assert reservation.is_file() and consumed.is_file()
        assert passed.exists() != hold.exists()
        latch = json.loads(consumed.read_text(encoding="utf-8"))
        assert latch["consumed"] is True
        assert latch["consumed_before_first_http_attempt"] is True