"""Production-owned fixed-endpoint TAIFEX transport.

Explicit approved execution only; no import-time acquisition or persistence.
The frozen bounds and validation order conform to the accepted A3 transport.
"""
from __future__ import annotations

import hashlib
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping

from .phase_i_i2_index_futures_adapters import (
    MAX_RESPONSE_BYTES,
    MAX_ROOT_ROWS,
    SOURCE_ENDPOINT,
    decode_taifex_payload,
)

TIMEOUT_SECONDS = 30
MAX_READ_BYTES = MAX_RESPONSE_BYTES + 1
class ProductionTransportError(RuntimeError):
    def __init__(self, code: str, *, status: int | None = None,
                 content_type: str | None = None, byte_count: int = 0,
                 response_sha256: str | None = None):
        self.code = code
        self.status = status
        self.content_type = content_type
        self.byte_count = byte_count
        self.response_sha256 = response_sha256
        super().__init__(code)


@dataclass(frozen=True)
class AcquiredSource:
    body: bytes
    http_status: int
    content_type: str
    response_byte_count: int
    response_sha256: str
    retrieved_at: str
    get_count: int = 1
    retry_count: int = 0


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _read_once(url: str, timeout: int) -> tuple[int, Mapping[str, str], bytes]:
    if url != SOURCE_ENDPOINT or timeout != TIMEOUT_SECONDS:
        raise ProductionTransportError("source_failed:transport_scope")
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json, application/octet-stream"})
    opener = urllib.request.build_opener(_RejectRedirects())
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        # HTTPError is the one response to this request, including redirects;
        # never follow or retry it.
        headers = dict(exc.headers.items()) if exc.headers else {}
        body = exc.read(MAX_READ_BYTES)
        return exc.code, headers, body
    with response:
        body = response.read(MAX_READ_BYTES)
        return int(response.status), dict(response.headers.items()), body


def _base_media_type(headers: Mapping[str, str]) -> str | None:
    raw = next((value for key, value in headers.items() if key.lower() == "content-type"), None)
    if not isinstance(raw, str):
        return None
    return raw.split(";", 1)[0].strip().lower() or None


def acquire_taifex_once(
    *,
    transport: Callable[[str, int], tuple[int, Mapping[str, str], bytes]] | None,
    clock: Callable[[], datetime] | None = None,
) -> AcquiredSource:
    """Acquire one fixed-endpoint response through an explicit delegate.

Execution-root single-use enforcement belongs to the approval-bound adapter.
An absent delegate fails before I/O; this module has no implicit acquisition.
    """
    if transport is None:
        raise ProductionTransportError("live_execution_not_rearmed")
    try:
        status, headers, body = transport(SOURCE_ENDPOINT, TIMEOUT_SECONDS)
    except Exception as exc:
        raise ProductionTransportError("source_failed:transport_exception") from exc
    if not isinstance(body, bytes):
        raise ProductionTransportError("source_failed:body_not_bytes", status=status)
    byte_count = len(body)
    digest = hashlib.sha256(body).hexdigest()
    media_type = _base_media_type(headers)
    if byte_count > MAX_RESPONSE_BYTES:
        raise ProductionTransportError("source_failed:response_too_large", status=status, content_type=media_type,
                               byte_count=min(byte_count, MAX_READ_BYTES), response_sha256=digest)
    if status != 200:
        raise ProductionTransportError("source_failed:http_status", status=status, content_type=media_type,
                               byte_count=byte_count, response_sha256=digest)
    if media_type not in {"application/octet-stream", "application/json"}:
        raise ProductionTransportError("source_failed:content_type", status=status, content_type=media_type,
                               byte_count=byte_count, response_sha256=digest)
    rows, decode_error = decode_taifex_payload(body)
    if decode_error:
        raise ProductionTransportError(decode_error, status=status, content_type=media_type,
                               byte_count=byte_count, response_sha256=digest)
    if rows is None or len(rows) > MAX_ROOT_ROWS:
        raise ProductionTransportError("source_failed:payload_invalid", status=status, content_type=media_type,
                               byte_count=byte_count, response_sha256=digest)
    observed_at = (clock or (lambda: datetime.now(timezone.utc)))()
    retrieved_at = observed_at.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return AcquiredSource(body=body, http_status=status, content_type=media_type,
                          response_byte_count=byte_count, response_sha256=digest,
                          retrieved_at=retrieved_at)
