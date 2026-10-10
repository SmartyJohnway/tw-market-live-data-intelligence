#!/usr/bin/env python3
"""Network-free integrity checks for the Phase J J0/J1 registry and matrix."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = "2455fd0875bc09d6bc5926a6267351aadb38beb1"
R1_START = "26cbe87dc73aab1fdff15bdad9efb828e0b9ca57"
R1_START_TREE = "0f08c5cc7478b904fa3084c17373a2c5224c0a24"
REGISTRY = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json"
MATRIX = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json"
PREFLIGHT = ROOT / "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json"
ROADMAP = ROOT / "ROADMAP.md"
HISTORICAL = [
    "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json",
    "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.md",
    "docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.json",
    "docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.md",
    "docs/governance/phase_j/PHASE_J_J_B03_A2_6_REPRESENTATIVE_INTEGRATED_ACCEPTANCE_AND_ACTIVATION_DECISION_2026-10-07.json",
    "docs/governance/phase_j/PHASE_J_J0_START_AND_J1_ACCEPTANCE_ARCHITECTURE_2026-10-11.json",
    "docs/governance/phase_j/PHASE_J_J0_START_AND_J1_ACCEPTANCE_ARCHITECTURE_2026-10-11.md",
    "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json",
    "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.md",
    "docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json",
    "docs/governance/phase_j/PHASE_J_J_B04_A6_INTEGRATED_MARKET_RESEARCH_INTERPRETATION_LIVE_ACCEPTANCE_2026-10-10.json",
    "docs/governance/phase_j/PHASE_J_J_B04_A6_INTEGRATED_MARKET_RESEARCH_INTERPRETATION_LIVE_ACCEPTANCE_2026-10-10.md",
    "docs/governance/phase_j/PHASE_J_J_B04_A6_R1_H3_STOCK_DAY_CLOSE_NUMERIC_CONTRACT_REPAIR_2026-10-10.json",
    "docs/governance/phase_j/PHASE_J_J_B04_A6_R1_H3_STOCK_DAY_CLOSE_NUMERIC_CONTRACT_REPAIR_2026-10-10.md",
]
RELEVANCE = {
    "MUST_HAVE_FOR_CONVERSATIONAL_J",
    "ACCEPTANCE_HARNESS_ONLY",
    "OPTIONAL_EVIDENCE_NOT_J_BLOCKING",
    "SAFE_FAIL_CLOSED_IS_SUFFICIENT",
}
LAYERS = {
    "contract_fixture", "deterministic_unit", "integration", "service_api",
    "workbench", "mcp", "fresh_install", "bounded_live", "real_agent",
}
STATUSES = {
    "COVERED_EXISTING", "COVERED_J0_J1", "PLANNED", "REQUIRES_LIVE_AUTH",
    "REQUIRES_REAL_AGENT_AUTH", "EXPECTED_FAIL_CLOSED", "NOT_APPLICABLE", "BLOCKED",
}
ROADMAP_SCENARIOS = [
    "normal TWSE", "normal TPEx", "multi-target", "current market evidence",
    "official EOD", "material disclosure", "no material disclosure", "corrected disclosure",
    "monthly revenue", "financial statements", "attention / disposition", "suspend / resume",
    "ex-dividend", "ex-right", "capital reduction", "reference-price discontinuity",
    "5D / 20D baseline", "TAIFEX context", "timing mismatch", "partial success", "stale",
    "missing", "source failure", "identity ambiguity", "unsupported identity",
    "authorization refusal", "resource bound",
]
EXPECTED_MCP = [
    "market_describe_capabilities", "market_validate_request", "market_preview_request",
    "market_read_result", "market_export_ai_handoff", "market_fetch_evidence",
]
EVIDENCE_KINDS = {
    "contract_authority", "fixture", "unit_test", "integration_test", "e2e_acceptance",
    "historical_live_acceptance", "service_test", "workbench_test", "mcp_test",
    "fresh_install_test", "real_agent_acceptance", "routing_authority", "governance_closure",
    "governance_review",
}
CURRENT_CAPABILITY_STATES = {
    "SUPPORTED_BOUNDED": "bounded",
    "SUPPORTED_LATEST_SCOPE": "bounded_latest_scope",
    "SAFE_FAIL_CLOSED": "safe_fail_closed",
    "UNRESOLVED_FAIL_CLOSED": "unresolved",
    "UNSUPPORTED_FAIL_CLOSED": "unsupported",
    "REPRESENTATIVE_SCOPE_ACCEPTED_PARTIAL": "partial",
    "UNSUPPORTED_FAMILIES_EXPLICIT": "unsupported",
    "H2_SUBTYPE_UNSUPPORTED_FAIL_CLOSED": "unsupported_subtype",
    "SUPPORTED_SAFETY_FAIL_CLOSED": "bounded_with_interpretation_guard",
    "OPTIONAL_EXPLICIT_CONTEXT": "optional",
    "SUPPORTED_TYPED_TIMING": "typed_semantics",
    "SUPPORTED_TYPED_PARTIAL": "typed_semantics",
    "SUPPORTED_TYPED_STALE": "typed_semantics",
    "SUPPORTED_TYPED_MISSING": "typed_semantics",
    "SUPPORTED_FAIL_CLOSED": "fail_closed",
    "SUPPORTED_GOVERNED_REFUSAL": "governed_refusal",
}
LAYER_EVIDENCE_KINDS = {
    "contract_fixture": {"fixture", "unit_test"},
    "deterministic_unit": {"unit_test"},
    "integration": {"integration_test", "e2e_acceptance", "historical_live_acceptance"},
    "service_api": {"service_test", "integration_test", "e2e_acceptance"},
    "workbench": {"workbench_test", "integration_test", "e2e_acceptance"},
    "mcp": {"mcp_test", "integration_test"},
    "fresh_install": {"fresh_install_test"},
    "bounded_live": {"historical_live_acceptance"},
    "real_agent": {"real_agent_acceptance"},
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _strict_json(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate JSON key {key!r} in {path}")
            out[key] = value
        return out

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def _external_ref(ref: str) -> bool:
    return ref.startswith("GitHub PR #326 review ")


def _local_ref_exists(ref: str) -> bool:
    return (ROOT / ref.split("#", 1)[0]).is_file()


def _validate_current_semantics(row: dict[str, Any]) -> None:
    sid = row["scenario_id"]
    status = row["current_readiness_status"]
    state = row.get("current_semantic_state", {})
    _require(row.get("current_purpose") == row.get("purpose"), f"{sid}: purpose must state current semantics")
    _require(bool(row.get("historical_readiness_summary")), f"{sid}: historical readiness summary missing")
    _require(row.get("historical_readiness_source") == str(PREFLIGHT.relative_to(ROOT)), f"{sid}: historical source mismatch")
    _require(state.get("readiness_status") == status, f"{sid}: structured/current readiness status mismatch")
    _require(state.get("capability_state") == CURRENT_CAPABILITY_STATES.get(status), f"{sid}: current capability state contradicts readiness")
    _require(state.get("complete_family_support_claimed") is False, f"{sid}: unqualified complete-family claim")
    _require(isinstance(state.get("accepted_routes"), list), f"{sid}: accepted routes must be explicit")
    _require(isinstance(state.get("uncovered_families"), list), f"{sid}: uncovered families must be explicit")
    coverage = row.get("coverage_expectation", {})
    _require(coverage.get("complete_family_claimed") is not True, f"{sid}: coverage claims unsupported full-family support")
    if sid == "J1-11":
        _require(state["capability_state"] == "partial" and bool(state["accepted_routes"]), "J1-11: representative accepted scope must remain partial")
        _require("phase_h_h1_tpex_composite_executor" in state["accepted_routes"], "J1-11: accepted H1 composite route missing")
        _require(set(state["uncovered_families"]) >= {"suspension", "resumption", "changed_trading_method"}, "J1-11: uncovered H1 families missing")
    if sid == "J1-12":
        _require(state["capability_state"] == "unsupported" and not state["accepted_routes"], "J1-12: suspension/resumption must remain unsupported")
    if sid in {"J1-13", "J1-15"}:
        _require(state["capability_state"] == "unsupported_subtype" and not state["accepted_routes"], f"{sid}: unsupported subtype cannot claim an accepted route")
    if sid == "J1-14":
        _require(state["capability_state"] == "bounded", "J1-14: accepted bounded route is not represented")
        _require("phase_h_h2_twse_exright_pre_executor" in state["accepted_routes"], "J1-14: exact accepted H2 route missing")
        _require(row.get("corporate_action_expectation", {}).get("accepted_route") == "phase_h_h2_twse_exright_pre_executor / TWSE TWT48U_ALL only", "J1-14: accepted route scope broadened")
    if sid == "J1-16":
        _require(state["capability_state"] == "bounded_with_interpretation_guard", "J1-16: bounded safety scope missing")
        _require(row.get("interpretation_guard_expectation", {}).get("ordinary_return_interpretation") == "blocked", "J1-16: ordinary-return guard must remain blocked")


def _validate_authority_roles(row: dict[str, Any]) -> None:
    sid = row["scenario_id"]
    refs = row.get("superseding_authority_refs", [])
    if sid in {"J1-11", "J1-12"}:
        b03 = [x for x in refs if x.get("ref") == "docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.json"]
        _require(len(b03) == 1 and b03[0].get("authority_kind") == "governance_record", f"{sid}: canonical J-B03 closure authority missing")
        _require("review_id" not in b03[0] and all(x.get("review_id") != "5479527453" for x in refs), f"{sid}: J-B04 review misbound to J-B03")
        closure = _strict_json(ROOT / b03[0]["ref"])
        _require(closure.get("gate") == "J-B03-C0" and closure.get("decision") == "J_B03_CLOSED_BOUNDED_CONVERSATIONAL_CORRECTNESS_SATISFIED", f"{sid}: referenced record is not J-B03 closure authority")
        accepted = closure.get("accepted_runtime_state", {})
        _require(accepted.get("selected_executor_id") == "phase_h_h1_tpex_composite_executor" and accepted.get("complete_h1_coverage_claimed") is False, f"{sid}: J-B03 current bounded scope does not match closure record")
    if sid in {"J1-13", "J1-14", "J1-15", "J1-16"}:
        b04 = [x for x in refs if x.get("ref") == "docs/governance/phase_j/PHASE_J_J_B04_A6_R2_TRANSPORT_LEDGER_VALIDATOR_REPAIR_AND_LIVE_REACCEPTANCE_2026-10-10.json"]
        _require(len(b04) == 1 and b04[0].get("authority_kind") == "governance_record", f"{sid}: canonical J-B04 authority missing")
        _require(b04[0].get("review_id") == "5479527453", f"{sid}: J-B04 closure review binding mismatch")


def _validate_coverage_cell(scenario_id: str, layer: str, cell: dict[str, Any]) -> None:
    status = cell.get("status")
    refs = cell.get("evidence_refs")
    _require(status in STATUSES, f"{scenario_id}/{layer}: invalid coverage status")
    _require(isinstance(refs, list), f"{scenario_id}/{layer}: evidence_refs must be an array")
    _require(all(isinstance(ref, dict) for ref in refs), f"{scenario_id}/{layer}: evidence references must be typed objects")
    if status != "PLANNED":
        _require(bool(refs), f"{scenario_id}/{layer}: covered/nonplanned cell lacks evidence")
    for ref in refs:
        path = ref.get("ref", "")
        kind = ref.get("kind")
        _require(path and kind in EVIDENCE_KINDS, f"{scenario_id}/{layer}: evidence kind/ref missing or unknown")
        _require(_external_ref(path) or _local_ref_exists(path), f"{scenario_id}/{layer}: evidence reference unresolved: {path}")
    if status in {"COVERED_EXISTING", "COVERED_J0_J1"}:
        allowed = LAYER_EVIDENCE_KINDS[layer]
        _require(any(ref["kind"] in allowed for ref in refs), f"{scenario_id}/{layer}: evidence kind does not prove this layer")
    if status == "COVERED_EXISTING" and layer == "integration":
        qualifying = [ref for ref in refs if ref["kind"] in LAYER_EVIDENCE_KINDS["integration"]]
        _require(bool(qualifying), f"{scenario_id}/integration: catalog/routing/unit evidence cannot qualify integration")
        _require(all(isinstance(ref.get("scenario_match"), str) and ref["scenario_match"].strip() for ref in qualifying), f"{scenario_id}/integration: scenario-level evidence match missing")
        for ref in qualifying:
            if ref["kind"] == "integration_test":
                _require(ref["ref"].startswith("tests/integration/"), f"{scenario_id}: integration evidence is not an integration test")
            elif ref["kind"] == "historical_live_acceptance":
                _require("LIVE_E2E" in ref["ref"] and _require_status_ok(ref["ref"]), f"{scenario_id}: historical live evidence is not accepted E2E")
            elif ref["kind"] == "e2e_acceptance":
                _require(_require_status_ok(ref["ref"]), f"{scenario_id}: E2E evidence is not accepted")
    if status == "COVERED_EXISTING" and layer == "bounded_live":
        live = [ref for ref in refs if ref["kind"] == "historical_live_acceptance" and ref.get("scenario_match")]
        _require(bool(live), f"{scenario_id}/bounded_live: exact accepted live evidence required")
        _require(any(_require_status_ok(ref["ref"]) for ref in live), f"{scenario_id}/bounded_live: historical live evidence is not accepted")
    if status in {"REQUIRES_LIVE_AUTH", "REQUIRES_REAL_AGENT_AUTH"}:
        _require((layer == "bounded_live") if status == "REQUIRES_LIVE_AUTH" else (layer == "real_agent"), f"{scenario_id}: authorization status appears in wrong layer")


def _require_status_ok(ref: str) -> bool:
    path = ROOT / ref
    if not path.is_file() or path.suffix != ".json":
        return False
    try:
        data = _strict_json(path)
    except (OSError, ValueError):
        return False
    return (
        data.get("status") in {"PASS", "OWNER_ACTIVATION_ACCEPTED"}
        or str(data.get("terminal_disposition", "")).endswith("PASS")
        or str(data.get("final_disposition", "")).endswith("ACCEPTED")
    )


def _validate() -> dict[str, Any]:
    registry = _strict_json(REGISTRY)
    matrix = _strict_json(MATRIX)
    preflight = _strict_json(PREFLIGHT)
    _require(registry.get("schema_version") == "phase_j_governed_scenario_registry.v1", "registry schema version mismatch")
    _require(matrix.get("schema_version") == "phase_j_coverage_matrix.v1", "coverage matrix schema version mismatch")
    _require(registry.get("authority_status") == "J1_R1_FROZEN_ACCEPTANCE_CANDIDATE", "registry must remain an R1 candidate pending independent review")
    _require(matrix.get("authority_status") == "J1_R1_FROZEN_ACCEPTANCE_CANDIDATE", "matrix must remain an R1 candidate pending independent review")
    _require(registry.get("phase_j_entry_state", {}).get("previous") == "NOT_STARTED", "previous Phase J state must remain historical NOT_STARTED")
    _require(registry.get("phase_j_entry_state", {}).get("current") == "STARTED", "Phase J must be marked STARTED")
    _require(registry.get("phase_j_entry_state", {}).get("entry_review_id") == "5479545125", "entry review binding mismatch")
    _require(registry.get("phase_j_entry_state", {}).get("j_b04_closure_review_id") == "5479527453", "J-B04 closure review binding mismatch")
    _require(registry.get("phase_j_entry_state", {}).get("start_authorization_sha256") == "46cb965043659cbc82eced142b3d7c12eef119b4942124513fabb6305e894198", "start authorization hash mismatch")
    _require(registry.get("entry_disposition") == {"J-B01": "NON_BLOCKING", "J-B02": "NON_BLOCKING", "J-B03": "CLOSED", "J-B04": "CLOSED / CLEARED"}, "current J-B disposition mismatch")
    public = registry.get("public_contracts", {})
    _require(public.get("request") == "unified_market_evidence_request.v3", "request contract drift")
    _require(public.get("result") == "unified_market_evidence_result.v3", "result contract drift")
    _require(public.get("audit") == "unified_market_evidence_audit_package.v3", "audit contract drift")
    _require(public.get("mcp_tool_count") == 6 and public.get("mcp_tools") == EXPECTED_MCP, "MCP must remain the exact six-tool surface")
    _require(registry.get("live_authorization") == "NOT_GRANTED", "bounded-live authority must remain ungranted")
    _require(registry.get("real_agent_authorization") == "NOT_GRANTED", "real-agent authority must remain ungranted")
    _require(registry.get("baseline_authority") == {
        "head": BASE,
        "tree": "1c42fd165bbbbd32249b9a43fc2b813182b31ca3",
        "origin_main": "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a",
        "branch": "phase-j/j-b04-a5-bounded-live-source-acceptance",
        "pr_326": "OPEN_DRAFT_UNMERGED",
    }, "baseline authority binding mismatch")
    _require(registry.get("product_constraints") == {
        "adds_product_capability": False,
        "production_runtime_changes": False,
        "public_contract_expansion": False,
        "new_source_or_route": False,
        "network_acquisition": False,
        "security_master_mutation": False,
        "real_agent_execution": False,
        "phase_k_started": False,
    }, "Phase J J0/J1 scope constraints mismatch")
    _require(registry.get("roadmap_requirement_inventory") == ROADMAP_SCENARIOS, "Roadmap J.1 requirement inventory drift")
    _require("# [ ] Phase J — Integrated Research Acceptance" in ROADMAP.read_text(encoding="utf-8"), "Roadmap Phase J checkbox was changed")

    expected_rows = preflight["golden_scenario_coverage_matrix"]
    expected_ids = [row["scenario_id"] for row in expected_rows]
    scenarios = registry.get("scenarios")
    _require(isinstance(scenarios, list), "registry scenarios must be an array")
    ids = [row.get("scenario_id") for row in scenarios]
    _require(len(ids) == len(set(ids)), "duplicate registry scenario ID")
    _require(ids == expected_ids, "registry must preserve every inherited J1 scenario ID and order")
    _require(registry.get("scenario_id_authority", {}).get("source") == "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json", "scenario identity authority mismatch")
    _require(registry.get("scenario_id_authority", {}).get("stable_ids_preserved") is True, "stable ID preservation is not asserted")

    for row, inherited in zip(scenarios, expected_rows):
        sid = row["scenario_id"]
        for key in [
            "title", "roadmap_required", "purpose", "current_purpose", "historical_readiness_summary",
            "current_semantic_state", "product_relevance_class", "market_scope",
            "target_class", "required_data_needs", "required_evidence_families", "identity_expectation",
            "source_expectation", "period_expectation", "timing_expectation", "currentness_expectation",
            "coverage_expectation", "missing_expectation", "partial_expectation",
            "corporate_action_expectation", "interpretation_guard_expectation", "authorization_expectation",
            "resource_bound_expectation", "citation_expectation", "lineage_expectation",
            "expected_semantic_assertions", "forbidden_claims", "accepted_fail_closed_outcomes",
            "network_profile", "authority_refs", "historical_readiness_source",
        ]:
            _require(key in row, f"{sid}: missing required field {key}")
        _require(row["title"] == inherited["scenario"], f"{sid}: inherited title changed")
        _require(row["roadmap_required"] is inherited["roadmap_required"], f"{sid}: Roadmap required flag changed")
        _require(row["product_relevance_class"] == inherited["product_relevance_class"], f"{sid}: product relevance classification changed")
        _require(row["historical_readiness_source"] == "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json", f"{sid}: historical preflight trace missing")
        _require(row["historical_readiness_summary"].get("preflight_reason") == inherited.get("reason"), f"{sid}: historical preflight meaning changed")
        _validate_current_semantics(row)
        _validate_authority_roles(row)
        _require(row["network_profile"] in registry["network_profiles"], f"{sid}: invalid network profile")
        _require(row["product_relevance_class"] in RELEVANCE, f"{sid}: unknown product relevance class")
        _require(row["expected_semantic_assertions"], f"{sid}: no golden semantic assertions")
        _require(row["forbidden_claims"], f"{sid}: no forbidden-claim assertions")
        _require(row["authority_refs"], f"{sid}: missing authority references")
        _require(row.get("live_authorization", {}).get("granted") is False, f"{sid}: live authorization was granted")
        _require(row.get("real_agent_authorization", {}).get("granted") is False, f"{sid}: real-agent authorization was granted")
        for auth in [row.get("live_authorization", {}), row.get("real_agent_authorization", {})]:
            _require(auth.get("status") in {"REQUIRED", "NOT_GRANTED_FOR_NEW_ACTIVITY"}, f"{sid}: authorization state is not explicit")
        _require(any(ref.startswith("ROADMAP.md J.1") for ref in row["roadmap_requirement_refs"]), f"{sid}: missing Roadmap trace")
        _require(row["roadmap_requirement_refs"] == [f"ROADMAP.md J.1 — {inherited['scenario']}"], f"{sid}: Roadmap requirement mapping mismatch")
        for ref in row["authority_refs"]:
            value = ref.get("ref", "")
            _require(value and (_external_ref(value) or _local_ref_exists(value)), f"{sid}: authority reference is not resolvable: {value}")

    matrix_rows = matrix.get("scenarios")
    _require(isinstance(matrix_rows, list), "coverage rows must be an array")
    matrix_ids = [row.get("scenario_id") for row in matrix_rows]
    _require(len(matrix_ids) == len(set(matrix_ids)), "duplicate matrix scenario ID")
    _require(set(matrix_ids) == set(ids), "registry/matrix scenario IDs differ")
    _require(set(matrix.get("coverage_dimensions", [])) == LAYERS, "coverage dimensions mismatch")
    _require(set(matrix.get("coverage_statuses", [])) == STATUSES, "coverage status enum mismatch")
    baselines = matrix.get("layer_baselines", [])
    _require({row.get("layer") for row in baselines} == {"service_api", "workbench", "mcp", "fresh_install", "integration"}, "existing cross-layer baseline inventory incomplete")
    for baseline in baselines:
        _require(baseline.get("status") == "COVERED_EXISTING" and baseline.get("semantics"), f"{baseline.get('layer')}: baseline semantics missing")
        for ref in baseline.get("evidence_refs", []):
            _require(isinstance(ref, dict) and ref.get("kind") in EVIDENCE_KINDS and _local_ref_exists(ref.get("ref", "")), f"{baseline.get('layer')}: typed baseline evidence missing")
            _require(bool(ref.get("scope_note")), f"{baseline.get('layer')}: baseline scope note missing")
    for row in matrix_rows:
        sid = row["scenario_id"]
        _require(set(row.get("layers", {})) == LAYERS, f"{sid}: incomplete coverage dimensions")
        for layer, cell in row["layers"].items():
            _validate_coverage_cell(sid, layer, cell)
    fixture_cases = _strict_json(ROOT / "tests/fixtures/phase_j/j0_j1_semantic_fixtures.json")
    fixture_ids = {fixture.get("scenario_id") for fixture in fixture_cases}
    for row in matrix_rows:
        sid = row["scenario_id"]
        for layer in ("contract_fixture", "deterministic_unit"):
            cell = row["layers"][layer]
            if cell["status"] == "COVERED_J0_J1":
                _require(sid in fixture_ids, f"{sid}/{layer}: marked covered but no acceptance fixture exists")
    _require(len(fixture_ids) == len(fixture_cases), "duplicate fixture scenario ID")

    counts = Counter(cell["status"] for row in matrix_rows for cell in row["layers"].values())
    layer_statuses = {layer: Counter(row["layers"][layer]["status"] for row in matrix_rows) for layer in sorted(LAYERS)}
    _require(Counter(row["product_relevance_class"] for row in scenarios) == Counter(preflight["scenario_product_relevance"].values()), "scenario relevance aggregate differs from preflight")
    expected_summary = {
        "scenario_count": len(matrix_rows),
        "cell_status_counts": dict(counts),
        "per_layer_status_counts": {layer: dict(values) for layer, values in layer_statuses.items()},
        "integration_status_counts": dict(Counter(row["layers"]["integration"]["status"] for row in matrix_rows)),
        "scenario_level_integration_claims": sum(row["layers"]["integration"]["status"] == "COVERED_EXISTING" for row in matrix_rows),
    }
    _require(matrix.get("coverage_summary") == expected_summary, "coverage aggregate summary is stale or inconsistent")

    # Frozen historical evidence must remain byte-identical to the authorized base.
    result = subprocess.run(["git", "diff", "--quiet", R1_START, "--", *HISTORICAL], cwd=ROOT, check=False)
    _require(result.returncode == 0, "historical readiness/A6 evidence changed from authorized base")
    return {
        "status": "PASS",
        "scenario_count": len(scenarios),
        "roadmap_required_count": sum(row["roadmap_required"] is True for row in scenarios),
        "product_relevance_counts": dict(Counter(row["product_relevance_class"] for row in scenarios)),
        "coverage_status_counts": dict(counts),
        "per_layer_status_counts": {key: dict(value) for key, value in layer_statuses.items()},
        "scenario_level_integration_claims": expected_summary["scenario_level_integration_claims"],
        "fixture_scenario_count": len(fixture_ids),
        "historical_immutability": "PASS",
        "phase_j_state": "STARTED",
        "mcp_tool_count": 6,
    }


def main() -> int:
    try:
        report = _validate()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
