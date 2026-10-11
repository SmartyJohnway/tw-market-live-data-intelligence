#!/usr/bin/env python3
"""Validate the additive, network-free Phase J J2 coverage candidate."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
START = "230606eb0b51b2004dbeac72f8c2908abe0372d3"
START_TREE = "225a964207cc4a9edded1e2928a7cac1ba303d4a"
MAIN = "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
AUTH = "6657ce311e1d360cf3ab9af6f8f1d4ca78b68cb84d7dfa750cb1254b30ca10a2"
REGISTRY_REL = "docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json"
MATRIX_REL = "docs/governance/phase_j/PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json"
DELTA_REL = "docs/governance/phase_j/PHASE_J_J2_DETERMINISTIC_CROSS_LAYER_COVERAGE_DELTA_V1.json"
EFFECTIVE_REL = "docs/governance/phase_j/PHASE_J_J2_EFFECTIVE_COVERAGE_MATRIX_V1.json"
LEDGER_REL = "docs/governance/phase_j/PHASE_J_J2_DETERMINISTIC_CROSS_LAYER_EXECUTION_LEDGER_V1.json"
REGISTRY_SHA = "b26712d1389b904ff003b22aa135caac43ab8f6fc7b32dad571b70438248c864"
MATRIX_SHA = "5d07ab2618e6bfa6c79f796df28cd69df5c105fb8f60396c293675737febcd45"
REVIEW = "5481271339"
TARGETS = [
    "J1-01", "J1-07", "J1-08", "J1-10", "J1-11", "J1-12", "J1-13",
    "J1-14", "J1-16", "J1-18", "J1-20", "J1-22", "J1-23", "J1-24",
    "J1-25", "J1-26", "J1-27",
]
STATUSES = {
    "COVERED_EXISTING", "COVERED_J0_J1", "PLANNED", "REQUIRES_LIVE_AUTH",
    "REQUIRES_REAL_AGENT_AUTH", "EXPECTED_FAIL_CLOSED", "NOT_APPLICABLE", "BLOCKED",
}
LAYERS = [
    "contract_fixture", "deterministic_unit", "integration", "service_api",
    "workbench", "mcp", "fresh_install", "bounded_live", "real_agent",
]
EVIDENCE_KIND_BY_LAYER = {"service_api": "service_test", "mcp": "mcp_test"}
ALLOWED_FILES = {
    "scripts/validate_phase_j_j2_deterministic_cross_layer.py",
    "tests/integration/test_phase_j_j2_deterministic_cross_layer.py",
    DELTA_REL, EFFECTIVE_REL, LEDGER_REL,
    "docs/governance/phase_j/PHASE_J_J2_DETERMINISTIC_CROSS_LAYER_SCENARIO_EXECUTION_2026-10-11.json",
    "docs/governance/phase_j/PHASE_J_J2_DETERMINISTIC_CROSS_LAYER_SCENARIO_EXECUTION_2026-10-11.md",
}


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _strict_json(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r} in {path}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def _status_counts(matrix: dict[str, Any]) -> dict[str, int]:
    counts = Counter(cell["status"] for row in matrix["scenarios"] for cell in row["layers"].values())
    return {status: counts[status] for status in matrix["coverage_statuses"]}


def _validate() -> dict[str, Any]:
    registry_path, matrix_path = ROOT / REGISTRY_REL, ROOT / MATRIX_REL
    delta_path, effective_path, ledger_path = ROOT / DELTA_REL, ROOT / EFFECTIVE_REL, ROOT / LEDGER_REL
    _require(_sha(registry_path) == REGISTRY_SHA, "accepted J1 registry hash changed")
    _require(_sha(matrix_path) == MATRIX_SHA, "accepted J1 coverage matrix hash changed")
    registry, baseline = _strict_json(registry_path), _strict_json(matrix_path)
    delta, effective, ledger = _strict_json(delta_path), _strict_json(effective_path), _strict_json(ledger_path)

    _require(_git("rev-parse", START) == START, "starting commit missing")
    _require(_git("rev-parse", f"{START}^{{tree}}") == START_TREE, "starting tree authority mismatch")
    _require(_git("rev-parse", "origin/main") == MAIN, "origin/main authority drift")
    _require(_git("merge-base", "--is-ancestor", START, "HEAD") == "", "starting authority is not an ancestor")
    _require(_git("rev-parse", "HEAD") != START, "J2 implementation/evidence commits missing")

    changed = set(_git("diff", "--name-only", f"{START}..HEAD").splitlines())
    _require(changed <= ALLOWED_FILES, f"J2 changed files outside acceptance/evidence scope: {sorted(changed - ALLOWED_FILES)}")
    _require(not any(path.startswith(("server/", "schemas/", "frontend/", "docs/data_capabilities/")) for path in changed), "production/runtime or public contract changed")
    for history_rel in (
        "docs/governance/phase_j/PHASE_J_J0_START_AND_J1_ACCEPTANCE_ARCHITECTURE_2026-10-11.json",
        "docs/governance/phase_j/PHASE_J_J0_START_AND_J1_ACCEPTANCE_ARCHITECTURE_2026-10-11.md",
        "docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.json",
        "docs/governance/phase_j/PHASE_J_J_B04_A6_INTEGRATED_MARKET_RESEARCH_INTERPRETATION_LIVE_ACCEPTANCE_2026-10-10.json",
        "docs/governance/phase_j/PHASE_J_J_B04_A6_R1_H3_STOCK_DAY_CLOSE_NUMERIC_CONTRACT_REPAIR_2026-10-10.json",
        "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json",
    ):
        before = subprocess.run(["git", "show", f"{START}:{history_rel}"], cwd=ROOT, capture_output=True)
        _require(before.returncode == 0 and (ROOT / history_rel).read_bytes() == before.stdout, f"historical evidence changed: {history_rel}")

    _require(registry["public_contracts"] == {
        "request": "unified_market_evidence_request.v3",
        "result": "unified_market_evidence_result.v3",
        "audit": "unified_market_evidence_audit_package.v3",
        "mcp_tool_count": 6,
        "mcp_tools": ["market_describe_capabilities", "market_validate_request", "market_preview_request", "market_read_result", "market_export_ai_handoff", "market_fetch_evidence"],
    }, "J1 public contract/MCP authority changed")
    _require(registry["live_authorization"] == "NOT_GRANTED" and registry["real_agent_authorization"] == "NOT_GRANTED", "J2 may not grant live or real-agent authority")
    _require(registry["phase_j_entry_state"]["current"] == "STARTED" and registry["entry_disposition"]["J-B03"] == "CLOSED" and registry["entry_disposition"]["J-B04"] == "CLOSED / CLEARED", "Phase J/J-B state changed")
    _require(baseline["coverage_dimensions"] == LAYERS, "accepted nine-layer model changed")
    _require(baseline["coverage_statuses"] == list(baseline["coverage_statuses"]) and set(baseline["coverage_statuses"]) == STATUSES, "J1 coverage vocabulary changed")
    _require(delta["schema_version"] == "phase_j_j2_coverage_delta.v1", "coverage delta schema mismatch")
    _require(delta["authority_status"] == "J2_FROZEN_ACCEPTANCE_CANDIDATE", "delta must remain a candidate")
    authority = delta["baseline_authority"]
    _require(authority == {
        "registry_path": REGISTRY_REL, "registry_sha256": REGISTRY_SHA,
        "matrix_path": MATRIX_REL, "matrix_sha256": MATRIX_SHA,
        "j1_independent_review_id": REVIEW, "starting_head": START,
        "starting_tree": START_TREE, "origin_main": MAIN,
        "owner_authorization_sha256": AUTH,
    }, "J2 baseline/authorization binding mismatch")
    _require(delta["target_scenario_ids"] == TARGETS, "J2 target set/order mismatch")
    _require(delta["authorization"] == {"bounded_live": "NOT_GRANTED", "real_agent": "NOT_GRANTED"}, "J2 authorization state changed")
    _require(delta["network_activity"] == {"market_get": 0, "market_head": 0, "market_post": 0, "browser": 0, "firecrawl": 0, "security_master_acquisition": 0, "security_master_mutation": 0}, "network/security-master activity not zero")

    base_rows = {row["scenario_id"]: row for row in baseline["scenarios"]}
    registry_rows = {row["scenario_id"]: row for row in registry["scenarios"]}
    _require(list(base_rows) == [row["scenario_id"] for row in registry["scenarios"]], "accepted registry/matrix scenario IDs differ")
    _require(set(TARGETS) <= set(base_rows), "J2 target absent from accepted registry/matrix")
    rebuilt = copy.deepcopy(baseline)
    rebuilt["authority_status"] = "J2_EFFECTIVE_COVERAGE_MATRIX_CANDIDATE"
    rebuilt["derivation"] = {
        "baseline_matrix_path": MATRIX_REL, "baseline_matrix_sha256": MATRIX_SHA,
        "delta_path": DELTA_REL, "delta_sha256": _sha(delta_path),
        "j1_independent_review_id": REVIEW, "introduced_by_tranche": "PHASE_J_J2",
    }
    rebuilt_rows = {row["scenario_id"]: row for row in rebuilt["scenarios"]}
    promotions = delta["promotions"]
    _require(promotions, "J2 delta contains no coverage promotion")
    seen: set[tuple[str, str]] = set()
    for promotion in promotions:
        sid, layer = promotion.get("scenario_id"), promotion.get("layer")
        _require(sid in TARGETS and layer in LAYERS, "promotion outside J2 target/layer set")
        key = (sid, layer)
        _require(key not in seen, f"duplicate promotion {sid}/{layer}")
        seen.add(key)
        _require(promotion.get("baseline_status") == "PLANNED" and promotion.get("new_status") == "COVERED_EXISTING", f"invalid promotion status: {sid}/{layer}")
        _require(promotion.get("introduced_by_tranche") == "PHASE_J_J2" and promotion.get("scenario_match"), f"promotion provenance/match missing: {sid}/{layer}")
        _require(layer not in {"bounded_live", "real_agent"}, "J2 may not promote live or real-agent layers")
        expected_kind = EVIDENCE_KIND_BY_LAYER.get(layer)
        _require(expected_kind is not None, f"J2 layer is not promotable here: {layer}")
        cell = rebuilt_rows[sid]["layers"][layer]
        _require(cell["status"] == promotion["baseline_status"], f"promotion baseline status drift: {sid}/{layer}")
        refs = promotion.get("evidence_refs")
        _require(isinstance(refs, list) and len(refs) == 1, f"promotion requires exact typed evidence: {sid}/{layer}")
        for ref in refs:
            path, node = ref.get("ref"), ref.get("test_node_id")
            _require(ref.get("kind") == expected_kind, f"layer/evidence type mismatch: {sid}/{layer}")
            _require(isinstance(path, str) and (ROOT / path).is_file(), f"evidence ref missing: {sid}/{layer}")
            _require(isinstance(node, str) and node.startswith(path + "::") and ref.get("scenario_match") == promotion["scenario_match"], f"scenario-specific test node/evidence match missing: {sid}/{layer}")
        cell["status"] = promotion["new_status"]
        cell["evidence_refs"] = copy.deepcopy(refs)
        cell["introduced_by_tranche"] = "PHASE_J_J2"
    _require(effective == rebuilt, "effective matrix is not mechanically baseline + validated delta")

    ledger_rows = {row["scenario_id"]: row for row in ledger["scenarios"]}
    _require(ledger["target_scenario_ids"] == TARGETS and len(ledger_rows) == 17 and set(ledger_rows) == set(TARGETS), "J2 execution ledger must adjudicate exactly all 17 target scenarios")
    _require(ledger["scenario_adjudication_count"] == 17, "J2 scenario adjudication count mismatch")
    _require(ledger["baseline_authority"] == authority, "ledger authority differs from delta")
    _require(ledger["terminal_disposition"] == "PHASE_J_J2_HARD_BLOCK_EXISTING_SURFACE_GAP", "surface gaps must remain terminal hard block")
    for sid, row in ledger_rows.items():
        _require(row["scenario_id"] == sid and row["test_node_ids"], f"{sid}: no exact acceptance/oracle node")
        _require(row["fixture_input_refs"] == ["tests/fixtures/phase_j/j0_j1_semantic_fixtures.json"], f"{sid}: synthetic fixture provenance missing")
        _require(row["network_dispatch_count"] == 0 and row["additional_execution_count"] == 0, f"{sid}: unexpected network or follow-on execution")
        _require(set(row["semantic_assertions_checked"]) and set(row["forbidden_claims_checked"]), f"{sid}: semantic/forbidden-claim adjudication incomplete")
        _require(row["execution_classification"] in {"FIXTURE_BACKED_PRODUCTION_PATH", "PREEXECUTION_FAIL_CLOSED", "STORED_RESULT_PROJECTION", "EXISTING_SURFACE_GAP"}, f"{sid}: unknown classification")
        _require(set(row["layers_passed"]) <= set(row["layers_attempted"]) | {"integration", "fresh_install"}, f"{sid}: passed layer absent from attempted/evidence-backed layers")
        _require({item["layer"] for item in row["layers_blocked"]} <= set(LAYERS), f"{sid}: invalid blocked layer")
        _require(row["layers_passed"] or row["layers_blocked"], f"{sid}: no execution/gap adjudication")
    for promotion in promotions:
        row = ledger_rows[promotion["scenario_id"]]
        _require(promotion["layer"] in row["layers_passed"], f"promotion lacks passing scenario execution: {promotion['scenario_id']}/{promotion['layer']}")

    for row in base_rows.values():
        sid = row["scenario_id"]
        _require(effective_rows_cell(effective, sid, "bounded_live") == row["layers"]["bounded_live"], f"{sid}: bounded-live changed")
        _require(effective_rows_cell(effective, sid, "real_agent") == row["layers"]["real_agent"], f"{sid}: real-agent changed")
    _require(ledger["network_activity"] == delta["network_activity"], "network ledger mismatch")
    _require(ledger["product_boundary"] == {"production_runtime_changes": 0, "public_schema_changes": 0, "new_routes": 0, "new_capabilities": 0, "mcp_tool_count": 6, "security_master_mutation": 0}, "product boundary changed")
    _require(ledger["authorization"] == {"bounded_live": "NOT_GRANTED", "real_agent": "NOT_GRANTED", "phase_k": "NOT_STARTED"}, "J2 authorization/Phase K state changed")
    _require(ledger["execution_summary"]["existing_surface_gap"] > 0, "J2 must not claim PASS while required surfaces remain uncovered")
    return {
        "status": "PASS",
        "terminal_disposition": ledger["terminal_disposition"],
        "scenario_adjudications": len(ledger_rows),
        "coverage_promotions": len(promotions),
        "baseline_status_counts": _status_counts(baseline),
        "effective_status_counts": _status_counts(effective),
        "existing_surface_gaps": ledger["execution_summary"]["existing_surface_gap"],
        "network_activity": ledger["network_activity"],
    }


def effective_rows_cell(matrix: dict[str, Any], scenario_id: str, layer: str) -> dict[str, Any]:
    return next(row for row in matrix["scenarios"] if row["scenario_id"] == scenario_id)["layers"][layer]


if __name__ == "__main__":
    try:
        print(json.dumps(_validate(), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        raise SystemExit(1)
