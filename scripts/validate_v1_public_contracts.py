#!/usr/bin/env python3
"""Offline release gate for the V1 public-contract inventory."""

from __future__ import annotations

import json
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
