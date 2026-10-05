"""Validate the offline Phase J entry preflight record against fixed guardrails."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json"
SCENARIOS = (
    "normal TWSE", "normal TPEx", "multi-target", "current market evidence",
    "official EOD", "material disclosure", "no material disclosure",
    "corrected disclosure", "monthly revenue", "financial statements",
    "attention / disposition", "suspend / resume", "ex-dividend", "ex-right",
    "capital reduction", "reference-price discontinuity", "5D / 20D baseline",
    "TAIFEX context", "timing mismatch", "partial success", "stale", "missing",
    "source failure", "identity ambiguity", "unsupported identity",
    "authorization refusal", "resource bound",
)
READINESS_CLASSES = {
    "PRODUCTION_READY", "ACCEPTANCE_READY_WITH_EXISTING_RUNTIME",
    "CONTRACT_PRESENT_RUNTIME_INACTIVE", "PARTIAL_MARKET_COVERAGE",
    "HISTORICAL_EVIDENCE_ONLY", "MISSING_REQUIRED_CAPABILITY",
    "MISSING_ACCEPTANCE_INFRASTRUCTURE", "NOT_REQUIRED_FOR_J_ENTRY",
}
OUTCOMES = {
    "PHASE_J_READINESS_PREFLIGHT_PASS_READY_FOR_OWNER_J0_AUTHORIZATION",
    "PHASE_J_READINESS_PREFLIGHT_HOLD_FOR_BOUNDED_PREDECESSOR_GAPS",
    "PHASE_J_READINESS_PREFLIGHT_HOLD_FOR_CONTRACT_OR_GOVERNANCE_REPAIR",
}
GAP_CLASSES = {
    "CAPABILITY_ABSENT", "CONTRACT_PRESENT_RUNTIME_INACTIVE",
    "MARKET_COVERAGE_INCOMPLETE", "ACCEPTANCE_LAYER_GAP",
    "CURRENT_AUTHORITY_INCONSISTENT",
}
LAYERS = {
    "contract fixture", "deterministic unit", "integration", "service API",
    "Workbench", "MCP", "fresh-install", "real bounded network", "real AI / agent",
}
SEMANTICS = {
    "correct identity", "correct source", "correct period", "correct currentness",
    "correct missing", "correct partial", "correct corporate-action handling",
    "correct authorization", "correct bounded execution", "correct citations",
    "correct no-trading boundary",
}


def validate_record(record: dict, roadmap: str, closure: dict, mcp_count: int) -> dict:
    """Check record consistency; do not infer a product strategy from source code."""
    assert closure["status"] == "PHASE_I_COMPLETED_INDEPENDENT_EXIT_REVIEW_PASS"
    assert record["phase_i_closure"]["path"] == "docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json"
    assert record["phase_i_closure"]["status"] == closure["status"]
    assert "# [x] Phase I — Cross-Market & Optional Context" in roadmap
    assert "# [ ] Phase J — Integrated Research Acceptance" in roadmap
    j1 = roadmap.split("## J.1 Golden Research Scenarios", 1)[1].split("## J.2 Acceptance Layers", 1)[0]
    roadmap_scenarios = [line.strip() for line in j1.split("```", 2)[1].splitlines() if line.strip()]
    if roadmap_scenarios[0] == "text":
        roadmap_scenarios.pop(0)
    assert tuple(roadmap_scenarios) == SCENARIOS
    assert record["roadmap_phase_status"] == {"G": "unchecked", "H": "unchecked", "I": "complete", "J": "not_started"}
    assert record["phase_j_started"] is False
    assert record["phase_j_implementation_authorized"] is False
    assert record["market_GETs"] == {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "MOPS": 0, "other_market_research": 0}
    assert record["mcp_tool_count"] == mcp_count == 6
    assert record["final_disposition"] in OUTCOMES

    rows = record["golden_scenario_coverage_matrix"]
    ids = [row["scenario_id"] for row in rows]
    names = [row["scenario"] for row in rows]
    assert len(ids) == len(set(ids)) == len(SCENARIOS)
    assert len(names) == len(set(names)) == len(SCENARIOS)
    assert set(names) == set(SCENARIOS)
    assert all(row["readiness_class"] in READINESS_CLASSES for row in rows)
    assert all(row["roadmap_required"] is True for row in rows)
    assert all(isinstance(row["j_entry_blocker"], bool) for row in rows)
    assert all(row["reason"] and row["required_capability_or_contract"] and row["accepted_evidence"] for row in rows)
    blockers = record["j_blockers"]
    blocker_ids = {blocker["blocker_id"] for blocker in blockers}
    assert len(blocker_ids) == len(blockers)
    assert all(blocker["gap_class"] in GAP_CLASSES for blocker in blockers)
    assert all(blocker["scenario_ids"] and blocker["smallest_bounded_tranche"] for blocker in blockers)
    assert all(set(blocker["scenario_ids"]) <= set(ids) for blocker in blockers)
    for row in rows:
        assert set(row["blocker_ids"]) <= blocker_ids
        assert bool(row["blocker_ids"]) == row["j_entry_blocker"]
    blocked = any(row["j_entry_blocker"] for row in rows)
    if blocked:
        assert record["final_disposition"] != "PHASE_J_READINESS_PREFLIGHT_PASS_READY_FOR_OWNER_J0_AUTHORIZATION"
    if record["final_disposition"] == "PHASE_J_READINESS_PREFLIGHT_PASS_READY_FOR_OWNER_J0_AUTHORIZATION":
        assert not blocked
        assert not any(row["readiness_class"] in {
            "CONTRACT_PRESENT_RUNTIME_INACTIVE", "PARTIAL_MARKET_COVERAGE",
            "HISTORICAL_EVIDENCE_ONLY", "MISSING_REQUIRED_CAPABILITY",
            "MISSING_ACCEPTANCE_INFRASTRUCTURE"} for row in rows)
    else:
        assert blocked
        assert record["phase_j_implementation_authorized"] is False

    assert set(record["acceptance_layer_inventory"]) == LAYERS
    assert all(layer["reusable_for_j"] in (True, False, "partial") for layer in record["acceptance_layer_inventory"].values())
    assert set(record["golden_expected_semantics_readiness"]) == SEMANTICS
    assert all(item["status"] in {"READY", "PARTIAL", "BLOCKED"} for item in record["golden_expected_semantics_readiness"].values())
    assert all(value is False for value in record["scope_containment"].values())
    return {"status": "PASS", "scenario_count": len(rows), "blocker_count": len(blockers),
            "disposition": record["final_disposition"], "mcp_tool_count": mcp_count,
            "market_gets": sum(record["market_GETs"].values())}


def validate() -> dict:
    from server.unified_mcp.tool_contracts import build_tool_specs

    record = json.loads(RECORD.read_text(encoding="utf-8"))
    closure = json.loads((ROOT / record["phase_i_closure"]["path"]).read_text(encoding="utf-8"))
    return validate_record(record, (ROOT / "ROADMAP.md").read_text(encoding="utf-8"), closure, len(build_tool_specs()))


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
