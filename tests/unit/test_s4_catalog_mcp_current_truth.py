"""Offline S4 summary consistency; runtime authorities are read, never repaired."""
import copy
import json
from pathlib import Path

import pytest

from scripts import validate_l5_extension_publication_conformance as publication
from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
from server.services.phase_h_h1_tpex_composite import SOURCES
from server.services.unified_local_service import describe_capabilities

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


@pytest.mark.parametrize("item,cid,market,executor", [
    ("H1", "trading_status_context", "TPEX", "phase_h_h1_tpex_composite_executor"),
    ("H2", "corporate_action_context", "TWSE", "phase_h_h2_twse_exright_pre_executor"),
    ("H3", "recent_performance", "TWSE", "phase_h_h3_twse_recent_performance_executor"),
    ("H4", "discontinuity_safety", None, None),
    ("session_status", "session_status", None, None),
])
def test_current_summary_matches_route_registry_and_publication(item, cid, market, executor):
    catalog = load(publication.CATALOG)
    routing = load(publication.ROUTING)
    portable = load(publication.PORTABLE)
    caps = {c["capability_id"]: c for c in catalog["data_need_capabilities"]}
    routes = {r["capability_id"]: r for r in routing["routes"]}
    projected = {c["capability_id"]: c for c in describe_capabilities()["capabilities"]}
    registry = build_production_runtime_adapter_registry()
    reference = (ROOT / "docs/reference/MCP_REFERENCE.md").read_text(encoding="utf-8")
    row = next(line for line in reference.splitlines() if line.startswith(f"| {item} |"))
    assert f"`{cid}`" in row
    if item == "H4":
        assert cid not in caps and cid not in routes and cid not in projected
        derived = next(d for d in catalog["phase_h_contract"]["derived_evidence"] if d["evidence_id"] == cid)
        route = next(d for d in routing["derived_contracts"] if d["evidence_id"] == cid)
        assert derived["request_capability"] is False and derived["network_required"] is False
        assert route["routing_status"] == "derived_zero_network"
        assert route["selected_executor_id"] is None and route["network_required"] is False
        assert derived["requires_upstream_evidence"] == ["corporate_action_context", "recent_performance"]
        assert "zero-network" in row and "no independent request capability" in row
        return
    cap, route, mcp = caps[cid], routes[cid], projected[cid]
    assert next(c for c in portable["data_need_capabilities"] if c["capability_id"] == cid) == cap
    assert mcp["description"] == cap["description"]
    assert mcp["known_limitations"] == cap["known_limitations"]
    quick = next(line for line in (ROOT / publication.QUICK).read_text(encoding="utf-8").splitlines()
                 if line.startswith(f"| `{cid}` |"))
    assert route["selected_executor_id"] == executor
    if executor:
        assert route["routing_status"] == "resolved" and route["supported_markets"] == [market]
        assert registry.get_route(executor, cid, market) is not None
        assert route["network_required"] is True
        assert "executable subject to" in quick
    else:
        assert route["routing_status"] == "blocked" and route["blocking_reasons"]
        assert not any(r.capability_id == cid for r in registry._by_route.values())
        assert all(m["production_executor_available"] is False for m in mcp["markets"])
        assert "NOT currently executable" in quick
        assert "blocked" in cap["description"] and "not currently executable" in row
        assert cap["support_status"] == "runtime_executable"  # semantic label is not activation
    top = " ".join(catalog["known_limitations"])
    limitations = " ".join(cap["known_limitations"])
    if item == "H1":
        assert [s["source_contract_id"] for s in SOURCES] == [
            "tpex_trading_warning_information", "tpex_disposal_information", "tpex_cmode"]
        assert route["estimated_network_requests_per_invocation"] == 3
        for text in (top, limitations, row):
            assert all(token in text for token in ("attention", "disposition", "cmode", "unresolved",
                                                   "changed_trading_method", "suspension", "resumption"))
        assert "zero canonical coverage" in top and "zero canonical coverage" in row
        assert "no canonical coverage" in limitations
        assert "only active H1 route" not in top
    elif item == "H2":
        for text in (top, row):
            assert "TWT48U_ALL" in text and "preannouncement" in text
            assert "full historical coverage" in text and "TWT49U" in text
            assert "subtype coverage remains incomplete" in text
        assert "pre-announcement" in limitations and "TWT49U" in limitations
        assert "same-target H3" in row and "H2 remains inactive" not in top
    elif item == "H3":
        assert cap["allowed_parameters"]["lookback_trading_days"]["maximum"] == 20
        assert "TPEx blocked and non-executable" in row
        assert "TPEX H3 remains blocked and non-executable" in limitations
        tpex = next(m for m in mcp["markets"] if m["market"] == "TPEX")
        assert tpex["production_executor_available"] is False
    assert portable["known_limitations"] == catalog["known_limitations"]


@pytest.mark.parametrize("target", ["h1", "h2", "session", "other_top", "route"])
def test_l5_rejects_drift_including_every_s4_protected_field(target):
    snapshot = publication.load_snapshot()
    if target in ("h1", "h2", "other_top"):
        index = {"h1": 4, "h2": 5, "other_top": 6}[target]
        snapshot["catalog"]["known_limitations"][index] += " unauthorized alteration"
    elif target == "session":
        next(c for c in snapshot["catalog"]["data_need_capabilities"]
             if c["capability_id"] == "session_status")["description"] = "Executable session retrieval"
    else:
        route = snapshot["routing"]["routes"][0]
        route["network_required"] = not route["network_required"]
    # Even synchronized derived output cannot authorize a changed canonical field.
    snapshot["portable"] = publication.generator.generate_portable_json_obj(
        snapshot["catalog"], snapshot["catalog_hash"], snapshot["catalog_lineage"])
    snapshot["quick"] = publication.generator.generate_portable_markdown_text(
        snapshot["portable"], snapshot["catalog_hash"], snapshot["routing"],
        snapshot["routing_hash"], snapshot["routing_lineage"])
    codes = {e["code"] for e in publication.validate_snapshot(snapshot)["errors"]}
    assert "A4_CATALOG_SEMANTIC_CHANGE_REQUIRED" in codes


def test_s4_exact_delta_keeps_historical_baseline_and_requires_predecessors():
    snapshot = publication.load_snapshot()
    before = copy.deepcopy(snapshot["baseline_catalog"])
    expected = publication.s4_expected_catalog(before)
    assert before == snapshot["baseline_catalog"]
    assert publication.functional_view(expected, "data_need_capabilities") == publication.functional_view(
        snapshot["catalog"], "data_need_capabilities")
    before["known_limitations"][4] = "wrong predecessor"
    with pytest.raises(ValueError, match="predecessor mismatch"):
        publication.s4_expected_catalog(before)
