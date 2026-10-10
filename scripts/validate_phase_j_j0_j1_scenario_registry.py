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
REGISTRY = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json"
MATRIX = ROOT / "docs/governance/phase_j/PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json"
PREFLIGHT = ROOT / "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json"
ROADMAP = ROOT / "ROADMAP.md"
HISTORICAL = [
    "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.json",
    "docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.md",
    "docs/governance/phase_j/PHASE_J_J_B03_C0_CLOSURE_AND_READINESS_RECONCILIATION_2026-10-07.json",
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


def _validate() -> dict[str, Any]:
    registry = _strict_json(REGISTRY)
    matrix = _strict_json(MATRIX)
    preflight = _strict_json(PREFLIGHT)
    _require(registry.get("schema_version") == "phase_j_governed_scenario_registry.v1", "registry schema version mismatch")
    _require(matrix.get("schema_version") == "phase_j_coverage_matrix.v1", "coverage matrix schema version mismatch")
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
            "title", "roadmap_required", "purpose", "product_relevance_class", "market_scope",
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
        if sid in {"J1-11", "J1-12"}:
            _require(any(ref.get("review_id") == "5479527453" for ref in row.get("superseding_authority_refs", [])), f"{sid}: J-B03 superseding authority missing")
        if sid in {"J1-13", "J1-14", "J1-15", "J1-16"}:
            _require(any(ref.get("review_id") == "5479527453" for ref in row.get("superseding_authority_refs", [])), f"{sid}: J-B04 superseding authority missing")
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
            _require(_local_ref_exists(ref), f"{baseline.get('layer')}: baseline evidence missing: {ref}")
    for row in matrix_rows:
        sid = row["scenario_id"]
        _require(set(row.get("layers", {})) == LAYERS, f"{sid}: incomplete coverage dimensions")
        for layer, cell in row["layers"].items():
            status = cell.get("status")
            refs = cell.get("evidence_refs")
            _require(status in STATUSES, f"{sid}/{layer}: invalid coverage status")
            _require(isinstance(refs, list), f"{sid}/{layer}: evidence_refs must be an array")
            if status != "PLANNED":
                _require(bool(refs), f"{sid}/{layer}: covered/nonplanned cell lacks evidence")
            for ref in refs:
                _require(_external_ref(ref) or _local_ref_exists(ref), f"{sid}/{layer}: evidence reference is not resolvable: {ref}")
            if status == "REQUIRES_LIVE_AUTH":
                _require(layer == "bounded_live", f"{sid}: live-auth status appears outside bounded_live")
            if status == "REQUIRES_REAL_AGENT_AUTH":
                _require(layer == "real_agent", f"{sid}: real-agent status appears outside real_agent")
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

    # Frozen historical evidence must remain byte-identical to the authorized base.
    result = subprocess.run(["git", "diff", "--quiet", BASE, "--", *HISTORICAL], cwd=ROOT, check=False)
    _require(result.returncode == 0, "historical readiness/A6 evidence changed from authorized base")
    return {
        "status": "PASS",
        "scenario_count": len(scenarios),
        "roadmap_required_count": sum(row["roadmap_required"] is True for row in scenarios),
        "product_relevance_counts": dict(Counter(row["product_relevance_class"] for row in scenarios)),
        "coverage_status_counts": dict(counts),
        "per_layer_status_counts": {key: dict(value) for key, value in layer_statuses.items()},
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
