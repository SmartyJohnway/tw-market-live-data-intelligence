"""Bounded serialization and request-body reads for Unified HTTP surfaces."""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, Request
from starlette.responses import Response

from .unified_payload_bounds import MAX_UNIFIED_REQUEST_BYTES, MAX_UNIFIED_RESPONSE_BYTES


async def read_bounded_request_body(
    request: Request, max_bytes: int = MAX_UNIFIED_REQUEST_BYTES,
) -> bytes:
    """Read at most max_bytes from the ASGI stream, rejecting before overgrowth."""
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 0:
        raise ValueError("request_body_bound_invalid")
    content_length = request.headers.get("content-length")
    if content_length is not None and content_length.isascii() and content_length.isdecimal():
        if int(content_length) > max_bytes:
            raise HTTPException(status_code=413, detail="request_too_large")

    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        if not isinstance(chunk, bytes):
            chunk = bytes(chunk)
        if len(chunk) > max_bytes - total:
            raise HTTPException(status_code=413, detail="request_too_large")
        if chunk:
            chunks.append(chunk)
            total += len(chunk)
    return b"".join(chunks)


def measure_json_utf8(
    content: Any, *, max_bytes: int | None = None, ensure_ascii: bool = False,
    allow_nan: bool = False, sort_keys: bool = False, indent: int | None = None,
    separators: tuple[str, str] | None = None, newline_translation: bool = False,
) -> int:
    encoder = json.JSONEncoder(
        ensure_ascii=ensure_ascii, allow_nan=allow_nan, sort_keys=sort_keys,
        indent=indent, separators=separators,
    )
    total = 0
    for token in encoder.iterencode(content):
        for start in range(0, len(token), 8192):
            part = token[start:start + 8192]
            total += len(part.encode("utf-8"))
            if newline_translation:
                total += part.count("\n")
            if max_bytes is not None and total > max_bytes:
                return max_bytes + 1
    return total


def measure_text_utf8(
    value: str, *, max_bytes: int | None = None, newline_translation: bool = False,
) -> int:
    total = 0
    for start in range(0, len(value), 8192):
        part = value[start:start + 8192]
        total += len(part.encode("utf-8"))
        if newline_translation:
            total += part.count("\n")
        if max_bytes is not None and total > max_bytes:
            return max_bytes + 1
    return total


def serialize_bounded_json(content: Any, max_bytes: int) -> bytes | None:
    """Serialize once, retaining no more than max_bytes before failing closed."""
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    output = bytearray()
    for token in encoder.iterencode(content):
        for start in range(0, len(token), 8192):
            part = token[start:start + 8192].encode("utf-8")
            if len(part) > max_bytes - len(output):
                return None
            output.extend(part)
    return bytes(output)


def encode_json_response(content: Any) -> bytes:
    """Serialize using Starlette JSONResponse-compatible JSON settings once."""
    encoded = serialize_bounded_json(content, MAX_UNIFIED_RESPONSE_BYTES)
    if encoded is None:
        raise ValueError("response_too_large")
    return encoded


def bounded_json_response(
    content: Any, *, status_code: int = 200,
    max_bytes: int = MAX_UNIFIED_RESPONSE_BYTES,
) -> Response:
    encoded = serialize_bounded_json(content, max_bytes)
    if encoded is None:
        encoded = serialize_bounded_json({"error": "response_too_large"}, max_bytes)
        assert encoded is not None
        status_code = 500
    return Response(content=encoded, status_code=status_code, media_type="application/json")
