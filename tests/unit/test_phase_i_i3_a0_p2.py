from __future__ import annotations

import json
import shutil
import socket
import ssl
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from scripts import phase_i_i3_a0_attempt_authority as latch
from scripts import phase_i_i3_a0_source_transport as transport
from scripts import validate_phase_i_i3_a0_attempt2 as attempt2_validator


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("P2 test attempted external socket use")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


class Response:
    def __init__(self, body=b'{"date":"20260930","data":[]}', *, status=200,
                 content_type="application/json"):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.read_limits = []
        self.closed = False
        self.offset = 0

    def getcode(self):
        return self.status

    def read(self, limit):
        self.read_limits.append(limit)
        if isinstance(self.body, Exception):
            raise self.body
        chunk = self.body[self.offset:self.offset + limit]
        self.offset += len(chunk)
        return chunk

    def close(self):
        self.closed = True


class Opener:
    def __init__(self, response=None, error=None):
        self.response, self.error = response, error
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


def opener_factory_for(opener, captured=None):
    def factory(*handlers):
        if captured is not None:
            captured.extend(handlers)
        return opener
    return factory


def read(market="TWSE", response=None, error=None, *, policy=None, captured=None):
    op = Opener(response or Response(), error)
    telemetry, body = transport.read_once(
        market, policy=policy, opener_factory=opener_factory_for(op, captured),
        now=lambda: "2026-10-02T00:00:00Z",
    )
    return telemetry, body, op


def test_reviewed_chain_has_exact_five_historical_hashes_and_reservation_uses_them():
    chain = latch.load_reviewed_authority_chain()
    reservation = latch.build_reservation(
        owner_authority="future-owner-decision", starting_main="a" * 40,
        branch="future-branch", branch_head="b" * 40, tree="c" * 40,
        max_gets={"TWSE": 1, "TPEx": 1, "retry": 0},
    )
    for key, digest in latch.ANCHOR_FIELDS.items():
        assert chain[key] == digest
        assert reservation[key] == digest
    consumed = latch.build_consumed_latch(reservation, consumed_at="2030-01-01T00:00:00Z")
    latch.validate_consumed_latch(consumed)
    assert consumed["consumed"] is True


@pytest.mark.parametrize("changed", [
    "attempt_1_record_sha256", "p0_mapping_sha256", "p0_record_sha256",
    "p1_authority_sha256", "p1_record_sha256",
])
def test_future_latch_rejects_changed_or_swapped_hash(changed):
    reservation = latch.build_reservation(
        owner_authority="future-owner-decision", starting_main="a" * 40,
        branch="future-branch", branch_head="b" * 40, tree="c" * 40,
        max_gets={"TWSE": 1, "TPEx": 1, "retry": 0},
    )
    reservation[changed] = "0" * 64
    with pytest.raises(ValueError, match="reservation_anchor_mismatch"):
        latch.validate_reservation(reservation)


def test_missing_and_swapped_attempt1_p0_hashes_fail():
    reservation = latch.build_reservation(owner_authority="future", starting_main="a" * 40,
        branch="b", branch_head="c" * 40, tree="d" * 40, max_gets={})
    del reservation["p0_record_sha256"]
    with pytest.raises(ValueError, match="reservation_anchor_mismatch:p0_record_sha256"):
        latch.validate_reservation(reservation)
    reservation = latch.build_reservation(owner_authority="future", starting_main="a" * 40,
        branch="b", branch_head="c" * 40, tree="d" * 40, max_gets={})
    reservation["attempt_1_record_sha256"], reservation["p0_record_sha256"] = (
        reservation["p0_record_sha256"], reservation["attempt_1_record_sha256"])
    with pytest.raises(ValueError):
        latch.validate_reservation(reservation)


def test_unreviewed_local_authority_path_is_not_an_api():
    with pytest.raises(TypeError):
        latch.load_reviewed_authority_chain(Path("unreviewed.json"))
    with pytest.raises(TypeError):
        latch.build_reservation(owner_authority="x", starting_main="x", branch="x",
            branch_head="x", tree="x", max_gets={}, authority_path=Path("unreviewed.json"))


def test_missing_reviewed_authority_fails_closed(monkeypatch, tmp_path):
    original = latch.AUTHORITY_PATH
    monkeypatch.setattr(latch, "AUTHORITY_PATH", original)
    original_read_text = Path.read_text
    def missing(self, *args, **kwargs):
        if self == original:
            raise FileNotFoundError("reviewed authority absent")
        return original_read_text(self, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", missing)
    with pytest.raises(FileNotFoundError, match="reviewed authority absent"):
        latch.load_reviewed_authority_chain()


def test_attempt2_validator_requires_erratum_and_historical_misanchored_bytes(tmp_path):
    for rel in ("docs/governance/phase_i/acceptance_runs/i3-a0-attempt2-authority-reservation.json",
                "docs/governance/phase_i/acceptance_runs/i3-a0-attempt2-authority-consumed.json",
                attempt2_validator.ERRATUM_REL):
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(attempt2_validator.ROOT / rel, dest)
    attempt2_validator.validate_provenance(tmp_path)
    erratum_path = tmp_path / attempt2_validator.ERRATUM_REL
    erratum = json.loads(erratum_path.read_text(encoding="utf-8"))
    erratum["correct_authority_value"] = "43ef038ffd33a455ae52eff18a8f08e52436164b6d27d6140090b368810df5e0"
    erratum_path.write_text(json.dumps(erratum), encoding="utf-8")
    with pytest.raises(AssertionError):
        attempt2_validator.validate_provenance(tmp_path)
    erratum_path.unlink()
    with pytest.raises(FileNotFoundError):
        attempt2_validator.validate_provenance(tmp_path)


def test_twse_compatibility_context_keeps_certificate_and_hostname_verification():
    captured = []
    opener = Opener(Response())
    telemetry, body = transport.read_once("TWSE", opener_factory=opener_factory_for(opener, captured))
    handler = next(h for h in captured if isinstance(h, transport.HTTPSHandler))
    context = handler._context
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        assert context.verify_flags & ssl.VERIFY_X509_STRICT == 0
    assert telemetry["ssl_policy"] == "compatibility"
    assert telemetry["retry_count"] == 0 and body is not None


def test_tpex_uses_default_strict_tls_and_no_compatibility_fallback():
    captured = []
    telemetry, body, _op = read("TPEx", Response(b'[]'), captured=captured)
    handler = next(h for h in captured if isinstance(h, transport.HTTPSHandler))
    assert handler._context.verify_mode == ssl.CERT_REQUIRED
    assert handler._context.check_hostname is True
    assert handler._context.verify_flags == ssl.create_default_context().verify_flags
    assert telemetry["ssl_policy"] == "strict" and body == b"[]"
    calls = []
    with pytest.raises(ValueError, match="market_tls_policy_mismatch"):
        transport.build_market_opener("TWSE", policy="strict", opener_factory=lambda *h: calls.append(h))
    assert calls == []
    assert len(_op.calls) == 1


@pytest.mark.parametrize("market,policy,error", [
    ("TWSE", "unsafe-explicit", "unsafe_tls_forbidden"),
    ("TWSE", "wat", "Invalid ssl policy"),
    ("TPEx", "compatibility", "market_tls_policy_mismatch"),
])
def test_forbidden_or_wrong_tls_policy_rejected_before_opener(market, policy, error):
    called = []
    with pytest.raises(ValueError, match=error):
        transport.read_once(market, policy=policy, opener_factory=lambda *h: called.append(h))
    assert called == []


def test_custom_url_and_ssl_context_rejected_before_opener():
    called = []
    context = ssl.create_default_context()
    with pytest.raises(ValueError, match="caller_endpoint_forbidden"):
        transport.read_once("TWSE", endpoint="https://example.com", opener_factory=lambda *h: called.append(h))
    with pytest.raises(ValueError, match="caller_ssl_context_forbidden"):
        transport.read_once("TWSE", ssl_context=context, opener_factory=lambda *h: called.append(h))
    assert called == []


def test_fixed_endpoint_and_bounds_and_json_mime_parameters():
    response = Response(b'{"date":"20260930","data":[]}', content_type="application/json; charset=utf-8")
    telemetry, body, op = read("TWSE", response)
    req, timeout = op.calls[0]
    assert req.full_url == transport.URLS["TWSE"]
    assert req.get_method() == "GET" and timeout == 30
    assert response.read_limits == [transport.READ_CHUNK_BYTES] * 2
    assert telemetry["base_mime"] == "application/json"
    assert telemetry["response_byte_count"] == len(body)
    assert telemetry["retry_count"] == 0 and body == response.body


def test_tpex_fixed_endpoint_json_array_success():
    telemetry, body, op = read("TPEx", Response(b'[]'))
    assert op.calls[0][0].full_url == transport.URLS["TPEx"]
    assert telemetry["base_mime"] == "application/json" and body == b"[]"


def test_http_non_200_and_redirect_are_http_failures_without_follow():
    telemetry, body, _ = read("TWSE", Response(b'{"data":[]}', status=503))
    assert telemetry["error_code"] == "http_status_not_200" and telemetry["http_status"] == 503 and body is None
    redirect = HTTPError(transport.URLS["TWSE"], 302, "redirect", {"Location": "https://elsewhere.invalid"}, None)
    telemetry, body, op = read("TWSE", error=redirect)
    assert telemetry["http_status"] == 302 and body is None
    assert len(op.calls) == 1


def test_bad_mime_oversize_and_read_error_fail_closed():
    telemetry, body, _ = read("TWSE", Response(b'{"data":[]}', content_type="text/html"))
    assert telemetry["error_code"] == "unsupported_content_type" and body is None
    telemetry, body, response_op = read("TWSE", Response(b"x" * (transport.MAX_BYTES + 2)))
    assert telemetry["response_byte_count"] == 0
    assert telemetry["partial_response_byte_count"] == transport.MAX_BYTES + 1
    assert telemetry["error_code"] == "response_byte_limit_exceeded" and body is None
    assert max(response_op.response.read_limits) <= transport.READ_CHUNK_BYTES
    telemetry, body, _ = read("TWSE", Response(OSError("read broke")))
    assert telemetry["reason_classification"] == "os_network_error" and body is None


@pytest.mark.parametrize("reason,classification", [
    (ssl.SSLCertVerificationError(1, "Missing Subject Key Identifier"), "ssl_certificate_verification_failed"),
    (socket.gaierror(-2, "no such host"), "dns_resolution_failed"),
    (ConnectionRefusedError(111, "refused"), "connection_refused"),
    (ConnectionResetError(104, "reset"), "connection_reset"),
    (TimeoutError("timed out"), "timeout"),
    (OSError(101, "network unreachable"), "os_network_error"),
])
def test_bounded_urlerror_reason_classification(reason, classification):
    telemetry, body, _ = read("TWSE", error=URLError(reason))
    assert telemetry["error_code"] == "URLError"
    assert telemetry["reason_type"] == type(reason).__name__
    assert telemetry["reason_classification"] == classification
    assert body is None
    if isinstance(reason, ssl.SSLCertVerificationError):
        assert "Missing Subject Key Identifier" in telemetry["verify_message"]
        assert len(telemetry["verify_message"]) <= 256


def test_phase_h_missing_ski_diagnostic_is_synthetic_only():
    error = URLError(ssl.SSLCertVerificationError(1, "Missing Subject Key Identifier"))
    result = transport.classify_exception(error)
    assert result["error_code"] == "URLError"
    assert result["reason_type"] == "SSLCertVerificationError"
    assert result["reason_classification"] == "ssl_certificate_verification_failed"
