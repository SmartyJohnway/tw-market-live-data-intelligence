"""Bounded fixed-loopback HTTP delegation for the Unified Local Service."""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

from . import LOCAL_SERVICE_CONTRACT_VERSION
from .tool_contracts import CONTROL_PACKAGE_PATTERN
import re

DEFAULT_SERVICE_URL = "http://127.0.0.1:8000"
MAX_REQUEST_BYTES = 1 * 1024 * 1024
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
TIMEOUT_SECONDS = 15.0

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_CONTROL_ID = re.compile(CONTROL_PACKAGE_PATTERN)


class LocalServiceClientError(Exception):
    def __init__(self, code: str, *, status_code: int | None = None, payload: dict[str, Any] | None = None):
        self.code = code
        self.status_code = status_code
        self.payload = payload
        super().__init__(code)


def validate_loopback_service_url(value: str) -> str:
    """Return a normalized allowed base URL or fail before any connection."""
    if not isinstance(value, str):
        raise LocalServiceClientError("local_service_url_invalid")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise LocalServiceClientError("local_service_url_invalid") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname not in _LOOPBACK_HOSTS
        or port is None
        or not 1 <= port <= 65535
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise LocalServiceClientError("local_service_url_invalid")
    host = "[::1]" if parsed.hostname == "::1" else "127.0.0.1" if parsed.hostname == "localhost" else parsed.hostname
    return urlunsplit(("http", f"{host}:{port}", "", "", ""))


class UnifiedLocalServiceClient:
    """A one-operation/one-request adapter with no fallback endpoint or retry."""

    def __init__(self, base_url: str = DEFAULT_SERVICE_URL, *, timeout_seconds: float = TIMEOUT_SECONDS, max_response_bytes: int = MAX_RESPONSE_BYTES):
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise LocalServiceClientError("local_service_timeout_invalid")
        if not isinstance(max_response_bytes, int) or max_response_bytes <= 0:
            raise LocalServiceClientError("local_service_response_bound_invalid")
        self.base_url = validate_loopback_service_url(base_url)
        self.timeout_seconds = float(timeout_seconds)
        self.max_response_bytes = max_response_bytes

    def _url(self, route: str) -> str:
        return f"{self.base_url}{route}"

    async def _request(self, method: str, route: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body: bytes | None = None
        headers: dict[str, str] = {"Accept": "application/json"}
        if payload is not None:
            try:
                body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            except (TypeError, ValueError) as exc:
                raise LocalServiceClientError("local_service_request_invalid") from exc
            if len(body) > MAX_REQUEST_BYTES:
                raise LocalServiceClientError("local_service_request_too_large")
            headers["Content-Type"] = "application/json"
        timeout = httpx.Timeout(self.timeout_seconds)
        try:
            async with httpx.AsyncClient(
                trust_env=False,
                follow_redirects=False,
                timeout=timeout,
                headers=headers,
            ) as client:
                async with client.stream(method, self._url(route), content=body) as response:
                    if response.is_redirect:
                        raise LocalServiceClientError("local_service_protocol_invalid")
                    received = bytearray()
                    async for chunk in response.aiter_bytes():
                        received.extend(chunk)
                        if len(received) > self.max_response_bytes:
                            raise LocalServiceClientError("local_service_response_too_large")
        except LocalServiceClientError:
            raise
        except httpx.TimeoutException as exc:
            raise LocalServiceClientError("local_service_timeout") from exc
        except httpx.HTTPError as exc:
            raise LocalServiceClientError("local_service_unavailable") from exc
        try:
            decoded = json.loads(bytes(received).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LocalServiceClientError("local_service_protocol_invalid") from exc
        if not isinstance(decoded, dict):
            raise LocalServiceClientError("local_service_protocol_invalid")
        if response.status_code != 200:
            raise LocalServiceClientError("local_service_http_error", status_code=response.status_code, payload=decoded)
        return decoded

    async def describe_capabilities(self) -> dict[str, Any]:
        return await self._request("GET", "/api/unified/capabilities")

    async def verify_service_contract(self) -> dict[str, Any]:
        payload = await self.describe_capabilities()
        if payload.get("service_contract_version") != LOCAL_SERVICE_CONTRACT_VERSION:
            raise LocalServiceClientError("local_service_contract_incompatible")
        return payload

    async def validate_request(self, request_envelope: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/unified/validate-request", request_envelope)

    async def preview_request(self, request_envelope: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/unified/preview-request", request_envelope)

    @staticmethod
    def _validate_control_package_id(control_package_id: object) -> str:
        if not isinstance(control_package_id, str) or _CONTROL_ID.fullmatch(control_package_id) is None:
            raise LocalServiceClientError("control_package_id_invalid")
        return control_package_id

    async def read_result(self, control_package_id: object) -> dict[str, Any]:
        identifier = self._validate_control_package_id(control_package_id)
        return await self._request("POST", "/api/unified/result-package", {"control_package_id": identifier})

    async def export_ai_handoff(self, control_package_id: object) -> dict[str, Any]:
        identifier = self._validate_control_package_id(control_package_id)
        return await self._request("GET", f"/api/unified/result-package/{identifier}/handoff")
