"""Validate J-B03-C0 closure and Phase-J readiness reconciliation."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.json"
PREFLIGHT = ROOT / "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json"
S3 = ROOT / "docs/governance/phase_j/PHASE_J_J_B03_S3_NATIVE_EVIDENCE_FALLBACK_PRODUCT_CONTRACT_2026-10-06.json"
A26 = ROOT / "docs/governance/phase_j/PHASE_J_J_B03_A2_6_REPRESENTATIVE_INTEGRATED_ACCEPTANCE_AND_ACTIVATION_DECISION_2026-10-07.json"
ROUTING = ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json"

def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def validate_record(record, preflight, s3, a26, routing):
    assert record["decision"] == "J_B03_CLOSED_BOUNDED_CONVERSATIONAL_CORRECTNESS_SATISFIED"
    assert record["closure_review_disposition"] == "J_B03_CLOSE_RECOMMENDED"
    assert record["product_exit_basis"]["satisfied"] is True
    assert record["product_exit_basis"]["full_h1_required_for_j_b03_closure"] is False
    assert record["issue_disposition"]["H0-SRC-01E"]["state"] == "OPEN"
    assert record["issue_disposition"]["H0-SRC-01E"]["j_b03_closure_blocker"] is False
    assert record["issue_disposition"]["H0-SRC-02"]["state"] == "OPEN"
    assert record["issue_disposition"]["H0-SRC-02"]["j_b03_closure_blocker"] is False
    assert record["issue_disposition"]["J-B03"]["current_state"] == "CLOSED"
    assert record["issue_disposition"]["J-B04"]["current_state"] == "BLOCKING"
    assert record["issue_disposition"]["Phase J"]["current_state"] == "NOT_STARTED"
    assert record["phase_j_readiness"]["remaining_entry_blockers"] == ["J-B04"]
    assert record["phase_j_readiness"]["phase_j_started"] is False
    assert record["phase_j_readiness"]["ready_for_j0_authorization"] is False
    assert record["scope_containment"]["MCP_tool_count"] == 6
    assert record["scope_containment"]["market_GETs"] == 0
    assert record["scope_containment"]["market_HEADs"] == 0
    assert record["scope_containment"]["market_POSTs"] == 0

    # Historical preflight stays historical: it identified both B03 and B04 as blockers.
    r = {x["blocker_id"]: x for x in preflight["reclassified_blockers"]}
    assert r["J-B03"]["new_j_entry_blocker"] is True
    assert r["J-B04"]["new_j_entry_blocker"] is True

    # S3 is the later, narrower product authority that makes representative closure possible.
    assert s3["decision"]["primary_disposition"] == "J_B03_S3_NATIVE_EVIDENCE_FALLBACK_ACCEPTED"
    assert "representative" in json.dumps(s3, ensure_ascii=False).lower()

    # A2.6 must contain the accepted production activation, while preserving incomplete-H1 truth.
    text = json.dumps(a26, ensure_ascii=False)
    assert "J_B03_A2_6_PRODUCTION_ACTIVATION_ACCEPTED" in text
    assert "H0-SRC-02" in text

    route = next(x for x in routing["routes"] if x["capability_id"] == "trading_status_context")
    assert route["runtime_executable"] is True
    assert route["selected_executor_id"] == "phase_h_h1_tpex_composite_executor"
    assert route["output_evidence_contract"] == "trading_status_context_composite.v1"
    limits = " ".join(route["known_limitations"])
    assert "attention and disposition" in limits
    assert "suspension" in limits and "resumption" in limits
    assert "H0-SRC-02" in limits
    return {"status":"PASS","j_b03":"CLOSED","remaining_blocker":"J-B04","mcp":6,"market_gets":0}

def validate():
    return validate_record(_load(RECORD), _load(PREFLIGHT), _load(S3), _load(A26), _load(ROUTING))

if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
