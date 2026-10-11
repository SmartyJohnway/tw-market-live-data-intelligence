#!/usr/bin/env python3
"""Validate and evaluate Phase J3 typed golden semantics (never golden prose)."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / "docs/governance/phase_j/PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json"
TRACE = ROOT / "docs/governance/phase_j/PHASE_J_J3_SEMANTIC_TRACEABILITY_V1.json"
REGISTRY = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json"
MATRIX = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json"
BASE = "7454c4613e50759265ebf4c96ec6571117b2c1a4"
TREE = "75f6f907102ab469e0e7a6de381eec206ba9620a"
MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
AUTH = "7dd958505bbd70fda4c0b7be712c98c05987e4552a7c6ee89c4affde5a6a91e0"
AUTH_STATEMENT = "AUTHORIZE PHASE J J3 GOLDEN EXPECTED SEMANTICS ON HEAD 7454c4613e50759265ebf4c96ec6571117b2c1a4 TREE 75f6f907102ab469e0e7a6de381eec206ba9620a AFTER J2-R1 EXACT-HEAD INDEPENDENT REVIEW 5481723267 AND J2 CLOSURE/J3 START AUTHORIZATION REVIEW 5481754513: perform a strictly network-free Phase J J3 tranche that preserves the independently accepted J1 27-scenario registry, accepted J1 baseline matrix, accepted J2-R1 deterministic cross-layer evidence and all historical J2 records as immutable authorities, and formalizes machine-verifiable golden expected semantics for all 27 governed scenarios across correct identity, source, period, currentness, missing, partial, corporate-action handling, authorization, bounded execution, citations/lineage, and no-trading boundaries without using exact natural-language output as acceptance; reuse existing Unified Request/Result/Audit V3, Workbench, Local Service, MCP and semantic evidence contracts, add only acceptance/governance schemas or data, validators and tests, make no production runtime, public schema, route, capability, Security Master or six-tool MCP changes, make zero market/source requests, zero bounded-live executions and zero real-agent executions, grant no live or real-agent authority, do not start J4 or Phase K, do not merge or mark PR #326 ready, require focused semantic/regression validation, strict duplicate-key JSON validation, compileall, git diff --check and clean-archive default-CI with zero candidate-only failures, publish a validated implementation commit followed only by sanitized evidence, and stop for exact-head independent review."
DIMENSIONS = {"identity", "source", "period", "currentness", "missing", "partial", "corporate_action", "authorization", "bounded_execution", "citations_lineage", "no_trading"}
J2 = {
    "PHASE_J_J2_R1_COVERAGE_DELTA_V1.json": "321e9008ebca8d8a42e77993ae9329b274dd3e05ad5553554890f97e65618539",
    "PHASE_J_J2_R1_EFFECTIVE_COVERAGE_MATRIX_V1.json": "8fe53871a764d66dcca6d3a5531d4801008c58f77e74ace7eede637f15436c3a",
    "PHASE_J_J2_R1_WORKBENCH_HEADLESS_EXECUTION_LEDGER_V1.json": "2c30451e2dc6071191d7d5107149770c4d34767cc45c26b5fa819b68249239fa",
    "PHASE_J_J2_R1_WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.json": "74e27776bf9768613cbc25f1f6cf3c81687f29be2551f4f9e31141772ac29487",
    "PHASE_J_J2_R1_WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.md": "eb324584ef03103137eec03a5190ba5bb6c2bd7d6b1d66c16693cae3920975f0",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def _path(value, dotted):
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


_MISSING = object()


def evaluate_scenario(scenario: dict, observed: dict) -> list[str]:
    """Return typed semantic failures. Free-form wording is deliberately ignored."""
    errors = []
    for assertion in scenario["assertions"]:
        actual = _path(observed.get(assertion["context"], {}), assertion["path"])
        if assertion["predicate"] != "equals" or actual is _MISSING or actual != assertion["expected"]:
            errors.append(f"{assertion['assertion_id']}: expected {assertion['expected']!r}")
    facts = observed.get("facts", {})
    checks = [
        (facts.get("source_state") == "source_failed" and facts.get("valid_empty") is True, "source_failed cannot be valid_empty"),
        (facts.get("evidence_state") in {"missing", "no_evidence_in_covered_scope", "missing_or_not_yet_available_or_no_evidence"} and facts.get("numeric_value") == 0, "missing cannot become zero"),
        (facts.get("partial") is True and facts.get("result_status") == "full_success", "partial cannot become full_success"),
        (facts.get("authorization") == "refused" and facts.get("execution_started") is True, "refusal cannot start execution"),
        (facts.get("identity_resolution") == "ambiguous" and facts.get("execution_started") is True, "ambiguous identity cannot execute"),
        (facts.get("h4_state") == "coverage_incomplete" and facts.get("ordinary_return_interpretation") == "allowed", "H4 incomplete coverage must block ordinary return"),
        (facts.get("resource_bound") == "enforced" and facts.get("unbounded_execution") is True, "resource bound cannot be bypassed"),
        (facts.get("citation_source") is not None and facts.get("evidence_source") is not None and facts["citation_source"] != facts["evidence_source"], "citation/source mismatch"),
        (facts.get("result_id") is not None and facts.get("audit_result_id") is not None and facts["result_id"] != facts["audit_result_id"], "Result/Audit lineage mismatch"),
        (bool(observed.get("violated_forbidden_claim_ids")), "forbidden semantic claim present"),
    ]
    errors.extend(message for failed, message in checks if failed)
    return errors


def _git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate_contract() -> dict:
    golden, trace, registry = read_json(GOLDEN), read_json(TRACE), read_json(REGISTRY)
    require(_git("rev-parse", BASE + "^{tree}") == TREE, "authorized base tree changed")
    require(_git("rev-parse", "origin/main") == MAIN, "origin/main changed")
    require(_git("merge-base", "--is-ancestor", BASE, "HEAD") is not None, "base ancestry missing")
    require(sha(REGISTRY) == "b26712d1389b904ff003b22aa135caac43ab8f6fc7b32dad571b70438248c864", "J1 registry changed")
    require(sha(MATRIX) == "5d07ab2618e6bfa6c79f796df28cd69df5c105fb8f60396c293675737febcd45", "J1 matrix changed")
    for name, expected in J2.items():
        require(sha(REGISTRY.parent / name) == expected, f"accepted J2-R1 artifact changed: {name}")
    scenarios, source = golden["scenarios"], registry["scenarios"]
    require([x["scenario_id"] for x in scenarios] == [x["scenario_id"] for x in source], "scenario identity/order mismatch")
    require(len(scenarios) == 27 and len({x["scenario_id"] for x in scenarios}) == 27, "expected exactly 27 stable J1 scenarios")
    require(golden["baseline_binding"]["owner_authorization_sha256"] == AUTH, "Owner authorization hash mismatch")
    require(hashlib.sha256(AUTH_STATEMENT.encode("utf-8")).hexdigest() == AUTH, "exact Owner authorization statement hash mismatch")
    require(golden["baseline_binding"]["head"] == BASE and golden["baseline_binding"]["tree"] == TREE, "J3 baseline mismatch")
    require(golden["dimensions"] == ["identity", "source", "period", "currentness", "missing", "partial", "corporate_action", "authorization", "bounded_execution", "citations_lineage", "no_trading"], "dimension set/order mismatch")
    forward = {(m["scenario_id"], m["source_assertion_id"]) for m in trace["forward_assertion_mappings"]}
    reverse = {(s["scenario_id"], a["assertion_id"]) for s in scenarios for a in s["assertions"]}
    source_assertions = {(s["scenario_id"], a["assertion_id"]) for s in source for a in s["expected_semantic_assertions"]}
    require(forward == reverse == source_assertions, "J1/J3 assertion traceability is not bidirectionally complete")
    forbidden = {(m["scenario_id"], m["claim_id"]) for m in trace["forbidden_claim_mappings"]}
    golden_forbidden = {(s["scenario_id"], f["claim_id"]) for s in scenarios for f in s["forbidden_claims"]}
    source_forbidden = {(s["scenario_id"], f["claim_id"]) for s in source for f in s["forbidden_claims"]}
    require(forbidden == golden_forbidden == source_forbidden, "J1/J3 forbidden-claim traceability incomplete")
    for scenario, source_scenario in zip(scenarios, source):
        require(set(scenario["dimensions"]) == DIMENSIONS, f"{scenario['scenario_id']}: dimensions missing")
        require([x["assertion_id"] for x in scenario["assertions"]] == [x["assertion_id"] for x in source_scenario["expected_semantic_assertions"]], f"{scenario['scenario_id']}: J1 assertion dropped/reordered")
        for dim, value in scenario["dimensions"].items():
            require(value["applicability"] in {"APPLICABLE", "NOT_APPLICABLE"}, f"{scenario['scenario_id']}/{dim}: applicability missing")
            require(value["authority_refs"], f"{scenario['scenario_id']}/{dim}: no provenance")
        require(len(scenario["forbidden_claims"]) == len(source_scenario["forbidden_claims"]), f"{scenario['scenario_id']}: forbidden claim dropped")
    banned = {"expected_answer", "golden_answer", "expected_markdown", "exact_response", "expected_sentence", "expected_paragraph"}
    def walk(node):
        if isinstance(node, dict):
            require(not (set(node) & banned), "golden prose field is prohibited")
            for value in node.values(): walk(value)
        elif isinstance(node, list):
            for value in node: walk(value)
    walk(golden)
    require(golden["contracts"] == registry["public_contracts"], "public V3 contract drift")
    require(golden["contracts"]["mcp_tool_count"] == 6, "MCP count drift")
    require(golden["phase_state"] == {"Phase_J": "STARTED", "J0": "COMPLETE", "J1": "INDEPENDENTLY_ACCEPTED", "J2": "CLOSED_INDEPENDENTLY_ACCEPTED", "J3": "AUTHORIZED_TO_START", "J4": "NOT_STARTED", "Phase_K": "NOT_STARTED"}, "Phase J state drift")
    require(golden["authorization_state"] == {"bounded_live": "NOT_GRANTED", "real_agent": "NOT_GRANTED"}, "future execution authority drift")
    require(golden["network_policy"] == "NETWORK_FREE", "J3 network policy drift")
    require(registry["live_authorization"] == registry["real_agent_authorization"] == "NOT_GRANTED", "J1 authorization drift")
    require(trace["accepted_j2_r1"]["review"] == "5481723267", "accepted J2-R1 review mismatch")
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    tools = [x.name for x in build_tool_contract_snapshot().tools]
    require(tools == golden["contracts"]["mcp_tools"], "MCP tool contract drift")
    entry = json.loads((ROOT / "docs/governance/phase_j/PHASE_J_J2_R1_WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.json").read_text())
    require(entry["Phase_J"] == "STARTED" and entry["Phase_K"] == "NOT_STARTED", "phase state drift")
    return {"scenario_count": len(scenarios), "dimension_count": len(DIMENSIONS), "j1_assertions_mapped": len(forward), "j1_forbidden_claims_mapped": len(forbidden), "orphan_assertions": 0, "dropped_assertions": 0, "mcp_tools": len(tools)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate_contract(), indent=2))
