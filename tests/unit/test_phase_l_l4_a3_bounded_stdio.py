from __future__ import annotations

import asyncio
import io
from types import SimpleNamespace

from mcp.types import JSONRPCMessage
from server.unified_mcp.bounded_stdio import BoundedStdin
from server.unified_payload_bounds import MAX_UNIFIED_REQUEST_BYTES


def _read_all(stream: BoundedStdin) -> list[str]:
    async def collect():
        result = []
        async for line in stream:
            result.append(line)
        return result
    return asyncio.run(collect())


def test_stdio_frame_accepts_limit_minus_one_and_limit():
    for limit in (7, 8):
        stream = BoundedStdin(io.BytesIO(b"x" * (limit - 1) + b"\n"), max_line_bytes=limit)
        assert _read_all(stream) == ["x" * (limit - 1) + "\n"]
        assert stream.oversized is False


def test_stdio_frame_over_limit_terminates_without_yielding_truncated_json(capsys):
    stream = BoundedStdin(io.BytesIO(b"{" + b"x" * 8 + b"\n"), max_line_bytes=8)
    assert _read_all(stream) == []
    assert stream.oversized is True
    assert "frame exceeds" in capsys.readouterr().err


def test_stdio_first_frame_prefetch_rejects_before_launcher_service_check():
    async def check(data: bytes):
        stream = BoundedStdin(io.BytesIO(data), max_line_bytes=8)
        accepted = await stream.prefetch_first_frame()
        return accepted, stream

    accepted, stream = asyncio.run(check(b"{" + b"x" * 8 + b"\n"))
    assert accepted is False
    assert stream.oversized is True


def test_oversized_first_stdio_frame_performs_no_local_service_call(monkeypatch, capsys):
    from scripts import run_unified_market_evidence_mcp as launcher
    oversized = b"{" + b"x" * MAX_UNIFIED_REQUEST_BYTES + b"\n"
    monkeypatch.setattr(launcher.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(oversized)))
    monkeypatch.setattr(launcher, "_runtime_version", lambda: "1.29.0")
    monkeypatch.setattr(
        launcher, "UnifiedLocalServiceClient",
        lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("Local Service must not be touched")),
    )
    assert asyncio.run(launcher._serve(launcher.DEFAULT_SERVICE_URL)) == 0
    assert "frame exceeds" in capsys.readouterr().err


def test_stdio_prefetch_preserves_valid_sdk_line_and_production_limit():
    async def check():
        stream = BoundedStdin(io.BytesIO(b'{"jsonrpc":"2.0"}\n'))
        assert await stream.prefetch_first_frame() is True
        return [line async for line in stream]

    assert asyncio.run(check()) == ['{"jsonrpc":"2.0"}\n']
    assert MAX_UNIFIED_REQUEST_BYTES == 1 * 1024 * 1024


def test_bounded_stream_remains_compatible_with_mcp_129_jsonrpc_parser():
    line = (
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":'
        '{"protocolVersion":"2024-11-05","capabilities":{},'
        '"clientInfo":{"name":"bounded-test","version":"1"}}}\n'
    )
    parsed = JSONRPCMessage.model_validate_json(_read_all(BoundedStdin(io.BytesIO(line.encode("utf-8"))))[0])
    assert parsed.root.method == "initialize"
