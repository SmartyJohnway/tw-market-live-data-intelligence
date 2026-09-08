#!/usr/bin/env python3
"""Offline semantic drift gate for current Agent-facing product surfaces."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXPECTED_TOOLS = {
    "market_describe_capabilities",
    "market_validate_request",
    "market_preview_request",
    "market_read_result",
    "market_export_ai_handoff",
    "market_fetch_evidence",
}
CURRENT_TEXT_PATHS = (
    ROOT / "skills/tw-market-evidence-agent/SKILL.md",
    ROOT / "skills/tw-market-evidence-agent/references/current_limitations.md",
    ROOT / "docs/agent_usage_guide.md",
)
FORBIDDEN_CURRENT_STATEMENTS = (
    "Direct Unified MCP/service execution is not currently available",
    "Until M8R-06 is implemented",
    "Mode B2 authorization/execution, Mode C packaging, and Unified MCP execution remain future",
    "manual handoff only",
)


def fail(code: str, detail: object = None) -> int:
    print(
        json.dumps(
            {"status": "FAIL", "reason_code": code, "detail": detail},
            ensure_ascii=False,
        )
    )
    return 1


def main() -> int:
    from server.unified_mcp.tool_contracts import build_tool_specs

    actual_tools = {tool.name for tool in build_tool_specs()}
    if actual_tools != EXPECTED_TOOLS:
        return fail("mcp_tool_contract_drift", sorted(actual_tools))

    canonical = json.loads(
        (
            ROOT
            / "docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json"
        ).read_text(encoding="utf-8")
    )
    portable = json.loads(
        (
            ROOT
            / "skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json"
        ).read_text(encoding="utf-8")
    )
    if canonical.get("schema_version") != portable.get("schema_version"):
        return fail("portable_catalog_schema_drift")

    current_text = "\n".join(
        path.read_text(encoding="utf-8") for path in CURRENT_TEXT_PATHS
    )
    missing = sorted(tool for tool in EXPECTED_TOOLS if tool not in current_text)
    if missing:
        return fail("current_surface_missing_tool", missing)
    stale = [
        text
        for text in FORBIDDEN_CURRENT_STATEMENTS
        if text.lower() in current_text.lower()
    ]
    if stale:
        return fail("stale_current_runtime_statement", stale)
    if (
        "execute-once" not in current_text.lower()
        and "execute once" not in current_text.lower()
    ):
        return fail("execute_once_semantics_missing")
    if "ai-ready handoff" not in current_text.lower():
        return fail("mode_c_handoff_semantics_missing")

    sync = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_portable_catalog_sync.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if sync.returncode:
        return fail("portable_catalog_deep_sync_failed", sync.stdout + sync.stderr)

    print(
        json.dumps({"status": "PASS", "tool_count": 6, "tools": sorted(actual_tools)})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
