from __future__ import annotations

import hashlib
import json

import pytest

from server.services.phase_i_i2_index_futures_adapters import MAX_RESPONSE_BYTES, SOURCE_ENDPOINT
from server.services.phase_i_i2_live_acceptance_candidate import (
    A3TransportError,
    TIMEOUT_SECONDS,
    acquire_taifex_once,
)


def _transport(body=b"[]", *, status=200, content_type="application/octet-stream; charset=binary"):
    calls = []

    def fake(url, timeout):
        calls.append((url, timeout))
        return status, {"Content-Type": content_type}, body

    return fake, calls


def test_one_fixed_acquisition_has_frozen_timeout_and_telemetry_only():
    body = b"[]"
    fake, calls = _transport(body)
    acquired = acquire_taifex_once(transport=fake)
    assert calls == [(SOURCE_ENDPOINT, TIMEOUT_SECONDS)]
    assert (acquired.get_count, acquired.retry_count) == (1, 0)
    assert acquired.http_status == 200
    assert acquired.content_type == "application/octet-stream"
    assert acquired.response_byte_count == 2
    assert acquired.response_sha256 == hashlib.sha256(body).hexdigest()
    assert acquired.body == body  # memory return for immediate normalization only


def test_application_json_with_parameters_is_accepted():
    body = b"[]"
    fake, calls = _transport(body, content_type="application/json; charset=utf-8")
    acquired = acquire_taifex_once(transport=fake)
    assert calls == [(SOURCE_ENDPOINT, TIMEOUT_SECONDS)]
    assert acquired.content_type == "application/json"
    assert acquired.response_sha256 == hashlib.sha256(body).hexdigest()


@pytest.mark.parametrize(
    "kwargs,code",
    [
        ({"status": 302}, "http_status"),
        ({"status": 403}, "http_status"),
        ({"content_type": "text/html"}, "content_type"),
        ({"body": b"x" * (MAX_RESPONSE_BYTES + 1)}, "response_too_large"),
    ],
)
def test_transport_rejections_never_retry(kwargs, code):
    fake, calls = _transport(**kwargs)
    with pytest.raises(A3TransportError, match=code):
        acquire_taifex_once(transport=fake)
    assert len(calls) == 1


def test_transport_exception_is_one_failed_attempt_without_retry():
    calls = []

    def fail(url, timeout):
        calls.append((url, timeout))
        raise TimeoutError("fixture timeout")

    with pytest.raises(A3TransportError, match="transport_exception"):
        acquire_taifex_once(transport=fail)
    assert len(calls) == 1


def test_live_delegate_omission_stays_disarmed():
    with pytest.raises(A3TransportError, match="live_execution_not_rearmed"):
        acquire_taifex_once(transport=None)


def test_cli_live_flag_is_rejected_before_transport(monkeypatch, capsys):
    from scripts.run_phase_i_i2_a3_bounded_live_acceptance import main

    monkeypatch.setattr("sys.argv", ["run_phase_i_i2_a3_bounded_live_acceptance.py", "--live"])
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 2
    assert "live_execution_not_rearmed" in capsys.readouterr().err


@pytest.mark.parametrize(
    "body,code",
    [
        (b"\xff", "invalid_utf8_or_json"),
        (b"{\"not\":\"array\"}", "root_not_array"),
        (b"not json", "invalid_utf8_or_json"),
        (json.dumps([{}] * 5001).encode(), "too_many_rows"),
        (json.dumps([{}, 1]).encode(), "row_not_object"),
    ],
)
def test_payload_contract_rejections_are_one_attempt_and_hash_only(body, code):
    fake, calls = _transport(body)
    with pytest.raises(A3TransportError, match=code) as caught:
        acquire_taifex_once(transport=fake)
    assert len(calls) == 1
    assert caught.value.response_sha256 == hashlib.sha256(body).hexdigest()
