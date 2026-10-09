#!/usr/bin/env python3
"""Validate A6-P0 inventory, Security Master gate, and dormant runtime state."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BASELINE = "0576c8304764e6b7ba9e90305b34b63c50fd3fc6"
MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_P0_INTEGRATED_ACCEPTANCE_PREFLIGHT_2026-10-09.json"
CLOSEOUT = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_FINAL_CLOSEOUT_2026-10-09.json"


def _strict(path: Path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise AssertionError(f"duplicate_json_key:{key}")
            out[key] = value
        return out
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate() -> dict:
    record = _strict(RECORD)
    closeout = _strict(CLOSEOUT)
    assert closeout["disposition"] == "PASS"
    assert closeout["a5_component_status"]["A5_overall"] == "COMPLETE_PASS"
    assert closeout["session_2"]["terminal_reason"] == "PASS"
    assert closeout["independent_review"]["result"] == "PASS"
    assert closeout["canonical_runtime_state_at_closeout"] == {
        "H2_runtime": "INACTIVE", "selected_executor_id": None,
        "J-B04": "BLOCKING", "Phase J": "NOT_STARTED", "MCP": 6,
    }
    for session_path in (
        "docs/governance/phase_j/acceptance_runs/j-b04-a5-session-78e1b2c1db127926",
        "docs/governance/phase_j/acceptance_runs/j-b04-a5-session-bb17ab31639e6e68",
    ):
        assert _git("diff", "--quiet", BASELINE, "HEAD", "--", session_path) == ""
    assert _git("diff", "--quiet", BASELINE, "HEAD", "--", str(CLOSEOUT.relative_to(ROOT))) == ""

    assert record["gate"] == "J-B04-A6-P0"
    assert record["disposition"] == "J_B04_A6_P0_BLOCKED_SECURITY_MASTER_NOT_INITIALIZED"
    assert record["architecture_inventory_complete"] is True
    assert record["security_master_state"] == "NOT_INITIALIZED"
    assert record["production_identity_verified"] is False
    assert record["security_master_bootstrap_performed"] is False
    assert record["production_identity_required"] is True
    assert record["acceptance_only_identity_fallback"] is False
    assert record["identity_resolution"]["result"] == "not_attempted"
    assert record["security_master_release_id"] is None
    assert record["security_master_manifest_hash"] is None
    assert record["network_counts"] == {
        "market_GET": 0, "market_HEAD": 0, "market_POST": 0,
        "Security_Master_live_acquisition": 0,
    }
    architecture = record["architecture"]
    assert architecture["execution_order"] == ["identity", "H3", "H2", "H4", "Result V3", "Audit V3", "handoff"]
    assert architecture["result_v3"]["schema_change_required"] is False
    assert architecture["audit_v3"]["schema_change_required"] is False
    assert "actual HTTP dispatch counts" in architecture["audit_v3"]["gap"]
    assert architecture["future_bounded_live_contract"]["max_official_get_dispatches_per_session"] <= 10
    assert architecture["future_bounded_live_contract"]["designed_not_authorized"] is True
    assert len(architecture["handoff_coverage_matrix"]) == 9
    assert architecture["no_trading_boundary"]
    ci = record["validation"]["default_ci_exact_base_head"]
    assert ci["new_failure_delta"] == 0
    assert ci["new_failure_nodes"] == [] and ci["resolved_failure_nodes"] == []
    assert ci["base_failed_nodes"] == ci["head_failed_nodes"]
    assert ci["network_may_have_occurred"] is False

    routing = _strict(ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    h2_route = next(item for item in routing["routes"] if item.get("capability_id") == "corporate_action_context")
    assert h2_route["selected_executor_id"] is None and h2_route["routing_status"] == "plan_only"
    catalog = _strict(ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    h2_capability = next(item for item in catalog["data_need_capabilities"] if item.get("capability_id") == "corporate_action_context")
    assert h2_capability["runtime_executable"] is False
    assert h2_capability["phase_h_activation_state"] == "inactive"

    from server.unified_mcp.tool_contracts import build_tool_specs
    assert len(build_tool_specs()) == 6
    actual = _git("rev-parse", "origin/main")
    assert actual == MAIN
    return {
        "status": "PASS",
        "disposition": record["disposition"],
        "historical_a5_sessions_unchanged": True,
        "A5_closeout_sha256": hashlib.sha256(CLOSEOUT.read_bytes()).hexdigest(),
        "network_counts": record["network_counts"],
        "H2_runtime": "INACTIVE", "selected_executor_id": None,
        "J-B04": "BLOCKING", "Phase J": "NOT_STARTED", "MCP": 6,
        "origin_main": actual,
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
