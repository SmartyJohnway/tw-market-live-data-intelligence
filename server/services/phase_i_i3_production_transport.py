"""Single-dispatch official I3 transport for the dormant A4 candidate.

No fallback, retry, caller-controlled URL, or raw-body persistence is provided.
Tests inject an opener; production calls occur only through approved dispatch.
"""
from __future__ import annotations

import hashlib
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import Message
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener

from scripts.ssl_policy import build_ssl_context

MAX_BYTES = 4 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024
TIMEOUT_SECONDS = 30
URLS = {
    "TWSE": "https://www.twse.com.tw/rwd/zh/fund/T86?date={date}&selectType=ALLBUT0999&response=json",
    "TPEX": "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading",
}
TLS_POLICY = {"TWSE": "compatibility", "TPEX": "strict"}


class _RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class Acquisition:
    body: bytes
    telemetry: dict[str, Any]


class AcquisitionError(RuntimeError):
    def __init__(self, code: str, telemetry: dict[str, Any]):
        super().__init__(code)
        self.code = code
        self.telemetry = telemetry


def fixed_url(market: str, resolved_source_trade_date: str | None = None) -> str:
    if market not in URLS:
        raise ValueError("i3_market_unsupported")
    if market == "TWSE":
        if not isinstance(resolved_source_trade_date, str):
            raise ValueError("i3_twse_bound_date_required")
        try:
            from datetime import date
            parsed = date.fromisoformat(resolved_source_trade_date)
        except ValueError as exc:
            raise ValueError("i3_twse_bound_date_invalid") from exc
        if parsed.isoformat() != resolved_source_trade_date:
            raise ValueError("i3_twse_bound_date_invalid")
        return URLS[market].format(date=parsed.strftime("%Y%m%d"))
    if resolved_source_trade_date is not None:
        raise ValueError("i3_tpex_query_date_forbidden")
    return URLS[market]


def _opener(policy: str):
    if policy == "strict":
        return build_opener(_RejectRedirect())
    if policy == "compatibility":
        context = build_ssl_context("compatibility")
        if not isinstance(context, ssl.SSLContext) or context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
            raise ValueError("i3_verified_compatibility_context_invalid")
        return build_opener(_RejectRedirect(), HTTPSHandler(context=context))
    raise ValueError("i3_tls_policy_invalid")


def _base_telemetry(market: str) -> dict[str, Any]:
    return {
        "mode": "official_https_live", "network_get_count": 0, "retry_count": 0,
        "http_status": None, "content_type": None, "complete_body_received": False,
        "response_byte_count": 0, "partial_response_byte_count": 0,
        "response_sha256": None, "tls_policy": TLS_POLICY[market],
        "redirect_policy": "reject", "raw_payload_persisted": False,
        "failure_phase": None, "error_code": None,
    }


def acquire_once(
    market: str,
    *,
    resolved_source_trade_date: str | None = None,
    opener: Any | None = None,
    clock: Callable[[], datetime] | None = None,
) -> Acquisition:
    """Perform one fixed-endpoint GET and return only a complete bounded body."""
    url = fixed_url(market, resolved_source_trade_date)
    policy = TLS_POLICY[market]
    client = opener if opener is not None else _opener(policy)
    telemetry = _base_telemetry(market)
    now = clock or (lambda: datetime.now(timezone.utc))
    timestamp = now()
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("i3_retrieval_clock_timezone_required")
    telemetry["retrieved_at"] = timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "tw-market-live-data-intelligence/1.0"}, method="GET")
        # This is the only HTTP dispatch boundary in this module.
        telemetry["network_get_count"] = 1
        response = client.open(req, timeout=TIMEOUT_SECONDS)
    except HTTPError as exc:
        telemetry.update(http_status=exc.code, content_type=exc.headers.get("Content-Type"), failure_phase="http_response", error_code="http_error")
        raise AcquisitionError("http_error", telemetry) from exc
    except (URLError, OSError, TimeoutError) as exc:
        telemetry.update(failure_phase="connection", error_code=type(exc).__name__[:64])
        raise AcquisitionError("transport_error", telemetry) from exc

    partial = bytearray()
    try:
        status = getattr(response, "status", None)
        telemetry["http_status"] = status if status is not None else response.getcode()
        headers = getattr(response, "headers", Message())
        raw_type = headers.get("Content-Type")
        mime = raw_type.split(";", 1)[0].strip().lower() if isinstance(raw_type, str) else ""
        telemetry["content_type"] = mime or None
        if mime != "application/json":
            telemetry.update(failure_phase="response_headers", error_code="unsupported_mime")
            raise AcquisitionError("unsupported_mime", telemetry)
        declared = headers.get("Content-Length")
        if isinstance(declared, str) and declared.isascii() and declared.isdecimal():
            declared_int = int(declared)
            telemetry["declared_content_length"] = declared_int
            if declared_int > MAX_BYTES:
                telemetry.update(failure_phase="response_headers", error_code="response_byte_limit_exceeded")
                raise AcquisitionError("response_byte_limit_exceeded", telemetry)
        else:
            declared_int = None
        while True:
            chunk = response.read(min(READ_CHUNK_BYTES, MAX_BYTES - len(partial) + 1))
            if not chunk:
                break
            if len(partial) + len(chunk) > MAX_BYTES:
                telemetry.update(failure_phase="response_body_read", partial_response_byte_count=min(MAX_BYTES + 1, len(partial) + len(chunk)), error_code="response_byte_limit_exceeded")
                raise AcquisitionError("response_byte_limit_exceeded", telemetry)
            partial.extend(chunk)
        if declared_int is not None and len(partial) != declared_int:
            telemetry.update(failure_phase="response_body_read", partial_response_byte_count=len(partial), error_code="content_length_mismatch")
            raise AcquisitionError("content_length_mismatch", telemetry)
        if telemetry["http_status"] != 200:
            telemetry.update(failure_phase="http_response", error_code="http_status_not_200")
            raise AcquisitionError("http_status_not_200", telemetry)
        body = bytes(partial)
        if not body:
            telemetry.update(failure_phase="response_body_read", error_code="empty_body")
            raise AcquisitionError("empty_body", telemetry)
        telemetry.update(complete_body_received=True, response_byte_count=len(body), partial_response_byte_count=0,
                        response_sha256=hashlib.sha256(body).hexdigest(), retrieved_at=timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"))
        return Acquisition(body, telemetry)
    except AcquisitionError:
        # No partial bytes escape the transport layer.
        raise
    except (URLError, OSError, TimeoutError) as exc:
        telemetry.update(failure_phase="response_body_read", complete_body_received=False,
                        partial_response_byte_count=len(partial), response_byte_count=0,
                        response_sha256=None, error_code=type(exc).__name__[:64])
        raise AcquisitionError("body_read_failed", telemetry) from exc
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()
