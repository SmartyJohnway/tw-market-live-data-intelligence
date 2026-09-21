"""Non-production semantic validators for the frozen Phase H V3 candidate.

JSON Schema Draft-07 cannot express sibling arithmetic or array set equality.
These pure, zero-network validators close those exact-contract gaps without
activating runtime, sources, planning, execution, or persistence.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from math import isclose
from pathlib import Path
from typing import Any


class PhaseHV3ContractValidationError(ValueError):
    """A candidate Phase H V3 evidence object violates a frozen invariant."""


def _fail(code: str) -> None:
    raise PhaseHV3ContractValidationError(code)


RETURN_PCT_ABS_TOLERANCE = 1e-9
"""Absolute tolerance for serialized JSON return percentages; no rounding."""


H1_DECLARED_STATUS_TYPES = {
    "attention", "disposition", "changed_trading_method", "suspension", "resumption",
}


def _validate_declared_scope(
    coverage: Mapping[str, Any], declared_key: str, covered_key: str, uncovered_key: str,
    *, required_declared: set[str] | None = None,
) -> None:
    declared = set(coverage.get(declared_key) or [])
    covered = set(coverage.get(covered_key) or [])
    uncovered = set(coverage.get(uncovered_key) or [])
    if not declared or covered & uncovered or declared != covered | uncovered:
        _fail("declared_coverage_scope_mismatch")
    if required_declared is not None and declared != required_declared:
        _fail("declared_coverage_scope_not_canonical")


def validate_trading_status_context_semantics(value: Mapping[str, Any]) -> None:
    """H0-C scope is all five canonical types because Request V3 has no selector."""
    coverage = value.get("coverage")
    if not isinstance(coverage, Mapping):
        _fail("missing_h1_coverage")
    _validate_declared_scope(
        coverage, "declared_status_types", "covered_status_types", "uncovered_status_types",
        required_declared=H1_DECLARED_STATUS_TYPES,
    )
    if value.get("status") == "no_evidence_in_covered_scope":
        required = (
            coverage.get("declared_scope_complete") is True,
            not coverage.get("uncovered_status_types"),
            not coverage.get("failed_source_families"),
            coverage.get("retrieval_succeeded") is True,
            coverage.get("source_contract_validated") is True,
            coverage.get("exact_target_search_succeeded") is True,
        )
        if not all(required):
            _fail("h1_no_evidence_not_complete_exact_scope")


def validate_corporate_action_context_semantics(value: Mapping[str, Any]) -> None:
    """H0-D coverage is explicit; unavailable routes remain declared and uncovered."""
    coverage = value.get("coverage")
    if not isinstance(coverage, Mapping):
        _fail("missing_h2_coverage")
    _validate_declared_scope(
        coverage, "declared_event_subtypes", "covered_event_subtypes", "uncovered_event_subtypes",
    )
    if value.get("status") == "no_evidence_in_covered_scope":
        required = (
            coverage.get("declared_scope_complete") is True,
            not coverage.get("uncovered_event_subtypes"),
            not coverage.get("failed_source_families"),
            coverage.get("retrieval_succeeded") is True,
            coverage.get("source_contract_validated") is True,
            coverage.get("exact_target_search_succeeded") is True,
        )
        if not all(required):
            _fail("h2_no_evidence_not_complete_exact_scope")


def validate_recent_performance_semantics(value: Mapping[str, Any]) -> None:
    """Enforce H0-E precedence, N+1 cardinality, and observation accounting."""

    requested = value.get("requested_observations")
    valid = value.get("valid_observation_count")
    missing = value.get("missing_observation_count")
    observations = value.get("observations")
    end = value.get("governed_end_observation")
    baselines = value.get("baselines")
    available = value.get("available_baselines")
    unavailable = value.get("unavailable_baselines")
    status = value.get("coverage_status")

    if not isinstance(requested, int) or isinstance(requested, bool) or not 1 <= requested <= 20:
        _fail("invalid_requested_observations")
    if not isinstance(valid, int) or isinstance(valid, bool) or not isinstance(missing, int) or isinstance(missing, bool):
        _fail("invalid_observation_accounting")
    if valid + missing != requested:
        _fail("observation_accounting_mismatch")
    if not isinstance(observations, list) or len(observations) != valid:
        _fail("valid_observation_count_mismatch")
    dates = [item.get("trade_date") for item in observations if isinstance(item, Mapping)]
    if len(dates) != len(set(dates)):
        _fail("duplicate_observation_trade_date")
    if dates != sorted(dates):
        _fail("observations_not_deterministically_ordered")
    if observations:
        if value.get("first_observation_date") != dates[0] or value.get("last_observation_date") != dates[-1]:
            _fail("observation_date_bounds_mismatch")
    elif value.get("first_observation_date") is not None or value.get("last_observation_date") is not None:
        _fail("empty_observation_date_bounds_must_be_null")

    if not isinstance(baselines, list) or not baselines:
        _fail("baselines_required")
    available_from_records: set[int] = set()
    unavailable_from_records: set[int] = set()
    for baseline in baselines:
        if not isinstance(baseline, Mapping):
            _fail("invalid_baseline_record")
        lookback = baseline.get("lookback_trading_days")
        required = baseline.get("required_distinct_close_count")
        actual = baseline.get("actual_distinct_close_count")
        baseline_status = baseline.get("status")
        if required != lookback + 1:
            _fail("baseline_n_plus_one_mismatch")
        if baseline_status == "available":
            available_from_records.add(lookback)
            if not isinstance(end, Mapping) or actual != required or baseline.get("recent_return_pct") is None:
                _fail("available_baseline_missing_required_evidence")
            end_date = end.get("trade_date")
            if end_date in dates:
                _fail("governed_end_duplicate_observation_date")
            if baseline.get("end_observation_date") != end_date:
                _fail("baseline_end_observation_identity_mismatch")
            if not isinstance(lookback, int) or len(observations) < lookback:
                _fail("baseline_insufficient_ordered_observations")
            start = observations[-lookback]
            if baseline.get("start_observation_date") != start.get("trade_date"):
                _fail("baseline_start_observation_identity_mismatch")
            if baseline.get("start_observation_date") >= end_date:
                _fail("baseline_chronology_invalid")
            close_start = start.get("close")
            close_end = end.get("close")
            if not isinstance(close_start, (int, float)) or isinstance(close_start, bool) or close_start == 0:
                _fail("baseline_start_close_invalid")
            if not isinstance(close_end, (int, float)) or isinstance(close_end, bool):
                _fail("baseline_end_close_invalid")
            expected_return = (close_end - close_start) / abs(close_start) * 100
            if not isclose(baseline["recent_return_pct"], expected_return, abs_tol=RETURN_PCT_ABS_TOLERANCE, rel_tol=0.0):
                _fail("baseline_return_arithmetic_mismatch")
        else:
            unavailable_from_records.add(lookback)
            if baseline.get("recent_return_pct") is not None:
                _fail("unavailable_baseline_has_return")
    if set(available or []) != available_from_records or set(unavailable or []) != unavailable_from_records:
        _fail("baseline_summary_mismatch")

    if status == "complete":
        if missing != 0 or valid != requested or end is None or not available_from_records or unavailable_from_records:
            _fail("complete_coverage_invariant")
    elif status == "partial":
        if not available_from_records or (missing == 0 and not unavailable_from_records):
            _fail("partial_coverage_invariant")
    elif status == "insufficient":
        if valid == 0 or available_from_records:
            _fail("insufficient_coverage_invariant")
    elif status == "unavailable":
        if valid != 0 or available_from_records:
            _fail("unavailable_coverage_invariant")
    elif status in {"source_failed", "binding_failed", "unsupported", "not_applicable"}:
        if available_from_records:
            _fail("failure_or_nonapplicable_has_available_baseline")
    else:
        _fail("unknown_coverage_status")

    volume = value.get("volume_context")
    if isinstance(volume, Mapping) and volume.get("current_volume_basis") == "intraday_cumulative":
        if volume.get("comparison_alignment") != "partial_session_vs_completed_sessions":
            _fail("intraday_volume_alignment_mismatch")


def validate_discontinuity_safety_semantics(value: Mapping[str, Any]) -> None:
    """Enforce H0-F subtype coverage sets and interpretation-state legality."""

    relevant = set(value.get("relevant_event_subtypes") or [])
    covered = set(value.get("covered_event_subtypes") or [])
    uncovered = set(value.get("uncovered_event_subtypes") or [])
    failed_sources = value.get("failed_source_families") or []
    upstream_failures = value.get("upstream_failures") or []
    effective_events = value.get("effective_event_evidence_references") or []
    references = value.get("official_reference_evidence_references") or []
    state = value.get("state")
    raw_status = value.get("raw_metric_status")
    permission = value.get("ordinary_return_interpretation")
    guard = value.get("interpretation_guard")
    window = value.get("comparison_window")

    if not isinstance(window, Mapping) or window.get("start_observation_date") >= window.get("end_observation_date"):
        _fail("comparison_window_chronology_invalid")

    if covered & uncovered or relevant != covered | uncovered:
        _fail("relevant_coverage_set_mismatch")
    has_coverage_failure = bool(uncovered or failed_sources or upstream_failures)

    if state == "no_material_discontinuity_detected":
        if has_coverage_failure or effective_events or raw_status != "available" or permission != "allowed" or guard != "none":
            _fail("no_material_discontinuity_illegal")
    elif state == "discontinuity_detected_reference_available":
        if has_coverage_failure or not effective_events or not references or permission != "blocked" or guard != "PRICE_BASIS_DISCONTINUITY_REFERENCE_AVAILABLE":
            _fail("reference_available_state_illegal")
    elif state == "discontinuity_detected_reference_unavailable":
        if has_coverage_failure or not effective_events or references or permission != "blocked" or guard != "NOT_COMPARABLE_AS_ORDINARY_RETURN":
            _fail("reference_unavailable_state_illegal")
    elif state == "coverage_incomplete":
        if not has_coverage_failure or permission != "blocked" or guard != "CORPORATE_ACTION_COVERAGE_INCOMPLETE":
            _fail("coverage_incomplete_state_illegal")
    else:
        _fail("unknown_discontinuity_state")


def validate_h2_h3_h4_cross_evidence(
    h2: Mapping[str, Any], h3: Mapping[str, Any], h4: Mapping[str, Any],
) -> None:
    """Pure fixture-level consistency check; production artifact loading stays deferred."""
    validate_corporate_action_context_semantics(h2)
    validate_recent_performance_semantics(h3)
    validate_discontinuity_safety_semantics(h4)
    available = [item for item in h3.get("baselines", []) if item.get("status") == "available"]
    if len(available) != 1:
        _fail("cross_evidence_requires_one_available_baseline")
    baseline = available[0]
    window = h4["comparison_window"]
    if (window.get("start_observation_date"), window.get("end_observation_date")) != (
        baseline.get("start_observation_date"), baseline.get("end_observation_date"),
    ):
        _fail("h4_h3_window_mismatch")
    h2_coverage = h2["coverage"]
    if set(h4.get("covered_event_subtypes") or []) - set(h2_coverage.get("covered_event_subtypes") or []):
        _fail("h4_h2_covered_scope_contradiction")
    if set(h4.get("uncovered_event_subtypes") or []) - set(h2_coverage.get("uncovered_event_subtypes") or []):
        _fail("h4_h2_uncovered_scope_contradiction")


def main() -> None:
    """Validate the repository-contained non-authoritative H0-G samples."""
    root = Path(__file__).resolve().parents[1]
    examples = json.loads(
        (root / "tests" / "fixtures" / "phase_h_contract_v3" / "contract_examples.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (root / "docs" / "governance" / "phase_h" / "PHASE_H_H0_G_V3_SCHEMA_FREEZE_MANIFEST.json").read_text(encoding="utf-8")
    )
    for section in ("semantic_inputs", "v3_normative_artifacts", "protected_v1_v2_authority"):
        for item in manifest[section]:
            path = root / item["path"]
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != item["sha256"] or len(content) != item["bytes"]:
                _fail(f"manifest_integrity_mismatch:{item['path']}")
    validate_trading_status_context_semantics(examples["h1_attention_available"])
    validate_trading_status_context_semantics(examples["h1_no_evidence_complete"])
    validate_corporate_action_context_semantics(examples["h2_preannouncement_and_final"])
    for key in ("h3_1d", "h3_5d", "h3_20d"):
        validate_recent_performance_semantics(examples[key])
    for key in ("h4_no_material", "h4_reference_available", "h4_reference_unavailable", "h4_coverage_incomplete"):
        validate_discontinuity_safety_semantics(examples[key])
    h4 = dict(examples["h4_coverage_incomplete"])
    h4["comparison_window"] = {
        **h4["comparison_window"],
        "start_observation_date": examples["h3_5d"]["baselines"][0]["start_observation_date"],
        "end_observation_date": examples["h3_5d"]["baselines"][0]["end_observation_date"],
    }
    validate_h2_h3_h4_cross_evidence(examples["h2_preannouncement_and_final"], examples["h3_5d"], h4)
    print("phase_h_v3_contracts: PASS")


if __name__ == "__main__":
    main()
