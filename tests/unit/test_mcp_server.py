import asyncio
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from server import mcp_server


READONLY_TOOLS = {
    "read_latest_market_snapshot",
    "read_watchlist_observations",
    "read_ai_context_pack",
    "read_chatgpt_briefing",
    "read_m3g_caveats_register",
    "read_source_contract_baseline",
}

LIVE_PROBE_TOOLS = {
    "probe_twse_openapi",
    "probe_tpex_openapi",
    "probe_yahoo_finance",
    "probe_twse_mis",
    "probe_finmind",
}


def decode_text_response(response):
    assert len(response) == 1
    return json.loads(response[0].text)


def test_list_tools_only_includes_readonly_context_tools():
    tools = asyncio.run(mcp_server.list_tools())
    tool_names = {tool.name for tool in tools}

    assert tool_names == READONLY_TOOLS
    assert tool_names.isdisjoint(LIVE_PROBE_TOOLS)


def test_readonly_tool_response_includes_governance_metadata():
    response = asyncio.run(mcp_server.call_tool("read_m3g_caveats_register", {}))
    data = decode_text_response(response)

    assert data["status"] == "ok"
    assert data["governance"]["execution_mode"] == "readonly_local_artifact_read"
    assert data["governance"]["network_calls"] is False
    assert data["governance"]["production_refresh"] is False
    assert data["governance"]["frontend_refresh"] is False
    assert data["governance"]["live_probe_execution"] is False
    assert data["content_type"] == "markdown"
    assert "CAV-M3G" in data["content"]


def test_json_local_artifact_read_works():
    response = asyncio.run(mcp_server.call_tool("read_ai_context_pack", {}))
    data = decode_text_response(response)

    assert data["status"] == "ok"
    assert data["content_type"] == "json"
    assert isinstance(data["content"], dict)
    assert data["source_path"] == "research/generated/ai_context_pack.json"


def test_markdown_local_artifact_read_works():
    response = asyncio.run(mcp_server.call_tool("read_chatgpt_briefing", {}))
    data = decode_text_response(response)

    assert data["status"] == "ok"
    assert data["content_type"] == "markdown"
    assert isinstance(data["content"], str)


def test_missing_file_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setitem(
        mcp_server.READONLY_TOOL_SPECS,
        "read_ai_context_pack",
        {
            "path": "tmp/does-not-exist.json",
            "content_type": "json",
            "description": "missing test artifact",
        },
    )
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    response = asyncio.run(mcp_server.call_tool("read_ai_context_pack", {}))
    data = decode_text_response(response)

    assert data["status"] == "missing_file"
    assert data["error"] == "Required local context artifact not found"
    assert data["governance"]["network_calls"] is False
    assert data["governance"]["live_probe_execution"] is False


def test_live_probe_tool_call_returns_unavailable_without_execution(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("live probe should not be present or executed")

    monkeypatch.setattr(mcp_server, "probe_mis", fail_if_called, raising=False)

    response = asyncio.run(mcp_server.call_tool("probe_twse_mis", {}))
    data = decode_text_response(response)

    assert data["status"] == "unavailable"
    assert data["error"] == "Live probe MCP tools are not exposed in MCP-01 readonly mode"
    assert data["governance"]["network_calls"] is False
    assert data["governance"]["live_probe_execution"] is False


def test_unknown_tool_returns_governed_unavailable_response():
    response = asyncio.run(mcp_server.call_tool("unknown_tool", {}))
    data = decode_text_response(response)

    assert data["status"] == "unavailable"
    assert data["error"] == "Unknown MCP tool is not available in MCP-01 readonly mode"
    assert data["governance"]["production_refresh"] is False
