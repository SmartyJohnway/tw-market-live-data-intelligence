"""R3 tests for observed HTTP 520 retry and Attempt 3 lifecycle; no live sockets."""
import io
import json
import socket
from urllib.error import HTTPError

import pytest

from scripts import run_phase_i_i3_a3_attempt_4_bounded_live_acceptance as attempt4
from scripts import run_phase_i_i3_a3_bounded_live_acceptance as a3
from scripts.phase_i_i3_a3_retry_policy_v2 import (
    MAX_HTTP_DISPATCHES_PER_MARKET,
    MAX_RETRIES_PER_MARKET,
    RETRYABLE_HTTP_STATUS,
    retryable_transport_failure,
)

FIXTURES = a3.ROOT / "tests/fixtures/phase_i_i3_a0"


@pytest.fixture(autouse=True)
def deny_sockets(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("r3_external_socket_forbidden")
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


def tpex_body():
    payload = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(
        encoding="utf-8"))["unique_candidate_a"]
    return json.dumps(payload, ensure_ascii=False).encode()


def http_error(code: int):
    return HTTPError(
        "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading",
        code,
        f"synthetic {code}",
        {"Content-Type": "application/json"},
        None,
    )


def test_r3_keeps_ten_dispatch_cap_and_adds_only_observed_520():
    assert MAX_HTTP_DISPATCHES_PER_MARKET == 10
    assert MAX_RETRIES_PER_MARKET == 9
    assert 520 in RETRYABLE_HTTP_STATUS
    assert 521 not in RETRYABLE_HTTP_STATUS
    assert retryable_transport_failure({
        "complete_body_received": False,
        "error_code": "http_status_not_200",
        "http_status": 520,
        "reason_classification": None,
        "failure_phase": "http_response_headers",
    })
    assert not retryable_transport_failure({
        "complete_body_received": False,
        "error_code": "http_status_not_200",
        "http_status": 404,
        "reason_classification": None,
        "failure_phase": "http_response_headers",
    })


def test_observed_attempt3_pattern_can_continue_past_520():
    body = tpex_body()
    factory = SequenceFactory([
        Opener(Response(body, reset=True)),
        Opener(Response(body, reset=True)),
        Opener(Response(body, reset=True)),
        Opener(error=ConnectionResetError(10054, "synthetic reset")),
        Opener(error=TimeoutError("synthetic timeout")),
        Opener(error=TimeoutError("synthetic timeout")),
        Opener(error=TimeoutError("synthetic timeout")),
        Opener(error=http_error(520)),
        Opener(Response(body)),
    ])
    dispatch = {"count": 0}
    history = {}
    sleeps = []
    observation, acquired = attempt4.acquire_with_retry(
        "TPEX",
        on_http_dispatch=lambda: dispatch.__setitem__("count", dispatch["count"] + 1),
        attempt_history=history,
        sleeper=sleeps.append,
        opener_factory=factory,
    )
    assert dispatch["count"] == 9
    assert factory.calls == 9
    assert len(history["TPEX"]) == 9
    assert history["TPEX"][7]["http_status"] == 520
    assert observation["complete_body_received"] is True
    assert acquired == body


def test_ten_http_520_responses_stop_without_eleventh_dispatch():
    factory = SequenceFactory([Opener(error=http_error(520)) for _ in range(10)])
    dispatch = {"count": 0}
    history = {}
    observation, acquired = attempt4.acquire_with_retry(
        "TPEX",
        on_http_dispatch=lambda: dispatch.__setitem__("count", dispatch["count"] + 1),
        attempt_history=history,
        sleeper=lambda _: None,
        opener_factory=factory,
    )
    assert dispatch["count"] == 10
    assert factory.calls == 10
    assert len(history["TPEX"]) == 10
    assert observation["http_status"] == 520
    assert acquired is None


def test_404_stops_immediately_even_with_budget_remaining():
    factory = SequenceFactory([Opener(error=http_error(404))])
    dispatch = {"count": 0}
    history = {}
    observation, acquired = attempt4.acquire_with_retry(
        "TPEX",
        on_http_dispatch=lambda: dispatch.__setitem__("count", dispatch["count"] + 1),
        attempt_history=history,
        sleeper=lambda _: pytest.fail("404 must not retry"),
        opener_factory=factory,
    )
    assert dispatch["count"] == 1
    assert observation["http_status"] == 404
    assert acquired is None


def test_attempt3_history_is_immutable_and_attempt4_is_separate():
    attempt4.historical_attempts_intact()
    assert attempt4.RESERVATION.endswith("i3-a3-attempt-4-live-authority-reservation.json")
    assert attempt4.CONSUMED.endswith("i3-a3-attempt-4-live-authority-consumed.json")
    assert not (a3.ROOT / attempt4.RESERVATION).exists()
    assert not (a3.ROOT / attempt4.CONSUMED).exists()


def test_previous_owner_authorities_are_rejected():
    for owner in ("", "made-up", a3.OWNER, attempt4.ATTEMPT2_OWNER, attempt4.ATTEMPT3_OWNER):
        with pytest.raises(RuntimeError, match="fresh_separate_owner_authority_required"):
            attempt4.fresh_owner_reference(owner)
