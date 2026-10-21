"""Offline A5 TEST / ACCEPTANCE ONLY proof; never a runtime family registry.

The two examples come from frozen A1, while all live values come from existing
Catalog/Route/schema/source/executor authorities. Trusted existing test fixtures
are invoked explicitly; no provider, discovery, persistent state or output I/O.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import subprocess

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
A1 = "docs/governance/phase_l/PHASE_L_L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT.v1.json"
EXAMPLES = "docs/governance/phase_l/acceptance_runs/l5-a1-20261018T140202Z/existing_family_conformance_examples.json"
REQUEST = "schemas/unified_market_evidence_request.v3.schema.json"
BASE = "09d6db51cf242316632bffb7ee96eef88014a039"


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def schema_errors(value: dict, path: str) -> list[str]:
    return sorted(e.message for e in Draft7Validator(read(path), format_checker=FormatChecker()).iter_errors(value))


def request_probe() -> list[dict]:
    rows = []
    for example in read(EXAMPLES)["examples"]:
        family = example["capability_id"]
        for mode in ("type", "capability_id", "both"):
            need = {"priority": "required", "parameters": {}}
            if mode in {"type", "both"}:
                need["type"] = family
            if mode in {"capability_id", "both"}:
                need["capability_id"] = family
            request = {"schema_version": "unified_market_evidence_request.v3", "request_id": "a5-fixture",
                       "targets": [{"input": "2330"}], "data_needs": [need], "execution_mode": "preview"}
            errors = schema_errors(request, REQUEST)
            rows.append({"family": family, "mode": mode, "valid": not errors, "errors": errors})
    return rows


def build_case(family: str, market: str, scenario: str = "available") -> dict:
    """Transform existing accepted payload fixtures, using supplied local fetchers."""
    from tests.unit import test_phase_g_monthly_revenue as revenue
    from tests.unit import test_phase_g_material_disclosures as disclosures
    from tests.unit.test_phase_h_imp_6_v3_projection_handoff import _inputs
    from scripts.phase_g import mops_monthly_revenue, mops_material_disclosures
    from scripts.m8r_05c.canonical import hash_body_excluding_key
    from scripts.m8r_05c.lineage_resolver import build_lineage_map
    from scripts.m8r_05c.citation_builder import build_citation_index
    from scripts.m8r_05c.result_builder import build_result
    from scripts.m8r_05c.audit_package_builder import build_audit_package
    from scripts.m8r_05c.markdown_renderer import render_result_markdown

    example = next(x for x in read(EXAMPLES)["examples"] if x["capability_id"] == family)
    target = deepcopy(revenue.TARGET)
    code = "2330" if market == "TWSE" else "6488"
    target.update(market=market, security_code=code, canonical_target_id=f"{market}:{code}")
    module = mops_monthly_revenue if family == "monthly_revenue" else mops_material_disclosures
    payload = revenue.HEAD + revenue.ROW if family == "monthly_revenue" else disclosures.CSV
    payload = payload.replace("2330", code)
    if scenario == "missing":
        payload = payload.replace(code, "2317").replace(target["security_name_zh"], "其他")
    if scenario == "partial":
        if family != "material_disclosures":
            raise ValueError("partial scenario is only a disclosure acquisition state here")
        head, row = payload.split("\n", 1)
        payload = head + "\n" + "".join(row.replace("測試", f"測試{i}") for i in range(51))
    calls = []

    def csv_fetcher(url):
        calls.append({"transport": "csv", "url": url, "fixture_only": True})
        if scenario == "source_failed":
            raise OSError("fixture-only transport failure")
        return payload

    def json_fetcher(url):
        calls.append({"transport": "json", "url": url, "fixture_only": True})
        return []

    operation = module.execute([target], market, observed_at="2026-09-16T00:00:00Z",
                               csv_fetcher=csv_fetcher, json_fetcher=json_fetcher)[0]
    inputs = _inputs(include_h1=False, include_h2=False, include_h3=False)
    inputs.request = {"schema_version": "unified_market_evidence_request.v3", "request_id": f"a5-{family}-{market}-{scenario}",
                      "targets": [{"input": code}], "data_needs": [{"type": family, "priority": "required", "parameters": {}}],
                      "execution_mode": "preview"}
    identity = inputs.f3_validation["target_results"][0]["canonical_identity"]
    snapshot = read("tests/fixtures/m8r_05a_f3/verified_security_master_snapshot.json")
    record = next(x for x in snapshot["records"] if x["canonical_target_id"] == target["canonical_target_id"])
    identity.update(target, isin=record["identity"]["isin"])
    inputs.f3_validation["target_results"][0]["original_input"] = code
    path, opid = f"evidence/{family}/{market}_{code}.json", f"op-{family}-{market}"
    reference = {"relative_path": path, "sha256": digest(operation), "schema_version": operation["schema_version"],
                 "byte_size": len(json.dumps(operation, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())}
    inputs.plan["operations"] = [{"operation_id": opid, "capability_id": family,
        "executor_id": example["executor_id"], "market": market, "canonical_target_ids": [target["canonical_target_id"]],
        "expected_evidence_contract": example["operation_evidence_contract_id"]}]
    inputs.receipt.update(total_operations=1, succeeded_operations=1, failed_operations=0, overall_status="succeeded")
    inputs.bundle.update(total_item_count=1, overall_status="succeeded", operation_evidence_entries=[{
        "operation_id": opid, "status": "succeeded", "result_item_count": 1, "artifacts": [reference], "warnings": []}],
        artifact_inventory=[{**reference, "evidence_contract": operation["schema_version"]}])
    inputs.receipt["execution_receipt_hash"] = hash_body_excluding_key(inputs.receipt, "execution_receipt_hash")
    inputs.bundle["bundle_hash"] = hash_body_excluding_key(inputs.bundle, "bundle_hash")
    inputs.evidence_artifacts = {path: operation}
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    citations = build_citation_index(build_lineage_map(inputs), inputs.bundle, result["schema_version"])
    audit = build_audit_package(result, inputs, citations, "ai_context/unified_market_evidence_result.v3.json",
                                output_schema_version="unified_market_evidence_audit_package.v3")
    return {"family": family, "market": market, "scenario": scenario, "request": inputs.request,
            "target": target, "plan_operation": deepcopy(inputs.plan["operations"][0]), "operation_evidence": deepcopy(operation),
            "artifact_reference": reference, "result": result, "audit": audit,
            "handoff": render_result_markdown(result), "fixture_fetch_calls": calls,
            "fixture_authorities": ["tests/unit/test_phase_g_monthly_revenue.py::HEAD/ROW/TARGET",
                                    "tests/unit/test_phase_g_material_disclosures.py::CSV",
                                    "tests/unit/test_phase_h_imp_6_v3_projection_handoff.py::_inputs",
                                    "tests/fixtures/m8r_05a_f3/verified_security_master_snapshot.json"]}


def validate_case(case: dict) -> list[dict]:
    """Independently reject identity, semantic, hash, citation and output drift."""
    from scripts.phase_g.research_executor import ROUTES
    from scripts.m8r_05c.citation_builder import _build_citation_id
    from scripts.m8r_05c.canonical import hash_body_excluding_key
    from scripts.m8r_05c.markdown_renderer import render_result_markdown
    errors = []

    def check(ok, code, detail):
        if not ok:
            errors.append({"code": code, "detail": detail})

    examples = {x["capability_id"]: x for x in read(EXAMPLES)["examples"]}
    family, market = case.get("family"), case.get("market")
    if family not in examples:
        return [{"code": "A5_NEW_FAMILY_DETECTED", "detail": str(family)}]
    e = examples[family]
    operation, plan, result, audit = (case[k] for k in ("operation_evidence", "plan_operation", "result", "audit"))
    check(not schema_errors(case["request"], REQUEST) and case["request"]["data_needs"][0].get("type") == family,
          "A5_CAPABILITY_IDENTITY_DRIFT", "Request type must carry semantic capability identity; no alias")
    check(operation.get("capability_id") == family and plan.get("capability_id") == family,
          "A5_CAPABILITY_IDENTITY_DRIFT", "operation capability")
    check(operation.get("schema_version") == e["operation_evidence_contract_id"] and
          not schema_errors(operation, "schemas/" + e["operation_evidence_contract_id"] + ".schema.json"),
          "A5_OPERATION_CONTRACT_DRIFT", "operation contract/schema")
    check(operation.get("executor_id") == plan.get("executor_id") == e["executor_id"],
          "A5_EXECUTOR_IDENTITY_DRIFT", "trusted executor identity")
    check(market in {"TWSE", "TPEX"} and plan.get("market") == market and case["target"].get("market") == market,
          "A5_ROUTE_IDENTITY_DRIFT", "market/route")
    expected_source = ROUTES.get((family, market), {}).get("contract")
    check(operation.get("source", {}).get("source_family") == e["source_authority_identity"],
          "A5_SOURCE_AUTHORITY_DRIFT", "source family")
    check(operation.get("source", {}).get("source_contract_id") == expected_source,
          "A5_SOURCE_CONTRACT_DRIFT", "family-market source contract")
    target = result.get("targets", [{}])[0]
    typed = target.get("evidence", {}).get(family, {})
    check(typed.get("schema_version") == e["typed_evidence_contract_id"] and
          not schema_errors(typed, "schemas/" + e["typed_evidence_contract_id"] + ".schema.json"),
          "A5_TYPED_CONTRACT_DRIFT", "typed contract/schema")
    check(not schema_errors(result, "schemas/unified_market_evidence_result.v3.schema.json"),
          "A5_RESULT_PROJECTION_DRIFT", "Result V3 schema")
    check(typed.get("status") == operation.get("status") and typed.get("source", {}).get("source_contract_id") == expected_source,
          "A5_CROSS_MARKET_NORMALIZATION_DRIFT", "stable typed schema/status and market-specific provenance")
    check(typed.get("source", {}).get("market") == market, "A5_ROUTE_IDENTITY_DRIFT", "typed market")
    if family == "monthly_revenue":
        check(typed.get("value") == operation.get("value"), "A5_RESULT_PROJECTION_DRIFT", "signed values/units/nulls")
    else:
        for source_item, item in zip(operation.get("items", []), typed.get("items", [])):
            check(all(item.get(k) == source_item.get(k) for k in ("published_at", "source_fact_date", "subject", "revision_relation")) and
                  item.get("description") == source_item.get("description_raw", "")[:8192],
                  "A5_RESULT_PROJECTION_DRIFT", "disclosure values and bounded description")
    check(all(typed.get("coverage", {}).get(k) == v for k, v in operation.get("coverage", {}).items()
              if k in typed.get("coverage", {})) and typed.get("currentness", {}).get("observed_at") == operation.get("observed_at"),
          "A5_RESULT_PROJECTION_DRIFT", "source/effective/publication vs observation time")
    tid, opid = case["target"]["canonical_target_id"], plan.get("operation_id")
    ref = case["artifact_reference"]
    check(operation.get("target") == {k: case["target"][k] for k in ("canonical_target_id", "market", "security_code")} and
          target.get("canonical_identity", {}).get("canonical_target_id") == tid and plan.get("canonical_target_ids") == [tid],
          "A5_LINEAGE_DRIFT", "target binding")
    check(ref.get("sha256") == digest(operation), "A5_LINEAGE_DRIFT", "retained operation bytes hash")
    expected_cite = _build_citation_id(opid, ref["relative_path"])
    citations = target.get("citations", [])
    check(len(citations) == 1 and citations[0].get("citation_id") == expected_cite and
          typed.get("citation_ids") == [expected_cite] and
          citations[0].get("artifact_reference") == ref["relative_path"] and
          citations[0].get("normalized_evidence_hash") == ref["sha256"] and
          citations[0].get("source_contract_id") == expected_source and
          citations[0].get("retrieved_at") != operation.get("observed_at"),
          "A5_CITATION_DRIFT", "canonical operation/artifact citation and retrieved-at distinction")
    entries = audit.get("citation_to_operation_map", [])
    check(len(entries) == 1 and all(entries[0].get(k) == v for k, v in {
        "citation_id": expected_cite, "operation_id": opid, "executor_id": e["executor_id"],
        "capability_id": family, "canonical_target_id": tid, "artifact_hash": ref["sha256"],
        "artifact_relative_path": ref["relative_path"]}.items()), "A5_CITATION_DRIFT", "Audit citation provenance")
    lineage = audit.get("operation_lineage", [])
    inventory = audit.get("artifact_inventory", [])
    check(len(lineage) == 1 and all(lineage[0].get(k) == v for k, v in {
        "operation_id": opid, "capability_id": family, "executor_id": e["executor_id"],
        "market": market, "canonical_target_ids": [tid], "evidence_contract": e["operation_evidence_contract_id"]}.items()) and
        len(inventory) == 1 and inventory[0].get("sha256") == ref["sha256"] and
        inventory[0].get("relative_path") == ref["relative_path"],
        "A5_LINEAGE_DRIFT", "Audit operation and retained artifact inventory")
    check(audit.get("result_id") == result.get("result_id") and audit.get("result_hash") == result.get("result_hash") and
          result.get("result_hash") == hash_body_excluding_key(result, "result_hash") and
          audit.get("integrity_verification", {}).get("result_hash_verified") is True and
          not schema_errors(audit, "schemas/unified_market_evidence_audit_package.v3.schema.json"),
          "A5_AUDIT_PROJECTION_DRIFT", "same Result identity/hash and Audit V3 schema")
    check(case["handoff"] == render_result_markdown(result) and expected_cite in case["handoff"] and
          typed.get("status", "") in case["handoff"], "A5_HANDOFF_DRIFT", "canonical derived output without state/citation invention")
    return errors


def dimension_matrix() -> list[dict]:
    """Proof mappings are acceptance metadata, never dispatch or identity authority."""
    result = []
    for e in read(EXAMPLES)["examples"]:
        for d in read(A1)["dimensions"]:
            cls = d["classification"]
            outcome = "PLATFORM_INHERITED_PASS" if cls == "PLATFORM_PROVIDED" else "DERIVED_PASS" if cls == "DERIVED" else "PASS"
            result.append({"family": e["capability_id"], "dimension_id": d["dimension_id"], "name": d["name"],
                "A1_classification": cls, "applicability": "APPLICABLE", "current_authority": d["canonical_owner"],
                "exact_evidence_path_symbol": d["evidence_files"],
                "executed_acceptance_symbols": ["scripts/validate_l5_existing_family_conformance.py::validate_case",
                    "scripts/validate_l5_existing_family_conformance.py::validate_snapshot",
                    "tests/unit/test_l5_a5_existing_family_conformance.py"],
                "proof_type": "EXISTING_PLATFORM_GATE" if cls == "PLATFORM_PROVIDED" else "EXECUTED_FAMILY_TRACE_AND_EXISTING_GATE",
                "conformance_result": outcome,
                "notes": {"DIM-21": "Optional raw schema declared: retained operation-evidence schema; full raw provider payload retention is not promised.",
                          "DIM-22": "Optional replay declared: platform retained-package replay, never refetch; missing predecessor fails closed.",
                          "DIM-35": "Owner clarified capability_id semantic namespace is carried by Request V3 type; no registry or alias.",
                          "DIM-36": "Existing A1 T1-T12 version authority inherited unchanged; no transition is performed."}.get(d["dimension_id"], d["acceptance_evidence"])})
    return result


def platform_proof() -> dict:
    """Bounded structural evidence; behavioral protection is delegated to existing suites."""
    family_modules = ("scripts/phase_g/mops_monthly_revenue.py", "scripts/phase_g/mops_material_disclosures.py")
    sources = {}
    for path in family_modules:
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
        functions = sorted(n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        calls = [n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        sources[path] = {"defined_functions": functions,
            "private_lifecycle_functions": sorted(set(functions) & {"init", "start", "stop", "status", "doctor"}),
            "shared_source_stages_present": all(name in calls for name in ("fetch_once", "normalize_source_rows", "bind_rows")),
            "family_retention_or_security_policy_functions": [name for name in functions if any(x in name for x in ("retention", "secret", "network_policy", "concurrency_policy"))]}
    return {"family_modules": sources, "behavioral_gates": [
        "tests/unit/test_unified_retention_inventory.py", "tests/unit/test_unified_replay_inspector.py",
        "tests/unit/test_phase_l_l4_a2_path_containment.py", "tests/unit/test_phase_l_l4_a3_input_output_bounds.py",
        "tests/unit/test_phase_l_l4_a4_injection_secret_boundary.py", "tests/unit/test_phase_l_l4_a6_resource_boundaries.py",
        "tests/unit/test_phase_l_l1_source_acquisition_timing.py"],
        "retention_owner": "server/services/unified_retention_inventory.py::classify_artifact_family",
        "replay_owner": "server/services/unified_replay_inspector.py",
        "resource_owner": "server/resource_boundaries.py",
        "authorization_owner": "server/services/unified_mode_b2.py",
        "raw_provider_payload_retained_by_default": False}


def load_snapshot() -> dict:
    from scripts.phase_g.research_executor import ROUTES
    from scripts.validate_l5_extension_publication_conformance import load_snapshot as publication_snapshot
    from server.services.unified_retention_inventory import classify_artifact_family
    from server.unified_mcp.tool_contracts import build_tool_specs
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    registry = build_production_runtime_adapter_registry()
    return {"examples": read(EXAMPLES)["examples"], "dimensions": dimension_matrix(),
            "catalog": read("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json"),
            "routing": read("docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json"),
            "executor_metadata": read("config/m8r_06_03_executor_registry_metadata.json")["executors"],
            "source_routes": [{"capability_id": cap, "market": market, "contract": r["contract"]} for (cap, market), r in sorted(ROUTES.items())],
            "trusted_bindings": [{"capability_id": r.capability_id, "market": r.market,
                "executor_id": r.executor_id, "callable": callable(r.adapter)} for r in registry._by_route.values()],
            "publication": publication_snapshot(), "tools": sorted(t.name for t in build_tool_specs()),
            "family_registry": None, "family_owned_policies": [], "platform_proof": platform_proof(),
            "protected_product_diff": subprocess.check_output(["git", "diff", BASE, "--name-only", "--",
                "server", "schemas", "config", "docs/data_capabilities", "scripts/phase_g", "scripts/m8r_05c",
                "skills/tw-market-evidence-agent", "docs/agent_usage_guide.md"], cwd=ROOT, text=True).splitlines(),
            "retention": {name: classify_artifact_family(name) for name in ("operation_evidence_and_source_snapshots", "persisted_result_json", "persisted_audit_package", "persisted_ai_handoff", "unknown_a5_fixture")}}


def validate_snapshot(s: dict) -> list[dict]:
    from scripts.validate_l5_extension_publication_conformance import validate_snapshot as publication_check, EXPECTED_TOOLS
    errors = []
    def fail(code, detail): errors.append({"code": code, "detail": detail})
    examples = {e["capability_id"]: e for e in read(EXAMPLES)["examples"]}
    if {e.get("capability_id") for e in s["examples"]} != set(examples) or s.get("family_registry") is not None:
        fail("A5_NEW_FAMILY_DETECTED", "exactly the two frozen examples; no family registry")
    frozen = {d["dimension_id"]: d for d in read(A1)["dimensions"]}
    cells = s["dimensions"]
    keys = [(r.get("family"), r.get("dimension_id")) for r in cells]
    if len(keys) != 72 or set(keys) != {(f, d) for f in examples for d in frozen} or len(set(keys)) != 72:
        fail("A5_DIMENSION_UNACCOUNTED", "exactly 36 frozen dimensions x 2 families")
    for row in cells:
        d = frozen.get(row.get("dimension_id"), {})
        mandatory = ("family", "dimension_id", "name", "A1_classification", "applicability", "current_authority",
                     "exact_evidence_path_symbol", "executed_acceptance_symbols", "proof_type", "conformance_result", "notes")
        if (any(not row.get(k) for k in mandatory) or row.get("A1_classification") != d.get("classification")
                or row.get("current_authority") != d.get("canonical_owner")
                or row.get("conformance_result") not in {"PASS", "PLATFORM_INHERITED_PASS", "DERIVED_PASS"}):
            fail("A5_DIMENSION_UNACCOUNTED", str(row.get("dimension_id")))
    if set(s["tools"]) != EXPECTED_TOOLS:
        fail("A5_NEW_CAPABILITY_DETECTED", "six-tool surface")
    if s.get("family_owned_policies") or s["retention"]["unknown_a5_fixture"]["state_class"] != "UNCLASSIFIED_REQUIRES_POLICY":
        fail("A5_PLATFORM_INHERITANCE_DRIFT", "retention/security/resource remain platform-owned")
    if any(row["private_lifecycle_functions"] or row["family_retention_or_security_policy_functions"] or
           not row["shared_source_stages_present"] for row in s["platform_proof"]["family_modules"].values()):
        fail("A5_PLATFORM_INHERITANCE_DRIFT", "no private lifecycle/policy; shared transport-contract-semantic stages")
    if s.get("protected_product_diff"):
        fail("A5_NEW_FAMILY_DETECTED", "A5 requires unchanged product authority: " + str(s["protected_product_diff"]))
    for f, e in examples.items():
        caps = [r for r in s["catalog"]["data_need_capabilities"] if r["capability_id"] == f]
        routes = [r for r in s["routing"]["routes"] if r["capability_id"] == f]
        if len(caps) != 1 or caps[0].get("support_status") != "runtime_executable":
            fail("A5_CAPABILITY_IDENTITY_DRIFT", f)
        if len(routes) != 1 or routes[0].get("selected_executor_id") != e["executor_id"] or routes[0].get("supported_markets") != ["TWSE", "TPEX"] or routes[0].get("output_evidence_contract") != e["operation_evidence_contract_id"]:
            fail("A5_ROUTE_IDENTITY_DRIFT", f)
        authorities = [r for r in s["catalog"]["available_source_families"] if r["source_family"] == e["source_authority_identity"]]
        if len(authorities) != 1 or authorities[0].get("runtime_availability") is not True or authorities[0].get("market_scope") != ["TWSE", "TPEX"]:
            fail("A5_SOURCE_AUTHORITY_DRIFT", f)
        for market in ("TWSE", "TPEX"):
            rows = [r for r in s["executor_metadata"] if r["capability_id"] == f and r["market"] == market]
            if len(rows) != 1 or rows[0]["executor_id"] != e["executor_id"] or rows[0]["expected_evidence_contract"] != e["operation_evidence_contract_id"] or rows[0].get("timeout_seconds", 0) <= 0 or rows[0].get("output_policy") != "contained_artifact_only":
                fail("A5_EXECUTOR_IDENTITY_DRIFT", f + ":" + market)
            bindings = [r for r in s["trusted_bindings"] if r["capability_id"] == f and r["market"] == market]
            if len(bindings) != 1 or bindings[0]["executor_id"] != e["executor_id"] or bindings[0]["callable"] is not True:
                fail("A5_EXECUTOR_IDENTITY_DRIFT", "trusted callable:" + f + ":" + market)
        sources = [r for r in s["source_routes"] if r["capability_id"] == f]
        if len(sources) != 2 or {r["market"] for r in sources} != {"TWSE", "TPEX"} or {r["contract"] for r in sources} != set(e["source_contract_ids"]):
            fail("A5_SOURCE_CONTRACT_DRIFT", f)
    if publication_check(s["publication"])["status"] != "PASS":
        fail("A5_PUBLICATION_DRIFT", "delegated accepted A4 deterministic gate")
    baseline_ids = set(read(REQUEST)["properties"]["data_needs"]["items"]["properties"]["type"]["enum"])
    if {r["capability_id"] for r in s["catalog"]["data_need_capabilities"]} != baseline_ids:
        fail("A5_NEW_CAPABILITY_DETECTED", "closed Request/Catalog vocabulary")
    return errors


def build_evidence() -> dict:
    snapshot = load_snapshot()
    cases = [build_case(e["capability_id"], m) for e in snapshot["examples"] for m in ("TWSE", "TPEX")]
    scenarios = [build_case(f, "TWSE", state) for f in ("monthly_revenue", "material_disclosures") for state in ("missing", "source_failed")]
    scenarios.append(build_case("material_disclosures", "TWSE", "partial"))
    issues = validate_snapshot(snapshot)
    for case in cases + scenarios:
        issues.extend(validate_case(case))
    for e in snapshot["examples"]:
        pair = [c for c in cases if c["family"] == e["capability_id"]]
        normalized = []
        for c in pair:
            typed = deepcopy(c["result"]["targets"][0]["evidence"][c["family"]])
            typed.pop("source"); typed.pop("citation_ids")
            for item in typed.get("items", []):
                item.pop("citation_id", None)
            normalized.append(typed)
        if normalized[0] != normalized[1]:
            issues.append({"code": "A5_CROSS_MARKET_NORMALIZATION_DRIFT", "detail": e["capability_id"]})
    probes = request_probe()
    if not all(p["valid"] == (p["mode"] == "type") for p in probes):
        issues.append({"code": "A5_CAPABILITY_IDENTITY_DRIFT", "detail": "Request representation probe"})
    return {"authority_kind": "TEST_ACCEPTANCE_ONLY", "network": False, "writes": False,
            "runtime_discovery": False, "new_registry": False, "status": "FAIL" if issues else "PASS",
            "errors": issues, "dimensions": snapshot["dimensions"], "request_probe": probes,
            "cases": cases, "semantic_scenarios": scenarios, "retention": snapshot["retention"],
            "platform_proof": snapshot["platform_proof"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--full-evidence", action="store_true", help="Print deterministic in-memory traces to stdout")
    args = parser.parse_args()
    evidence = build_evidence()
    summary = {k: v for k, v in evidence.items() if k not in {"cases", "semantic_scenarios", "dimensions", "retention"}}
    summary.update(representative_families=2, family_dimension_cells=len(evidence["dimensions"]),
                   cross_market_cases=len(evidence["cases"]), semantic_scenarios=len(evidence["semantic_scenarios"]))
    print(json.dumps(evidence if args.full_evidence else summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
