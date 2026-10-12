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

try:
    from scripts.m8r_05c.phase_h_semantics import (
        validate_trading_status_context_semantics as _validate_h1_semantics,
    )
except ModuleNotFoundError:  # Support direct execution as `python scripts/...py`.
    from m8r_05c.phase_h_semantics import (
        validate_trading_status_context_semantics as _validate_h1_semantics,
    )


class PhaseHV3ContractValidationError(ValueError):
    """A candidate Phase H V3 evidence object violates a frozen invariant."""


def _fail(code: str) -> None:
    raise PhaseHV3ContractValidationError(code)


def _unique_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while rejecting duplicate keys at every nesting level."""
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _fail(f"duplicate_json_key:{key}")
        value[key] = item
    return value


def strict_json_loads(text: str) -> Any:
    """Parse governance JSON without the duplicate-key ambiguity of json.loads defaults."""
    try:
        return json.loads(text, object_pairs_hook=_unique_object_pairs)
    except json.JSONDecodeError as exc:
        raise PhaseHV3ContractValidationError("current_authority_json_invalid") from exc


def _load_current_authority_json(path: Path) -> Any:
    try:
        return strict_json_loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise PhaseHV3ContractValidationError("current_authority_json_invalid") from exc


def _matches_frozen_bytes(content: bytes, item: Mapping[str, Any]) -> bool:
    """Compare frozen text artifacts without making OS newline conversion authority."""
    normalized = content.replace(b"\r\n", b"\n")
    candidates = (
        content,
        normalized,
        normalized.replace(b"\n", b"\r\n"),
    )
    return any(
        len(candidate) == item["bytes"]
        and hashlib.sha256(candidate).hexdigest() == item["sha256"]
        for candidate in candidates
    )


RETURN_PCT_ABS_TOLERANCE = 1e-9
"""Absolute tolerance for serialized JSON return percentages; no rounding."""


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
    """H0-C scope is canonical; v2 native evidence remains unresolved."""
    try:
        _validate_h1_semantics(value)
    except ValueError as exc:
        raise PhaseHV3ContractValidationError(str(exc)) from exc


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
    # H0-G remains historical freeze evidence. H-ACT tranches are allowed to
    # advance current runtime-state projections (catalog/routing) and this current
    # validator without rewriting the historical freeze manifest.
    activation_mutable = {
        "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json",
        "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json",
        "schemas/unified_market_evidence_request.v3.schema.json",
        "schemas/unified_market_evidence_result.v3.schema.json",
        "schemas/unified_market_evidence_audit_package.v3.schema.json",
        "scripts/validate_phase_h_v3_contracts.py",
    }
    for section in ("semantic_inputs", "v3_normative_artifacts", "protected_v1_v2_authority"):
        for item in manifest[section]:
            if item["path"] in activation_mutable:
                continue
            path = root / item["path"]
            content = path.read_bytes()
            if not _matches_frozen_bytes(content, item):
                _fail(f"manifest_integrity_mismatch:{item['path']}")

    request_v3 = _load_current_authority_json(root / "schemas/unified_market_evidence_request.v3.schema.json")
    v3_need_types = request_v3["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]
    expected_h0_g_need_types = [
        "identity", "current_observation", "official_eod_reference", "recent_performance",
        "session_status", "source_currentness", "evidence_quality", "material_disclosures",
        "monthly_revenue", "trading_status_context", "corporate_action_context",
    ]
    if v3_need_types != [*expected_h0_g_need_types, "market_state_context", "index_futures_context", "cash_institutional_flow_context"]:
        _fail("phase_i_v3_request_extension_not_additive")
    additive_v3_schema_hashes = {
        "schemas/unified_market_evidence_request.v3.schema.json": "b0901dbf63db3a8bc44b8fec4cb0cdc90f77e153d954266f98c690453864f3f6",
        "schemas/unified_market_evidence_result.v3.schema.json": "9269fc9e5e07884fa2de791eae902ee57b3d937dbb793318ca4aff1a93fc5bcb",
        "schemas/unified_market_evidence_audit_package.v3.schema.json": "94208ac6f4c13bcde294de1a8c7cf6be23245d738b5dcd36fffcac1ab134c4cc",
    }
    for relative_path, expected_hash in additive_v3_schema_hashes.items():
        if hashlib.sha256((root / relative_path).read_bytes()).hexdigest() != expected_hash:
            _fail(f"phase_i_v3_additive_schema_drift:{relative_path}")

    h1_v1_path = "schemas/trading_status_context_evidence.v1.schema.json"
    h1_v1_sha256 = hashlib.sha256((root / h1_v1_path).read_bytes()).hexdigest()
    if h1_v1_sha256 != "638200509cde05613d17bd4158d1676c3c086d2b10aa2f50fb85d52febe30ecf":
        _fail("h1_v1_schema_changed")
    h1_v1 = _load_current_authority_json(root / h1_v1_path)
    h1_v2 = _load_current_authority_json(root / "schemas/trading_status_context_evidence.v2.schema.json")
    h1_v2_sha256 = hashlib.sha256((root / "schemas/trading_status_context_evidence.v2.schema.json").read_bytes()).hexdigest()
    if h1_v2_sha256 != "818de1e9c501b4c4d0bb06d6a1503dafba7b63dc60977791f7842cd8b5a31d38":
        _fail("h1_v2_schema_current_authority_drift")
    if h1_v2.get("properties", {}).get("schema_version", {}).get("const") != "trading_status_context_evidence.v2":
        _fail("h1_v2_schema_version_invalid")
    if h1_v2.get("definitions", {}).get("status_type") != h1_v1.get("definitions", {}).get("status_type"):
        _fail("h1_v2_canonical_status_types_changed")
    result_v3 = _load_current_authority_json(root / "schemas/unified_market_evidence_result.v3.schema.json")
    h1_union = result_v3.get("definitions", {}).get("trading_status_context", {}).get("oneOf", [])
    h1_versions = {
        item.get("properties", {}).get("schema_version", {}).get("const")
        for item in h1_union
        if isinstance(item, dict) and isinstance(item.get("properties"), dict)
    }
    composite_branches = [item for item in h1_union if item.get("$ref") == "#/definitions/trading_status_context_composite"]
    if (len(h1_union) != 3
            or h1_versions != {"trading_status_context_evidence.v1", "trading_status_context_evidence.v2"}
            or len(composite_branches) != 1):
        _fail("result_v3_h1_version_union_invalid")
    composite_path = root / "schemas/trading_status_context_composite.v1.schema.json"
    if hashlib.sha256(composite_path.read_bytes()).hexdigest() != "3d34a1cb2112716211e39536b221994952aabd1c2723d3ed5f61ee8b0f224106":
        _fail("h1_composite_schema_current_authority_drift")
    operation_result_v2_path = root / "schemas/unified_market_evidence_operation_result.v2.schema.json"
    if hashlib.sha256(operation_result_v2_path.read_bytes()).hexdigest() != "9d6430254215ae0b4048e0352f6902c629e4069530b1c9a267f1ee50d4c5bd64":
        _fail("operation_result_v2_composition_authority_drift")

    catalog = _load_current_authority_json(
        root / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json"
    )
    routing = _load_current_authority_json(
        root / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json"
    )
    _load_current_authority_json(root / "config/m8r_06_03_executor_registry_metadata.json")
    orchestrator_disposition = _load_current_authority_json(
        root / "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json"
    )
    h3_disposition = next((item for item in orchestrator_disposition.get("surfaces", [])
                           if item.get("surface_id") == "phase_h_h3_twse_recent_performance_executor"), None)
    if h3_disposition is None or h3_disposition.get("current_status") != "H-ACT-H3 selected TWSE route is Owner-accepted and active":
        _fail("h3_orchestrator_disposition_current_truth_invalid")
    versions = catalog["contract_versions"]
    if versions.get("preferred_request_schema_version") != "unified_market_evidence_request.v3":
        _fail("phase_h_preferred_request_version_drift")
    if versions.get("emitted_result_schema_version") != "unified_market_evidence_result.v3":
        _fail("phase_h_preferred_result_version_drift")
    if versions.get("future_candidate_request_schema_version") is not None or versions.get("future_candidate_result_schema_version") is not None:
        _fail("phase_h_future_candidate_state_stale")
    if versions.get("v3_runtime_authority_status") != "v3_preferred_selected_routes_active":
        _fail("phase_h_runtime_authority_state_invalid")
    if catalog["phase_h_contract"].get("runtime_authority") != "v3_preferred_selected_routes_active":
        _fail("phase_h_contract_runtime_authority_invalid")
    if catalog["phase_h_contract"].get("preferred_runtime_request_schema_version") != "unified_market_evidence_request.v3":
        _fail("phase_h_contract_preferred_request_invalid")
    if catalog["phase_h_contract"].get("active_phase_h_source_count") != 5:
        _fail("phase_h_active_source_count_invalid")
    active = [item for item in routing["phase_h_source_authority"]["records"] if item.get("activation_state") == "active"]
    if routing["phase_h_source_authority"].get("active_source_count") != 5:
        _fail("phase_h_routing_active_source_count_invalid")
    if {(item.get("source_id"), item.get("runtime_executable")) for item in active} != {
        ("H1-TPEX-ATTENTION-OPENAPI", True),
        ("H1-TPEX-DISPOSITION-OPENAPI", True),
        ("H1-TPEX-CHANGED-TRADING-OPENAPI", True),
        ("H3-TWSE-DEFAULT-BOUNDED", True),
        ("H2-TWSE-EXRIGHT-PRE-OPENAPI", True),
    } or len(active) != 5:
        _fail("phase_h_active_source_set_invalid")
    if routing.get("activation_status") != "selected_phase_h_routes_active":
        _fail("phase_h_routing_activation_status_invalid")
    routing_scope = routing.get("routing_scope", "")
    if not all(source_id in routing_scope for source_id in (
        "H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI",
        "H1-TPEX-CHANGED-TRADING-OPENAPI", "H3-TWSE-DEFAULT-BOUNDED"
    )) or any(token in routing_scope.lower() for token in (
        "branch-local candidate", "pending live", "pending rollback", "pending owner review"
    )):
        _fail("phase_h_routing_scope_current_truth_invalid")
    h1_route = next((item for item in routing.get("routes", []) if item.get("capability_id") == "trading_status_context"), None)
    h1_capability = next((item for item in catalog.get("data_need_capabilities", []) if item.get("capability_id") == "trading_status_context"), None)
    if (h1_route is None or h1_capability is None
            or h1_route.get("selected_executor_id") != "phase_h_h1_tpex_composite_executor"
            or h1_route.get("candidate_executor_ids") != ["phase_h_h1_tpex_composite_executor"]
            or h1_route.get("output_evidence_contract") != "trading_status_context_composite.v1"
            or h1_route.get("source_compatibility_key") != "H1-TPEX-COMPOSITE"
            or h1_route.get("supported_markets") != ["TPEX"]
            or "partial_attention_disposition_plus_native_cmode" not in h1_capability.get("coverage_modes", [])):
        _fail("phase_h_h1_composite_route_authority_invalid")
    descriptors = _load_current_authority_json(root / "config/phase_h_h1_dormant_source_descriptors.json")
    descriptor_states = {item.get("source_id"): (item.get("activation_state"), item.get("runtime_executable")) for item in descriptors.get("sources", [])}
    for source_id in ("H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI"):
        if descriptor_states.get(source_id) != ("active", True):
            _fail(f"phase_h_active_descriptor_mismatch:{source_id}")
    if descriptor_states.get("H1-TPEX-SUSPEND-TODAY-OPENAPI") != ("inactive", False):
        _fail("phase_h_tpex_suspend_today_must_remain_inactive")
    if descriptor_states.get("H1-TPEX-SUSPEND-HISTORY-OPENAPI") != ("eligible", False):
        _fail("phase_h_tpex_suspend_history_must_remain_dormant")
    metadata = _load_current_authority_json(root / "config/m8r_06_03_executor_registry_metadata.json")
    if not any(item.get("executor_id") == "phase_h_h1_tpex_composite_executor"
               and item.get("expected_evidence_contract") == "trading_status_context_composite.v1"
               for item in metadata.get("executors", [])):
        _fail("phase_h_composite_executor_metadata_missing")
    recent = next((item for item in catalog["data_need_capabilities"] if item.get("capability_id") == "recent_performance"), None)
    recent_route = next((item for item in routing["routes"] if item.get("capability_id") == "recent_performance"), None)
    if recent is None or recent.get("support_status") != "runtime_executable" or recent.get("runtime_executable") is not True or recent.get("phase_h_activation_state") != "selected_route_active":
        _fail("h3_catalog_candidate_authority_invalid")
    if recent_route is None:
        _fail("h3_routing_candidate_authority_missing")
    if recent_route.get("runtime_executable") is not True or recent_route.get("provisional") is not False or recent_route.get("routing_status") != "resolved":
        _fail("h3_routing_candidate_state_invalid")
    if recent_route.get("supported_markets") != ["TWSE"] or recent_route.get("selected_executor_id") != "phase_h_h3_twse_recent_performance_executor" or recent_route.get("candidate_executor_ids") != ["phase_h_h3_twse_recent_performance_executor"]:
        _fail("h3_routing_selected_executor_invalid")
    if recent_route.get("network_required") is not True or recent_route.get("batching_scope") != "none" or recent_route.get("approval_required") is not True or recent_route.get("capability_requires_execution_approval") is not True:
        _fail("h3_routing_execution_bounds_invalid")
    if recent_route.get("supported_instrument_families") != ["company_share"] or recent_route.get("supported_instrument_types") != ["common_share"]:
        _fail("h3_routing_instrument_scope_invalid")
    if any(item.get("capability_id") == "recent_performance" and (
        item.get("supported_instrument_families") != ["company_share"]
        or item.get("supported_instrument_types") != ["common_share"]
    ) for item in routing["routes"]):
        _fail("h3_routing_duplicate_or_conflicting_instrument_scope")
    if recent_route.get("parameter_mapping", {}).get("lookback_trading_days") != "data_need.parameters.lookback_trading_days" or recent_route.get("output_evidence_contract") != "recent_performance_evidence.v1" or recent_route.get("source_compatibility_key") != "H3-TWSE-DEFAULT-BOUNDED":
        _fail("h3_routing_contract_binding_invalid")
    source_states = {item.get("market"): item for item in recent_route.get("source_authority_states", [])}
    if source_states.get("TWSE", {}).get("activation_state") != "active" or source_states.get("TPEX", {}).get("activation_state") != "blocked" or source_states.get("TPEX", {}).get("governance_issue_ids") != ["H0-SRC-10", "H0-SRC-12"]:
        _fail("h3_market_source_authority_invalid")
    h2_sources = [item for item in routing["phase_h_source_authority"]["records"] if str(item.get("source_id", "")).startswith("H2-")]
    active_h2 = [item for item in h2_sources if item.get("activation_state") == "active" and item.get("runtime_executable") is True]
    if ([(item.get("source_id"), item.get("source_contract")) for item in active_h2] != [("H2-TWSE-EXRIGHT-PRE-OPENAPI", "TWT48U_ALL")]
            or any(item.get("activation_state") == "active" or item.get("runtime_executable") is True for item in h2_sources if item not in active_h2)):
        _fail("a6_h2_activation_scope_invalid")
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
