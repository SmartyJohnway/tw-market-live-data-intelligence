"""Deterministic Unified Request contract-version resolution.

V3 is the preferred production Request/Result authority after H-ACT-V3.
V1 and V2 remain accepted compatibility contracts. Runtime executability is
still governed by the version-specific Catalog/Route pair and normal
authorization/execute-once controls; promotion does not activate new routes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
REQUEST_SCHEMA_PATHS = {
    "unified_market_evidence_request.v1": (
        ROOT / "schemas" / "unified_market_evidence_request.v1.schema.json"
    ),
    "unified_market_evidence_request.v2": (
        ROOT / "schemas" / "unified_market_evidence_request.v2.schema.json"
    ),
    "unified_market_evidence_request.v3": (
        ROOT / "schemas" / "unified_market_evidence_request.v3.schema.json"
    ),
}

# Each declared Request version keeps its frozen planning pair. V3 is the
# current preferred authority; V1/V2 remain compatibility authorities.
REQUEST_CAPABILITY_CATALOG_PATHS = {
    "unified_market_evidence_request.v1": ROOT / "docs" / "data_capabilities" / "unified_market_evidence_capability_catalog.v2.json",
    "unified_market_evidence_request.v2": ROOT / "docs" / "data_capabilities" / "unified_market_evidence_capability_catalog.v2.json",
    "unified_market_evidence_request.v3": ROOT / "docs" / "data_capabilities" / "unified_market_evidence_capability_catalog.v3.json",
}
REQUEST_ROUTING_MATRIX_PATHS = {
    "unified_market_evidence_request.v1": ROOT / "docs" / "data_capabilities" / "m8r_05b_capability_to_executor_routing_matrix.v2.json",
    "unified_market_evidence_request.v2": ROOT / "docs" / "data_capabilities" / "m8r_05b_capability_to_executor_routing_matrix.v2.json",
    "unified_market_evidence_request.v3": ROOT / "docs" / "data_capabilities" / "m8r_05b_capability_to_executor_routing_matrix.v3.json",
}
PREFERRED_REQUEST_SCHEMA_VERSION = "unified_market_evidence_request.v3"
PREFERRED_RESULT_SCHEMA_VERSION = "unified_market_evidence_result.v3"
PREFERRED_AUDIT_SCHEMA_VERSION = "unified_market_evidence_audit_package.v3"

PASSIVE_REQUEST_SCHEMA_VERSIONS = frozenset(REQUEST_SCHEMA_PATHS)
EXECUTION_REQUEST_SCHEMA_VERSIONS = frozenset((
    "unified_market_evidence_request.v1",
    "unified_market_evidence_request.v2",
    "unified_market_evidence_request.v3",
))


class UnsupportedRequestSchemaVersion(ValueError):
    """Raised when a caller did not declare one of the governed versions."""


def resolve_request_schema(request: Mapping[str, Any]) -> dict[str, Any]:
    """Load exactly the schema declared by ``request.schema_version``.

    The error is deliberately version-specific so callers fail closed before
    attempting any identity, capability, routing, or network work.
    """

    version = request.get("schema_version") if isinstance(request, Mapping) else None
    path = REQUEST_SCHEMA_PATHS.get(version)
    if path is None:
        raise UnsupportedRequestSchemaVersion("unsupported_request_schema_version")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_planning_authority_paths(schema_version: str) -> tuple[Path, Path]:
    """Return the one frozen catalog/routing pair for a declared Request."""
    catalog = REQUEST_CAPABILITY_CATALOG_PATHS.get(schema_version)
    routing = REQUEST_ROUTING_MATRIX_PATHS.get(schema_version)
    if catalog is None or routing is None:
        raise UnsupportedRequestSchemaVersion("unsupported_request_schema_version")
    return catalog, routing
