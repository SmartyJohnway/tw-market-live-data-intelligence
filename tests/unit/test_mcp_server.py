import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

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


def write_target_config(repo_root):
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "market_targets.json").write_text(
        json.dumps({"test": {"symbols": {"standard": ["2330", "8069"]}}}),
        encoding="utf-8",
    )


def valid_run_summary(targets=None, sources=None, results=None):
    return {
        "targets": targets or ["2330"],
        "sources_requested": sources or ["TWSE_OpenAPI"],
        "results": results if results is not None else {"TWSE_OpenAPI": {"2330": {"status": "ok"}}},
    }


def test_list_tools_includes_readonly_context_and_one_controlled_tool_only():
    tools = asyncio.run(mcp_server.list_tools())
    tool_names = {tool.name for tool in tools}

    assert READONLY_TOOLS.issubset(tool_names)
    assert mcp_server.CONTROLLED_LIVE_PROBE_TOOL in tool_names
    assert mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL in tool_names
    evidence_tools = {name for name in tool_names if "evidence" in name and name.startswith("read_m3g04")}
    assert evidence_tools == {mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL}
    assert tool_names == READONLY_TOOLS | {mcp_server.CONTROLLED_LIVE_PROBE_TOOL, mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL}
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
        return {
            "returncode": 0,
            "stdout_tail": "controlled ok",
            "stderr_tail": "",
            "controlled_summary": {"timestamp": "2026-06-26T00:00:00+00:00"},
            "runner_started": True,
            "network_calls_may_have_occurred": True,
            "repo_artifacts_updated": False,
            "temporary_evidence_directory_removed": True,
        }

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
    assert data["governance"]["runner_started"] is True
    assert data["governance"]["network_calls_may_have_occurred"] is True
    assert data["generated_artifacts_updated"] is False
    assert data["frontend_artifacts_updated"] is False
    assert data["production_refreshed"] is False
    assert "not realtime-guaranteed" in data["statement"]
    assert "not a trading signal" in data["statement"]
    assert data["retrieval_metadata"]["delay_status"] == "source-dependent and not guaranteed realtime"
    assert data["result"]["controlled_summary"]["timestamp"] == "2026-06-26T00:00:00+00:00"
    assert data["result"]["repo_artifacts_updated"] is False
    assert data["result"]["temporary_evidence_directory_removed"] is True


def test_controlled_tool_duplicate_scope_fails_closed_without_runner(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("controlled runner should not execute")

    monkeypatch.setattr(mcp_server, "run_controlled_probe_runner", fail_if_called)

    duplicate_sources = dict(VALID_CONTROLLED_ARGS, requested_sources=["TWSE_OpenAPI", "TWSE_OpenAPI"])
    source_data = decode_text_response(
        asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, duplicate_sources))
    )
    assert source_data["status"] == "failed_closed"
    assert source_data["failure_reason"] == "duplicate_source_scope"

    duplicate_targets = dict(VALID_CONTROLLED_ARGS, requested_targets=["2330", "2330"], max_targets=2)
    target_data = decode_text_response(
        asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, duplicate_targets))
    )
    assert target_data["status"] == "failed_closed"
    assert target_data["failure_reason"] == "duplicate_target_scope"


def test_controlled_runner_wrapper_uses_temp_cwd_and_returns_summary(monkeypatch, tmp_path):
    runner_path = tmp_path / mcp_server.CONTROLLED_RUNNER_RELATIVE_PATH
    runner_path.parent.mkdir(parents=True)
    runner_path.write_text("# fake runner path for wrapper test\n", encoding="utf-8")
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    calls = []

    def fake_subprocess_run(command, cwd, env, **kwargs):
        calls.append({"command": command, "cwd": Path(cwd), "env": env, "kwargs": kwargs})
        evidence_dir = Path(cwd) / "research" / "live_probe_runs" / "m3g_04"
        evidence_dir.mkdir(parents=True)
        (evidence_dir / "run_summary_20260626_000000.json").write_text(
            json.dumps({"timestamp": "2026-06-26T00:00:00+00:00", "results": {}}),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, stdout="wrapper ok", stderr="")

    monkeypatch.setattr(mcp_server.subprocess, "run", fake_subprocess_run)

    result = mcp_server.run_controlled_probe_runner(["TWSE_OpenAPI"], ["2330"])

    assert result["status"] == "ok"
    assert result["returncode"] == 0
    assert result["controlled_summary"] == {"timestamp": "2026-06-26T00:00:00+00:00", "results": {}}
    assert result["runner_started"] is True
    assert result["network_calls_may_have_occurred"] is True
    assert result["repo_artifacts_updated"] is False
    assert result["temporary_evidence_directory_removed"] is True
    assert calls[0]["command"][0] == sys.executable
    assert calls[0]["cwd"] != tmp_path
    assert calls[0]["kwargs"]["timeout"] == mcp_server.CONTROLLED_RUNNER_TIMEOUT_SECONDS
    assert str(tmp_path) in calls[0]["env"]["PYTHONPATH"]


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


def test_controlled_tool_timeout_result_does_not_claim_no_network(monkeypatch):
    def fake_timeout_runner(sources, targets):
        return {
            "status": "controlled_runner_timeout",
            "returncode": None,
            "stdout_tail": "partial out",
            "stderr_tail": "partial err",
            "controlled_summary": None,
            "runner_started": True,
            "network_calls_may_have_occurred": True,
            "repo_artifacts_updated": False,
            "temporary_evidence_directory_removed": True,
            "error": "Controlled runner timed out",
        }

    monkeypatch.setattr(mcp_server, "run_controlled_probe_runner", fake_timeout_runner)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, VALID_CONTROLLED_ARGS)))

    assert data["status"] == "controlled_runner_timeout"
    assert data["runner_started"] is True
    assert data["network_calls_may_have_occurred"] is True
    assert data["governance"]["runner_started"] is True
    assert data["governance"]["network_calls_may_have_occurred"] is True
    assert data["governance"]["network_calls"] is True
    assert data["governance"]["live_probe_execution"] is True
    assert data["generated_artifacts_updated"] is False
    assert data["frontend_artifacts_updated"] is False
    assert data["production_refreshed"] is False


def test_controlled_runner_timeout_does_not_claim_no_network(monkeypatch, tmp_path):
    runner_path = tmp_path / mcp_server.CONTROLLED_RUNNER_RELATIVE_PATH
    runner_path.parent.mkdir(parents=True)
    runner_path.write_text("# fake runner path for timeout test\n", encoding="utf-8")
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    def fake_timeout(command, cwd, env, **kwargs):
        raise subprocess.TimeoutExpired(command, timeout=kwargs["timeout"], output="partial out", stderr="partial err")

    monkeypatch.setattr(mcp_server.subprocess, "run", fake_timeout)

    result = mcp_server.run_controlled_probe_runner(["TWSE_OpenAPI"], ["2330"])

    assert result["status"] == "controlled_runner_timeout"
    assert result["returncode"] is None
    assert result["runner_started"] is True
    assert result["network_calls_may_have_occurred"] is True
    assert result["repo_artifacts_updated"] is False


def test_controlled_tool_runner_error_after_launch_does_not_claim_no_network(monkeypatch):
    def fake_error_runner(sources, targets):
        raise RuntimeError("runner failed after launch")

    monkeypatch.setattr(mcp_server, "run_controlled_probe_runner", fake_error_runner)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_LIVE_PROBE_TOOL, VALID_CONTROLLED_ARGS)))

    assert data["status"] == "controlled_runner_error_after_launch"
    assert data["failure_reason"] == "controlled_runner_error_after_launch"
    assert data["detail"] == "runner failed after launch"
    assert data["runner_started"] is True
    assert data["network_calls_may_have_occurred"] is True
    assert data["governance"]["runner_started"] is True
    assert data["governance"]["network_calls_may_have_occurred"] is True
    assert data["governance"]["network_calls"] is True
    assert data["governance"]["live_probe_execution"] is True
    assert data["generated_artifacts_updated"] is False
    assert data["frontend_artifacts_updated"] is False
    assert data["production_refreshed"] is False


def test_evidence_readback_tool_does_not_execute_controlled_runner(monkeypatch, tmp_path):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("controlled runner must not execute during evidence readback")

    monkeypatch.setattr(mcp_server, "run_controlled_probe_runner", fail_if_called)
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {})))

    assert data["status"] == "no_evidence_available"
    assert data["governance"]["network_calls"] is False
    assert data["governance"]["live_probe_execution"] is False


def test_evidence_readback_missing_directory_returns_no_evidence(monkeypatch, tmp_path):
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {})))

    assert data["status"] == "no_evidence_available"
    assert data["selected_runs"] == []
    assert data["governance"]["network_calls"] is False
    assert data["governance"]["live_probe_execution"] is False


def test_evidence_readback_empty_directory_returns_no_evidence(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {})))

    assert data["status"] == "no_evidence_available"
    assert data["selected_runs"] == []


def test_evidence_readback_latest_valid_run_summary_is_returned(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_000000.json").write_text(
        json.dumps(valid_run_summary(results={"old": True})), encoding="utf-8"
    )
    (evidence_dir / "run_summary_20260624_010000.json").write_text(
        json.dumps(valid_run_summary(results={"latest": True, "freshness": "not realtime"})), encoding="utf-8"
    )
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(
        asyncio.run(
            mcp_server.call_tool(
                mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL,
                {"requested_sources": ["TWSE_OpenAPI"], "requested_targets": ["2330"]},
            )
        )
    )

    assert data["status"] == "ok"
    assert data["selected_runs"] == ["research/live_probe_runs/m3g_04/run_summary_20260624_010000.json"]
    assert data["run_summaries"][0]["content"]["results"]["latest"] is True
    assert data["source_filters_applied"] == ["TWSE_OpenAPI"]
    assert data["target_filters_applied"] == ["2330"]


def test_evidence_readback_without_explicit_filters_reports_empty_applied_filters(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_010000.json").write_text(json.dumps(valid_run_summary()), encoding="utf-8")
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {})))

    assert data["status"] == "ok"
    assert data["source_filters_applied"] == []
    assert data["target_filters_applied"] == []


def test_evidence_readback_invalid_latest_candidate_is_not_silently_skipped(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_020000.json").write_text("{bad json", encoding="utf-8")
    (evidence_dir / "run_summary_20260624_010000.json").write_text(json.dumps(valid_run_summary()), encoding="utf-8")
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {})))

    assert data["status"] == "invalid_evidence_json"
    assert data["selected_runs"] == []
    assert data["invalid_evidence_path"] == "research/live_probe_runs/m3g_04/run_summary_20260624_020000.json"


def test_evidence_readback_max_runs_applies_after_matching(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_030000.json").write_text(
        json.dumps(valid_run_summary(sources=["Yahoo_Finance"], results={"source": "yahoo"})), encoding="utf-8"
    )
    (evidence_dir / "run_summary_20260624_020000.json").write_text(
        json.dumps(valid_run_summary(sources=["TWSE_OpenAPI"], results={"source": "twse-new"})), encoding="utf-8"
    )
    (evidence_dir / "run_summary_20260624_010000.json").write_text(
        json.dumps(valid_run_summary(sources=["TWSE_OpenAPI"], results={"source": "twse-old"})), encoding="utf-8"
    )
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(
        asyncio.run(
            mcp_server.call_tool(
                mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL,
                {"requested_sources": ["TWSE_OpenAPI"], "max_runs": 1},
            )
        )
    )

    assert data["status"] == "ok"
    assert data["selected_runs"] == ["research/live_probe_runs/m3g_04/run_summary_20260624_020000.json"]
    assert data["run_summaries"][0]["content"]["results"]["source"] == "twse-new"
    assert data["scanned_runs"] == [
        "research/live_probe_runs/m3g_04/run_summary_20260624_030000.json",
        "research/live_probe_runs/m3g_04/run_summary_20260624_020000.json",
    ]


def test_evidence_readback_max_runs_bound_is_enforced():
    data = decode_text_response(
        asyncio.run(
            mcp_server.call_tool(
                mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL,
                {"max_runs": mcp_server.CONTROLLED_EVIDENCE_READBACK_MAX_RUNS + 1},
            )
        )
    )

    assert data["status"] == "failed_closed"
    assert data["failure_reason"] == "invalid_max_runs"


def test_evidence_readback_invalid_requested_sources_fail_closed():
    data = decode_text_response(
        asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {"requested_sources": ["FinMind"]}))
    )

    assert data["status"] == "failed_closed"
    assert data["failure_reason"] == "source_outside_allowlist"


def test_evidence_readback_invalid_requested_targets_fail_closed():
    data = decode_text_response(
        asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {"requested_targets": ["999999"]}))
    )

    assert data["status"] == "failed_closed"
    assert data["failure_reason"] == "target_outside_allowlist"


def test_evidence_readback_duplicate_source_or_target_filters_fail_closed():
    duplicate_sources = decode_text_response(
        asyncio.run(
            mcp_server.call_tool(
                mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL,
                {"requested_sources": ["TWSE_OpenAPI", "TWSE_OpenAPI"]},
            )
        )
    )
    duplicate_targets = decode_text_response(
        asyncio.run(
            mcp_server.call_tool(
                mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL,
                {"requested_targets": ["2330", "2330"]},
            )
        )
    )

    assert duplicate_sources["status"] == "failed_closed"
    assert duplicate_sources["failure_reason"] == "duplicate_source_scope"
    assert duplicate_targets["status"] == "failed_closed"
    assert duplicate_targets["failure_reason"] == "duplicate_target_scope"


def test_evidence_readback_invalid_json_returns_structured_error(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_010000.json").write_text("{bad json", encoding="utf-8")
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {})))

    assert data["status"] == "invalid_evidence_json"
    assert data["invalid_evidence_path"] == "research/live_probe_runs/m3g_04/run_summary_20260624_010000.json"
    assert "line" in data["parse_error"]


def test_evidence_readback_missing_required_shape_returns_structured_error(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_010000.json").write_text(json.dumps({"run": "latest"}), encoding="utf-8")
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {})))

    assert data["status"] == "invalid_evidence_shape"
    assert data["invalid_evidence_path"] == "research/live_probe_runs/m3g_04/run_summary_20260624_010000.json"
    assert data["shape_error"]["error"] == "missing_required_fields"
    assert data["shape_error"]["missing_fields"] == ["targets", "sources_requested", "results"]


def test_evidence_readback_duplicate_sources_or_targets_in_evidence_fail_closed(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_020000.json").write_text(
        json.dumps(valid_run_summary(targets=["2330", "2330"])), encoding="utf-8"
    )
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    duplicate_targets = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {})))

    assert duplicate_targets["status"] == "invalid_evidence_shape"
    assert duplicate_targets["shape_error"] == {"field": "targets", "error": "targets must not contain duplicates"}

    (evidence_dir / "run_summary_20260624_030000.json").write_text(
        json.dumps(valid_run_summary(sources=["TWSE_OpenAPI", "TWSE_OpenAPI"])), encoding="utf-8"
    )

    duplicate_sources = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {})))

    assert duplicate_sources["status"] == "invalid_evidence_shape"
    assert duplicate_sources["shape_error"] == {
        "field": "sources_requested",
        "error": "sources_requested must not contain duplicates",
    }


def test_evidence_readback_requested_sources_filter_nonmatching_summaries(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_020000.json").write_text(
        json.dumps(valid_run_summary(sources=["Yahoo_Finance"], results={"source": "yahoo"})), encoding="utf-8"
    )
    (evidence_dir / "run_summary_20260624_010000.json").write_text(
        json.dumps(valid_run_summary(sources=["TWSE_OpenAPI"], results={"source": "twse"})), encoding="utf-8"
    )
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(
        asyncio.run(
            mcp_server.call_tool(
                mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL,
                {"requested_sources": ["TWSE_OpenAPI"]},
            )
        )
    )

    assert data["status"] == "ok"
    assert data["selected_runs"] == ["research/live_probe_runs/m3g_04/run_summary_20260624_010000.json"]
    assert data["run_summaries"][0]["content"]["results"]["source"] == "twse"
    assert data["source_filters_applied"] == ["TWSE_OpenAPI"]


def test_evidence_readback_requested_targets_filter_nonmatching_summaries(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_020000.json").write_text(
        json.dumps(valid_run_summary(targets=["8069"], results={"target": "8069"})), encoding="utf-8"
    )
    (evidence_dir / "run_summary_20260624_010000.json").write_text(
        json.dumps(valid_run_summary(targets=["2330"], results={"target": "2330"})), encoding="utf-8"
    )
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(
        asyncio.run(
            mcp_server.call_tool(
                mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL,
                {"requested_targets": ["2330"]},
            )
        )
    )

    assert data["status"] == "ok"
    assert data["selected_runs"] == ["research/live_probe_runs/m3g_04/run_summary_20260624_010000.json"]
    assert data["run_summaries"][0]["content"]["results"]["target"] == "2330"
    assert data["target_filters_applied"] == ["2330"]


def test_evidence_readback_valid_summaries_but_no_filter_match_returns_no_matching(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_010000.json").write_text(
        json.dumps(valid_run_summary(sources=["Yahoo_Finance"], targets=["8069"])), encoding="utf-8"
    )
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(
        asyncio.run(
            mcp_server.call_tool(
                mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL,
                {"requested_sources": ["TWSE_OpenAPI"], "requested_targets": ["2330"]},
            )
        )
    )

    assert data["status"] == "no_matching_evidence_available"
    assert data["selected_runs"] == []
    assert data["run_summaries"] == []


def test_evidence_readback_rejects_path_traversal_or_arbitrary_path_input():
    data = decode_text_response(
        asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {"path": "../../secret"}))
    )

    assert data["status"] == "failed_closed"
    assert data["failure_reason"] == "unsupported_argument"


def test_evidence_readback_valid_response_includes_governance_and_no_realtime_claim(monkeypatch, tmp_path):
    evidence_dir = tmp_path / mcp_server.CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run_summary_20260624_010000.json").write_text(json.dumps(valid_run_summary()), encoding="utf-8")
    write_target_config(tmp_path)
    monkeypatch.setattr(mcp_server, "REPO_ROOT", tmp_path)

    data = decode_text_response(asyncio.run(mcp_server.call_tool(mcp_server.CONTROLLED_EVIDENCE_READBACK_TOOL, {})))
    governance = data["governance"]

    assert data["status"] == "ok"
    assert governance["production_refresh"] is False
    assert governance["frontend_refresh"] is False
    assert governance["generated_artifact_writes"] is False
    assert governance["network_calls"] is False
    assert governance["live_probe_execution"] is False
    assert governance["evidence_readback_only"] is True
    assert governance["full_market_scan"] is False
    assert governance["trading_signal"] is False
    assert "not a realtime guarantee" in data["statement"]
    assert "generated artifacts were not updated" in data["statement"]
    assert "frontend artifacts were not updated" in data["statement"]
    assert "production snapshots were not updated" in data["statement"]
