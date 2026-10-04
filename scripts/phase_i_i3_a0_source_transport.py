"""Bounded research-only I3-A0 transport; no invocation occurs during P2."""
from __future__ import annotations

import json
import socket
import ssl
from datetime import datetime, timezone
from email.message import Message
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from scripts.ssl_policy import (
    SSL_POLICY_COMPATIBILITY,
    SSL_POLICY_STRICT,
    SSL_POLICY_UNSAFE,
    build_ssl_context,
    validate_ssl_policy,
)

URLS = {
    "TWSE": "https://www.twse.com.tw/rwd/zh/fund/T86?date=20260930&selectType=ALLBUT0999&response=json",
    "TPEx": "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading",
}
MARKET_SSL_POLICY = {"TWSE": SSL_POLICY_COMPATIBILITY, "TPEx": SSL_POLICY_STRICT}
MAX_BYTES = 4 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024
TIMEOUT_SECONDS = 30
RETRY_COUNT = 0
ALLOWED_MIME = {"application/json"}
REASON_CLASSIFICATIONS = {
    "ssl_certificate_verification_failed", "dns_resolution_failed", "connection_refused",
    "connection_reset", "timeout", "os_network_error", "tls_error", "unknown_transport_error",
}


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def base_mime(content_type: str | None) -> str | None:
    if not content_type:
        return None
    message = Message()
    message["content-type"] = content_type
    return message.get_content_type().lower()


def policy_for_market(market: str, policy: str | None = None) -> str:
    if market not in MARKET_SSL_POLICY:
        raise ValueError("unreviewed_market")
    expected = MARKET_SSL_POLICY[market]
    selected = expected if policy is None else validate_ssl_policy(policy)
    if selected == SSL_POLICY_UNSAFE:
        raise ValueError("unsafe_tls_forbidden")
    if selected != expected:
        raise ValueError("market_tls_policy_mismatch")
    return selected


def build_market_opener(market: str, *, policy: str | None = None,
                        endpoint: str | None = None, ssl_context: ssl.SSLContext | None = None,
                        opener_factory: Callable = build_opener):
    """Construct fixed-host HTTPS opener; caller cannot supply URL or context."""
    if market not in URLS:
        raise ValueError("unreviewed_market")
    if endpoint is not None:
        raise ValueError("caller_endpoint_forbidden")
    if ssl_context is not None:
        raise ValueError("caller_ssl_context_forbidden")
    selected = policy_for_market(market, policy)
    context = build_ssl_context(selected)
    if selected == SSL_POLICY_COMPATIBILITY:
        if not isinstance(context, ssl.SSLContext):
            raise RuntimeError("verified_compatibility_context_required")
        if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
            raise RuntimeError("compatibility_context_must_verify_peer_and_hostname")
        handlers = [HTTPSHandler(context=context), RejectRedirects()]
    else:
        # ssl_policy strict is represented by the platform's default verified context.
        handlers = [HTTPSHandler(), RejectRedirects()]
    return opener_factory(*handlers)


def classify_reason(reason: Any) -> dict[str, Any]:
    """Bounded, allowlisted transport error telemetry; never serializes repr(exc)."""
    name = type(reason).__name__
    message = None
    verify_code = None
    errno = getattr(reason, "errno", None)
    if isinstance(reason, ssl.SSLCertVerificationError):
        classification = "ssl_certificate_verification_failed"
        candidate_code = getattr(reason, "verify_code", None)
        verify_code = candidate_code if type(candidate_code) is int else None
        candidate = getattr(reason, "verify_message", None)
        if not isinstance(candidate, str):
            candidate = str(reason)
        message = candidate[:256] if isinstance(candidate, str) else None
    elif isinstance(reason, socket.gaierror):
        classification = "dns_resolution_failed"
    elif isinstance(reason, ConnectionRefusedError):
        classification = "connection_refused"
    elif isinstance(reason, ConnectionResetError):
        classification = "connection_reset"
    elif isinstance(reason, (TimeoutError, socket.timeout)):
        classification = "timeout"
    elif isinstance(reason, ssl.SSLError):
        classification = "tls_error"
    elif isinstance(reason, OSError):
        classification = "os_network_error"
    else:
        classification = "unknown_transport_error"
    if classification not in REASON_CLASSIFICATIONS:
        classification = "unknown_transport_error"
    return {
        "error_code": "URLError", "reason_type": name,
        "reason_classification": classification,
        "verify_code": verify_code, "verify_message": message,
        "errno": errno if type(errno) is int else None,
    }


def classify_exception(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, HTTPError):
        return {"error_code": "http_status_not_200", "reason_type": None,
                "reason_classification": None, "http_status": exc.code}
    if isinstance(exc, URLError):
        return classify_reason(exc.reason)
    if isinstance(exc, (TimeoutError, socket.timeout, OSError, ssl.SSLError)):
        return classify_reason(exc)
    return {"error_code": type(exc).__name__, "reason_type": type(exc).__name__,
            "reason_classification": "unknown_transport_error", "verify_code": None,
            "verify_message": None, "errno": None}


def _decode_json(body: bytes) -> Any:
    decoded = body.decode("utf-8-sig")
    return json.loads(decoded)


def read_once(market: str, *, policy: str | None = None, endpoint: str | None = None,
              ssl_context: ssl.SSLContext | None = None, opener_factory: Callable = build_opener,
              now: Callable[[], str] = utc_now,
              on_http_dispatch: Callable[[], None] | None = None) -> tuple[dict[str, Any], bytes | None]:
    """One fixed GET. Tests inject an opener; this helper has no retry/fallback."""
    selected = policy_for_market(market, policy)
    if endpoint is not None:
        raise ValueError("caller_endpoint_forbidden")
    if ssl_context is not None:
        raise ValueError("caller_ssl_context_forbidden")
    opener = build_market_opener(market, policy=selected, opener_factory=opener_factory)
    request = Request(URLS[market], headers={"Accept": "application/json", "User-Agent": "tw-market-i3-a0-research/1.0"}, method="GET")
    telemetry: dict[str, Any] = {
        "market": market, "endpoint": URLS[market], "method": "GET", "timeout_seconds": TIMEOUT_SECONDS,
        "retry_count": RETRY_COUNT, "redirect_policy": "reject", "ssl_policy": selected,
        "tls_verification_mode": "verified_tls_compatibility_context" if selected == SSL_POLICY_COMPATIBILITY else "default_verified_tls",
        "http_status": None, "content_type": None, "base_mime": None,
        "retrieved_at": now(), "response_byte_count": 0, "response_sha256": None,
        "error_code": None,
        "complete_body_received": False, "partial_response_byte_count": 0,
        "declared_content_length": None, "failure_phase": None,
    }
    try:
        # This is the only observer site: policy, TLS, opener and Request guards
        # have passed, and the next operation attempts the HTTP dispatch.
        if on_http_dispatch is not None:
            on_http_dispatch()
        response = opener.open(request, timeout=TIMEOUT_SECONDS)
    except HTTPError as exc:
        telemetry.update(classify_exception(exc))
        telemetry["failure_phase"] = "http_response_headers"
        telemetry["http_status"] = exc.code
        telemetry["content_type"] = exc.headers.get("Content-Type") if exc.headers else None
        telemetry["base_mime"] = base_mime(telemetry["content_type"])
        try:
            exc.close()
        except Exception:
            pass
        return telemetry, None
    except Exception as exc:
        telemetry.update(classify_exception(exc))
        telemetry["failure_phase"] = "connection_setup_or_http_headers"
        return telemetry, None
    buffer = bytearray()
    phase = "http_response_headers"
    try:
        telemetry["http_status"] = getattr(response, "status", None) or response.getcode()
        headers = getattr(response, "headers", {})
        telemetry["content_type"] = headers.get("Content-Type")
        telemetry["base_mime"] = base_mime(telemetry["content_type"])
        declared = headers.get("Content-Length")
        if (not headers.get("Transfer-Encoding") and isinstance(declared, str)
                and len(declared) <= 20 and declared.isascii() and declared.isdigit()):
            telemetry["declared_content_length"] = int(declared)
        if telemetry["declared_content_length"] is not None and telemetry["declared_content_length"] > MAX_BYTES:
            telemetry.update(error_code="response_byte_limit_exceeded", failure_phase="http_response_headers")
            return telemetry, None
        phase = "response_body_read"
        while True:
            limit = min(READ_CHUNK_BYTES, MAX_BYTES + 1 - len(buffer))
            chunk = response.read(limit)
            if not isinstance(chunk, bytes) or len(chunk) > limit:
                telemetry.update(error_code="response_body_read_contract_violation", failure_phase="response_body_read")
                return telemetry, None
            if not chunk:
                break
            buffer.extend(chunk)
            telemetry["partial_response_byte_count"] = len(buffer)
            if len(buffer) > MAX_BYTES:
                telemetry.update(error_code="response_byte_limit_exceeded", failure_phase="response_body_read")
                return telemetry, None
        length = telemetry["declared_content_length"]
        if length is not None and len(buffer) != length:
            telemetry.update(error_code="content_length_mismatch", failure_phase="response_body_read")
            return telemetry, None
        telemetry["complete_body_received"] = True
        body = bytes(buffer)
    except Exception as exc:
        telemetry.update(classify_exception(exc))
        telemetry["failure_phase"] = phase
        return telemetry, None
    finally:
        try:
            response.close()
        except Exception:
            pass
    telemetry["response_byte_count"] = len(body)
    import hashlib
    telemetry["response_sha256"] = hashlib.sha256(body).hexdigest()
    if len(body) > MAX_BYTES:
        telemetry["error_code"] = "response_byte_limit_exceeded"
        return telemetry, None
    if telemetry["http_status"] != 200:
        telemetry["error_code"] = "http_status_not_200"
        return telemetry, None
    if telemetry["base_mime"] not in ALLOWED_MIME:
        telemetry["error_code"] = "unsupported_content_type"
        return telemetry, None
    try:
        root = _decode_json(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        telemetry["error_code"] = "invalid_json_payload"
        return telemetry, None
    if not isinstance(root, (list, dict)):
        telemetry["error_code"] = "unexpected_json_root"
        return telemetry, None
    return telemetry, body
