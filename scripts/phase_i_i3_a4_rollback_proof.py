"""Read-only I3-ROLL-001 proof against the post-A3 baseline commit."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "5c26e7b541bdb6c0d70a39c1e0eab8e129823373"
BASELINE_TREE = "ac72a639cba570d8a8cfc743934c6131f88fad42"
I3 = "cash_institutional_flow_context"
EXECUTOR = "phase_i_i3_cash_institutional_flow_context_executor"


def _git(*args: str) -> str:
    # Git objects may contain UTF-8 source text while Windows defaults to cp950.
    # Decode explicitly so this read-only rollback proof is portable.
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL).decode("utf-8").strip()


def _baseline_json(path: str) -> dict[str, Any]:
    return json.loads(_git("show", f"{BASELINE}:{path}"))


def prove_i3_rollback() -> dict[str, Any]:
    """Show restoring baseline authority removes I3 while retaining I1/I2/MCP."""
    if _git("show", "-s", "--format=%T", BASELINE) != BASELINE_TREE:
        raise ValueError("i3_roll_baseline_tree_mismatch")
    catalog = _baseline_json("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _baseline_json("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    metadata = _baseline_json("config/m8r_06_03_executor_registry_metadata.json")
    request_schema = _baseline_json("schemas/unified_market_evidence_request.v3.schema.json")
    result_schema = _baseline_json("schemas/unified_market_evidence_result.v3.schema.json")
    audit_schema = _baseline_json("schemas/unified_market_evidence_audit_package.v3.schema.json")
    if any(item.get("capability_id") == I3 for item in catalog.get("data_need_capabilities", [])):
        raise ValueError("i3_roll_catalog_contains_i3")
    if any(item.get("capability_id") == I3 for item in routing.get("routes", [])):
        raise ValueError("i3_roll_routing_contains_i3")
    if any(item.get("executor_id") == EXECUTOR for item in metadata.get("executors", [])):
        raise ValueError("i3_roll_runtime_metadata_contains_i3")
    if I3.encode() in json.dumps(request_schema).encode() or I3 in result_schema.get("definitions", {}) or I3.encode() in json.dumps(audit_schema).encode():
        raise ValueError("i3_roll_public_v3_support_remains")
    by_executor: dict[str, int] = {}
    for entry in metadata.get("executors", []):
        by_executor[entry["executor_id"]] = by_executor.get(entry["executor_id"], 0) + 1
    if by_executor.get("phase_i_i1_market_state_executor") != 2:
        raise ValueError("i3_roll_i1_routes_not_preserved")
    if by_executor.get("phase_i_i2_index_futures_context_executor") != 1:
        raise ValueError("i3_roll_i2_routes_not_preserved")
    i1_ledger = _baseline_json("docs/governance/phase_i/PHASE_I_I1_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-09-30.json")
    i2_ledger = _baseline_json("docs/governance/phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-10-01.json")
    i1_sources = i1_ledger.get("runtime_authority", {}).get("active_source_count")
    i2_sources = i2_ledger.get("accepted_runtime_authority", {}).get("active_i2_sources")
    if i1_sources != 3 or i2_sources != 1:
        raise ValueError("i3_roll_i1_i2_sources_not_preserved")
    from server.unified_mcp.tool_contracts import build_tool_specs
    tool_count = len(build_tool_specs())
    if tool_count != 6:
        raise ValueError("i3_roll_mcp_count_changed")
    return {"rollback_id": "I3-ROLL-001", "status": "PASS", "baseline_commit": BASELINE,
            "baseline_tree": BASELINE_TREE, "i3_active_sources": 0, "i3_routes": 0,
            "i3_executor_reachable": False, "i3_public_v3_support": False,
            "i1_active_sources": i1_sources, "i1_routes": 2,
            "i2_active_sources": i2_sources, "i2_routes": 1, "mcp_tool_count": tool_count,
            "destructive_git_rollback_performed": False}
