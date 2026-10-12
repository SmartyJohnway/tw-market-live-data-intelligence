from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "governance" / "phase_j"
START_HEAD = "a0ea2163ce4b4bb0cb81997c6a350a9312e05bb7"
START_TREE = "11cb2f2104abba2257a79bb5736705d848cf5a43"
ATTEMPT6_RECEIPT_SHA = "74d439aa5083bc53f874bdba094f5268adf40485da7346e530d4c08bd3bdff33"
ATTEMPT6_OUTPUT_SHA = "5e971dbd6b2059d13fd7f91efc990edcd23ee883d7c5dd2daa10a7275533325b"
RECON = DOC / "PHASE_J_CLOSURE_AUTHORITY_RECONCILIATION_2026-10-12.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(check_git: bool = True) -> dict[str, object]:
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    require("# [x] Phase J — Integrated Research Acceptance" in roadmap, "ROADMAP_PHASE_J_HEADING_NOT_CHECKED")
    require("[x] Phase J — Integrated Research Acceptance" in roadmap, "ROADMAP_PHASE_J_CHECKLIST_NOT_CHECKED")
    require("real AI / agent" in roadmap, "ROADMAP_REAL_AGENT_LAYER_MISSING")
    require("不是每個 scenario 都要每層完整重跑" in roadmap, "ROADMAP_COVERAGE_POLICY_MISSING")
    require("correct currentness" in roadmap and "correct no-trading boundary" in roadmap, "ROADMAP_J3_SEMANTICS_MISSING")
    require("tool-call sequencing" in roadmap, "ROADMAP_PHASE_K_SEQUENCING_MISSING")
    require("# [ ] Phase K — Multi-Agent Compatibility & Evaluation" in roadmap, "PHASE_K_STATE_DRIFT")

    attempt_path = DOC / "PHASE_J_FINAL_REAL_AGENT_ATTEMPT_6_RECEIPT_2026-10-12.json"
    output_path = DOC / "PHASE_J_FINAL_REAL_AGENT_ATTEMPT_6_OUTPUT_2026-10-12.txt"
    require(sha256(attempt_path) == ATTEMPT6_RECEIPT_SHA, "ATTEMPT6_HISTORY_MUTATED")
    require(sha256(output_path) == ATTEMPT6_OUTPUT_SHA, "ATTEMPT6_OUTPUT_MUTATED")
    attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
    require(attempt["disposition"] == "PHASE_J_REAL_AGENT_ATTEMPT_6_HARD_BLOCK_TOOL_POLICY_VIOLATION", "ATTEMPT6_DISPOSITION_REWRITTEN")
    require(attempt["semantic_evaluation"]["result_interpretation"] == "PASS", "ATTEMPT6_J3_RESULT_INTERPRETATION_NOT_PASS")
    require(attempt["slot"]["result_lineage_obtained"] is True, "ATTEMPT6_RESULT_LINEAGE_MISSING")
    require(attempt["mcp_outcome"]["handoff_retrieved"] is False, "ATTEMPT6_HANDOFF_HISTORY_DRIFT")
    require(attempt["boundaries"]["fresh_market_get_head_post"] == [0, 0, 0], "ATTEMPT6_MARKET_NETWORK_NONZERO")
    require(attempt["boundaries"]["new_j1_21_executions"] == 0, "ATTEMPT6_NEW_J1_EXECUTION")
    require(attempt["boundaries"]["new_packages"] == 0, "ATTEMPT6_NEW_PACKAGE")
    sequence = [event["name"] for event in attempt["formal_mcp_event_sequence"]]
    require(sequence == ["market_export_ai_handoff", "market_read_result", "market_read_result"], "ATTEMPT6_EVENT_SEQUENCE_DRIFT")
    require(attempt["formal_mcp_event_sequence"][0]["event"] == "blocked_tool_call", "ATTEMPT6_FIRST_EXPORT_NOT_BLOCKED")
    require(attempt["formal_mcp_event_sequence"][2]["success"] is True, "ATTEMPT6_READ_RESULT_NOT_SUCCESSFUL")

    closure = (ROOT / "scripts" / "validate_phase_j_final_closure_r1.py").read_text(encoding="utf-8")
    require("AGENT_OPERATIONS_INCOMPLETE" in closure, "CLOSURE_R1_AGENT_RULE_MISSING")
    require(">={'market_read_result','market_export_ai_handoff'}" in closure, "CLOSURE_R1_AGENT_RULE_NOT_SET_BASED")

    contracts = (ROOT / "server" / "unified_mcp" / "tool_contracts.py").read_text(encoding="utf-8")
    require("Read or verify the governed Result for one finalized control package" in contracts, "READ_RESULT_CONTRACT_DRIFT")
    require("Export the existing governed AI-ready handoff for one finalized control package" in contracts, "HANDOFF_CONTRACT_DRIFT")

    recon = json.loads(RECON.read_text(encoding="utf-8"))
    require(recon["disposition"] == "PHASE_J_CLOSURE_AUTHORITY_RECONCILIATION_PASS", "RECONCILIATION_DISPOSITION_INVALID")
    require(recon["attempt6_adjudication"]["real_agent_layer_satisfied"] is True, "REAL_AGENT_LAYER_NOT_SATISFIED")
    require(recon["phase_state"]["remaining_obligations"] == [], "REMAINING_OBLIGATIONS_NONEMPTY")
    require(recon["phase_state"]["phase_j"] == "COMPLETE", "PHASE_J_NOT_COMPLETE")
    require(recon["phase_state"]["phase_k"] == "NOT_STARTED", "PHASE_K_STARTED")

    for current_name in ("PROJECT.md", "HANDOFF.md", "AGENTS.md"):
        current_text = (ROOT / current_name).read_text(encoding="utf-8")
        require("PHASE_J_CLOSURE_AUTHORITY_RECONCILIATION_PASS" in current_text, f"CURRENT_AUTHORITY_NOT_RECONCILED:{current_name}")
        require("Phase K" in current_text and "NOT_STARTED" in current_text, f"PHASE_K_BOUNDARY_MISSING:{current_name}")

    if check_git:
        git = lambda *args: subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
        require(git("branch", "--show-current") == "phase-j/j-b04-a5-bounded-live-source-acceptance", "BRANCH_DRIFT")
        require(git("rev-parse", "origin/main") == "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a", "MAIN_DRIFT")
        changed = set(git("diff", "--name-only", START_HEAD, "HEAD").splitlines())
        allowed = {
            "ROADMAP.md", "PROJECT.md", "HANDOFF.md", "AGENTS.md",
            "docs/governance/phase_j/PHASE_J_CLOSURE_AUTHORITY_RECONCILIATION_2026-10-12.json",
            "docs/governance/phase_j/PHASE_J_CLOSURE_AUTHORITY_RECONCILIATION_2026-10-12.md",
            "scripts/validate_phase_j_closure_authority_reconciliation.py",
            "tests/unit/test_phase_j_closure_authority_reconciliation.py",
        }
        require(changed <= allowed, f"UNAUTHORIZED_RECONCILIATION_DIFF:{sorted(changed - allowed)}")

    return {
        "status": "PASS",
        "phase_j": "COMPLETE",
        "real_agent_layer": "SATISFIED",
        "remaining_obligations": [],
        "phase_k": "NOT_STARTED",
        "attempt7_required": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, ensure_ascii=False))
