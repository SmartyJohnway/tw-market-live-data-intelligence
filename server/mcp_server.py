"""MCP server for readonly Taiwan market context artifacts.

MCP-01 exposes local readonly context tools first. MCP-02 adds one explicit,
confirmed, bounded controlled live-probe evidence entrypoint. The module still
does not import or expose legacy individual live probe functions.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
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

CONTROLLED_LIVE_PROBE_TOOL = "run_m3g04_controlled_live_probe_evidence"
CONTROLLED_EVIDENCE_READBACK_TOOL = "read_m3g04_latest_controlled_probe_evidence"
CONTROLLED_RUNNER_RELATIVE_PATH = "scripts/run_m3g04_controlled_live_probe.py"
CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH = "research/live_probe_runs/m3g_04"
CONTROLLED_ALLOWED_SOURCES = ("TWSE_OpenAPI", "TPEx_OpenAPI", "TWSE_MIS", "Yahoo_Finance")
CONTROLLED_ALLOWED_SOURCE_SET = set(CONTROLLED_ALLOWED_SOURCES)
CONTROLLED_MAX_TARGETS = 5
CONTROLLED_EVIDENCE_READBACK_MAX_RUNS = 5
CONTROLLED_RUNNER_TIMEOUT_SECONDS = 60
CONTROLLED_OUTPUT_TAIL_CHARS = 4000


def _load_allowed_targets() -> set[str]:
    target_config = REPO_ROOT / "config" / "market_targets.json"
    try:
        data = json.loads(target_config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()

    allowed: set[str] = set()
    for group in data.values():
        symbols = group.get("symbols", {}) if isinstance(group, dict) else {}
        standard_symbols = symbols.get("standard", []) if isinstance(symbols, dict) else []
        for symbol in standard_symbols:
            if isinstance(symbol, str):
                allowed.add(symbol)
    return allowed


def controlled_probe_governance(
    executed: bool,
    *,
    runner_started: bool = False,
    network_calls_may_have_occurred: bool = False,
) -> dict[str, Any]:
    """Governance metadata for the explicit MCP-02 controlled probe surface.

    `executed=False` is reserved for validation failures or missing runner path
    before subprocess launch. Once the controlled runner has started or may have
    started, MCP-02 must not claim that network calls/live execution did not
    happen, even if the runner later fails or times out.
    """
    return {
        "surface": "MCP explicit controlled live probe tool",
        "execution_mode": "explicit_confirmed_controlled_probe",
        "network_calls": bool(executed),
        "network_calls_may_have_occurred": bool(network_calls_may_have_occurred),
        "production_refresh": False,
        "frontend_refresh": False,
        "artifact_writes": False,
        "live_probe_execution": bool(executed),
        "runner_started": bool(runner_started),
        "full_market_scan": False,
        "trading_signal": False,
        "caveats": [
            "controlled_evidence_collection_only",
            "not_production_refresh",
            "not_frontend_refresh",
            "not_live_market_guarantee",
            "no_trading_signal",
        ],
    }


def _controlled_failure(arguments: dict[str, Any], reason: str, detail: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "tool": CONTROLLED_LIVE_PROBE_TOOL,
        "status": "failed_closed",
        "governance": controlled_probe_governance(executed=False),
        "requested_scope": {
            "requested_sources": arguments.get("requested_sources"),
            "requested_targets": arguments.get("requested_targets"),
            "max_targets": arguments.get("max_targets"),
        },
        "executed_scope": {"requested_sources": [], "requested_targets": []},
        "failure_reason": reason,
        "generated_artifacts_updated": False,
        "frontend_artifacts_updated": False,
        "production_refreshed": False,
        "statement": "Generated artifacts, frontend artifacts, and production snapshots were not updated.",
    }
    if detail:
        payload["detail"] = detail
    return payload



def _controlled_runner_failure_after_launch(
    arguments: dict[str, Any], reason: str, detail: str | None = None
) -> dict[str, Any]:
    payload = _controlled_failure(arguments, reason, detail)
    payload["status"] = reason
    payload["governance"] = controlled_probe_governance(
        executed=True,
        runner_started=True,
        network_calls_may_have_occurred=True,
    )
    payload["executed_scope"] = {
        "requested_sources": arguments.get("requested_sources", []),
        "requested_targets": arguments.get("requested_targets", []),
    }
    payload["runner_started"] = True
    payload["network_calls_may_have_occurred"] = True
    return payload


def _validate_controlled_probe_arguments(arguments: dict[str, Any]) -> tuple[bool, str | None, str | None]:
    if arguments.get("confirm_controlled_live_probe") is not True:
        return False, "missing_explicit_confirmation", "confirm_controlled_live_probe must be true"
    for flag in ("no_artifact_writes", "no_frontend_writes", "no_production_refresh"):
        if arguments.get(flag) is not True:
            return False, "write_or_refresh_not_explicitly_forbidden", f"{flag} must be true"

    sources = arguments.get("requested_sources")
    targets = arguments.get("requested_targets")
    if not isinstance(sources, list) or not sources or not all(isinstance(item, str) for item in sources):
        return False, "invalid_source_scope", "requested_sources must be a non-empty string list"
    if not isinstance(targets, list) or not targets or not all(isinstance(item, str) for item in targets):
        return False, "invalid_target_scope", "requested_targets must be a non-empty string list"
    if len(set(sources)) != len(sources):
        return False, "duplicate_source_scope", "requested_sources must not contain duplicates"
    if any(source not in CONTROLLED_ALLOWED_SOURCE_SET for source in sources):
        return False, "source_outside_allowlist", "requested_sources must stay within the controlled source allowlist"

    max_targets = arguments.get("max_targets")
    if not isinstance(max_targets, int) or max_targets < 1 or max_targets > CONTROLLED_MAX_TARGETS:
        return False, "invalid_max_targets", f"max_targets must be an integer from 1 to {CONTROLLED_MAX_TARGETS}"
    if len(targets) > max_targets or len(targets) > CONTROLLED_MAX_TARGETS:
        return False, "target_count_exceeds_bound", "requested_targets exceeds max_targets or controlled maximum"
    if len(set(targets)) != len(targets):
        return False, "duplicate_target_scope", "requested_targets must not contain duplicates"

    allowed_targets = _load_allowed_targets()
    if not allowed_targets:
        return False, "target_allowlist_unavailable", "config/market_targets.json could not be loaded"
    if any(target not in allowed_targets for target in targets):
        return False, "target_outside_allowlist", "requested_targets must stay within config/market_targets.json standard symbols"
    return True, None, None


def run_controlled_probe_runner(sources: list[str], targets: list[str]) -> dict[str, Any]:
    """Run only the bounded controlled M3G-04 runner path; never import legacy probes.

    The existing runner writes its evidence files under the process working
    directory. MCP-02 executes it from an isolated temporary directory with the
    repository on PYTHONPATH so no repository generated, frontend, or production
    artifacts are updated by this MCP surface.
    """
    runner_path = REPO_ROOT / CONTROLLED_RUNNER_RELATIVE_PATH
    if not runner_path.is_file():
        raise FileNotFoundError(f"Controlled runner not found: {CONTROLLED_RUNNER_RELATIVE_PATH}")

    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(REPO_ROOT) if not existing_pythonpath else f"{REPO_ROOT}{os.pathsep}{existing_pythonpath}"
    with tempfile.TemporaryDirectory(prefix="mcp_controlled_probe_") as tmpdir:
        command = [
            sys.executable,
            str(runner_path),
            "--targets",
            *targets,
            "--sources",
            *sources,
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=tmpdir,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=CONTROLLED_RUNNER_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "status": "controlled_runner_timeout",
                "returncode": None,
                "stdout_tail": (exc.stdout or "")[-CONTROLLED_OUTPUT_TAIL_CHARS:],
                "stderr_tail": (exc.stderr or "")[-CONTROLLED_OUTPUT_TAIL_CHARS:],
                "controlled_summary": None,
                "runner_started": True,
                "network_calls_may_have_occurred": True,
                "repo_artifacts_updated": False,
                "temporary_evidence_directory_removed": True,
                "error": f"Controlled runner timed out after {CONTROLLED_RUNNER_TIMEOUT_SECONDS} seconds",
            }
        except Exception as exc:
            return {
                "status": "controlled_runner_error_after_launch",
                "returncode": None,
                "stdout_tail": "",
                "stderr_tail": "",
                "controlled_summary": None,
                "runner_started": True,
                "network_calls_may_have_occurred": True,
                "repo_artifacts_updated": False,
                "temporary_evidence_directory_removed": True,
                "error": str(exc),
            }
        evidence_dir = Path(tmpdir) / "research" / "live_probe_runs" / "m3g_04"
        summaries = sorted(evidence_dir.glob("run_summary_*.json"))
        summary: dict[str, Any] | None = None
        if summaries:
            try:
                summary = json.loads(summaries[-1].read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                summary = {"parse_error": f"Controlled runner summary is not valid JSON: {exc.msg}"}

        return {
            "status": "ok" if completed.returncode == 0 else "runner_failed",
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-CONTROLLED_OUTPUT_TAIL_CHARS:],
            "stderr_tail": completed.stderr[-CONTROLLED_OUTPUT_TAIL_CHARS:],
            "controlled_summary": summary,
            "runner_started": True,
            "network_calls_may_have_occurred": True,
            "repo_artifacts_updated": False,
            "temporary_evidence_directory_removed": True,
        }


def run_controlled_live_probe_evidence(arguments: dict[str, Any] | None) -> dict[str, Any]:
    args = arguments or {}
    valid, reason, detail = _validate_controlled_probe_arguments(args)
    if not valid:
        return _controlled_failure(args, reason or "invalid_scope", detail)

    sources = list(args["requested_sources"])
    targets = list(args["requested_targets"])
    try:
        result = run_controlled_probe_runner(sources, targets)
    except FileNotFoundError as exc:
        return _controlled_failure(args, "controlled_runner_missing", str(exc))
    except Exception as exc:
        return _controlled_runner_failure_after_launch(args, "controlled_runner_error_after_launch", str(exc))

    status = result.get("status") or ("ok" if result.get("returncode") == 0 else "runner_failed")
    runner_started = bool(result.get("runner_started"))
    network_calls_may_have_occurred = bool(result.get("network_calls_may_have_occurred"))
    return {
        "tool": CONTROLLED_LIVE_PROBE_TOOL,
        "status": status,
        "governance": controlled_probe_governance(
            executed=runner_started or network_calls_may_have_occurred,
            runner_started=runner_started,
            network_calls_may_have_occurred=network_calls_may_have_occurred,
        ),
        "requested_scope": {
            "requested_sources": sources,
            "requested_targets": targets,
            "max_targets": args.get("max_targets"),
        },
        "executed_scope": {"requested_sources": sources, "requested_targets": targets},
        "result": result,
        "retrieval_metadata": {
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "freshness_assessment": "bounded controlled evidence collection only; not a live market guarantee",
            "delay_status": "source-dependent and not guaranteed realtime",
        },
        "generated_artifacts_updated": False,
        "frontend_artifacts_updated": False,
        "production_refreshed": False,
        "runner_started": runner_started,
        "network_calls_may_have_occurred": network_calls_may_have_occurred,
        "statement": "Generated artifacts, frontend artifacts, and production snapshots were not updated; this is not realtime-guaranteed data and not a trading signal.",
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


def evidence_readback_governance() -> dict[str, Any]:
    """Governance metadata for MCP-03 readonly controlled evidence readback."""
    return {
        "surface": "MCP controlled evidence readonly readback tool",
        "execution_mode": "readonly_local_controlled_evidence_read",
        "network_calls": False,
        "live_probe_execution": False,
        "production_refresh": False,
        "frontend_refresh": False,
        "generated_artifact_writes": False,
        "evidence_readback_only": True,
        "full_market_scan": False,
        "trading_signal": False,
        "caveats": [
            "controlled_evidence_readback_only",
            "not_live_probe_execution",
            "not_production_refresh",
            "not_frontend_refresh",
            "not_generated_artifact_refresh",
            "not_live_market_guarantee",
            "no_trading_signal",
        ],
    }


def _evidence_readback_statement() -> str:
    return (
        "No network calls were made; no live probe was executed; generated artifacts were not updated; "
        "frontend artifacts were not updated; production snapshots were not updated. This is controlled "
        "local evidence readback only, not a realtime guarantee, not production current market state, "
        "and not a trading signal."
    )


def _controlled_evidence_readback_failure(
    arguments: dict[str, Any],
    reason: str,
    detail: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "tool": CONTROLLED_EVIDENCE_READBACK_TOOL,
        "status": "failed_closed",
        "governance": evidence_readback_governance(),
        "requested_scope": {
            "requested_sources": arguments.get("requested_sources"),
            "requested_targets": arguments.get("requested_targets"),
            "max_runs": arguments.get("max_runs", 1),
        },
        "resolved_scope": {"requested_sources": [], "requested_targets": [], "max_runs": None},
        "evidence_directory": CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH,
        "selected_runs": [],
        "failure_reason": reason,
        "freshness": {
            "assessment": "No freshness can be inferred from rejected readback arguments.",
            "delay_caveat": "not_live_market_guarantee",
        },
        "statement": _evidence_readback_statement(),
    }
    if detail:
        payload["detail"] = detail
    return payload


def _validate_evidence_readback_arguments(arguments: dict[str, Any]) -> tuple[bool, str | None, str | None, dict[str, Any]]:
    if not isinstance(arguments, dict):
        return False, "invalid_arguments", "arguments must be an object", {}
    unexpected = sorted(set(arguments) - {"requested_sources", "requested_targets", "max_runs"})
    if unexpected:
        return False, "unsupported_argument", f"unsupported arguments: {', '.join(unexpected)}", {}

    max_runs = arguments.get("max_runs", 1)
    if not isinstance(max_runs, int) or max_runs < 1 or max_runs > CONTROLLED_EVIDENCE_READBACK_MAX_RUNS:
        return (
            False,
            "invalid_max_runs",
            f"max_runs must be an integer from 1 to {CONTROLLED_EVIDENCE_READBACK_MAX_RUNS}",
            {},
        )

    sources = arguments.get("requested_sources")
    source_filter_requested = sources is not None
    if sources is None:
        resolved_sources = list(CONTROLLED_ALLOWED_SOURCES)
    elif not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
        return False, "invalid_source_scope", "requested_sources must be a string list when provided", {}
    else:
        if len(set(sources)) != len(sources):
            return False, "duplicate_source_scope", "requested_sources must not contain duplicates", {}
        if any(source not in CONTROLLED_ALLOWED_SOURCE_SET for source in sources):
            return False, "source_outside_allowlist", "requested_sources must stay within the controlled source allowlist", {}
        resolved_sources = list(sources)

    targets = arguments.get("requested_targets")
    allowed_targets = _load_allowed_targets()
    if not allowed_targets:
        return False, "target_allowlist_unavailable", "config/market_targets.json could not be loaded", {}
    target_filter_requested = targets is not None
    if targets is None:
        resolved_targets = sorted(allowed_targets)
    elif not isinstance(targets, list) or not all(isinstance(item, str) for item in targets):
        return False, "invalid_target_scope", "requested_targets must be a string list when provided", {}
    else:
        if len(set(targets)) != len(targets):
            return False, "duplicate_target_scope", "requested_targets must not contain duplicates", {}
        if any(target not in allowed_targets for target in targets):
            return False, "target_outside_allowlist", "requested_targets must stay within config/market_targets.json standard symbols", {}
        resolved_targets = list(targets)

    return (
        True,
        None,
        None,
        {
            "requested_sources": resolved_sources,
            "requested_targets": resolved_targets,
            "max_runs": max_runs,
            "source_filter_requested": source_filter_requested,
            "target_filter_requested": target_filter_requested,
        },
    )


def validate_run_summary_shape(summary: Any) -> dict[str, Any] | None:
    """Validate the canonical controlled run summary shape before readback."""
    if not isinstance(summary, dict):
        return {"field": "<root>", "error": "run summary must be a JSON object"}

    required_fields = ("targets", "sources_requested", "results")
    missing_fields = [field for field in required_fields if field not in summary]
    if missing_fields:
        return {"field": "<root>", "error": "missing_required_fields", "missing_fields": missing_fields}

    targets = summary["targets"]
    if not isinstance(targets, list) or not all(isinstance(item, str) for item in targets):
        return {"field": "targets", "error": "targets must be a string list"}
    if len(set(targets)) != len(targets):
        return {"field": "targets", "error": "targets must not contain duplicates"}

    sources_requested = summary["sources_requested"]
    if not isinstance(sources_requested, list) or not all(isinstance(item, str) for item in sources_requested):
        return {"field": "sources_requested", "error": "sources_requested must be a string list"}
    if len(set(sources_requested)) != len(sources_requested):
        return {"field": "sources_requested", "error": "sources_requested must not contain duplicates"}

    results = summary["results"]
    if not isinstance(results, (dict, list)):
        return {"field": "results", "error": "results must be an object or array"}

    return None


def _run_summary_matches_requested_filters(summary: dict[str, Any], resolved_scope: dict[str, Any]) -> bool:
    """Return true only when explicit requested filters match summary content."""
    if resolved_scope.get("source_filter_requested"):
        summary_sources = set(summary["sources_requested"])
        if not set(resolved_scope["requested_sources"]).issubset(summary_sources):
            return False

    if resolved_scope.get("target_filter_requested"):
        summary_targets = set(summary["targets"])
        if not set(resolved_scope["requested_targets"]).issubset(summary_targets):
            return False

    return True


def read_controlled_probe_evidence(arguments: dict[str, Any] | None) -> dict[str, Any]:
    """Read existing local M3G-04 controlled probe evidence summaries only."""
    args = arguments or {}
    valid, reason, detail, resolved_scope = _validate_evidence_readback_arguments(args)
    if not valid:
        return _controlled_evidence_readback_failure(args if isinstance(args, dict) else {}, reason or "invalid_arguments", detail)

    evidence_dir = (REPO_ROOT / CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH).resolve()
    allowed_dir = (REPO_ROOT / CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH).resolve()
    if evidence_dir != allowed_dir or not evidence_dir.is_relative_to(REPO_ROOT.resolve()):
        return _controlled_evidence_readback_failure(args, "invalid_evidence_directory", "evidence directory resolved outside repo")

    base_payload: dict[str, Any] = {
        "tool": CONTROLLED_EVIDENCE_READBACK_TOOL,
        "governance": evidence_readback_governance(),
        "requested_scope": {
            "requested_sources": args.get("requested_sources"),
            "requested_targets": args.get("requested_targets"),
            "max_runs": args.get("max_runs", 1),
        },
        "resolved_scope": resolved_scope,
        "evidence_directory": CONTROLLED_EVIDENCE_DIRECTORY_RELATIVE_PATH,
        "source_filters_applied": resolved_scope["requested_sources"] if resolved_scope["source_filter_requested"] else [],
        "target_filters_applied": resolved_scope["requested_targets"] if resolved_scope["target_filter_requested"] else [],
        "freshness": {
            "assessment": "Existing controlled evidence summary read from local disk only; not a live market guarantee.",
            "delay_caveat": "source-dependent historical evidence; not realtime-guaranteed",
        },
        "statement": _evidence_readback_statement(),
    }

    if not evidence_dir.is_dir():
        return {**base_payload, "status": "no_evidence_available", "selected_runs": [], "run_summaries": []}

    summaries = sorted(evidence_dir.glob("run_summary_*.json"), key=lambda path: path.name, reverse=True)
    if not summaries:
        return {**base_payload, "status": "no_evidence_available", "selected_runs": [], "run_summaries": []}

    matching_summaries = []
    scanned_runs = []
    for path in summaries:
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        scanned_runs.append(relative_path)
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {
                **base_payload,
                "status": "invalid_evidence_json",
                "selected_runs": [],
                "scanned_runs": scanned_runs,
                "run_summaries": [],
                "invalid_evidence_path": relative_path,
                "parse_error": f"{exc.msg} at line {exc.lineno} column {exc.colno}",
            }

        shape_error = validate_run_summary_shape(summary)
        if shape_error is not None:
            return {
                **base_payload,
                "status": "invalid_evidence_shape",
                "selected_runs": [],
                "scanned_runs": scanned_runs,
                "run_summaries": [],
                "invalid_evidence_path": relative_path,
                "shape_error": shape_error,
            }

        if _run_summary_matches_requested_filters(summary, resolved_scope):
            matching_summaries.append((path, summary))
            if len(matching_summaries) >= resolved_scope["max_runs"]:
                break

    if not matching_summaries:
        return {
            **base_payload,
            "status": "no_matching_evidence_available",
            "selected_runs": [],
            "scanned_runs": scanned_runs,
            "run_summaries": [],
        }

    selected_paths = matching_summaries
    run_summaries = []
    selected_runs = []
    for path, summary in selected_paths:
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        selected_runs.append(relative_path)
        run_summaries.append({"path": relative_path, "content": summary})

    return {
        **base_payload,
        "status": "ok",
        "selected_runs": selected_runs,
        "scanned_runs": scanned_runs,
        "run_summaries": run_summaries,
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
    """List readonly local context tools plus explicit controlled MCP-02/MCP-03 tools."""
    readonly_tools = [
        Tool(
            name=name,
            description=spec["description"],
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        )
        for name, spec in READONLY_TOOL_SPECS.items()
    ]
    controlled_tool = Tool(
        name=CONTROLLED_LIVE_PROBE_TOOL,
        description="Run an explicit, confirmed, bounded M3G-04 controlled live-probe evidence collection without production/frontend/generated artifact refresh.",
        inputSchema={
            "type": "object",
            "properties": {
                "confirm_controlled_live_probe": {"type": "boolean"},
                "requested_sources": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(CONTROLLED_ALLOWED_SOURCES)},
                    "minItems": 1,
                    "maxItems": len(CONTROLLED_ALLOWED_SOURCES),
                },
                "requested_targets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": CONTROLLED_MAX_TARGETS,
                },
                "max_targets": {"type": "integer", "minimum": 1, "maximum": CONTROLLED_MAX_TARGETS},
                "no_artifact_writes": {"type": "boolean"},
                "no_frontend_writes": {"type": "boolean"},
                "no_production_refresh": {"type": "boolean"},
            },
            "required": [
                "confirm_controlled_live_probe",
                "requested_sources",
                "requested_targets",
                "max_targets",
                "no_artifact_writes",
                "no_frontend_writes",
                "no_production_refresh",
            ],
            "additionalProperties": False,
        },
    )
    evidence_readback_tool = Tool(
        name=CONTROLLED_EVIDENCE_READBACK_TOOL,
        description="Read existing local M3G-04 controlled live-probe evidence summaries without network calls, live probe execution, or artifact refresh.",
        inputSchema={
            "type": "object",
            "properties": {
                "requested_sources": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(CONTROLLED_ALLOWED_SOURCES)},
                    "minItems": 1,
                    "maxItems": len(CONTROLLED_ALLOWED_SOURCES),
                },
                "requested_targets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": CONTROLLED_MAX_TARGETS,
                },
                "max_runs": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": CONTROLLED_EVIDENCE_READBACK_MAX_RUNS,
                    "default": 1,
                },
            },
            "additionalProperties": False,
        },
    )
    return [*readonly_tools, controlled_tool, evidence_readback_tool]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Handle readonly MCP tool requests without executing live probes."""
    if name in READONLY_TOOL_SPECS:
        return _json_text(read_local_context_tool(name))
    if name == CONTROLLED_LIVE_PROBE_TOOL:
        return _json_text(run_controlled_live_probe_evidence(arguments))
    if name == CONTROLLED_EVIDENCE_READBACK_TOOL:
        return _json_text(read_controlled_probe_evidence(arguments))
    return _json_text(unavailable_tool_response(name))


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
