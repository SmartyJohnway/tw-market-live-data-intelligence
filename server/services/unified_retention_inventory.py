"""Read-only, fail-closed retention classification for known TW-Market state families.

This module is policy metadata only. It does not inspect or mutate files, databases,
timestamps, or network state. Callers must bind an artifact to a known family using
governed lineage/ownership; path names and extensions are not classification authority.
"""
from __future__ import annotations

from typing import Any


_COMMON_REQUIRED = ("explicit_future_policy", "verified_backup_manifest_and_hashes")


def _entry(
    family: str,
    state_class: str,
    authority_role: str,
    replay_required: str,
    audit_required: str,
    rebuildable: str,
    network_required: str,
    mutable_authority_required: str,
    deletion_eligible: str,
    prerequisites: tuple[str, ...],
    backup_tier: str,
    integrity_binding: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "artifact_family": family,
        "state_class": state_class,
        "authority_role": authority_role,
        "replay_required": replay_required,
        "audit_required": audit_required,
        "rebuildable": rebuildable,
        "network_required_to_rebuild": network_required,
        "current_mutable_authority_required_to_rebuild": mutable_authority_required,
        "deletion_eligible": deletion_eligible,
        "deletion_prerequisites": list(prerequisites),
        "backup_tier": backup_tier,
        "integrity_binding": integrity_binding,
        "notes": notes,
    }


_FAMILIES = (
    _entry("security_master_active_release_pointer", "CANONICAL_USER_STATE", "active identity authority pointer", "NO", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", ("explicit_state_replacement", "verified_backup_manifest_and_hashes"), "CORE", "release_id_and_manifest_hash", "Current pointer selects installation identity authority; do not replace from a fresh download."),
    _entry("security_master_release_history_and_rollback_artifacts", "CANONICAL_USER_STATE", "versioned identity authority and rollback history", "CONDITIONAL", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", ("supported_release_supersession_contract", "verified_backup_manifest_and_hashes"), "CORE", "release_manifest_content_schema_hashes", "Immutable qualified releases support history and rollback."),
    _entry("persistent_watchlists_and_revision_database", "CANONICAL_USER_STATE", "durable user state", "NO", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", ("explicit_user_state_export_or_replacement", "verified_backup_manifest_and_hashes"), "CORE", "sqlite_integrity_and_revision_hash_chain", "Includes current Watchlists, revisions, and tombstones."),
    _entry("user_product_settings", "CANONICAL_USER_STATE", "durable user configuration", "NO", "CONDITIONAL", "UNKNOWN", "NO", "UNKNOWN", "NOT_YET_ELIGIBLE", ("settings_authority_inventory", "verified_backup_manifest_and_hashes"), "CORE", "configuration_schema_if_present", "No single current persisted user-settings store was established; classification remains conservative."),
    _entry("finalized_control_package", "GOVERNED_EVIDENCE", "execution authority and evidence envelope", "YES", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", ("explicit_future_policy", "verified_backup_manifest_and_hashes", "lineage_and_reference_closure"), "FULL_GOVERNED", "control_manifest_member_sha256_and_lineage", "Package contains finalized control, evidence, and execution lineage."),
    _entry("request_and_plan", "GOVERNED_EVIDENCE", "authorized intent and planned scope", "YES", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", _COMMON_REQUIRED, "FULL_GOVERNED", "control_manifest_sha256_and_schema_version", "Retained as finalized package predecessors."),
    _entry("authorization_and_consumption_binding", "GOVERNED_EVIDENCE", "one-shot authorization and binding", "YES", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", _COMMON_REQUIRED, "FULL_GOVERNED", "control_manifest_sha256_and_consumption_lineage", "Never recreate or reuse authority during replay."),
    _entry("execution_claim", "GOVERNED_EVIDENCE", "finalized authorization consumption claim", "YES", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", _COMMON_REQUIRED, "FULL_GOVERNED", "package_hash_and_claim_receipt_binding", "Claim state and identity establish one-shot execution finality."),
    _entry("execution_receipt", "GOVERNED_EVIDENCE", "execution completion record", "YES", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", _COMMON_REQUIRED, "FULL_GOVERNED", "package_hash_and_claim_binding", "Receipt identity and timing are retained execution evidence."),
    _entry("evidence_bundle", "GOVERNED_EVIDENCE", "evidence artifact inventory and lineage", "YES", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", _COMMON_REQUIRED, "FULL_GOVERNED", "bundle_hash_inventory_and_lineage", "Bundle references retained source and operation artifacts."),
    _entry("f3_historical_validation_artifact", "GOVERNED_EVIDENCE", "historical identity validation evidence", "YES", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", ("explicit_future_policy", "verified_backup_manifest_and_hashes", "retained_historical_identity_authority"), "FULL_GOVERNED", "retained_bytes_and_bound_hash", "A2 proves missing historical F3 cannot be rebuilt from current Security Master."),
    _entry("operation_evidence_and_source_snapshots", "GOVERNED_EVIDENCE", "retained source observation and lineage", "YES", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", _COMMON_REQUIRED, "FULL_GOVERNED", "bundle_inventory_and_sha256", "Includes governed payload snapshots required by accepted lineage."),
    _entry("selection_provenance", "GOVERNED_EVIDENCE", "user selection lineage", "CONDITIONAL", "YES", "NOT_REBUILDABLE", "NO", "NO", "PROHIBITED", _COMMON_REQUIRED, "FULL_GOVERNED", "control_manifest_sha256_and_request_binding", "Retained when included in finalized package."),
    _entry("persisted_result_json", "GOVERNED_EVIDENCE", "canonical governed output", "NO", "YES", "DETERMINISTIC_FROM_RETAINED_AUTHORITY", "NO", "NO", "NOT_YET_ELIGIBLE", ("verified_retained_predecessors", "explicit_future_policy", "verified_backup_manifest_and_hashes"), "FULL_GOVERNED", "result_schema_lineage_and_audit_hash", "READ_EXISTING reads these bytes; replay may reproduce in memory from retained authority."),
    _entry("persisted_result_markdown", "GOVERNED_EVIDENCE", "canonical human-readable governed output", "NO", "YES", "DETERMINISTIC_FROM_RETAINED_AUTHORITY", "NO", "NO", "NOT_YET_ELIGIBLE", ("verified_retained_predecessors", "explicit_future_policy", "verified_backup_manifest_and_hashes"), "FULL_GOVERNED", "result_projection_and_package_lineage", "Do not treat as cache while it is a persisted canonical triplet member."),
    _entry("persisted_audit_package", "GOVERNED_EVIDENCE", "canonical audit and lineage record", "YES", "YES", "DETERMINISTIC_FROM_RETAINED_AUTHORITY", "NO", "NO", "PROHIBITED", ("verified_retained_predecessors", "explicit_future_policy", "verified_backup_manifest_and_hashes"), "FULL_GOVERNED", "audit_hash_and_replay_manifest", "Audit and reference metadata are governed evidence, never disposable cache."),
    _entry("persisted_ai_handoff", "REBUILDABLE_DERIVED", "derived projection", "NO", "CONDITIONAL", "DETERMINISTIC_FROM_RETAINED_AUTHORITY", "NO", "NO", "POTENTIALLY_ELIGIBLE", ("prove_not_canonical_release_output", "verified_retained_predecessors", "explicit_future_policy", "verified_backup_manifest_and_hashes"), "DERIVED", "projection_inputs_and_lineage_if_persisted", "L0 treats AI Handoff as rebuildable unless a release contract explicitly retains it."),
    _entry("finalized_package_indexes", "REBUILDABLE_DERIVED", "lookup acceleration", "NO", "NO", "DETERMINISTIC_FROM_RETAINED_AUTHORITY", "NO", "NO", "POTENTIALLY_ELIGIBLE", ("prove_rebuild_from_retained_authority", "explicit_future_policy"), "DERIVED", "source_package_identity_if_bound", "Classification applies only to confirmed indexes, not similarly named governed files."),
    _entry("cache", "UNCLASSIFIED_REQUIRES_POLICY", "unresolved", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "NOT_YET_ELIGIBLE", ("identify_owner_and_lineage",), "UNDETERMINED", "UNDETERMINED", "The label cache alone does not establish ephemerality."),
    _entry("preview_only_temporary_material", "EPHEMERAL", "non-authoritative preview", "NO", "NO", "UNKNOWN", "NO", "NO", "EPHEMERAL", ("prove_preview_only_and_no_governed_references",), "NONE", "no_governed_binding_permitted", "Only material proven preview-only and unreferenced qualifies; deterministic rebuild is not assumed."),
    _entry("temporary_test_acceptance_runtime", "EPHEMERAL", "test-only runtime material", "NO", "NO", "UNKNOWN", "NO", "NO", "EPHEMERAL", ("prove_test_runtime_ownership_and_no_governed_references",), "NONE", "test_runtime_ownership", "Historical acceptance evidence itself is not covered by this family; rebuildability is not assumed."),
    _entry("operational_jsonl_diagnostics", "EPHEMERAL", "non-authoritative diagnosis", "NO", "NO", "UNKNOWN", "NO", "NO", "EPHEMERAL", ("prove_not_governed_audit_or_manifest_input",), "NONE", "runtime_event_schema_and_ownership", "Operational diagnostics are separate from governed Audit; any referenced record must be reclassified."),
    _entry("lifecycle_ownership_runtime_files", "EPHEMERAL", "process ownership/runtime coordination", "NO", "NO", "UNKNOWN", "NO", "NO", "EPHEMERAL", ("prove_no_live_owner_and_runtime_file_ownership",), "NONE", "lifecycle_identity_and_owner_process_binding", "Must not remove active ownership state; rebuildability is not assumed and this classifier performs no cleanup."),
    _entry("unclassified_artifact", "UNCLASSIFIED_REQUIRES_POLICY", "unresolved", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "NOT_YET_ELIGIBLE", ("identify_owner_authority_lineage_and_references",), "UNDETERMINED", "UNDETERMINED", "Unknown is never inferred to be ephemeral."),
)

_BY_FAMILY = {item["artifact_family"]: item for item in _FAMILIES}


def retention_inventory() -> tuple[dict[str, Any], ...]:
    """Return a deterministic copy of the bounded family registry."""
    return tuple({**item, "deletion_prerequisites": list(item["deletion_prerequisites"])} for item in _FAMILIES)


def classify_artifact_family(artifact_family: str) -> dict[str, Any]:
    """Return policy metadata for a caller-established family; unknown values fail closed.

    This lookup does not prove that any concrete artifact belongs to the family and does not
    authorize deletion. Use ``classify_artifact`` when evaluating a concrete artifact binding.
    """
    entry = _BY_FAMILY.get(artifact_family)
    if entry is None:
        entry = _BY_FAMILY["unclassified_artifact"]
    return {**entry, "artifact_family": artifact_family if entry["artifact_family"] == "unclassified_artifact" else entry["artifact_family"],
            "deletion_prerequisites": list(entry["deletion_prerequisites"])}


def classify_artifact(*, artifact_family: str | None = None, authority_binding_verified: bool = False,
                      governed_reference_found: bool | None = None) -> dict[str, Any]:
    """Fail closed unless the caller proves family binding and absence of conflicting lineage.

    This intentionally accepts no path-based classification interface.
    """
    if not isinstance(artifact_family, str) or not authority_binding_verified:
        return classify_artifact_family("unclassified_artifact")
    result = classify_artifact_family(artifact_family)
    if result["state_class"] == "EPHEMERAL" and governed_reference_found is not False:
        return classify_artifact_family("unclassified_artifact")
    return result
