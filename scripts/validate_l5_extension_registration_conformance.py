"""Offline acceptance check for explicit evidence-family registration seams.

This module is a TEST / ACCEPTANCE AUTHORITY ONLY. It does not define runtime
identity, dispatch, source, or schema authority, and it performs no discovery.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs/governance/phase_l/PHASE_L_L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_CHECKLIST.v1.json"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def validate_snapshot(snapshot: dict[str, Any], checklist: dict[str, Any]) -> list[dict[str, str]]:
    """Validate explicit snapshots; intentionally no I/O or dynamic lookup."""
    issues: list[dict[str, str]] = []
    forbidden_flags = (
        "not_runtime_registry", "not_capability_authority", "not_source_authority",
        "not_dispatch_authority", "not_plugin_manifest",
    )
    for flag in forbidden_flags:
        if checklist.get(flag) is not True:
            issues.append(_issue("A2_CHECKLIST_AUTHORITY_BOUNDARY_INVALID", flag))
    checked_rows = checklist.get("extension_relevant_registration_checks", [])
    row_ids = [row.get("registration_id") for row in checked_rows]
    if len(checked_rows) != 30 or len(set(row_ids)) != 30:
        issues.append(_issue("A2_EXTENSION_ROW_CHECKLIST_COVERAGE_INVALID", f"count={len(checked_rows)} unique={len(set(row_ids))}"))
    expected_extension_ids = set(snapshot.get("expected_extension_registration_ids", []))
    if expected_extension_ids and set(row_ids) != expected_extension_ids:
        issues.append(_issue("A2_EXTENSION_ROW_CHECKLIST_INVENTORY_MISMATCH", f"missing={sorted(expected_extension_ids-set(row_ids))} extra={sorted(set(row_ids)-expected_extension_ids)}"))
    negative_rows = checklist.get("not_extension_point_controls", [])
    negative_ids = [row.get("registration_id") for row in negative_rows]
    if len(negative_rows) != 9 or len(set(negative_ids)) != 9:
        issues.append(_issue("A2_NEGATIVE_CONTROL_COUNT_INVALID", f"count={len(negative_rows)} unique={len(set(negative_ids))}"))
    expected_negative_ids = set(snapshot.get("expected_negative_registration_ids", []))
    if expected_negative_ids and set(negative_ids) != expected_negative_ids:
        issues.append(_issue("A2_NEGATIVE_CONTROL_INVENTORY_MISMATCH", "checklist differs from frozen A1 negative controls"))
    if len(checklist.get("historical_duplication_controls", [])) != 2:
        issues.append(_issue("A2_HISTORICAL_DUPLICATION_CONTROL_COUNT_INVALID", "expected 2"))
    expected_historical_ids = set(snapshot.get("expected_historical_duplicate_ids", []))
    actual_historical_ids = {row.get("registration_id") for row in checklist.get("historical_duplication_controls", [])}
    if expected_historical_ids and actual_historical_ids != expected_historical_ids:
        issues.append(_issue("A2_HISTORICAL_DUPLICATION_INVENTORY_MISMATCH", "checklist differs from frozen A1 historical-duplicate controls"))
    if len(checklist.get("friction_group_ids", [])) != 8 or len(set(checklist.get("friction_group_ids", []))) != 8:
        issues.append(_issue("A2_FRICTION_GROUP_COVERAGE_INVALID", "expected 8 unique friction groups"))
    if checklist.get("new_canonical_authorities") != 0:
        issues.append(_issue("A2_NEW_CANONICAL_AUTHORITY", str(checklist.get("new_canonical_authorities"))))
    if checklist.get("runtime_discovery") is not False:
        issues.append(_issue("A2_RUNTIME_DISCOVERY_ENABLED", "checklist declares runtime discovery"))

    request_ids = set(snapshot.get("request_capabilities", []))
    catalog_rows = snapshot.get("catalog_capabilities", [])
    catalog_by_id = {row.get("id"): row for row in catalog_rows if isinstance(row, dict)}
    catalog_ids = set(catalog_by_id)
    if request_ids != catalog_ids:
        issues.append(_issue("A2_REQUEST_CATALOG_VOCABULARY_MISMATCH", f"request_only={sorted(request_ids-catalog_ids)} catalog_only={sorted(catalog_ids-request_ids)}"))

    routes = snapshot.get("routes", [])
    route_keys: set[tuple[str, str]] = set()
    for route in routes:
        cap, market = route.get("capability_id"), route.get("market")
        if cap not in catalog_ids:
            issues.append(_issue("A2_UNKNOWN_ROUTED_CAPABILITY", str(cap)))
            continue
        route_key = (cap, market)
        if route_key in route_keys:
            issues.append(_issue("A2_DUPLICATE_ROUTE_IDENTITY", f"{cap}@{market}"))
        route_keys.add(route_key)
        status = route.get("routing_status")
        selected = route.get("selected_executor_id")
        candidates = set(route.get("candidate_executor_ids") or [])
        if selected and selected not in candidates:
            issues.append(_issue("A2_SELECTED_EXECUTOR_NOT_A_CANDIDATE", f"{cap}@{market}:{selected}"))
        if status == "resolved" and route.get("runtime_executable") is True and not selected:
            issues.append(_issue("A2_EXECUTABLE_ROUTE_WITHOUT_SELECTION", f"{cap}@{market}"))
        if status in {"blocked", "plan_only"} and selected:
            issues.append(_issue("A2_BLOCKED_ROUTE_HAS_SELECTION", f"{cap}@{market}:{selected}"))

    metadata_rows = snapshot.get("executor_metadata", [])
    metadata_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    candidate_ids = {executor for route in routes for executor in (route.get("candidate_executor_ids") or [])}
    for meta in metadata_rows:
        executor, cap, market = meta.get("executor_id"), meta.get("capability_id"), meta.get("market")
        key = (executor, cap, market)
        if key in metadata_by_key:
            issues.append(_issue("A2_DUPLICATE_EXECUTOR_METADATA_ROUTE", repr(key)))
        metadata_by_key[key] = meta
        if cap not in catalog_ids:
            issues.append(_issue("A2_EXECUTOR_METADATA_UNKNOWN_CAPABILITY", str(cap)))
        if executor not in candidate_ids and executor not in set(snapshot.get("retained_executor_ids", [])):
            issues.append(_issue("A2_ORPHAN_EXECUTOR_IDENTITY", str(executor)))

    bindings: dict[tuple[str, str, str], dict[str, Any]] = {}
    for binding in snapshot.get("callable_bindings", []):
        key = (binding.get("executor_id"), binding.get("capability_id"), binding.get("market"))
        bindings[key] = binding
        if binding.get("executor_id") not in candidate_ids and binding.get("executor_id") not in set(snapshot.get("retained_executor_ids", [])):
            issues.append(_issue("A2_CALLABLE_UNKNOWN_EXECUTOR_IDENTITY", str(binding.get("executor_id"))))
    for route in routes:
        executor = route.get("selected_executor_id")
        if not executor:
            continue
        key = (executor, route.get("capability_id"), route.get("market"))
        if key not in metadata_by_key:
            issues.append(_issue("A2_SELECTED_ROUTE_WITHOUT_EXECUTOR_METADATA", repr(key)))
        binding = bindings.get(key)
        if not binding or binding.get("trusted_callable_bound") is not True:
            issues.append(_issue("A2_EXECUTOR_WITHOUT_TRUSTED_CALLABLE", repr(key)))
        if binding and binding.get("callable_executor_id") != executor:
            issues.append(_issue("A2_CALLABLE_EXECUTOR_ID_MISMATCH", repr(key)))

    # Every explicit typed-contract seam names versions present in the loader's
    # allowlist and local schema tree. Full semantic compatibility is deferred.
    typed = snapshot.get("typed_contract_views", {})
    loader_contracts = set(typed.get("loader", []))
    for seam in ("lineage", "projection", "result", "audit", "handoff"):
        values = set(typed.get(seam, []))
        unknown = values - loader_contracts
        if unknown:
            issues.append(_issue("A2_TYPED_EVIDENCE_CONTRACT_VERSION_MISMATCH", f"{seam}:{sorted(unknown)}"))
    for contract in loader_contracts:
        if contract not in set(snapshot.get("schema_contracts", [])):
            issues.append(_issue("A2_TYPED_EVIDENCE_SCHEMA_MISSING", contract))

    known_sources = set(snapshot.get("known_source_ids", []))
    for source in snapshot.get("source_bindings", []):
        source_id = source.get("source_id")
        if source_id not in known_sources:
            issues.append(_issue("A2_UNKNOWN_SOURCE_AUTHORITY", str(source_id)))
        if source.get("activation_state") not in {"active", "dormant", "inactive", "eligible", "blocked", "contract_only"}:
            issues.append(_issue("A2_INVALID_SOURCE_ACTIVATION_STATE", str(source_id)))
        if source.get("selected_for_route") is True and source.get("activation_state") != "active":
            issues.append(_issue("A2_DORMANT_SOURCE_SELECTED", str(source_id)))

    if set(snapshot.get("derived_catalog_capabilities", [])) != catalog_ids:
        issues.append(_issue("A2_DERIVED_CATALOG_VIEW_MISMATCH", "portable capability view differs from canonical Catalog"))

    for row in negative_rows:
        if row.get("promoted_to_extension_point") is not False:
            issues.append(_issue("A2_FORBIDDEN_EXTENSION_POINT_PROMOTION", str(row.get("registration_id"))))
    for row in checklist.get("historical_duplication_controls", []):
        if row.get("used_as_current_authority") is not False:
            issues.append(_issue("A2_HISTORICAL_DUPLICATE_AS_CURRENT_AUTHORITY", str(row.get("registration_id"))))
    return sorted(issues, key=lambda item: (item["code"], item["detail"]))


def _literal_assignment(path: Path, name: str) -> Any:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                return ast.literal_eval(node.value)
    raise ValueError(f"explicit registration {name} not found in {path.relative_to(ROOT)}")


def _source_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    route = _json(ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    for row in route.get("phase_h_source_authority", {}).get("records", []):
        records.append({"source_id": row.get("source_id"), "capability_id": row.get("capability_id"), "activation_state": row.get("activation_state", "inactive"), "selected_for_route": row.get("runtime_executable") is True})
    for name in ("phase_i_i1_source_authority.v1.json", "phase_i_i2_source_authority.v1.json", "phase_i_i3_source_authority.v1.json"):
        data = _json(ROOT / "docs/data_capabilities" / name)
        rows = data.get("records", data.get("sources", []))
        for row in rows:
            records.append({"source_id": row.get("source_id"), "capability_id": data.get("capability_id"), "activation_state": row.get("activation_state", "inactive"), "selected_for_route": row.get("activation_state") == "active"})
    return [row for row in records if row["source_id"]]


def load_snapshot(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read existing authorities and the trusted explicit runtime builder."""
    global ROOT
    ROOT = root.resolve()
    catalog = _json(ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = _json(ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    metadata = _json(ROOT / "config/m8r_06_03_executor_registry_metadata.json")
    a1_registration_inventory = _json(ROOT / "docs/governance/phase_l/acceptance_runs/l5-a1-20261018T140202Z/registration_authority_matrix.json")
    request_schema = _json(ROOT / "schemas/unified_market_evidence_request.v3.schema.json")
    request_ids = request_schema["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]
    typed_loader = _literal_assignment(ROOT / "scripts/m8r_05c/artifact_loader.py", "_RESEARCH_EVIDENCE_CONTRACTS")
    lineage_h = _literal_assignment(ROOT / "scripts/m8r_05c/lineage_resolver.py", "_PHASE_H_TYPED_CONTRACT_BY_DATA_NEED")
    lineage_i = _literal_assignment(ROOT / "scripts/m8r_05c/lineage_resolver.py", "_PHASE_I_TYPED_CONTRACT_BY_DATA_NEED")
    audit_map = _literal_assignment(ROOT / "scripts/m8r_05c/audit_package_builder.py", "_PHASE_H_CAPABILITIES")
    loader_ids = set(typed_loader)
    typed_values = {
        "loader": list(typed_loader),
        "lineage": list(lineage_h.values()) + list(lineage_i.values()),
        "projection": sorted(set(_extract_contract_literals(ROOT / "scripts/m8r_05c/evidence_projector.py")) & loader_ids),
        "result": sorted(set(_extract_contract_literals(ROOT / "scripts/m8r_05c/result_builder.py")) & loader_ids),
        "audit": list(audit_map),
        "handoff": sorted(set(_extract_contract_literals(ROOT / "scripts/m8r_05c/markdown_renderer.py")) & loader_ids),
    }
    schema_contracts = [p.name[:-len(".schema.json")] for p in (ROOT / "schemas").glob("*.schema.json")]
    portable = _json(ROOT / "skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json")
    source_records = _source_records()
    known_sources = sorted({row["source_id"] for row in source_records})
    # This import calls only the already-trusted registry builder. Its adapter
    # functions are materialized but never invoked; no provider call is made.
    sys.dont_write_bytecode = True
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry

    runtime_registry = build_production_runtime_adapter_registry()
    callable_rows = []
    for item in runtime_registry._by_route.values():
        callable_rows.append({"executor_id": item.executor_id, "capability_id": item.capability_id, "market": item.market, "trusted_callable_bound": callable(item.adapter), "callable_executor_id": item.executor_id})
    expanded_routes = []
    for route in routing["routes"]:
        for market in route.get("supported_markets", []):
            expanded_routes.append({**route, "market": market})
    orchestrator = _json(ROOT / "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json")
    retained_executor_ids = [row["surface_id"] for row in orchestrator.get("surfaces", []) if "executor" in row.get("surface_type", "") and "retained non-selected" in row.get("current_status", "")]
    snapshot = {
        "request_capabilities": request_ids,
        "catalog_capabilities": [{"id": row["capability_id"], "status": row["support_status"]} for row in catalog["data_need_capabilities"]],
        "routes": expanded_routes,
        "executor_metadata": metadata["executors"],
        "callable_bindings": callable_rows,
        "retained_executor_ids": retained_executor_ids,
        "expected_extension_registration_ids": [row["registration_id"] for row in a1_registration_inventory["registration_surfaces"] if row["classification"] != "NOT_AN_EXTENSION_POINT"],
        "expected_negative_registration_ids": [row["registration_id"] for row in a1_registration_inventory["registration_surfaces"] if row["classification"] == "NOT_AN_EXTENSION_POINT"],
        "expected_historical_duplicate_ids": [row["registration_id"] for row in a1_registration_inventory["registration_surfaces"] if row["classification"] == "HISTORICAL_DUPLICATION"],
        "typed_contract_views": typed_values,
        "schema_contracts": schema_contracts,
        "known_source_ids": known_sources,
        "source_bindings": source_records,
        "derived_catalog_capabilities": [row["capability_id"] for row in portable["data_need_capabilities"]],
    }
    checklist = _json(CHECKLIST if root.resolve() == ROOT else root / "docs/governance/phase_l/PHASE_L_L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_CHECKLIST.v1.json")
    return snapshot, checklist


def _extract_contract_literals(path: Path) -> list[str]:
    # Read-only source inspection. Only versioned evidence identity literals are
    # returned; this does not import arbitrary modules or discover extensions.
    text = path.read_text(encoding="utf-8")
    import re

    return sorted(set(re.findall(r"[A-Za-z][A-Za-z0-9_]*_evidence\.v[0-9]+", text)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        snapshot, checklist = load_snapshot(args.root)
        issues = validate_snapshot(snapshot, checklist)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        issues = [_issue("A2_AUTHORITY_READ_OR_SHAPE_ERROR", str(exc))]
    result = {"status": "PASS" if not issues else "FAIL", "issue_count": len(issues), "issues": issues, "network_access": False, "writes": False, "production_state_mutation": False, "runtime_discovery": False}
    if args.json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        print(f"L5 explicit registration conformance: {result['status']} ({len(issues)} issue(s))")
        for issue in issues:
            print(f"{issue['code']}: {issue['detail']}")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
