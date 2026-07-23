"""Deterministic Commit-1 correction checks; no runner or network access."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_inventory_and_routing_semantics_are_reconciled():
    catalog = {x["capability_id"]: x for x in load("docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json")["data_need_capabilities"]}
    inventory = load("docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json")["surfaces"]
    surfaces = {x["surface_id"]: x for x in inventory}
    routes = load("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.json")["routes"]
    assert {r["capability_id"] for r in routes} == set(catalog)
    for route in routes:
        capability = catalog[route["capability_id"]]
        assert route["capability_requires_execution_approval"] is capability["requires_approval_for_execution"]
        for executor_id in route["candidate_executor_ids"]:
            assert executor_id in surfaces
        selected = route["selected_executor_id"]
        if selected:
            assert selected in route["candidate_executor_ids"]
            assert surfaces[selected]["reusable_for_05b"] is True
            assert surfaces[selected]["disposition"] == "adapter_required"
        if route["routing_status"] == "blocked":
            assert route["blocking_reasons"]
            if route["runtime_executable"]:
                assert route["known_limitations"]
    session = next(r for r in routes if r["capability_id"] == "session_status")
    assert session["routing_status"] == "blocked"
    assert session["network_required"] is True
    assert set(session["candidate_executor_ids"]) <= set(surfaces)
    for surface_id in session["candidate_executor_ids"]:
        assert surfaces[surface_id]["supported_capabilities"] == ["session_status"] or "session_status" in surfaces[surface_id]["supported_capabilities"]
    for cap in ("identity", "source_currentness", "evidence_quality"):
        route = next(r for r in routes if r["capability_id"] == cap)
        assert route["capability_requires_execution_approval"] is False
        assert route["approval_required"] is False
        assert route["package_approval_policy"] == "inherits_from_upstream"
