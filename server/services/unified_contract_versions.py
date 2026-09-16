"""Dormant, deterministic Unified Request schema resolution.

This module intentionally has no current-runtime authority side effect.  The
V1 Local Service continues to select its V1 contract until the Phase G
activation commit.  Callers that opt into version-aware validation must select
the schema from the request's declared ``schema_version``; no trial fallback is
permitted.
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
}


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
