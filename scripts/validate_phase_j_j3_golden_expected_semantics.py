#!/usr/bin/env python3
"""Validate and evaluate Phase J3 typed golden semantics (never golden prose)."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / "docs/governance/phase_j/PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json"
TRACE = ROOT / "docs/governance/phase_j/PHASE_J_J3_SEMANTIC_TRACEABILITY_V1.json"
REGISTRY = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json"
MATRIX = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json"
BASE = "2d1b51e531f36f5f032971ad7916d805c9af1276"
TREE = "ed2d1c4ee6c3f9c1a198fd3c792a5f0ccc6afdec"
MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
AUTH = "8c3e497debe7329f4051a2d0f4884cbe2505dace97395f1beca46ab1d3f2d047"
AUTH_STATEMENT = "AUTHORIZE PHASE J J3-R1 GOLDEN SEMANTIC FIDELITY & LOSSLESS PROJECTION HARDENING ON HEAD 2d1b51e531f36f5f032971ad7916d805c9af1276 TREE ed2d1c4ee6c3f9c1a198fd3c792a5f0ccc6afdec AFTER EXACT-HEAD REVIEW 5481919568: perform a strictly network-free repair of the Phase J J3 golden expected semantics candidate, semantic traceability, validator, tests, and additive governance evidence only; preserve the accepted J1 registry and matrix, accepted J2-R1 evidence, historical J2 and J3 evidence commits, all 27 scenario IDs, all 11 semantic dimensions, Unified Request/Result/Audit V3, exactly six MCP tools, and all no-live/no-real-agent/no-product-expansion boundaries; make J1-to-J3 projection lossless by defining deterministic normalization for every J1 assertion operator actually present, validating each assertion's scenario_id, assertion_id, context, path, normalized predicate, and normalized expected value rather than ID presence alone, and validating exact deep projection of every J1 expectation family into its assigned J3 dimension, including coverage_expectation and complete_family_claimed semantics, while also preserving accepted_fail_closed_outcomes and the full machine-relevant content of forbidden claims; strengthen bidirectional traceability and negative mutation tests so unchanged IDs with changed values, paths, contexts, operators, omitted expectation families, or weakened forbidden-claim content fail validation; do not add a new semantic dimension, rules engine, public schema, runtime behavior, source, route, capability, MCP tool, market/source request, Security Master mutation, bounded-live execution, real-agent execution, J4 start, Phase K start, PR merge, or Ready-for-Review transition; require focused network-free validation, strict duplicate-key JSON validation, compileall, git diff --check, and clean-archive default-CI with zero candidate-only failures; publish a final validated implementation commit followed only by additive sanitized J3-R1 evidence and stop for exact-head independent review."
DIMENSIONS = {"identity", "source", "period", "currentness", "missing", "partial", "corporate_action", "authorization", "bounded_execution", "citations_lineage", "no_trading"}
DIMENSION_ORDER = ["identity", "source", "period", "currentness", "missing", "partial", "corporate_action", "authorization", "bounded_execution", "citations_lineage", "no_trading"]
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


def _git_bytes(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def validate_projection(registry: dict, golden: dict, trace: dict) -> dict:
    """Check semantic content in both directions, not only source IDs."""
    from scripts.phase_j_j3_projection import (
        EXPECTATION_PROJECTIONS, FORBIDDEN_CONTENT_FIELDS, build_content_trace, operator_inventory,
    )

    source_rows = registry["scenarios"]
    target_rows = golden["scenarios"]
    require([x["scenario_id"] for x in target_rows] == [x["scenario_id"] for x in source_rows], "scenario identity/order mismatch")
    require(len(target_rows) == 27 and len({x["scenario_id"] for x in target_rows}) == 27, "expected exactly 27 stable J1 scenarios")
    target_by_id = {row["scenario_id"]: row for row in target_rows}
    expected_keys = {}
    for family, (dimension, key) in EXPECTATION_PROJECTIONS.items():
        expected_keys.setdefault(dimension, set()).add(key)
    expected_keys["no_trading"] = {"inherits_global_boundary", "no_recommendation", "no_trade_action"}
    for source_row in source_rows:
        sid = source_row["scenario_id"]
        target = target_by_id[sid]
        source_assertion_ids = [item["assertion_id"] for item in source_row["expected_semantic_assertions"]]
        require(len(source_assertion_ids) == len(set(source_assertion_ids)), f"{sid}: duplicate J1 assertion ID")
        require(target["readiness_status"] == source_row["current_readiness_status"], f"{sid}: readiness status projection mismatch")
        require(target["accepted_fail_closed_outcomes"] == source_row["accepted_fail_closed_outcomes"], f"{sid}: accepted fail-closed outcomes projection mismatch")
        require(len(target["assertions"]) == len(source_row["expected_semantic_assertions"]), f"{sid}: assertion added/dropped")
        target_assertions = {row.get("assertion_id"): row for row in target["assertions"]}
        require(len(target_assertions) == len(target["assertions"]), f"{sid}: duplicate assertion ID")
        for source_assertion in source_row["expected_semantic_assertions"]:
            aid = source_assertion["assertion_id"]
            require(aid in target_assertions, f"{sid}/{aid}: assertion dropped")
            projected = target_assertions[aid]
            from scripts.phase_j_j3_projection import normalize_assertion
            normalized = normalize_assertion(sid, source_assertion)
            for field, value in normalized.items():
                require(projected.get(field) == value, f"{sid}/{aid}: assertion {field} projection mismatch")
        require(set(target["dimensions"]) == DIMENSIONS, f"{sid}: semantic dimension set mismatch")
        for dim in DIMENSION_ORDER:
            cell = target["dimensions"][dim]
            require(cell["applicability"] in {"APPLICABLE", "NOT_APPLICABLE"}, f"{sid}/{dim}: applicability missing")
            require(cell["authority_refs"], f"{sid}/{dim}: no provenance")
            require(set(cell["expectations"]) == expected_keys[dim], f"{sid}/{dim}: expectation family projection keys mismatch")
        for family, (dimension, key) in EXPECTATION_PROJECTIONS.items():
            require(target["dimensions"][dimension]["expectations"][key] == source_row[family], f"{sid}/{family}: deep projection mismatch")
        source_claims = source_row["forbidden_claims"]
        target_claims = target["forbidden_claims"]
        source_claim_ids = [item["claim_id"] for item in source_claims]
        require(len(source_claim_ids) == len(set(source_claim_ids)), f"{sid}: duplicate J1 forbidden claim ID")
        require(len(target_claims) == len(source_claims), f"{sid}: forbidden claim count mismatch")
        target_claim_map = {claim.get("claim_id"): claim for claim in target_claims}
        require(len(target_claim_map) == len(target_claims), f"{sid}: duplicate/replacement forbidden claim ID")
        require(set(target_claim_map) == {claim["claim_id"] for claim in source_claims}, f"{sid}: forbidden claim IDs mismatch")
        for source_claim in source_claims:
            target_claim = target_claim_map[source_claim["claim_id"]]
            for field in FORBIDDEN_CONTENT_FIELDS:
                expected = source_claim.get(field)
                require(target_claim.get(field) == expected, f"{sid}/{source_claim['claim_id']}: forbidden claim {field} projection mismatch")

    expected_content = build_content_trace(registry, golden)
    for name, rows in expected_content.items():
        actual = trace.get(name)
        require(actual == rows, f"trace content mapping mismatch: {name}")
        require(all(row["match"] and row["source_canonical_sha256"] == row["target_canonical_sha256"] for row in actual), f"trace hash mismatch: {name}")
    return {
        "assertion_operator_inventory": operator_inventory(registry),
        "assertion_projection_count": len(expected_content["assertion_content_mappings"]),
        "expectation_family_projection_count": len(expected_content["expectation_family_mappings"]),
        "forbidden_claim_projection_count": len(expected_content["forbidden_claim_content_mappings"]),
        "accepted_fail_closed_projection_count": len(expected_content["accepted_fail_closed_mappings"]),
        "readiness_status_projection_count": len(expected_content["readiness_status_mappings"]),
        "content_mismatches": 0,
        "orphan_source_elements": 0,
        "orphan_target_elements": 0,
    }


def validate_contract() -> dict:
    golden, trace, registry = read_json(GOLDEN), read_json(TRACE), read_json(REGISTRY)
    require(_git("rev-parse", BASE + "^{tree}") == TREE, "authorized base tree changed")
    require(_git("rev-parse", "origin/main") == MAIN, "origin/main changed")
    require(_git("merge-base", "--is-ancestor", BASE, "HEAD") is not None, "base ancestry missing")
    require(sha(REGISTRY) == "b26712d1389b904ff003b22aa135caac43ab8f6fc7b32dad571b70438248c864", "J1 registry changed")
    require(sha(MATRIX) == "5d07ab2618e6bfa6c79f796df28cd69df5c105fb8f60396c293675737febcd45", "J1 matrix changed")
    for name, expected in J2.items():
        require(sha(REGISTRY.parent / name) == expected, f"accepted J2-R1 artifact changed: {name}")
    historical_j3 = {
        "PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_V1.json": "c87557fd24b303d18edeaece467b9ffdf22096599b3538422326ffd27467d2b2",
        "PHASE_J_J3_SEMANTIC_TRACEABILITY_V1.json": "b93f452fdfbd02cec529165c100c96776e76b4a5b7bf3c47144053d1fd9e27f4",
    }
    for name, expected in historical_j3.items():
        actual = hashlib.sha256(_git_bytes("show", f"{BASE}:docs/governance/phase_j/{name}")).hexdigest()
        require(actual == expected, f"historical J3 candidate changed at authorized base: {name}")
    require(sha(REGISTRY.parent / "PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_2026-10-11.json") == "5c83046c04924c53fbe97b9f200a22363e139d43524b1d2edd1b27c8761a623a", "historical J3 governance JSON changed")
    require(sha(REGISTRY.parent / "PHASE_J_J3_GOLDEN_EXPECTED_SEMANTICS_2026-10-11.md") == "dc093e1e06cb4a442e7abc4310a33a80d532e5899914d17540e05ccb7b218bc8", "historical J3 governance Markdown changed")
    scenarios, source = golden["scenarios"], registry["scenarios"]
    require(golden["baseline_binding"]["owner_authorization_sha256"] == AUTH, "Owner authorization hash mismatch")
    require(hashlib.sha256(AUTH_STATEMENT.encode("utf-8")).hexdigest() == AUTH, "exact Owner authorization statement hash mismatch")
    require(golden["baseline_binding"]["head"] == BASE and golden["baseline_binding"]["tree"] == TREE, "J3-R1 baseline mismatch")
    require(golden["dimensions"] == DIMENSION_ORDER, "dimension set/order mismatch")
    forward = {(m["scenario_id"], m["source_assertion_id"]) for m in trace["forward_assertion_mappings"]}
    reverse = {(s["scenario_id"], a["assertion_id"]) for s in scenarios for a in s["assertions"]}
    source_assertions = {(s["scenario_id"], a["assertion_id"]) for s in source for a in s["expected_semantic_assertions"]}
    require(forward == reverse == source_assertions, "J1/J3 assertion ID traceability is not bidirectionally complete")
    forbidden = {(m["scenario_id"], m["claim_id"]) for m in trace["forbidden_claim_mappings"]}
    golden_forbidden = {(s["scenario_id"], f["claim_id"]) for s in scenarios for f in s["forbidden_claims"]}
    source_forbidden = {(s["scenario_id"], f["claim_id"]) for s in source for f in s["forbidden_claims"]}
    require(forbidden == golden_forbidden == source_forbidden, "J1/J3 forbidden-claim traceability incomplete")
    projection = validate_projection(registry, golden, trace)
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
    require(golden["authority_status"] == "J3_R1_FROZEN_ACCEPTANCE_CANDIDATE_PENDING_REVIEW", "J3-R1 candidate state mismatch")
    require(golden["phase_state"] == {"Phase_J": "STARTED", "J0": "COMPLETE", "J1": "INDEPENDENTLY_ACCEPTED", "J2": "CLOSED_INDEPENDENTLY_ACCEPTED", "J3": "R1_FROZEN_ACCEPTANCE_CANDIDATE_PENDING_REVIEW", "J4": "NOT_STARTED", "Phase_K": "NOT_STARTED"}, "Phase J state drift")
    require(golden["authorization_state"] == {"bounded_live": "NOT_GRANTED", "real_agent": "NOT_GRANTED"}, "future execution authority drift")
    require(golden["network_policy"] == "NETWORK_FREE", "J3 network policy drift")
    require(registry["live_authorization"] == registry["real_agent_authorization"] == "NOT_GRANTED", "J1 authorization drift")
    require(trace["accepted_j2_r1"]["review"] == "5481723267", "accepted J2-R1 review mismatch")
    require(golden["authority_reviews"].get("r1_review") == "5481919568", "J3-R1 predecessor review mismatch")
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    tools = [x.name for x in build_tool_contract_snapshot().tools]
    require(tools == golden["contracts"]["mcp_tools"], "MCP tool contract drift")
    entry = json.loads((ROOT / "docs/governance/phase_j/PHASE_J_J2_R1_WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.json").read_text())
    require(entry["Phase_J"] == "STARTED" and entry["Phase_K"] == "NOT_STARTED", "phase state drift")
    return {"scenario_count": len(scenarios), "dimension_count": len(DIMENSIONS), "j1_assertions_mapped": len(forward), "j1_forbidden_claims_mapped": len(forbidden), "orphan_assertions": 0, "dropped_assertions": 0, "mcp_tools": len(tools), **projection}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate_contract(), indent=2))
