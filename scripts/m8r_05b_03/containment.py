"""Evidence output containment; raw/session/credential-like fields are rejected."""
from __future__ import annotations

from typing import Any

from .errors import OrchestrationError

_FORBIDDEN = {"raw_payload", "raw_response", "cookie", "cookies", "authorization", "access_token", "refresh_token", "session_id", "set_cookie"}


def assert_contained(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in _FORBIDDEN:
                raise OrchestrationError("evidence_containment_violation")
            assert_contained(child)
    elif isinstance(value, list):
        for child in value:
            assert_contained(child)


def contained_evidence(raw: object, expected_contract: str) -> dict:
    if not isinstance(raw, dict):
        raise OrchestrationError("executor_result_invalid")
    evidence = raw.get("evidence")
    if raw.get("status") != "success" or not isinstance(evidence, dict) or not evidence:
        raise OrchestrationError("incomplete_evidence")
    if raw.get("evidence_contract") != expected_contract:
        raise OrchestrationError("expected_evidence_contract_mismatch")
    assert_contained(evidence)
    return evidence
