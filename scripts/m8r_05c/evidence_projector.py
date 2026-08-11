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

    if binding.status == "failed":
        return EvidenceEnvelopeProjection(
            status="failed",
            caveats=[f"operation_failed:{binding.error_code or 'unknown'}"],
        )

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

    # Extract from artifacts.
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
            )
            if not currentness_status:
                continue
            result: dict = {"currentness_status": currentness_status}
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
            caveats = item.get("caveats", [])
            if caveats:
                result["caveats"] = caveats
            return result

    return {
        "currentness_status": "calendar_status_unresolved",
        "caveats": ["no_eod_currentness_found_in_artifact"],
    }


def project_target_evidence(
    canonical_target_id: str,
    lineage: LineageMap,
    requested_data_needs: list[str],
    citation_map: dict[str, list[str]],
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
        proj.identity = _project_envelope(binding, _cite("identity"))

    if "current_observation" in requested_data_needs:
        binding = target_bindings.get("current_observation")
        proj.current_observation = _project_envelope(binding, _cite("current_observation"))

    if _OFFICIAL_EOD_NEED in requested_data_needs:
        binding = target_bindings.get(_OFFICIAL_EOD_NEED)
        proj.official_eod_reference = _project_official_eod(binding, _cite(_OFFICIAL_EOD_NEED))

    if "recent_performance" in requested_data_needs:
        binding = target_bindings.get("recent_performance")
        proj.recent_performance = _project_envelope(binding, _cite("recent_performance"))

    if "session_status" in requested_data_needs:
        binding = target_bindings.get("session_status")
        proj.session_status = _project_envelope(binding, _cite("session_status"))

    if "source_currentness" in requested_data_needs:
        binding = target_bindings.get("source_currentness")
        proj.source_currentness = _project_envelope(binding, _cite("source_currentness"))

    if "evidence_quality" in requested_data_needs:
        binding = target_bindings.get("evidence_quality")
        proj.evidence_quality = _project_envelope(binding, _cite("evidence_quality"))

    return proj
