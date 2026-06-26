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
CONTROLLED_RUNNER_RELATIVE_PATH = "scripts/run_m3g04_controlled_live_probe.py"
CONTROLLED_ALLOWED_SOURCES = {"TWSE_OpenAPI", "TPEx_OpenAPI", "TWSE_MIS", "Yahoo_Finance"}
CONTROLLED_MAX_TARGETS = 5


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


def controlled_probe_governance(executed: bool) -> dict[str, Any]:
    """Governance metadata for the explicit MCP-02 controlled probe surface."""
    return {
        "surface": "MCP explicit controlled live probe tool",
        "execution_mode": "explicit_confirmed_controlled_probe",
        "network_calls": bool(executed),
        "production_refresh": False,
        "frontend_refresh": False,
        "artifact_writes": False,
        "live_probe_execution": bool(executed),
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
    if any(source not in CONTROLLED_ALLOWED_SOURCES for source in sources):
        return False, "source_outside_allowlist", "requested_sources must stay within the controlled source allowlist"

    max_targets = arguments.get("max_targets")
    if not isinstance(max_targets, int) or max_targets < 1 or max_targets > CONTROLLED_MAX_TARGETS:
        return False, "invalid_max_targets", f"max_targets must be an integer from 1 to {CONTROLLED_MAX_TARGETS}"
    if len(targets) > max_targets or len(targets) > CONTROLLED_MAX_TARGETS:
        return False, "target_count_exceeds_bound", "requested_targets exceeds max_targets or controlled maximum"

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
        completed = subprocess.run(
            [
                "python",
                str(runner_path),
                "--targets",
                *targets,
                "--sources",
                *sources,
            ],
            cwd=tmpdir,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "repo_artifacts_updated": False,
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
        return _controlled_failure(args, "controlled_runner_error", str(exc))

    status = "ok" if result.get("returncode") == 0 else "runner_failed"
    return {
        "tool": CONTROLLED_LIVE_PROBE_TOOL,
        "status": status,
        "governance": controlled_probe_governance(executed=True),
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
    """List readonly local context tools plus one explicit controlled probe tool."""
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
                    "items": {"type": "string", "enum": sorted(CONTROLLED_ALLOWED_SOURCES)},
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
    return [*readonly_tools, controlled_tool]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Handle readonly MCP tool requests without executing live probes."""
    if name in READONLY_TOOL_SPECS:
        return _json_text(read_local_context_tool(name))
    if name == CONTROLLED_LIVE_PROBE_TOOL:
        return _json_text(run_controlled_live_probe_evidence(arguments))
    return _json_text(unavailable_tool_response(name))


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
