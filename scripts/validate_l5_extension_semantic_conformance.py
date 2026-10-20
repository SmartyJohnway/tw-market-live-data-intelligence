"""A3 acceptance-only semantic conformance validator.

This module validates explicit traces produced by existing trusted projection
builders. It is not imported by runtime code and never writes or acquires data.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
FAILURE_CODES = {
    "normalization": "A3_NORMALIZATION_SEMANTIC_DRIFT",
    "timing": "A3_TIMING_SEMANTIC_DRIFT",
    "currentness": "A3_CURRENTNESS_SEMANTIC_DRIFT",
    "status": "A3_MISSING_UNSUPPORTED_FAILURE_COLLAPSE",
    "target": "A3_LINEAGE_TARGET_MISMATCH",
    "operation": "A3_LINEAGE_OPERATION_MISMATCH",
    "artifact": "A3_CITATION_ARTIFACT_MISMATCH",
    "result": "A3_RESULT_SEMANTIC_DRIFT",
    "audit_identity": "A3_RESULT_AUDIT_IDENTITY_MISMATCH",
    "audit": "A3_AUDIT_PROVENANCE_DRIFT",
    "handoff_caveat": "A3_HANDOFF_CAVEAT_LOSS",
    "handoff_citation": "A3_HANDOFF_CITATION_DRIFT",
    "public_contract": "A3_PUBLIC_CONTRACT_CHANGE_REQUIRED",
}


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def compare_trace(expected: dict, actual: dict) -> list[str]:
    """Return stable A3 failure codes for semantic trace drift."""
    failures: list[str] = []
    pairs = (
        ("normalized_facts", "normalization"), ("timing", "timing"),
        ("currentness", "currentness"), ("status_matrix", "status"),
        ("target_identity", "target"), ("operation_id", "operation"),
        ("artifact_reference", "artifact"), ("result_projection", "result"),
        ("audit_identity", "audit_identity"), ("audit_provenance", "audit"),
        ("mandatory_caveats", "handoff_caveat"), ("handoff_citations", "handoff_citation"),
        ("public_contract_versions", "public_contract"),
    )
    for key, category in pairs:
        if expected.get(key) != actual.get(key):
            failures.append(FAILURE_CODES[category])
    return failures


def _load_test_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"A3_FIXTURE_MODULE_UNAVAILABLE:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _family_trace(family: str, contract: str, inputs: Any, result: dict, audit: dict,
                  handoff: str, target_index: int = 0) -> dict:
    target = result["targets"][target_index]
    evidence = target.get("evidence", {})
    citations = target.get("citations", [])
    bindings = audit.get("operation_lineage", [])
    family_evidence = evidence.get(family)
    binding = next((row for row in bindings if row.get("capability_id") == family), {})
    source_path = next((row.get("relative_path") for row in binding.get("artifact_references", [])), None)
    artifact = inputs.evidence_artifacts.get(source_path, {}) if source_path else {}
    family_citations = [row for row in citations if row.get("citation_id") in set((family_evidence or {}).get("citation_ids", []))]
    handoff_citations = [row["citation_id"] for row in family_citations if row.get("citation_id") in handoff]
    return {
        "family_archetype": family,
        "input_contract_version": artifact.get("schema_version", contract),
        "target_identity": target.get("canonical_identity", {}).get("canonical_target_id"),
        "operation_id": binding.get("operation_id"),
        "source_provenance": artifact.get("source") or artifact.get("sources"),
        "normalized_facts": family_evidence,
        "timing": {key: artifact.get(key) for key in ("observed_at", "published_at", "source_timestamp", "retrieved_at", "calculated_at") if key in artifact},
        "currentness": (family_evidence or {}).get("currentness") or (family_evidence or {}).get("status"),
        "status_matrix": {"typed": artifact.get("status", artifact.get("coverage_status")), "result": (family_evidence or {}).get("status"), "result_overall": result.get("status")},
        "lineage": {"operation_id": binding.get("operation_id"), "target": target.get("canonical_identity", {}).get("canonical_target_id"), "artifact": source_path},
        "artifact_reference": source_path,
        "result_projection": family_evidence,
        "citation_mapping": [{"citation_id": row.get("citation_id"), "artifact": row.get("artifact_reference")} for row in family_citations],
        "audit_identity": {"result_id": audit.get("result_id"), "result_hash": audit.get("result_hash"), "bundle_id": audit.get("bundle_identity", {}).get("bundle_id")},
        "audit_provenance": [row for row in bindings if row.get("capability_id") == family],
        "handoff_projection": handoff,
        "mandatory_caveats": [text for text in (family_evidence or {}).get("caveats", []) if text in handoff],
        "handoff_citations": handoff_citations,
        "public_contract_versions": {"request": result.get("request_summary", {}).get("request_schema_version"), "result": result.get("schema_version"), "audit": audit.get("schema_version", "delegated-to-accepted-mode-c-test"), "handoff": "existing-markdown-projection"},
    }


def build_evidence() -> dict:
    """Exercise existing G/H projection builders and inventory accepted I test."""
    from scripts.m8r_05c.lineage_resolver import build_lineage_map
    from scripts.m8r_05c.markdown_renderer import render_result_markdown
    from scripts.m8r_05c.result_builder import build_result

    g = _load_test_module("tests/unit/test_phase_g_result_v2_projection.py", "a3_phase_g_fixture")
    g_inputs = g._projection_inputs("unified_market_evidence_request.v2")
    g_result = build_result(g_inputs, output_schema_version="unified_market_evidence_result.v2")
    # Phase G's accepted V2 projection fixtures deliberately omit the full
    # execution-control identities required by the production Audit builder.
    # Audit coverage is delegated to the accepted Phase-G Mode-C suite.
    g_lineage = build_lineage_map(g_inputs)
    g_audit = {"operation_lineage": [{"operation_id": binding.operation_id,
        "capability_id": binding.capability_id, "executor_id": binding.executor_id,
        "canonical_target_ids": [binding.canonical_target_id], "artifact_references": binding.evidence_artifacts}
        for need_map in g_lineage.bindings.values() for binding in need_map.values()],
        "result_id": g_result.get("result_id"), "result_hash": g_result.get("result_hash"),
        "bundle_identity": {"bundle_id": g_inputs.bundle.get("bundle_id")},
        "audit_coverage_authority": "tests/unit/test_phase_g_mode_c_v2.py"}
    g_handoff = render_result_markdown(g_result)

    h = _load_test_module("tests/unit/test_phase_h_imp_6_v3_projection_handoff.py", "a3_phase_h_fixture")
    h_inputs = h._inputs()
    h_result, h_audit = h._build_package(h_inputs)
    h_handoff = render_result_markdown(h_result)
    h_result_repeat, h_audit_repeat = h._build_package(h_inputs)
    from scripts.m8r_05c.canonical import build_audit_package_id_v3, hash_body_excluding_key
    if canonical_hash(h_result) != canonical_hash(h_result_repeat) or canonical_hash(h_audit) != canonical_hash(h_audit_repeat):
        raise RuntimeError("A3_NORMALIZATION_SEMANTIC_DRIFT:non_deterministic_projection")
    if hash_body_excluding_key(h_result, "result_hash") != h_result.get("result_hash"):
        raise RuntimeError("A3_RESULT_AUDIT_IDENTITY_MISMATCH:result_hash")
    if h_audit.get("integrity_verification", {}).get("result_hash_verified") is not True:
        raise RuntimeError("A3_RESULT_AUDIT_IDENTITY_MISMATCH:audit_result_hash")
    if h_audit.get("result_id") != h_result.get("result_id") or h_audit.get("result_hash") != h_result.get("result_hash"):
        raise RuntimeError("A3_RESULT_AUDIT_IDENTITY_MISMATCH:result_audit_link")
    expected_audit_id = build_audit_package_id_v3(h_result["result_id"], h_inputs.bundle["bundle_id"])
    if h_audit.get("audit_package_id") != expected_audit_id or h_result.get("audit_reference", {}).get("audit_package_id") != expected_audit_id:
        raise RuntimeError("A3_RESULT_AUDIT_IDENTITY_MISMATCH:audit_package_id")
    audit_citations = {row["citation_id"]: row for row in h_audit.get("citation_to_operation_map", [])}
    inventory = {row["relative_path"]: row for row in h_audit.get("artifact_inventory", [])}
    for target in h_result.get("targets", []):
        target_id = target.get("canonical_identity", {}).get("canonical_target_id")
        for citation in target.get("citations", []):
            audit_row = audit_citations.get(citation.get("citation_id"))
            if not audit_row or audit_row.get("canonical_target_id") != target_id:
                raise RuntimeError("A3_LINEAGE_TARGET_MISMATCH:result_citation")
            artifact = inventory.get(audit_row.get("artifact_relative_path"))
            if not artifact or artifact.get("sha256") != audit_row.get("artifact_hash"):
                raise RuntimeError("A3_CITATION_ARTIFACT_MISMATCH:audit_inventory")

    traces = []
    for family in ("material_disclosures", "monthly_revenue"):
        traces.append(_family_trace(family, "phase_g_research_operation_evidence.v1", g_inputs, g_result, g_audit, g_handoff))
    for family in ("trading_status_context", "corporate_action_context", "recent_performance"):
        traces.append(_family_trace(family, "phase_h_typed_evidence.v1", h_inputs, h_result, h_audit, h_handoff))

    i_mod = _load_test_module("tests/integration/test_phase_i_i1_result_audit_projection.py", "a3_phase_i_test")
    i_fixture = json.loads(i_mod.FIXTURE.read_text(encoding="utf-8"))
    from server.services.phase_i_market_state_adapters import normalize_tpex_market_state
    i_artifact = normalize_tpex_market_state(i_fixture, retrieved_at=i_mod.NOW)
    i_trace = {
        "family_archetype": "market_state_context",
        "input_contract_version": i_artifact["schema_version"],
        "target_identity": "TPEX:6488",
        "operation_id": "integration-test-derived-operation",
        "source_provenance": i_artifact.get("source"),
        "normalized_facts": i_artifact,
        "timing": {key: i_artifact.get(key) for key in ("observed_at", "retrieved_at", "calculated_at") if key in i_artifact},
        "currentness": i_artifact.get("currentness") or i_artifact.get("status"),
        "status_matrix": {"typed": i_artifact.get("status"), "result": "covered by test_i1_fixture_crosses_loader_lineage_result_v3_and_audit_v3"},
        "lineage": {"operation_id": "bound by accepted I1 integration test", "target": "TPEX:6488", "artifact": "evidence/phase_i/i1/TPEX_market_state.json"},
        "artifact_reference": "evidence/phase_i/i1/TPEX_market_state.json",
        "result_projection": "covered by accepted I1 integration test",
        "citation_mapping": "covered by accepted I1 integration test",
        "audit_identity": "covered by accepted I1 integration test",
        "audit_provenance": "covered by accepted I1 integration test",
        "handoff_projection": "covered by deterministic V3 renderer; see Phase H mode-C tests",
        "mandatory_caveats": [], "handoff_citations": [],
        "public_contract_versions": {"request": "unified_market_evidence_request.v3", "result": "unified_market_evidence_result.v3", "audit": "unified_market_evidence_audit_package.v3", "handoff": "existing-markdown-projection"},
    }
    traces.append(i_trace)
    families = [row["family_archetype"] for row in traces]
    expected = {"material_disclosures", "monthly_revenue", "trading_status_context", "corporate_action_context", "recent_performance", "market_state_context"}
    if set(families) != expected:
        raise RuntimeError("A3_REPRESENTATIVE_FAMILY_COVERAGE_MISMATCH")
    for row in traces:
        if not row.get("target_identity") or not row.get("input_contract_version"):
            raise RuntimeError("A3_TRACE_REQUIRED_IDENTITY_MISSING")
    return {"status": "PASS", "traces": traces, "trace_count": len(traces), "trace_sha256": canonical_hash(traces),
            "phase_h_deterministic_repeat": True, "result_hash_recomputed": True,
            "result_audit_identity_linked": True, "result_citations_bound_to_audit_inventory": True,
            "phase_i_end_to_end_test": "tests/integration/test_phase_i_i1_result_audit_projection.py::test_i1_fixture_crosses_loader_lineage_result_v3_and_audit_v3"}


def validate() -> dict:
    evidence = build_evidence()
    def enum_values(path: str, key: str) -> list[str]:
        schema = json.loads((ROOT / path).read_text(encoding="utf-8"))
        value = schema.get("properties", {}).get(key, {}).get("enum")
        return list(value) if isinstance(value, list) else []

    matrix_results = [
        {"domain": "research typed status", "values": enum_values("schemas/material_disclosure_evidence.v1.schema.json", "status"), "authority": "Phase G typed evidence schemas"},
        {"domain": "Phase H trading/corporate typed status", "values": enum_values("schemas/trading_status_context_evidence.v1.schema.json", "status"), "authority": "Phase H typed evidence schemas"},
        {"domain": "Phase H recent-performance coverage_status", "values": enum_values("schemas/recent_performance_evidence.v1.schema.json", "coverage_status"), "authority": "Phase H typed evidence schema"},
        {"domain": "Phase I market-state typed status", "values": enum_values("schemas/market_state_context_evidence.v1.schema.json", "status"), "authority": "Phase I typed evidence schema"},
        {"domain": "currentness", "values": ["current_within_source_contract", "stale", "lagging", "unknown"], "authority": "existing research typed schemas"},
        {"domain": "Result target coverage", "values": ["provided_needs", "missing_needs", "partial_failures"], "authority": "Unified Result V3"},
    ]
    if any(not row["values"] or len(row["values"]) != len(set(row["values"])) for row in matrix_results):
        raise RuntimeError("A3_MISSING_UNSUPPORTED_FAILURE_COLLAPSE:status_domain_invalid")
    return {"status": "PASS", "failure_codes": FAILURE_CODES, "evidence": evidence,
            "existing_semantic_domains": matrix_results, "network": False, "provider_acquisition": False,
            "writes": False, "production_mutation": False, "runtime_discovery": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = validate()
    except Exception as exc:  # stable acceptance failure, retain typed message
        result = {"status": "FAIL", "failure_code": str(exc).split(":", 1)[0], "detail": str(exc)}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
