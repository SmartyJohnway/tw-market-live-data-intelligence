"""Deterministic Unified Request contract-version resolution.

V2 remains the preferred production Request authority. V3 is available only
for passive validation and preview. Execution remains limited to V1/V2 until
a later Owner-authorized activation gate.
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

# Passive V3 compatibility is explicit: V3 uses its frozen planning pair while
# current execution remains limited to V1/V2 until a later activation gate.
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
PASSIVE_REQUEST_SCHEMA_VERSIONS = frozenset(REQUEST_SCHEMA_PATHS)
EXECUTION_REQUEST_SCHEMA_VERSIONS = frozenset((
    "unified_market_evidence_request.v1",
    "unified_market_evidence_request.v2",
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
