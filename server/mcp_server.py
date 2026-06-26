"""MCP server for readonly Taiwan market context artifacts.

MCP-01 intentionally exposes local readonly context tools first. It does not
import or execute live probe modules; controlled live probing remains outside
this default MCP surface until a future explicitly governed milestone.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

app = Server("tw-market-mcp")

REPO_ROOT = Path(__file__).resolve().parents[1]

READONLY_TOOL_SPECS: dict[str, dict[str, str]] = {
    "read_latest_market_snapshot": {
        "path": "research/generated/latest_market_snapshot.json",
        "content_type": "json",
        "description": "Read the readonly latest market snapshot artifact from local disk.",
    },
    "read_watchlist_observations": {
        "path": "research/generated/watchlist_observations.json",
        "content_type": "json",
        "description": "Read the readonly watchlist observations artifact from local disk.",
    },
    "read_ai_context_pack": {
        "path": "research/generated/ai_context_pack.json",
        "content_type": "json",
        "description": "Read the readonly AI context pack artifact from local disk.",
    },
    "read_chatgpt_briefing": {
        "path": "research/generated/chatgpt_briefing.md",
        "content_type": "markdown",
        "description": "Read the readonly ChatGPT briefing artifact from local disk.",
    },
    "read_m3g_caveats_register": {
        "path": "docs/protocol/M3G_CURRENT_CAVEATS_REGISTER.md",
        "content_type": "markdown",
        "description": "Read the governed caveats register from local disk.",
    },
    "read_source_contract_baseline": {
        "path": "docs/protocol/M2_SOURCE_CONTRACT_BASELINE.md",
        "content_type": "markdown",
        "description": "Read the source contract baseline from local disk.",
    },
}

LEGACY_LIVE_PROBE_TOOLS = {
    "probe_twse_openapi",
    "probe_tpex_openapi",
    "probe_yahoo_finance",
    "probe_twse_mis",
    "probe_finmind",
}


def readonly_governance() -> dict[str, Any]:
    """Governance metadata shared by all MCP-01 readonly tool responses."""
    return {
        "surface": "MCP readonly context tool",
        "execution_mode": "readonly_local_artifact_read",
        "network_calls": False,
        "production_refresh": False,
        "frontend_refresh": False,
        "live_probe_execution": False,
        "caveats": [
            "readonly_local_context",
            "not_live_market_data",
            "not_trading_signal",
            "no_artifact_refresh",
        ],
    }


def _json_text(payload: dict[str, Any]) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]


def _resolve_source_path(source_path: str) -> Path:
    return (REPO_ROOT / source_path).resolve()


def read_local_context_tool(tool_name: str) -> dict[str, Any]:
    """Read a configured local context artifact with fail-closed semantics."""
    spec = READONLY_TOOL_SPECS.get(tool_name)
    if spec is None:
        return unavailable_tool_response(tool_name)

    source_path = spec["path"]
    content_type = spec["content_type"]
    payload: dict[str, Any] = {
        "governance": readonly_governance(),
        "tool": tool_name,
        "source_path": source_path,
        "content_type": content_type,
    }

    resolved_path = _resolve_source_path(source_path)
    if not resolved_path.is_file():
        payload.update(
            {
                "status": "missing_file",
                "error": "Required local context artifact not found",
            }
        )
        return payload

    raw_content = resolved_path.read_text(encoding="utf-8")
    if content_type == "json":
        try:
            content: Any = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            payload.update(
                {
                    "status": "invalid_json",
                    "error": f"Local context artifact is not valid JSON: {exc.msg}",
                }
            )
            return payload
    else:
        content = raw_content

    payload.update({"status": "ok", "content": content})
    return payload


def unavailable_tool_response(tool_name: str) -> dict[str, Any]:
    """Return a governed unavailable response for unknown or live probe tools."""
    error = "Live probe MCP tools are not exposed in MCP-01 readonly mode"
    if tool_name not in LEGACY_LIVE_PROBE_TOOLS:
        error = "Unknown MCP tool is not available in MCP-01 readonly mode"
    return {
        "governance": readonly_governance(),
        "tool": tool_name,
        "status": "unavailable",
        "error": error,
    }


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List only readonly local context tools for the AI agent."""
    return [
        Tool(
            name=name,
            description=spec["description"],
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        )
        for name, spec in READONLY_TOOL_SPECS.items()
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Handle readonly MCP tool requests without executing live probes."""
    if name in READONLY_TOOL_SPECS:
        return _json_text(read_local_context_tool(name))
    return _json_text(unavailable_tool_response(name))


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
