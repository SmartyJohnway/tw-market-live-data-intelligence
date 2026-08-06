"""Deterministic citation builder for M8R-05C.

Builds stable, unique citation IDs from evidence artifact lineage.
All citations reference relative paths only — never absolute local paths.

Rules:
- Each evidence artifact produces exactly one citation per (target, data_need).
- Citations are deduplicated if the same artifact serves multiple operations.
- Citation IDs are deterministic: based on operation_id + artifact sha256 prefix.
- Only artifacts with actual content produce citations.
- Unused citations are not emitted in the result.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .canonical import sha256_json
from .lineage_resolver import LineageMap, OperationBinding
from .models import CitationProjection, CitationToOperationEntry

_CITATION_ID_PREFIX = "cite-"
_CITATION_ID_LEN = 16


def _build_citation_id(operation_id: str, artifact_relative_path: str) -> str:
    """Deterministic citation ID from operation and artifact path."""
    scope = {"operation_id": operation_id, "relative_path": artifact_relative_path}
    digest = sha256_json(scope)
    return _CITATION_ID_PREFIX + digest[:_CITATION_ID_LEN]


@dataclass
class CitationIndex:
    """Full citation index for one projection run."""
    # citation_id → CitationProjection
    all_citations: dict[str, CitationProjection] = field(default_factory=dict)
    # (canonical_target_id, data_need) → list[citation_id]
    # Key: f"{canonical_target_id}::{data_need}"
    target_need_citations: dict[str, list[str]] = field(default_factory=dict)
    # Flat audit entries for audit package
    audit_entries: list[CitationToOperationEntry] = field(default_factory=list)
    # Set of used citation_ids (populated by result_builder after assembly)
    used_citation_ids: set[str] = field(default_factory=set)


def build_citation_index(
    lineage: LineageMap,
    bundle: dict,
) -> CitationIndex:
    """Build the complete citation index from the lineage map.

    Pure function: no network, no clock, no side effects.
    """
    index = CitationIndex()

    # Build a sha256 lookup from bundle artifact_inventory.
    artifact_sha_lookup: dict[str, str] = {}
    artifact_contract_lookup: dict[str, str] = {}
    for entry in bundle.get("artifact_inventory", []):
        if isinstance(entry, dict):
            rel_path = entry.get("relative_path")
            sha = entry.get("sha256")
            contract = entry.get("evidence_contract", "")
            if rel_path and sha:
                artifact_sha_lookup[rel_path] = sha
                artifact_contract_lookup[rel_path] = contract

    # Get bundle finalized_at for retrieved_at.
    bundle_finalized_at = bundle.get("finalized_at", "")

    # Iterate over all (target, data_need) bindings.
    for canonical_target_id, need_map in lineage.bindings.items():
        for data_need, binding in need_map.items():
            if not isinstance(binding, OperationBinding):
                continue
            if binding.status == "failed" or not binding.evidence_artifacts:
                # No successful artifacts → no citations.
                key = f"{canonical_target_id}::{data_need}"
                index.target_need_citations[key] = []
                continue

            cit_ids: list[str] = []
            for art_info in binding.evidence_artifacts:
                if not isinstance(art_info, dict):
                    continue
                rel_path = art_info.get("relative_path")
                if not rel_path:
                    continue

                sha256 = artifact_sha_lookup.get(rel_path, art_info.get("sha256", ""))
                evidence_contract = artifact_contract_lookup.get(
                    rel_path, art_info.get("schema_version", "")
                )
                cit_id = _build_citation_id(binding.operation_id, rel_path)

                if cit_id not in index.all_citations:
                    # Determine source_family from evidence_contract or executor_id.
                    source_family = binding.executor_id or "unknown"

                    citation = CitationProjection(
                        citation_id=cit_id,
                        source_family=source_family,
                        retrieved_at=bundle_finalized_at,
                        artifact_reference=rel_path,  # always relative
                        source_contract_id=evidence_contract or None,
                        normalized_evidence_hash=sha256 or None,
                    )
                    index.all_citations[cit_id] = citation

                    audit_entry = CitationToOperationEntry(
                        citation_id=cit_id,
                        operation_id=binding.operation_id,
                        capability_id=binding.capability_id,
                        executor_id=binding.executor_id,
                        artifact_relative_path=rel_path,
                        artifact_hash=sha256 or "",
                        canonical_target_id=canonical_target_id,
                        requested_data_need=data_need,
                    )
                    index.audit_entries.append(audit_entry)

                cit_ids.append(cit_id)

            key = f"{canonical_target_id}::{data_need}"
            index.target_need_citations[key] = cit_ids

    return index


def get_citations_for_target(
    index: CitationIndex,
    canonical_target_id: str,
    used_citation_ids: set[str],
) -> list[CitationProjection]:
    """Return the list of citations used for one target.

    Only emits citations referenced in used_citation_ids.
    """
    results: list[CitationProjection] = []
    seen: set[str] = set()
    for cit_id, citation in index.all_citations.items():
        if cit_id in used_citation_ids and cit_id not in seen:
            # Check that this citation belongs to this target.
            # We check all data_need keys for this target.
            for data_need_key, cit_ids in index.target_need_citations.items():
                if data_need_key.startswith(f"{canonical_target_id}::"):
                    if cit_id in cit_ids:
                        results.append(citation)
                        seen.add(cit_id)
                        break
    return results
