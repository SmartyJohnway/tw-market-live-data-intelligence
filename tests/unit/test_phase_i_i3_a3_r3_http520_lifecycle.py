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


def assert_attempt4_lifecycle(reservation, consumed, passed, held):
    if not any(path.exists() for path in (reservation, consumed, passed, held)):
        # Valid only before the single-use live authority is consumed.
        assert all(not path.exists() for path in (reservation, consumed, passed, held))
        return "pre_live"
    assert reservation.is_file() and consumed.is_file()
    assert passed.exists() != held.exists()
    latch = json.loads(consumed.read_text(encoding="utf-8"))
    assert latch["consumed"] is True
    assert latch["consumed_before_first_http_attempt"] is True
    assert latch["reservation_sha256"] == a3.sha(reservation)
    return "post_live"


def test_attempt4_pre_live_lifecycle_is_valid_without_artifacts(tmp_path):
    assert assert_attempt4_lifecycle(*(tmp_path / name for name in
        ("reservation.json", "consumed.json", "pass.json", "hold.json"))) == "pre_live"


def test_attempt3_history_is_immutable_and_attempt4_is_separate():
    attempt4.historical_attempts_intact()
    assert attempt4.RESERVATION.endswith("i3-a3-attempt-4-live-authority-reservation.json")
    assert attempt4.CONSUMED.endswith("i3-a3-attempt-4-live-authority-consumed.json")
    reservation = a3.ROOT / attempt4.RESERVATION
    consumed = a3.ROOT / attempt4.CONSUMED
    passed = a3.ROOT / attempt4.OUTCOME
    held = a3.ROOT / attempt4.HOLD
    assert assert_attempt4_lifecycle(reservation, consumed, passed, held) == "post_live"
    assert passed.is_file() and not held.exists()  # Committed Attempt 4 outcome.


def test_committed_attempt4_pass_lineage_and_containment():
    immutable = {
        attempt4.OUTCOME: "f89a52b894e5c101ee6016a97034d395823011baee591cb4272334e821baa021",
        attempt4.RESERVATION: "951228829ddcb4f4639f7cae03d35045d1aa148a89df3c48b15fc09fdb2077ed",
        attempt4.CONSUMED: "44abcb5393ef4f3d2956b921a50e237deaeb83571af538cfbff06f3b6edeb21f",
        f"{attempt4.ARTIFACT_ROOT}/evidence/phase_i/i3/i3a3-tpex-5347.json":
            "7550c023d639aa4e43389b33dc730b79d6d345ebcd71130c604420db04a80891",
        f"{attempt4.ARTIFACT_ROOT}/evidence/phase_i/i3/i3a3-twse-1101.json":
            "398bea2cdce82bb3d1066974ac9e009d87b4f4e9c8249328d36df7b8aaf7d048",
    }
    assert all(a3.sha(a3.ROOT / path) == digest for path, digest in immutable.items())
    record = json.loads((a3.ROOT / attempt4.OUTCOME).read_text(encoding="utf-8"))
    assert record["status"] == "PASS_READY_FOR_INDEPENDENT_REVIEW"
    assert record["A3_decision"] == "PASS" and record["candidate_reached"] is True
    expected_count = {"TPEX": 1, "TWSE": 1, "TAIFEX": 0, "other": 0}
    assert record["acquisition_callback_attempts"] == expected_count
    assert record["transport_attempt_count"] == expected_count
    assert record["http_dispatch_count"] == expected_count
    assert record["retry_count_by_market"] == {key: 0 for key in expected_count}
    assert record["raw_payload_persistence"] == "NONE"
    assert record["candidate"]["network_calls"] == 0
    assert record["candidate"]["simulated_source_acquisition_count"] == 2
    assert all(item["status"] == "succeeded" for item in record["candidate"]["operation_results"])
    assert record["candidate"]["alignment"] == {
        "status": "different_trade_date",
        "same_date_implies_simultaneous_publication": False,
        "numeric_same_session_interpretation_allowed": False,
    }
    for market, target, trade_date, size, digest in (
        ("TPEX", "TPEX:5347", "2026-10-02", 861949,
         "2d058996bf67a375e152f381dda1a8610c32cf3ecd1ed31240c89ac7fd020402"),
        ("TWSE", "TWSE:1101", "2026-09-30", 192873,
         "377cdd86c4720f630d8c008e3642eb6e24d02f118d2452d7d3738ee4bc7dbb86"),
    ):
        evidence = record["evidence"][market]
        live = record["source_telemetry"][market]
        assert evidence["canonical_target_id"] == target
        assert evidence["status"] == "complete" and evidence["unit"] == "share"
        assert evidence["trade_date"] == trade_date
        assert live["complete_body_received"] is True and live["http_status"] == 200
        assert live["response_byte_count"] == evidence["transport"]["response_byte_count"] == size
        assert live["response_sha256"] == evidence["transport"]["response_sha256"] == digest
    a3.production_containment()


def test_previous_owner_authorities_are_rejected():
    for owner in ("", "made-up", a3.OWNER, attempt4.ATTEMPT2_OWNER, attempt4.ATTEMPT3_OWNER):
        with pytest.raises(RuntimeError, match="fresh_separate_owner_authority_required"):
            attempt4.fresh_owner_reference(owner)
