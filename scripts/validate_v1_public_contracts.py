#!/usr/bin/env python3
"""Offline release gate for the V1 public-contract inventory."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPECTED_TOOLS = (
    "market_describe_capabilities",
    "market_validate_request",
    "market_preview_request",
    "market_read_result",
    "market_export_ai_handoff",
    "market_fetch_evidence",
)


def readme_current_product_truth_failures(
    readme_path: Path, *, current_product_version: str = "1.0.0-rc.1"
) -> list[str]:
    """Return contradictions that would misdescribe the current V1 product."""
    text = readme_path.read_text(encoding="utf-8")
    failures: list[str] = []
    if "Persistent Watchlists" not in text:
        failures.append("readme_missing_persistent_watchlist_support")
    if re.search(r"no[^\\n.]*persistent watchlist", text, flags=re.IGNORECASE):
        failures.append("readme_persistent_watchlist_contradiction")
    release_patterns_by_version = {
        "1.0.0-rc.1": (
            r"1\.0\.0-rc\.1",
            r"v0\.1\.0",
            r"latest\s+prerelease\s+(?:is|=|:)\s+[`*_]*v1\.0\.0-rc\.1",
            r"final\s+[`*_]*v1\.0\.0[`*_]*\s+(?:is\s+)?not\s+released",
            r"phase\s+g\s+(?:has\s+)?not\s+started",
        ),
        "1.0.0": (
            r"(?:productversion|product\s+version|version)\s*(?:=|:|records)?\s+[`*_]*1\.0\.0[`*_]*",
            r"v1\.0\.0-rc\.1",
            r"v0\.1\.0",
            r"latest\s+prerelease\s+(?:is|=|:)\s+[`*_]*v1\.0\.0-rc\.1",
            r"final\s+[`*_]*v1\.0\.0[`*_]*(?:\s+(?:is|has))?\s+not\s+(?:yet\s+)?(?:been\s+)?published",
            r"phase\s+g\s+(?:has\s+)?not\s+started",
        ),
    }
    required_patterns = release_patterns_by_version.get(current_product_version)
    if required_patterns is None:
        failures.append("readme_release_status_version_unsupported")
    elif any(not re.search(pattern, text, flags=re.IGNORECASE) for pattern in required_patterns):
        failures.append(
            "readme_published_rc_release_status_incomplete"
            if current_product_version == "1.0.0-rc.1"
            else "readme_final_promotion_release_status_incomplete"
        )
    if re.search(
        r"no\s+rc\s+tag\s+or\s+github\s+prerelease\s+has\s+been\s+created",
        text,
        flags=re.IGNORECASE,
    ):
        failures.append("readme_stale_prepublication_release_status")
    return failures


def _fail(code: str, detail: object | None = None) -> int:
    print(json.dumps({"status": "FAIL", "reason_code": code, "detail": detail}))
    return 1


def main() -> int:
    from scripts.product_version import product_version
    from server.main import app
    from server.unified_mcp import LOCAL_SERVICE_CONTRACT_VERSION
    from server.unified_mcp.tool_contracts import build_tool_specs

    inventory_path = ROOT / "docs/contracts/v1_public_contracts.json"
    try:
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _fail("v1_public_contract_inventory_unavailable", str(exc))

    if inventory.get("product_version") != product_version():
        return _fail("product_version_inventory_drift")
    if app.version != LOCAL_SERVICE_CONTRACT_VERSION:
        return _fail("local_service_contract_version_drift")
    tools = tuple(tool.name for tool in build_tool_specs())
    if tools != EXPECTED_TOOLS:
        return _fail("mcp_tool_inventory_drift", tools)
    if inventory.get("public_api", {}).get("mcp_tools") != list(EXPECTED_TOOLS):
        return _fail("mcp_tool_contract_inventory_drift")
    readme_failures = readme_current_product_truth_failures(
        ROOT / "README.md", current_product_version=product_version()
    )
    if readme_failures:
        return _fail("readme_current_product_truth_drift", readme_failures)

    for relative in inventory.get("public_api", {}).get("local_service", {}).get("schemas", []):
        schema_path = ROOT / relative
        if not schema_path.exists():
            schema_path = ROOT / "docs/contracts" / relative
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.validators.validator_for(schema).check_schema(schema)
        except (OSError, json.JSONDecodeError, jsonschema.exceptions.SchemaError) as exc:
            return _fail("public_contract_schema_invalid", {"path": relative, "detail": str(exc)})

    print(json.dumps({"status": "PASS", "product_version": product_version(), "tool_count": len(tools)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
