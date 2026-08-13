"""Launch the M8R-08B unified MCP adapter over stdio only."""
from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.stdio import stdio_server

from server.unified_mcp import ADAPTER_VERSION
from server.unified_mcp.local_service_client import DEFAULT_SERVICE_URL, LocalServiceClientError, UnifiedLocalServiceClient
from server.unified_mcp.server import build_unified_market_evidence_mcp_server

EXIT_CONFIGURATION = 2
EXIT_LOCAL_SERVICE = 3
EXIT_DEPENDENCY = 4


def _stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _runtime_version() -> str:
    return importlib.metadata.version("mcp")


async def _serve(service_url: str) -> int:
    if _runtime_version() != "1.29.0":
        _stderr("M8R-08B requires mcp==1.29.0")
        return EXIT_DEPENDENCY
    try:
        client = UnifiedLocalServiceClient(service_url)
        await client.verify_service_contract()
    except LocalServiceClientError as exc:
        _stderr(f"Unified Local Service startup check failed: {exc.code}")
        return EXIT_LOCAL_SERVICE
    app = build_unified_market_evidence_mcp_server(client=client)
    _stderr(f"Starting {ADAPTER_VERSION} over stdio")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="M8R-08 unified MCP stdio safe-tool adapter")
    parser.add_argument("--service-url", default=os.environ.get("UNIFIED_MARKET_EVIDENCE_SERVICE_URL", DEFAULT_SERVICE_URL))
    parser.add_argument("--startup-check", action="store_true", help="Verify SDK and Local Service compatibility, then exit.")
    args = parser.parse_args()
    if args.startup_check:
        async def check() -> int:
            if _runtime_version() != "1.29.0":
                _stderr("M8R-08B requires mcp==1.29.0")
                return EXIT_DEPENDENCY
            try:
                client = UnifiedLocalServiceClient(args.service_url)
                await client.verify_service_contract()
            except LocalServiceClientError as exc:
                _stderr(f"Unified Local Service startup check failed: {exc.code}")
                return EXIT_LOCAL_SERVICE
            _stderr(f"startup_check=ok adapter={ADAPTER_VERSION} mcp={_runtime_version()}")
            return 0
        return asyncio.run(check())
    return asyncio.run(_serve(args.service_url))


if __name__ == "__main__":
    raise SystemExit(main())
