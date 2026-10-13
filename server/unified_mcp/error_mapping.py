"""Sanitized MCP error results for bounded Local Service failures."""
from __future__ import annotations

import json
from typing import Any

from server.operational_diagnostics import new_trace_id, normalize_trace_id

from mcp.types import CallToolResult, TextContent

from .local_service_client import LocalServiceClientError


def _result(payload: dict[str, Any]) -> CallToolResult:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return CallToolResult(content=[TextContent(type="text", text=text)], structuredContent=payload, isError=True)


def map_local_service_error(exc: LocalServiceClientError, *, trace_id: str | None = None) -> CallToolResult:
    """Preserve bounded upstream details without leaking body/headers/exceptions."""
    if exc.code == "local_service_http_error" and isinstance(exc.payload, dict):
        payload: dict[str, Any] = {"http_status": exc.status_code}
        for key in ("error", "trace_id", "detail"):
            value = exc.payload.get(key)
            if isinstance(value, (str, int, float, bool)):
                payload[key] = value
        if "error" not in payload and "detail" not in payload:
            payload["error"] = "local_service_http_error"
        if "trace_id" not in payload:
            payload["trace_id"] = normalize_trace_id(trace_id) or new_trace_id()
        return _result(payload)
    return _result({"error": exc.code, "trace_id": normalize_trace_id(trace_id) or new_trace_id()})


def map_internal_error(*, trace_id: str | None = None) -> CallToolResult:
    return _result({"error": "mcp_adapter_internal_error", "trace_id": normalize_trace_id(trace_id) or new_trace_id()})
