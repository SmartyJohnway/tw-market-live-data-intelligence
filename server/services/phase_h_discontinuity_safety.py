"""Pure, fixture-safe Phase H H4 discontinuity derivation.

This module consumes caller-supplied governed H2 and H3 evidence only.  It
does not resolve identities, read artifacts, call sources, or write output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft7Validator

from scripts.validate_phase_h_v3_contracts import (
    validate_corporate_action_context_semantics,
    validate_recent_performance_semantics,
)


class H4DerivationError(ValueError):
    """Deterministic failure for invalid or unusable governed input evidence."""


_ROOT = Path(__file__).resolve().parents[2]
_H2_SCHEMA = json.loads((_ROOT / "schemas" / "corporate_action_context_evidence.v1.schema.json").read_text(encoding="utf-8"))
_H3_SCHEMA = json.loads((_ROOT / "schemas" / "recent_performance_evidence.v1.schema.json").read_text(encoding="utf-8"))
_H4_SCHEMA = json.loads((_ROOT / "schemas" / "discontinuity_safety_evidence.v1.schema.json").read_text(encoding="utf-8"))


def _validate(value: Mapping[str, Any], schema: Mapping[str, Any], code: str) -> None:
    error = next(iter(Draft7Validator(schema).iter_errors(value)), None)
    if error is not None:
        raise H4DerivationError(code)


def _identity(value: Mapping[str, Any]) -> tuple[str, str, str]:
    target = value.get("target")
    if not isinstance(target, Mapping):
        raise H4DerivationError("target_missing")
    identity = (target.get("canonical_target_id"), target.get("market"), target.get("security_code"))
    if not all(isinstance(part, str) and part for part in identity):
        raise H4DerivationError("target_invalid")
    return identity  # type: ignore[return-value]


def _stable_unique(values: Sequence[str]) -> list[str]:
    return sorted({value for value in values if isinstance(value, str) and value})


def _coverage_failure(
    h2: Mapping[str, Any], start: str, end: str,
) -> tuple[list[str], list[dict[str, str | None]], list[str]]:
    coverage = h2["coverage"]
    declared = set(coverage["declared_event_subtypes"])
    covered = set(coverage["covered_event_subtypes"])
    uncovered = set(coverage["uncovered_event_subtypes"])
    if not declared or covered & uncovered or declared != covered | uncovered:
        raise H4DerivationError("h2_coverage_scope_invalid")
    window = coverage["requested_window"]
    failures: list[dict[str, str | None]] = []
    caveats: list[str] = []
    if window["start"] > start or window["end"] < end:
        failures.append({"failure_type": "missing_required_evidence", "evidence_reference": None})
        caveats.append("h2_coverage_window_misaligned")
    if h2["status"] == "source_failed" or not coverage["retrieval_succeeded"] or not coverage["source_contract_validated"]:
        failures.append({"failure_type": "source_failed", "evidence_reference": None})
    if h2["status"] == "binding_failed" or not coverage["exact_target_search_succeeded"]:
        failures.append({"failure_type": "binding_failed", "evidence_reference": None})
    if h2["status"] in {"unsupported", "not_applicable"} or not coverage["declared_scope_complete"]:
        failures.append({"failure_type": "missing_required_evidence", "evidence_reference": None})
    return sorted(uncovered), failures, caveats


def derive_discontinuity_safety(
    *,
    h2_evidence: Mapping[str, Any],
    h3_evidence: Mapping[str, Any],
    h2_evidence_reference: str,
    h3_evidence_reference: str,
    event_evidence_references: Mapping[int, str] | None = None,
    official_reference_evidence_references: Mapping[int, str] | None = None,
) -> dict[str, Any]:
    """Derive one schema-valid H4 safety artifact without I/O or source access."""
    _validate(h2_evidence, _H2_SCHEMA, "h2_schema_invalid")
    _validate(h3_evidence, _H3_SCHEMA, "h3_schema_invalid")
    try:
        validate_corporate_action_context_semantics(h2_evidence)
    except ValueError as exc:
        raise H4DerivationError("h2_semantics_invalid") from exc
    try:
        validate_recent_performance_semantics(h3_evidence)
    except ValueError as exc:
        raise H4DerivationError("h3_semantics_invalid") from exc
    if not all(isinstance(ref, str) and ref for ref in (h2_evidence_reference, h3_evidence_reference)):
        raise H4DerivationError("input_evidence_reference_invalid")
    if _identity(h2_evidence) != _identity(h3_evidence):
        raise H4DerivationError("target_identity_mismatch")

    available = [baseline for baseline in h3_evidence["baselines"] if baseline["status"] == "available"]
    if len(available) != 1:
        raise H4DerivationError("h3_requires_exactly_one_available_baseline")
    baseline = available[0]
    start, end = baseline["start_observation_date"], baseline["end_observation_date"]
    if not isinstance(start, str) or not isinstance(end, str) or start >= end:
        raise H4DerivationError("h3_comparison_window_invalid")

    uncovered, failures, caveats = _coverage_failure(h2_evidence, start, end)
    coverage = h2_evidence["coverage"]
    relevant = sorted(coverage["declared_event_subtypes"])
    covered = sorted(coverage["covered_event_subtypes"])
    failed_sources = list(coverage["failed_source_families"])

    effective_events: list[tuple[int, Mapping[str, Any], str]] = []
    for index, event in enumerate(h2_evidence["events"]):
        lifecycle = event["event_lifecycle"]
        effective_date = event["effective_date"]
        if lifecycle in {"effective", "unresolved"} and effective_date is None:
            reference = (event_evidence_references or {}).get(index)
            if not reference:
                raise H4DerivationError("event_evidence_reference_missing")
            failures.append({"failure_type": "unresolved_effective_timing", "evidence_reference": reference})
            continue
        if lifecycle == "effective" and start < effective_date <= end:
            reference = (event_evidence_references or {}).get(index)
            if not reference:
                raise H4DerivationError("effective_event_reference_missing")
            if event["revision_relation"]["status"] == "unresolved":
                failures.append({"failure_type": "unresolved_revision", "evidence_reference": reference})
            else:
                effective_events.append((index, event, reference))
        elif lifecycle in {"announced", "scheduled", "unresolved"} and effective_date is not None and start < effective_date <= end:
            reference = (event_evidence_references or {}).get(index)
            if not reference:
                raise H4DerivationError("event_evidence_reference_missing")
            failures.append({"failure_type": "unresolved_effective_timing", "evidence_reference": reference})
        elif lifecycle in {"corrected", "amended", "cancelled"} and effective_date is None:
            reference = (event_evidence_references or {}).get(index)
            if not reference:
                raise H4DerivationError("event_evidence_reference_missing")
            failures.append({"failure_type": "missing_required_evidence", "evidence_reference": reference})
        elif lifecycle in {"corrected", "amended", "cancelled"} and effective_date is not None and start < effective_date <= end:
            reference = (event_evidence_references or {}).get(index)
            if not reference:
                raise H4DerivationError("event_evidence_reference_missing")
            if event["revision_relation"]["status"] == "unresolved":
                failures.append({"failure_type": "unresolved_revision", "evidence_reference": reference})
            else:
                failures.append({"failure_type": "missing_required_evidence", "evidence_reference": reference})

    citations = _stable_unique(
        list(h2_evidence.get("citation_ids", []))
        + list(h3_evidence.get("citation_ids", []))
        + [citation for event in h2_evidence["events"] for citation in event.get("citation_ids", [])]
    )
    event_refs = [reference for _, _, reference in effective_events]
    reference_refs: list[str] = []
    if failures or uncovered:
        state, guard = "coverage_incomplete", "CORPORATE_ACTION_COVERAGE_INCOMPLETE"
    elif effective_events:
        missing_reference = [index for index, event, _ in effective_events if event["official_reference_price"]["state"] != "value"]
        if missing_reference:
            state, guard = "discontinuity_detected_reference_unavailable", "NOT_COMPARABLE_AS_ORDINARY_RETURN"
        else:
            for index, _, _ in effective_events:
                reference = (official_reference_evidence_references or {}).get(index)
                if not reference:
                    raise H4DerivationError("official_reference_evidence_reference_missing")
                reference_refs.append(reference)
            state, guard = "discontinuity_detected_reference_available", "PRICE_BASIS_DISCONTINUITY_REFERENCE_AVAILABLE"
    else:
        state, guard = "no_material_discontinuity_detected", "none"

    output: dict[str, Any] = {
        "schema_version": "discontinuity_safety_evidence.v1",
        "target": dict(zip(("canonical_target_id", "market", "security_code"), _identity(h2_evidence))),
        "state": state,
        "comparison_window": {
            "start_observation_date": start,
            "end_observation_date": end,
            "start_price_basis": "official_close",
            "end_price_basis": "official_close",
        },
        "relevant_event_subtypes": relevant,
        "covered_event_subtypes": covered,
        "uncovered_event_subtypes": uncovered,
        "failed_source_families": _stable_unique(failed_sources),
        "upstream_failures": failures,
        "effective_event_evidence_references": _stable_unique(event_refs),
        "official_reference_evidence_references": _stable_unique(reference_refs),
        "input_evidence_references": _stable_unique([h2_evidence_reference, h3_evidence_reference]),
        "raw_metric_status": "available",
        "ordinary_return_interpretation": "allowed" if state == "no_material_discontinuity_detected" else "blocked",
        "interpretation_guard": guard,
        "deterministic_rule_version": "phase_h_discontinuity_safety.v1",
        "citation_ids": citations,
        "caveats": _stable_unique(caveats),
    }
    _validate(output, _H4_SCHEMA, "h4_output_schema_invalid")
    return output
