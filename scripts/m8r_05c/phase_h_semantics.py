"""Fail-closed semantic checks for typed Phase H trading-status artifacts."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


STATUS_TYPES = {
    "attention", "disposition", "changed_trading_method", "suspension", "resumption",
}
_SCALAR_TYPES = {str: "string", int: "number", float: "number", bool: "boolean", type(None): "null"}


def _fail(code: str) -> None:
    raise ValueError(code)


def has_trading_status_evidence(value: Mapping[str, Any]) -> bool:
    """Native facts count as evidence without changing the legacy item count."""
    return bool(value.get("items")) or bool(value.get("native_observations"))


def validate_trading_status_context_semantics(value: Mapping[str, Any]) -> None:
    """Validate H1 v1/v2 cross-field coverage and native-observation semantics."""
    coverage = value.get("coverage")
    if not isinstance(coverage, Mapping):
        _fail("missing_h1_coverage")
    declared = set(coverage.get("declared_status_types") or [])
    covered = set(coverage.get("covered_status_types") or [])
    uncovered = set(coverage.get("uncovered_status_types") or [])
    if not declared or covered & uncovered or declared != covered | uncovered:
        _fail("declared_coverage_scope_mismatch")
    if declared != STATUS_TYPES:
        _fail("declared_coverage_scope_not_canonical")

    items = value.get("items")
    if not isinstance(items, list):
        _fail("h1_items_invalid")
    item_types = {item.get("status_type") for item in items if isinstance(item, Mapping)}
    if len(item_types) != len(items) or not item_types.issubset(covered):
        _fail("h1_canonical_item_not_covered")

    if value.get("status") == "no_evidence_in_covered_scope":
        if has_trading_status_evidence(value):
            _fail("h1_evidence_conflicts_with_no_evidence")
        required = (
            not uncovered,
            not coverage.get("failed_source_families"),
            coverage.get("declared_scope_complete") is True,
            coverage.get("retrieval_succeeded") is True,
            coverage.get("source_contract_validated") is True,
            coverage.get("exact_target_search_succeeded") is True,
        )
        if not all(required):
            _fail("h1_no_evidence_not_complete_exact_scope")

    if value.get("schema_version") != "trading_status_context_evidence.v2":
        return

    observations = value.get("native_observations")
    if not isinstance(observations, list):
        _fail("h1_native_observations_invalid")
    if value.get("native_observation_count") != len(observations):
        _fail("h1_native_observation_count_mismatch")
    parent_citations = set(value.get("citation_ids") or [])
    for observation in observations:
        if not isinstance(observation, Mapping):
            _fail("h1_native_observation_invalid")
        if observation.get("semantic_status") != "unresolved":
            _fail("h1_native_semantics_must_remain_unresolved")
        if not isinstance(observation.get("semantic_caveat"), str) or not observation["semantic_caveat"].strip():
            _fail("h1_native_semantic_caveat_required")
        if not isinstance(observation.get("source_record_date"), str):
            _fail("h1_native_source_record_date_required")
        citations = observation.get("citation_ids")
        if not isinstance(citations, list) or not citations or not set(citations).issubset(parent_citations):
            _fail("h1_native_citation_lineage_invalid")
        source_value = observation.get("source_native_value")
        actual_type = _SCALAR_TYPES.get(type(source_value))
        if actual_type is None or observation.get("source_native_value_type") != actual_type:
            _fail("h1_native_value_type_mismatch")

    if observations:
        if value.get("status") == "no_evidence_in_covered_scope":
            _fail("h1_native_evidence_conflicts_with_no_evidence")
        if not items:
            if (
                value.get("status") != "partial"
                or coverage.get("status") != "partial"
                or coverage.get("declared_scope_complete") is not False
                or covered
                or uncovered != declared
                or coverage.get("retrieval_succeeded") is not True
                or coverage.get("exact_target_search_succeeded") is not True
            ):
                _fail("h1_native_only_requires_partial_uncovered_scope")
        for observation in observations:
            if (observation.get("source_native_field") == "SuspensionOfTrading"
                    and "suspension" in covered and "suspension" not in item_types):
                _fail("h1_native_observation_cannot_cover_suspension")
