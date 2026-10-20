#!/usr/bin/env python3
"""TEST / ACCEPTANCE AUTHORITY ONLY. Offline, read-only publication checks.

No runtime registry, dispatch/source authority, plugin manifest or discovery.
Existing independent sync gates remain required. The pinned baseline only bounds
this tranche's descriptive repairs; it is not current capability authority.
"""
from __future__ import annotations
import argparse
import ast
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import generate_portable_catalog as generator
from server.unified_mcp.tool_contracts import build_tool_specs

CATALOG = "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json"
ROUTING = "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json"
PORTABLE = "skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json"
QUICK = "skills/tw-market-evidence-agent/references/capability_quick_guide.md"
GUIDES = ("skills/tw-market-evidence-agent/SKILL.md", "docs/agent_usage_guide.md",
          "skills/tw-market-evidence-agent/references/current_limitations.md")
HISTORICAL = ("docs/ai/M8_AI_CAPABILITY_QUICK_GUIDE.md",
              "docs/data_capabilities/m8_source_capability_registry.json")
RUNTIME_INPUTS = ("scripts/m8r_05b_01/planner.py", "scripts/m8r_06_03_production_adapter.py",
                  "scripts/m8r_05c/evidence_projector.py")
BASE_REF = "91458d203ac28fe4ab00c89229ed1320bcb64753"
EXPECTED_TOOLS = {"market_describe_capabilities", "market_validate_request", "market_preview_request",
                  "market_read_result", "market_export_ai_handoff", "market_fetch_evidence"}


def load_snapshot() -> dict:
    def read(path):
        return (ROOT / path).read_text(encoding="utf-8")
    def baseline(path):
        return json.loads(subprocess.check_output(["git", "show", f"{BASE_REF}:{path}"], cwd=ROOT))
    return {
        "catalog": json.loads(read(CATALOG)), "routing": json.loads(read(ROUTING)),
        "portable": json.loads(read(PORTABLE)), "quick": read(QUICK),
        "guides": {path: read(path) for path in GUIDES},
        "catalog_hash": generator.get_file_sha256(ROOT / CATALOG),
        "routing_hash": generator.get_file_sha256(ROOT / ROUTING),
        "catalog_lineage": generator.get_canonical_source_lineage(ROOT / CATALOG),
        "routing_lineage": generator.get_canonical_source_lineage(ROOT / ROUTING),
        "tools": sorted(tool.name for tool in build_tool_specs()),
        "runtime_inputs": {p: read(p) for p in RUNTIME_INPUTS},
        "baseline_catalog": baseline(CATALOG), "baseline_routing": baseline(ROUTING),
    }


def functional_view(document: dict, key: str) -> dict:
    """Permit only the explicitly authorized I2 descriptive fields."""
    result = copy.deepcopy(document)
    for row in result[key]:
        if row.get("capability_id") == "index_futures_context":
            for name in ("description", "known_limitations", "capability_status_source"):
                row.pop(name, None)
    return result


def validate_snapshot(s: dict) -> dict:
    errors = []
    def reject(code, surface):
        item = {"code": code, "surface": surface}
        if item not in errors:
            errors.append(item)
    catalog, routing = s["catalog"], s["routing"]
    expected = generator.generate_portable_json_obj(catalog, s["catalog_hash"], s["catalog_lineage"])
    portable = copy.deepcopy(s["portable"])
    if portable.get("portable_metadata") != expected["portable_metadata"]:
        reject("A4_PORTABLE_LINEAGE_DRIFT", PORTABLE)
    portable.pop("portable_metadata", None)
    content = copy.deepcopy(expected)
    content.pop("portable_metadata", None)
    if portable != content:
        reject("A4_PORTABLE_CATALOG_DRIFT", PORTABLE)
    expected_guide = generator.generate_portable_markdown_text(
        expected, s["catalog_hash"], routing, s["routing_hash"], s["routing_lineage"])
    if s["quick"] != expected_guide:
        reject("A4_GUIDE_CATALOG_ROUTE_DRIFT", QUICK)
    if re.search(r"support status.?`? is authoritative for executability", s["quick"], re.I):
        reject("A4_GUIDE_CATALOG_ROUTE_DRIFT", QUICK)
    capabilities = {r["capability_id"]: r for r in catalog["data_need_capabilities"]}
    for route in routing["routes"]:
        cid = route["capability_id"]
        cap = capabilities.get(cid, {})
        _, effective = generator.route_publication(cap, [route])
        active = "executable subject to" in effective
        # Independently inspect the publication cell, not the generator's full output alone.
        rows = [line for line in s["quick"].splitlines() if line.startswith(f"| `{cid}` |")]
        if len(rows) != 1:
            reject("A4_GUIDE_CATALOG_ROUTE_DRIFT", cid)
            continue
        cells = rows[0].split("|")
        if len(cells) < 6:
            reject("A4_GUIDE_CATALOG_ROUTE_DRIFT", cid)
            continue
        if not active and "executable subject to" in cells[4]:
            reject("A4_BLOCKED_ROUTE_PUBLISHED_EXECUTABLE", cid)
        if active and re.search(r"owner.{0,30}pending|activation pending|plan-only|blocked", cells[4], re.I):
            reject("A4_ACTIVE_ROUTE_PUBLISHED_PENDING", cid)
    if set(s["tools"]) != EXPECTED_TOOLS:
        reject("A4_PUBLIC_MCP_SURFACE_DRIFT", "registered MCP")
    for path, text in s["guides"].items():
        words = " ".join(text.split())
        if path == GUIDES[0] and (set(re.findall(r"\bmarket_[a-z_]+\b", text)) - set(capabilities)) != EXPECTED_TOOLS:
            reject("A4_PUBLIC_MCP_SURFACE_DRIFT", path)
        for required in ("Catalog support != selected route executability", "session_status",
                         "index_futures_context", "CORPORATE_ACTION_COVERAGE_INCOMPLETE",
                         "Security Master", "preview", "provisional", "blocked"):
            if required.casefold() not in words.casefold():
                reject("A4_CURRENT_LIMITATION_DRIFT" if path == GUIDES[2]
                       else "A4_SKILL_GUIDE_CAPABILITY_DRIFT", path + ":" + required)
        if re.search(r"session_status`? (?:is |remains )?(?:currently )?executable", words, re.I):
            reject("A4_CURRENT_LIMITATION_DRIFT" if path == GUIDES[2]
                   else "A4_BLOCKED_ROUTE_PUBLISHED_EXECUTABLE", path)
        for historical in HISTORICAL:
            if historical in text:
                reject("A4_HISTORICAL_GUIDE_PROMOTED_AS_CURRENT", path)
        if re.search(r"activation pending|owner.{0,30}activation pending|activation candidate", words, re.I):
            reject("A4_ACTIVE_ROUTE_PUBLISHED_PENDING", path)
    i2 = [capabilities["index_futures_context"]] + [r for r in routing["routes"]
                                                  if r["capability_id"] == "index_futures_context"]
    for row in i2:
        if re.search(r"activation pending|activation candidate", json.dumps(row), re.I):
            reject("A4_STALE_OWNER_PENDING_PUBLICATION", "index_futures_context")
    for name, key in (("catalog", "data_need_capabilities"), ("routing", "routes")):
        if functional_view(s[name], key) != functional_view(s["baseline_" + name], key):
            reject("A4_CATALOG_SEMANTIC_CHANGE_REQUIRED", name)
    for path, source in s["runtime_inputs"].items():
        literals = [node.value for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)]
        for value in literals:
            if any(Path(p).name in value for p in (PORTABLE, QUICK, *GUIDES)):
                reject("A4_PUBLICATION_AUTHORITY_INVERSION", path)
    return {"status": "FAIL" if errors else "PASS", "authority_kind": "TEST_ACCEPTANCE_ONLY",
            "network": False, "writes": False, "runtime_discovery": False,
            "checks": [f"PUB-{n:02}" for n in range(1, 10)], "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_snapshot(load_snapshot())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        result = {"status": "FAIL", "errors": [{"code": "A4_PUBLICATION_INPUT_INVALID", "surface": type(exc).__name__}]}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2 if args.json else None))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
