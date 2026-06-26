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

VALID_CONTROLLED_ARGS = {
    "confirm_controlled_live_probe": True,
    "requested_sources": ["TWSE_OpenAPI"],
    "requested_targets": ["2330"],
    "max_targets": 1,
    "no_artifact_writes": True,
    "no_frontend_writes": True,
    "no_production_refresh": True,
}


def decode_text_response(response):
    assert len(response) == 1
    return json.loads(response[0].text)


def test_list_tools_includes_readonly_context_and_one_controlled_tool_only():
    tools = asyncio.run(mcp_server.list_tools())
    tool_names = {tool.name for tool in tools}

    assert READONLY_TOOLS.issubset(tool_names)
    assert mcp_server.CONTROLLED_LIVE_PROBE_TOOL in tool_names
    assert tool_names == READONLY_TOOLS | {mcp_server.CONTROLLED_LIVE_PROBE_TOOL}
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


def test_controlled_tool_without_confirmation_fails_closed_without_runner(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("controlled runner should not execute")

    monkeypatch.setattr(mcp_server, "run_controlled_probe_runner", fail_if_called)
    args = dict(VALID_CONTROLLED_ARGS, confirm_controlled_live_probe=False)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, args)))

    assert data["status"] == "failed_closed"
    assert data["failure_reason"] == "missing_explicit_confirmation"
    assert data["governance"]["network_calls"] is False
    assert data["governance"]["live_probe_execution"] is False


def test_controlled_tool_invalid_source_or_target_fails_closed_without_runner(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("controlled runner should not execute")

    monkeypatch.setattr(mcp_server, "run_controlled_probe_runner", fail_if_called)

    source_args = dict(VALID_CONTROLLED_ARGS, requested_sources=["FinMind"])
    source_data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, source_args)))
    assert source_data["status"] == "failed_closed"
    assert source_data["failure_reason"] == "source_outside_allowlist"

    target_args = dict(VALID_CONTROLLED_ARGS, requested_targets=["999999"])
    target_data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, target_args)))
    assert target_data["status"] == "failed_closed"
    assert target_data["failure_reason"] == "target_outside_allowlist"


def test_controlled_tool_write_or_refresh_request_fails_closed_without_runner(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("controlled runner should not execute")

    monkeypatch.setattr(mcp_server, "run_controlled_probe_runner", fail_if_called)
    args = dict(VALID_CONTROLLED_ARGS, no_artifact_writes=False)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, args)))

    assert data["status"] == "failed_closed"
    assert data["failure_reason"] == "write_or_refresh_not_explicitly_forbidden"
    assert data["generated_artifacts_updated"] is False
    assert data["frontend_artifacts_updated"] is False
    assert data["production_refreshed"] is False


def test_controlled_tool_valid_confirmation_calls_only_runner_wrapper(monkeypatch):
    calls = []

    def fake_runner(sources, targets):
        calls.append((sources, targets))
        return {"returncode": 0, "stdout_tail": "controlled ok", "stderr_tail": ""}

    monkeypatch.setattr(mcp_server, "run_controlled_probe_runner", fake_runner)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, VALID_CONTROLLED_ARGS)))

    assert calls == [(["TWSE_OpenAPI"], ["2330"])]
    assert data["status"] == "ok"
    assert data["governance"]["network_calls"] is True
    assert data["governance"]["live_probe_execution"] is True
    assert data["governance"]["production_refresh"] is False
    assert data["governance"]["frontend_refresh"] is False
    assert data["governance"]["artifact_writes"] is False
    assert data["governance"]["full_market_scan"] is False
    assert data["governance"]["trading_signal"] is False
    assert data["generated_artifacts_updated"] is False
    assert data["frontend_artifacts_updated"] is False
    assert data["production_refreshed"] is False
    assert "not realtime-guaranteed" in data["statement"]
    assert "not a trading signal" in data["statement"]
    assert data["retrieval_metadata"]["delay_status"] == "source-dependent and not guaranteed realtime"


def test_controlled_tool_missing_runner_path_returns_structured_failure(monkeypatch):
    def fake_missing_runner(sources, targets):
        raise FileNotFoundError("Controlled runner not found: scripts/run_m3g04_controlled_live_probe.py")

    monkeypatch.setattr(mcp_server, "run_controlled_probe_runner", fake_missing_runner)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, VALID_CONTROLLED_ARGS)))

    assert data["status"] == "failed_closed"
    assert data["failure_reason"] == "controlled_runner_missing"
    assert "Controlled runner not found" in data["detail"]
    assert data["governance"]["network_calls"] is False
    assert data["executed_scope"] == {"requested_sources": [], "requested_targets": []}


def test_controlled_tool_runner_error_returns_structured_failure(monkeypatch):
    def fake_error_runner(sources, targets):
        raise RuntimeError("runner failed")

    monkeypatch.setattr(mcp_server, "run_controlled_probe_runner", fake_error_runner)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, VALID_CONTROLLED_ARGS)))

    assert data["status"] == "failed_closed"
    assert data["failure_reason"] == "controlled_runner_error"
    assert data["detail"] == "runner failed"
    assert data["governance"]["network_calls"] is False
