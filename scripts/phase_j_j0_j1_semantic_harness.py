"""Network-free semantic checker for Phase J scenario acceptance fixtures.

This is test/governance support, not a production execution path.  It checks
typed facts projected from existing Result V3, Audit V3, and handoff artifacts;
it does not generate evidence or invoke any market source.
"""

from __future__ import annotations

from typing import Any


def _resolve_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split(".") if path else []:
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as exc:
                raise AssertionError(f"path {path!r} cannot resolve at {part!r}") from exc
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise AssertionError(f"path {path!r} cannot resolve at {part!r}")
    return current


def _check_assertion(assertion: dict[str, Any], artifacts: dict[str, Any]) -> None:
    context = assertion["context"]
    actual = _resolve_path(artifacts[context], assertion["path"])
    operator = assertion["operator"]
    expected = assertion.get("value")
    if operator == "equals":
        ok = actual == expected
    elif operator == "not_equals":
        ok = actual != expected
    elif operator == "contains":
        ok = expected in actual
    elif operator == "not_contains":
        ok = expected not in actual
    elif operator == "is_true":
        ok = actual is True
    elif operator == "is_false":
        ok = actual is False
    elif operator == "is_empty":
        ok = actual in (None, "", [], {})
    elif operator == "is_non_empty":
        ok = actual not in (None, "", [], {})
    else:
        raise AssertionError(f"unsupported semantic operator: {operator}")
    if not ok:
        raise AssertionError(
            f"{assertion.get('assertion_id', assertion['path'])}: expected "
            f"{context}.{assertion['path']} {operator} {expected!r}; got {actual!r}"
        )


def evaluate_scenario(scenario: dict[str, Any], fixture: dict[str, Any]) -> list[str]:
    """Check one synthetic or replayed semantic projection against its scenario.

    The fixture supplies normalized, bounded facts alongside the actual public
    artifact envelopes. It is explicitly acceptance-only and never a source
    payload. Handoff checks are substring guards, not golden prose comparisons.
    """
    if fixture.get("fixture_kind") not in {"synthetic", "governed_replay"}:
        raise AssertionError("fixture must identify synthetic or governed_replay provenance")
    if fixture.get("scenario_id") != scenario.get("scenario_id"):
        raise AssertionError("fixture scenario_id does not match registry row")
    artifacts = {
        "result": fixture.get("result_v3"),
        "audit": fixture.get("audit_v3"),
        "handoff": fixture.get("handoff"),
        "facts": fixture.get("semantic_facts"),
    }
    if not isinstance(artifacts["result"], dict) or artifacts["result"].get("schema_version") != "unified_market_evidence_result.v3":
        raise AssertionError("fixture must bind a Result V3 artifact")
    if not isinstance(artifacts["audit"], dict) or artifacts["audit"].get("schema_version") != "unified_market_evidence_audit_package.v3":
        raise AssertionError("fixture must bind an Audit V3 artifact")
    if artifacts["result"].get("result_id") != artifacts["audit"].get("result_id"):
        raise AssertionError("Result V3 and Audit V3 result identity mismatch")
    facts = artifacts["facts"]
    if facts.get("evidence_bearing") is True:
        if facts.get("citation_present") is not True:
            raise AssertionError("evidence-bearing fixture lacks a citation")
        if facts.get("lineage_continuous") is not True:
            raise AssertionError("evidence-bearing fixture lacks continuous lineage")
        if not artifacts["audit"].get("artifact_inventory"):
            raise AssertionError("evidence-bearing fixture lacks an Audit V3 artifact reference")
    if not isinstance(artifacts["handoff"], str):
        raise AssertionError("fixture must include a handoff projection")
    if not isinstance(artifacts["facts"], dict):
        raise AssertionError("fixture must include normalized semantic facts")

    checked: list[str] = []
    for assertion in scenario.get("expected_semantic_assertions", []):
        _check_assertion(assertion, artifacts)
        checked.append(assertion["assertion_id"])

    handoff_lower = artifacts["handoff"].casefold()
    for forbidden in scenario.get("forbidden_claims", []):
        marker = forbidden.get("handoff_text_marker")
        if marker and marker.casefold() in handoff_lower:
            raise AssertionError(f"forbidden handoff claim present: {forbidden['claim_id']}")
    return checked
