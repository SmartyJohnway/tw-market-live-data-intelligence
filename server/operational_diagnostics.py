"""Lean operational correlation and bounded diagnostics for the local runtime."""
from __future__ import annotations

import contextvars
import datetime as dt
import json
import os
from pathlib import Path
import sys
from typing import Any, TextIO
import uuid

TRACE_HEADER = "X-TW-Market-Trace-ID"
TRACE_ENV = "TW_MARKET_OPERATIONAL_TRACE_ID"
EVENT_PATH_ENV = "TW_MARKET_OPERATIONAL_EVENT_PATH"
EVENT_SCHEMA_VERSION = "tw_market_operational_event.v1"
MAX_STRING_CHARS = 256
MAX_EVENT_BYTES = 4096
MAX_EVENT_FILE_BYTES = 256 * 1024

_TRACE_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "tw_market_operational_trace_id", default=None
)
_LEVELS = frozenset({"INFO", "WARN", "ERROR"})
_REFERENCE_FIELDS = frozenset({
    "lifecycle_operation_id", "request_id", "execution_request_id",
    "governed_operation_id", "authorization_id", "execution_receipt_id",
})
_METRIC_FIELDS = frozenset({
    "duration_ms", "http_status", "request_bytes", "response_bytes",
    "child_returncode", "process_memory_bytes",
})


def normalize_trace_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return None
    return str(parsed)


def new_trace_id() -> str:
    return str(uuid.uuid4())


def bind_trace_id(value: object = None) -> tuple[str, contextvars.Token]:
    trace_id = normalize_trace_id(value) or new_trace_id()
    return trace_id, _TRACE_ID.set(trace_id)


def reset_trace_id(token: contextvars.Token) -> None:
    _TRACE_ID.reset(token)


def current_trace_id() -> str:
    current = _TRACE_ID.get()
    if current is not None:
        return current
    trace_id = new_trace_id()
    _TRACE_ID.set(trace_id)
    return trace_id


def _bounded_string(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value[:MAX_STRING_CHARS]


def build_event(
    *, component: str, event_code: str, status: str, trace_id: object = None,
    level: str = "INFO", reason_code: object = None,
    references: dict[str, object] | None = None,
    metrics: dict[str, object] | None = None,
) -> dict[str, Any]:
    normalized = normalize_trace_id(trace_id) or current_trace_id()
    event: dict[str, Any] = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "level": level if level in _LEVELS else "INFO",
        "component": _bounded_string(component) or "runtime",
        "event_code": _bounded_string(event_code) or "runtime.event",
        "trace_id": normalized,
        "status": _bounded_string(status) or "unknown",
    }
    reason = _bounded_string(reason_code)
    if reason is not None:
        event["reason_code"] = reason
    for key, value in (references or {}).items():
        if key in _REFERENCE_FIELDS:
            bounded = _bounded_string(value)
            if bounded is not None:
                event[key] = bounded
    bounded_metrics: dict[str, int | float | bool | None] = {}
    for key, value in (metrics or {}).items():
        if key in _METRIC_FIELDS and (
            value is None or isinstance(value, (int, float, bool))
        ):
            bounded_metrics[key] = value
    if bounded_metrics:
        event["metrics"] = bounded_metrics
    return event


def serialize_event(event: dict[str, Any]) -> str:
    line = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(line.encode("utf-8")) > MAX_EVENT_BYTES:
        raise ValueError("operational_event_too_large")
    return line


def event_path_from_env() -> Path | None:
    raw = os.environ.get(EVENT_PATH_ENV)
    if not raw:
        return None
    try:
        return Path(raw).expanduser().resolve()
    except (OSError, ValueError):
        return None


def emit_jsonl(event: dict[str, Any], path: Path | None = None) -> bool:
    target = path or event_path_from_env()
    if target is None:
        return False
    try:
        if not target.parent.is_dir():
            return False
        line = serialize_event(event) + "\n"
        encoded = line.encode("utf-8")
        existing = target.stat().st_size if target.exists() else 0
        if existing + len(encoded) > MAX_EVENT_FILE_BYTES:
            target.write_text("", encoding="utf-8")
        with target.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(line)
        return True
    except (OSError, ValueError):
        return False


def emit_stderr(event: dict[str, Any], stream: TextIO | None = None) -> bool:
    destination = stream or sys.stderr
    try:
        destination.write(serialize_event(event) + "\n")
        destination.flush()
        return True
    except (OSError, ValueError):
        return False


def emit_runtime_event(**kwargs: Any) -> bool:
    try:
        return emit_jsonl(build_event(**kwargs))
    except (TypeError, ValueError):
        return False
