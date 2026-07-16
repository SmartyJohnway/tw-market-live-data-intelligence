"""Reference validator for M8R-03B design contract instances.

This is intentionally lightweight and repository-local. It validates the design
fixtures and negative invariants added for M8R-03B, but it is not the final
production validator planned for M8R-03C.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

SCOPE_MODES = {"watchlist", "market_overview", "dynamic_research", "watchlist_subset"}
TIME_MODES = {"current", "recent", "current_plus_recent", "historical", "explicit_range"}
EVIDENCE_DEPTHS = {"quick", "standard", "deep", "diagnostic"}
COVERAGE_STATES = {"usable", "partial", "unavailable"}
CALCULATION_STATUSES = {"calculated", "partial", "input_unavailable", "formula_not_applicable", "stale_inputs", "error"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _require_object(value: Any, name: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{name} must be an object")
    return value


def _require_string(value: Any, name: str, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    _require(isinstance(value, str) and bool(value.strip()), f"{name} must be a non-empty string")


def _validate_time_scope(value: Any) -> None:
    scope = _require_object(value, "time_scope")
    _require(scope.get("mode") in TIME_MODES, "invalid time_scope.mode")
    _require("lookback_trading_days" in scope, "time_scope.lookback_trading_days required")
    ltd = scope.get("lookback_trading_days")
    _require(ltd is None or (isinstance(ltd, int) and ltd > 0), "lookback_trading_days must be null or positive integer")
    _require("explicit_range" in scope, "time_scope.explicit_range required")
    explicit = scope.get("explicit_range")
    if scope.get("mode") == "explicit_range":
        explicit_obj = _require_object(explicit, "explicit_range")
        _require(explicit_obj.get("range_type") in {"trading_days", "calendar_dates", "year_to_date", "named_period"}, "invalid explicit_range.range_type")
        _require_string(explicit_obj.get("user_text"), "explicit_range.user_text")
    else:
        _require(explicit is None, "explicit_range must be null unless mode=explicit_range")


def validate_conversation_intent(value: Any, *, persistent_watchlist_reference: Any = None, follow_up_context: Any = None) -> None:
    intent = _require_object(value, "conversation_intent")
    _require(intent.get("schema_version") == "m8r_ai_market_conversation_intent.v1", "invalid conversation_intent.schema_version")
    _require_string(intent.get("original_user_text"), "original_user_text")
    scopes = intent.get("scope_modes")
    _require(isinstance(scopes, list) and scopes, "scope_modes must be a non-empty array")
    unknown = set(scopes) - SCOPE_MODES
    _require(not unknown, f"unknown scope mode: {sorted(unknown)}")
    if "watchlist_subset" in scopes:
        parent_id = (follow_up_context or {}).get("parent_evidence_request_id") if isinstance(follow_up_context, dict) else None
        _require(persistent_watchlist_reference is not None or parent_id, "watchlist_subset requires watchlist reference or parent context")
    _validate_time_scope(intent.get("time_scope"))
    _require(intent.get("evidence_depth") in EVIDENCE_DEPTHS, "invalid evidence_depth")
    _require(isinstance(intent.get("explicit_user_constraints"), dict), "explicit_user_constraints must be object")
    _require(isinstance(intent.get("inferred_defaults"), dict), "inferred_defaults must be object")
    clarification = intent.get("clarification_required")
    _require(isinstance(clarification, bool), "clarification_required must be boolean")
    reason = intent.get("clarification_reason")
    if clarification:
        _require_string(reason, "clarification_reason")
    else:
        _require(reason is None, "clarification_reason must be null when clarification_required=false")


def _validate_evidence_requirement(value: Any, expected_priority: str | None = None) -> None:
    req = _require_object(value, "evidence_requirement")
    _require_string(req.get("capability_id"), "capability_id")
    _require(req.get("priority") in {"required", "useful", "optional"}, "invalid evidence priority")
    if expected_priority is not None:
        _require(req.get("priority") == expected_priority, "evidence priority does not match containing array")
    _validate_time_scope(req.get("time_scope"))
    _require_string(req.get("preferred_timing_class"), "preferred_timing_class")
    _require(isinstance(req.get("source_family_preference"), list), "source_family_preference must be array")
    _require_string(req.get("fallback_behavior"), "fallback_behavior")
    _require(isinstance(req.get("required_for_answer"), bool), "required_for_answer must be boolean")


def _validate_dynamic_entity(value: Any) -> None:
    entity = _require_object(value, "dynamic_entity_request")
    for field in ["input_reference", "entity_role", "selection_reason", "priority", "requested_source_timing_class", "fallback_behavior"]:
        _require_string(entity.get(field), field)
    _validate_time_scope(entity.get("requested_time_range"))
    _require(entity.get("persistent_watchlist_mutation") is False, "dynamic entity cannot mutate persistent watchlist")


def validate_evidence_request(value: Any) -> None:
    req = _require_object(value, "evidence_request")
    _require(req.get("schema_version") == "m8r_ai_evidence_request.v1", "invalid evidence_request.schema_version")
    _require_string(req.get("request_id"), "request_id")
    _require_string(req.get("original_user_text"), "original_user_text")
    validate_conversation_intent(
        req.get("conversation_intent"),
        persistent_watchlist_reference=req.get("persistent_watchlist_reference"),
        follow_up_context=req.get("follow_up_context"),
    )
    for field in ["explicit_user_constraints", "inferred_defaults", "identity_resolver_output"]:
        _require(isinstance(req.get(field), dict), f"{field} must be object")
    if req.get("persistent_watchlist_reference") is not None:
        ref = _require_object(req.get("persistent_watchlist_reference"), "persistent_watchlist_reference")
        _require_string(ref.get("watchlist_id"), "persistent_watchlist_reference.watchlist_id")
        _require(isinstance(ref.get("enabled_target_ids"), list), "persistent_watchlist_reference.enabled_target_ids must be array")
    for entity in req.get("dynamic_entity_requests", []):
        _validate_dynamic_entity(entity)
    _require(isinstance(req.get("market_context_requests"), list), "market_context_requests must be array")
    for field, priority in [("required_evidence", "required"), ("useful_evidence", "useful"), ("optional_evidence", "optional")]:
        items = req.get(field)
        _require(isinstance(items, list), f"{field} must be array")
        for item in items:
            _validate_evidence_requirement(item, expected_priority=priority)
    policy = _require_object(req.get("execution_policy"), "execution_policy")
    for flag in ["operator_confirmation_required", "network_allowed", "polling", "scheduler"]:
        _require(isinstance(policy.get(flag), bool), f"execution_policy.{flag} must be boolean")
    _require(policy.get("polling") is False and policy.get("scheduler") is False, "polling and scheduler must remain false")
    if req.get("follow_up_context"):
        follow = _require_object(req.get("follow_up_context"), "follow_up_context")
        if _time_mode(req.get("conversation_intent")) in {"current", "current_plus_recent"}:
            _require(follow.get("freshness_recheck_required") is True, "current MIS reuse requires freshness_recheck_required=true")
    clarification = req.get("clarification_required")
    _require(isinstance(clarification, bool), "evidence_request.clarification_required must be boolean")
    if clarification:
        _require_string(req.get("clarification_reason"), "evidence_request.clarification_reason")
    else:
        _require(req.get("clarification_reason") is None, "evidence_request.clarification_reason must be null when false")


def _time_mode(intent: Any) -> str | None:
    return ((intent or {}).get("time_scope") or {}).get("mode") if isinstance(intent, dict) else None


def _validate_derived_metric(value: Any) -> None:
    metric = _require_object(value, "derived_metric")
    for field in ["metric_id", "formula_id", "as_of"]:
        _require_string(metric.get(field), field)
    _require("value" in metric, "derived_metric.value required")
    _require("unit" in metric, "derived_metric.unit required")
    _validate_time_scope(metric.get("input_period"))
    _require(isinstance(metric.get("source_dependencies"), list), "source_dependencies must be array")
    _require(metric.get("calculation_status") in CALCULATION_STATUSES, "invalid calculation_status")


def _validate_missing_evidence(value: Any) -> None:
    missing = _require_object(value, "missing_evidence")
    _require_string(missing.get("capability_id"), "missing.capability_id")
    _require_string(missing.get("reason_code"), "missing.reason_code")
    _require(isinstance(missing.get("required_for_answer"), bool), "missing.required_for_answer must be boolean")
    _require_string(missing.get("impact"), "missing.impact")
    _require("fallback_used" in missing, "missing.fallback_used required")
    _require("recommended_follow_up" in missing, "missing.recommended_follow_up required")


def _validate_coverage_targets(targets: Any, requested_target_ids: list[str] | None = None) -> None:
    _require(isinstance(targets, list), "coverage.targets must be array")
    ids = []
    for target in targets:
        rec = _require_object(target, "coverage target")
        _require_string(rec.get("target_id"), "target_id")
        ids.append(rec["target_id"])
        _require(rec.get("coverage_state") in COVERAGE_STATES, "invalid coverage_state")
        _require(isinstance(rec.get("present_field_groups"), list), "present_field_groups must be array")
        _require(isinstance(rec.get("missing_field_groups"), list), "missing_field_groups must be array")
        state = rec["coverage_state"]
        if state == "unavailable":
            _require_string(rec.get("reason_code"), "reason_code")
        if state == "partial":
            _require(rec.get("missing_field_groups"), "partial coverage requires missing_field_groups")
        if state == "usable":
            _require(rec.get("present_field_groups"), "usable coverage requires present_field_groups")
    counts = Counter(ids)
    duplicated = [target_id for target_id, count in counts.items() if count > 1]
    _require(not duplicated, f"coverage target appears more than once: {duplicated}")
    if requested_target_ids is not None:
        _require(set(ids) == set(requested_target_ids), "every enabled requested target must appear exactly once in coverage")


def validate_bundle(value: Any) -> None:
    bundle = _require_object(value, "bundle")
    for field in ["schema_version", "bundle_id", "request_id", "generated_at_utc"]:
        _require_string(bundle.get(field), field)
    _require(isinstance(bundle.get("conversation_context"), dict), "conversation_context must be object")
    _require(isinstance(bundle.get("facts"), list), "facts must be array")
    for metric in bundle.get("derived_metrics", []):
        _validate_derived_metric(metric)
    _require(isinstance(bundle.get("resolution_assumptions"), list), "resolution_assumptions must be array")
    for missing in bundle.get("missing_evidence", []):
        _validate_missing_evidence(missing)
    coverage = _require_object(bundle.get("coverage"), "coverage")
    _validate_coverage_targets(coverage.get("targets"), coverage.get("requested_target_ids"))
    _require(isinstance(bundle.get("source_summary"), dict), "source_summary must be object")


def validate_fixture(value: Any) -> None:
    fixture = _require_object(value, "fixture")
    intent = fixture.get("parsed_conversation_intent")
    evidence_request = fixture.get("evidence_request")
    validate_conversation_intent(
        intent,
        persistent_watchlist_reference=evidence_request.get("persistent_watchlist_reference") if isinstance(evidence_request, dict) else None,
        follow_up_context=fixture.get("follow_up_context"),
    )
    validate_evidence_request(evidence_request)
    _validate_coverage_targets(fixture.get("expected_target_coverage"), fixture.get("expected_requested_target_ids"))
    _validate_derived_metric(fixture.get("sample_derived_metric"))
    for missing in fixture.get("sample_missing_evidence", []):
        _validate_missing_evidence(missing)
    for bundle in fixture.get("sample_bundles", []):
        validate_bundle(bundle)
