"""Bound raw MCP stdio JSON-RPC lines before the SDK parses JSON."""
from __future__ import annotations

import sys
from typing import BinaryIO

import anyio

from server.unified_payload_bounds import MAX_UNIFIED_REQUEST_BYTES


class BoundedStdin:
    """Async text-file compatible iterator with a bounded raw line buffer."""

    def __init__(self, binary_stdin: BinaryIO, *, max_line_bytes: int = MAX_UNIFIED_REQUEST_BYTES):
        if isinstance(max_line_bytes, bool) or not isinstance(max_line_bytes, int) or max_line_bytes < 0:
            raise ValueError("mcp_frame_bound_invalid")
        self._stream = binary_stdin
        self._limit = max_line_bytes
        self._buffer = bytearray()
        self._eof = False
        self.oversized = False
        self._prefetched: str | None = None

    def __aiter__(self) -> "BoundedStdin":
        return self

    async def __anext__(self) -> str:
        if self._prefetched is not None:
            line, self._prefetched = self._prefetched, None
            return line
        while True:
            newline = self._buffer.find(b"\n")
            if newline >= 0:
                if newline + 1 > self._limit:
                    self._reject()
                    raise StopAsyncIteration
                line = bytes(self._buffer[:newline + 1])
                del self._buffer[:newline + 1]
                return line.decode("utf-8", errors="replace")
            if len(self._buffer) > self._limit:
                self._reject()
                raise StopAsyncIteration
            if self._eof:
                if not self._buffer:
                    raise StopAsyncIteration
                if len(self._buffer) > self._limit:
                    self._reject()
                    raise StopAsyncIteration
                line = bytes(self._buffer)
                self._buffer.clear()
                return line.decode("utf-8", errors="replace")

            read_size = min(64 * 1024, self._limit - len(self._buffer) + 1)
            reader = getattr(self._stream, "read1", self._stream.read)
            chunk = await anyio.to_thread.run_sync(reader, max(1, read_size))
            if not chunk:
                self._eof = True
            else:
                self._buffer.extend(chunk)

    async def prefetch_first_frame(self) -> bool:
        """Bound the first frame before the launcher performs its service check."""
        try:
            self._prefetched = await self.__anext__()
        except StopAsyncIteration:
            return False
        return True

    def _reject(self) -> None:
        self.oversized = True
        print("MCP input frame exceeds the configured request bound; stdio transport terminated.", file=sys.stderr, flush=True)
