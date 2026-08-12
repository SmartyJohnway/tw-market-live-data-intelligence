"""Evidence projector for M8R-05C.

Projects evidence artifact JSON objects into EvidenceEnvelopeProjection
and official_eod_reference dict form.

This module:
- Is a pure function layer (no network, no clock, no side effects).
- Projects only requested data_need fields.
- Handles missing/failed operations gracefully (returns status=missing/failed).
- Preserves currentness semantics from the evidence artifact.
"""
from __future__ import annotations

from .lineage_resolver import LineageMap, OperationBinding
from .models import EvidenceEnvelopeProjection, TargetEvidenceProjection
from .errors import ProjectionError
from scripts.observation_contract import (
    build_ai_safe_market_context_projection_from_observation,
    promote_ai_safe_market_context_projection_for_controlled_context,
)

CURRENT_PROJECTOR_VERSION = "m8r_05c_v1_2"
PREVIOUS_PROJECTOR_VERSION = "m8r_05c_v1_1"
LEGACY_PROJECTOR_VERSION = "m8r_05c_v1"

# Data needs that use the generic evidence_envelope structure.
_ENVELOPE_DATA_NEEDS = {
    "identity",
    "current_observation",
    "recent_performance",
    "session_status",
    "source_currentness",
    "evidence_quality",
}

_OFFICIAL_EOD_NEED = "official_eod_reference"


def _project_envelope(
    binding: OperationBinding | None,
    citation_ids: list[str],
) -> EvidenceEnvelopeProjection:
    """Project an operation binding into an evidence envelope.

    If binding is None or failed, returns an envelope with status=missing/failed.
    """
    if binding is None:
        return EvidenceEnvelopeProjection(status="missing")

    if binding.status == "plan_only_not_executed":
        return EvidenceEnvelopeProjection(
            status="plan_only_not_executed",
            caveats=["capability_plan_only", "no_execution_attempted", "no_market_network_attempted"],
            citation_ids=citation_ids,
        )

    if binding.status == "failed":
        return EvidenceEnvelopeProjection(
            status="failed",
            caveats=[f"operation_failed:{binding.error_code or 'unknown'}"],
        )

    if binding.capability_id == "current_observation":
        has_m7b_input = any(isinstance(item, dict) and item.get("source") == "TWSE_MIS" and isinstance(item.get("twse_mis_rich_facts"), dict)
                            for artifact in binding.artifact_objects.values() for item in artifact.get("records", []))
        if has_m7b_input:
            return _project_current_observation(binding, citation_ids)
    # Merge observed fields from all artifact objects.
    merged_observed: dict = {}
    merged_missing: list[str] = []
    merged_caveats: list[str] = []
    timing_class: str | None = None
    fallback = False
    fallback_state: str | None = None
    currentness: dict = {}

    for artifact_obj in binding.artifact_objects.values():
        if not isinstance(artifact_obj, dict):
            continue
        # Try standard evidence object field layout.
        items = artifact_obj.get("records") if artifact_obj.get("schema_version") == "m8r_06_03_operation_evidence.v1" else artifact_obj.get("items", [artifact_obj])
        if not isinstance(items, list):
            items = [artifact_obj]

        for item in items:
            if not isinstance(item, dict):
                continue
            # Observed fields — merge all non-meta keys.
            for k, v in item.items():
                if k not in {
                    "schema_version", "retrieved_at", "source_family",
                    "timing_class", "session_status", "caveats",
                    "missing_fields", "fallback", "fallback_state",
                    "currentness", "trade_date", "expected_latest_completed_trade_date",
                }:
                    merged_observed[k] = v
            # Meta fields.
            if "timing_class" in item and timing_class is None:
                timing_class = item["timing_class"]
            if item.get("fallback"):
                fallback = True
            if item.get("fallback_state") and fallback_state is None:
                fallback_state = item["fallback_state"]
            if "caveats" in item and isinstance(item["caveats"], list):
                merged_caveats.extend(item["caveats"])
            if "missing_fields" in item and isinstance(item["missing_fields"], list):
                merged_missing.extend(item["missing_fields"])
            if "currentness" in item and isinstance(item["currentness"], dict):
                currentness.update(item["currentness"])

    status = "available" if merged_observed or currentness else "empty"

    return EvidenceEnvelopeProjection(
        status=status,
        timing_class=timing_class,
        caveats=sorted(set(merged_caveats)),
        observed_fields=merged_observed,
        missing_fields=sorted(set(merged_missing)),
        currentness=currentness,
        fallback=fallback,
        fallback_state=fallback_state,
        citation_ids=citation_ids,
    )


def _project_current_observation(binding: OperationBinding, citation_ids: list[str]) -> EvidenceEnvelopeProjection:
    """Admit only governed M7B standard facts plus Mode-C-only displayed depth."""
    item = next((record for artifact in binding.artifact_objects.values() if isinstance(artifact, dict)
                 for record in artifact.get("records", [])
                 if isinstance(record, dict)
                 and record.get("source") == "TWSE_MIS"
                 and isinstance(record.get("twse_mis_rich_facts"), dict)), {})
    projection = promote_ai_safe_market_context_projection_for_controlled_context(
        build_ai_safe_market_context_projection_from_observation(item)
    )
    if not (projection.get("safe_for_ai_context") is True and projection.get("exposure_status") == "ai_safe_context_enabled"):
        return EvidenceEnvelopeProjection(
            status="missing",
            caveats=["m7b_controlled_projection_blocked"],
            citation_ids=citation_ids,
        )
    rich = item.get("twse_mis_rich_facts", {}) if isinstance(item.get("twse_mis_rich_facts"), dict) else {}
    depth = rich.get("displayed_depth_facts", {}) if isinstance(rich.get("displayed_depth_facts"), dict) else {}
    limits = rich.get("limit_or_reference_facts", {}) if isinstance(rich.get("limit_or_reference_facts"), dict) else {}
    observed = {
        "instrument_context": projection.get("instrument_context", {}),
        "source_context": {key: item.get(key) for key in ("source", "source_type", "adapter_id") if item.get(key) is not None},
        "price_snapshot": projection.get("price_snapshot_context", {}),
        "reference_price_context": {key: limits.get(key) for key in ("limit_up", "limit_down") if limits.get(key) is not None},
        "displayed_quote_snapshot": {"best_bid": depth.get("best_bid"), "best_ask": depth.get("best_ask"), "semantic_label": "displayed_quote_snapshot"},
        "freshness_context": projection.get("freshness_context", {}),
        "market_session_context": projection.get("market_session_context", {}),
        "data_quality_context": projection.get("data_quality_context", {}),
    }
    if depth.get("applicable") is True:
        observed["extended_displayed_depth_snapshot"] = {
            "bid_prices": list(depth.get("bid_prices") or [])[:5], "ask_prices": list(depth.get("ask_prices") or [])[:5],
            "bid_displayed_quantities_raw": list(depth.get("bid_quantities_raw") or [])[:5], "ask_displayed_quantities_raw": list(depth.get("ask_quantities_raw") or [])[:5],
            "caveats": ["displayed_snapshot_only", "not_full_order_book", "not_true_liquidity", "not_support_resistance", "not_trading_signal", "quantity_unit_unverified"],
        }
    caveats = sorted(set((item.get("caveats") or []) + ["not_realtime_guaranteed"]))
    return EvidenceEnvelopeProjection(status="available", observed_fields=observed, caveats=caveats,
        currentness=projection.get("freshness_context", {}), citation_ids=citation_ids)


def _project_envelope_legacy(binding: OperationBinding | None, citation_ids: list[str]) -> EvidenceEnvelopeProjection:
    """Frozen v1 generic projection retained solely for immutable output verification."""
    if binding is None:
        return EvidenceEnvelopeProjection(status="missing")
    if binding.status in {"failed", "plan_only_not_executed"}:
        return EvidenceEnvelopeProjection(status="failed", caveats=[f"operation_failed:{binding.error_code or 'unknown'}"])
    observed, missing, caveats, currentness = {}, [], [], {}
    timing_class = None
    fallback, fallback_state = False, None
    excluded = {"schema_version", "retrieved_at", "source_family", "timing_class", "session_status", "caveats", "missing_fields", "fallback", "fallback_state", "currentness", "trade_date", "expected_latest_completed_trade_date"}
    for artifact in binding.artifact_objects.values():
        items = artifact.get("records") if artifact.get("schema_version") == "m8r_06_03_operation_evidence.v1" else artifact.get("items", [artifact])
        for item in items if isinstance(items, list) else [artifact]:
            if not isinstance(item, dict): continue
            observed.update({k: v for k, v in item.items() if k not in excluded})
            timing_class = timing_class or item.get("timing_class")
            caveats.extend(item.get("caveats", []) if isinstance(item.get("caveats"), list) else [])
            missing.extend(item.get("missing_fields", []) if isinstance(item.get("missing_fields"), list) else [])
            if isinstance(item.get("currentness"), dict): currentness.update(item["currentness"])
            fallback = fallback or bool(item.get("fallback")); fallback_state = fallback_state or item.get("fallback_state")
    return EvidenceEnvelopeProjection(status="available" if observed or currentness else "empty", timing_class=timing_class,
        caveats=sorted(set(caveats)), observed_fields=observed, missing_fields=sorted(set(missing)), currentness=currentness,
        fallback=fallback, fallback_state=fallback_state, citation_ids=citation_ids)


def _project_envelope_v1_1(binding: OperationBinding | None, citation_ids: list[str]) -> EvidenceEnvelopeProjection:
    """Frozen v1.1 envelope semantics for existing-output verification."""
    if binding is None:
        return EvidenceEnvelopeProjection(status="missing")
    if binding.status in {"failed", "plan_only_not_executed"}:
        return EvidenceEnvelopeProjection(status="failed", caveats=[f"operation_failed:{binding.error_code or 'unknown'}"])
    return _project_envelope(binding, citation_ids)


def _project_official_eod_legacy(binding: OperationBinding | None, citation_ids: list[str]) -> dict | None:
    if binding is None: return None
    if binding.status == "failed": return {"currentness_status": "calendar_status_unresolved", "caveats": [f"operation_failed:{binding.error_code or 'unknown'}"]}
    for artifact in binding.artifact_objects.values():
        for item in artifact.get("records", []) if isinstance(artifact.get("records"), list) else []:
            if not isinstance(item, dict): continue
            status = item.get("currentness_status") or item.get("currentness", {}).get("currentness_status")
            if status:
                result = {"currentness_status": status}
                for key in ("trade_date", "expected_latest_completed_trade_date", "session_status", "publication_grace_applied", "fallback_policy_used", "provisional_candidate_status"):
                    if key in item: result[key] = item[key]
                if item.get("caveats"): result["caveats"] = item["caveats"]
                return result
    return {"currentness_status": "calendar_status_unresolved", "caveats": ["no_eod_currentness_found_in_artifact"]}


def _project_official_eod(
    binding: OperationBinding | None,
    citation_ids: list[str],
) -> dict | None:
    """Project official_eod_reference from operation binding."""
    if binding is None:
        return None
    if binding.status == "failed":
        return {
            "currentness_status": "calendar_status_unresolved",
            "caveats": [f"operation_failed:{binding.error_code or 'unknown'}"],
        }

    # Currentness is an evidence dimension, not an availability gate.
    for artifact_obj in binding.artifact_objects.values():
        if not isinstance(artifact_obj, dict):
            continue
        items = artifact_obj.get("records") if artifact_obj.get("schema_version") == "m8r_06_03_operation_evidence.v1" else artifact_obj.get("items", [artifact_obj])
        if not isinstance(items, list):
            items = [artifact_obj]
        for item in items:
            if not isinstance(item, dict):
                continue
            currentness_status = (
                item.get("currentness_status")
                or item.get("currentness", {}).get("currentness_status")
                or "calendar_status_unresolved"
            )
            result: dict = {"status": "available", "currentness_status": currentness_status,
                "citation_ids": citation_ids}
            for field in ("source_id", "authority_level", "timing_class", "trade_date"):
                if field in item: result[field] = item[field]
            if artifact_obj.get("source_family"): result["source_family"] = artifact_obj["source_family"]
            expected_market, expected_symbol = binding.canonical_target_id.split(":", 1)
            source_market = str(item.get("market") or "").lower()
            source_market_ok = (expected_market == "TWSE" and source_market in {"listed", "twse"}) or (expected_market == "TPEX" and source_market in {"tpex_otc", "tpex"})
            if str(item.get("symbol")) != expected_symbol or (source_market and not source_market_ok):
                raise ProjectionError("official_eod_identity_mismatch")
            allowed_nested = {"price": ("open", "high", "low", "close", "previous_close", "change"), "activity": ("trade_volume", "trade_value", "transaction_count")}
            for field, allowed in allowed_nested.items():
                if isinstance(item.get(field), dict):
                    result[field] = {key: item[field][key] for key in allowed if key in item[field]}
            for field in [
                "trade_date",
                "expected_latest_completed_trade_date",
                "session_status",
                "publication_grace_applied",
                "fallback_policy_used",
                "provisional_candidate_status",
            ]:
                if field in item:
                    result[field] = item[field]
            caveats = list(item.get("caveats", []))
            classification = item.get("field_validation", {}).get("instrument_classification", {}) if isinstance(item.get("field_validation"), dict) else {}
            if classification.get("coverage_mode") == "bounded_seed_only" and classification.get("classification_status") == "unclassified":
                caveats = [c for c in caveats if c != "unclassified rows are excluded from deterministic metrics and AI context by default"]
                caveats.extend(["legacy_classifier_coverage_drift", "canonical_identity_preserved_from_verified_execution_binding"])
            if caveats:
                result["caveats"] = sorted(set(caveats))
            return result

    return {
        "currentness_status": "calendar_status_unresolved",
        "caveats": ["no_eod_currentness_found_in_artifact"],
    }


def project_target_evidence(
    canonical_target_id: str,
    lineage: LineageMap,
    requested_data_needs: list[str],
    citation_map: dict[str, list[str]], projector_version: str = CURRENT_PROJECTOR_VERSION,
) -> TargetEvidenceProjection:
    """Project the evidence for one canonical target.

    Parameters
    ----------
    canonical_target_id:
        The resolved target.
    lineage:
        The full lineage map from lineage_resolver.build_lineage_map().
    requested_data_needs:
        Sorted list of requested data_need types.
    citation_map:
        Map from (canonical_target_id, data_need) → list[citation_id].
        Key format: f"{canonical_target_id}::{data_need}".
    """
    target_bindings = lineage.bindings.get(canonical_target_id, {})
    proj = TargetEvidenceProjection()

    def _cite(data_need: str) -> list[str]:
        return citation_map.get(f"{canonical_target_id}::{data_need}", [])

    if "identity" in requested_data_needs:
        binding = target_bindings.get("identity")
        projector = _project_envelope_legacy if projector_version == LEGACY_PROJECTOR_VERSION else (_project_envelope_v1_1 if projector_version == PREVIOUS_PROJECTOR_VERSION else _project_envelope)
        proj.identity = projector(binding, _cite("identity"))

    if "current_observation" in requested_data_needs:
        binding = target_bindings.get("current_observation")
        projector = _project_envelope_legacy if projector_version == LEGACY_PROJECTOR_VERSION else (_project_envelope_v1_1 if projector_version == PREVIOUS_PROJECTOR_VERSION else _project_envelope)
        proj.current_observation = projector(binding, _cite("current_observation"))

    if _OFFICIAL_EOD_NEED in requested_data_needs:
        binding = target_bindings.get(_OFFICIAL_EOD_NEED)
        proj.official_eod_reference = (_project_official_eod_legacy if projector_version == LEGACY_PROJECTOR_VERSION else _project_official_eod)(binding, _cite(_OFFICIAL_EOD_NEED))

    if "recent_performance" in requested_data_needs:
        binding = target_bindings.get("recent_performance")
        projector = _project_envelope_legacy if projector_version == LEGACY_PROJECTOR_VERSION else (_project_envelope_v1_1 if projector_version == PREVIOUS_PROJECTOR_VERSION else _project_envelope)
        proj.recent_performance = projector(binding, _cite("recent_performance"))

    if "session_status" in requested_data_needs:
        binding = target_bindings.get("session_status")
        projector = _project_envelope_legacy if projector_version == LEGACY_PROJECTOR_VERSION else (_project_envelope_v1_1 if projector_version == PREVIOUS_PROJECTOR_VERSION else _project_envelope)
        proj.session_status = projector(binding, _cite("session_status"))

    if "source_currentness" in requested_data_needs:
        binding = target_bindings.get("source_currentness")
        projector = _project_envelope_legacy if projector_version == LEGACY_PROJECTOR_VERSION else (_project_envelope_v1_1 if projector_version == PREVIOUS_PROJECTOR_VERSION else _project_envelope)
        proj.source_currentness = projector(binding, _cite("source_currentness"))

    if "evidence_quality" in requested_data_needs:
        binding = target_bindings.get("evidence_quality")
        projector = _project_envelope_legacy if projector_version == LEGACY_PROJECTOR_VERSION else (_project_envelope_v1_1 if projector_version == PREVIOUS_PROJECTOR_VERSION else _project_envelope)
        proj.evidence_quality = projector(binding, _cite("evidence_quality"))

    return proj
