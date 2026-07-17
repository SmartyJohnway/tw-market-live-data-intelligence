"""Deterministic, evidence-only migration for historical M8R-03E v1 packages."""
from __future__ import annotations
import copy
from scripts.m8r_03e_context_validator import (
    PACKAGE_SCHEMA_VERSION, artifact_hash_without, canonical_json, sha256_json,
    validate_schema, validate_watchlist_ai_context_package,
)

# Product/conversation instructions are deliberately discarded, never recast as facts.
PRODUCT_FIELDS = {"conversation_scope", "prohibitions", "allowed_interpretations", "prohibited_inferences"}
EVIDENCE_RESTRICTION_TOKENS = (
    "current", "stale", "source", "evidence", "identity", "lifecycle", "history",
    "observation", "eod", "return", "calculation", "price", "adjusted",
)
CALCULATION_TOKENS = ("return", "calculation", "price", "adjusted", "performance")


def _is_evidence_restriction(item: object) -> bool:
    text = canonical_json(item).lower()
    return any(token in text for token in EVIDENCE_RESTRICTION_TOKENS)


def _limitation(item: object, *, target_id: str | None, scope: str, ordinal: int) -> dict:
    text = canonical_json(item)
    return {
        "code": "legacy_evidence_restriction_" + sha256_json({"item": item, "ordinal": ordinal})[:12],
        "scope": scope,
        "target_id": target_id,
        "reason": "Historical v1 evidence-domain restriction retained without importing conversation policy: " + text,
    }


def _finalize(package: dict) -> None:
    package["context_package_id"] = "m8r03e-context-" + sha256_json(
        {k: package[k] for k in package if k not in {"context_package_id", "package_hash"}}
    )[:16]
    package["package_hash"] = artifact_hash_without(package, "package_hash")
    budget = package.get("context_budget", {})
    if budget.get("serialized_size_basis") == "canonical_json_utf8_final_package_including_package_hash":
        budget["final_serialized_bytes"] = len(canonical_json(package).encode())
        package["package_hash"] = artifact_hash_without(package, "package_hash")


def migrate_watchlist_ai_context_package_v1_to_v2(v1_package: dict) -> dict:
    """Validate historical v1, preserve evidence, and emit a canonical v2 package.

    The v1 manifest/count compatibility record is evidence lineage metadata, not a
    substitute for the v2 manifest. Legacy product fields are dropped unless an
    individual restriction explicitly describes evidence or calculation scope.
    """
    validate_schema(v1_package, "m8r_watchlist_ai_context_package.v1.schema.json")
    source = copy.deepcopy(v1_package)
    package = {k: copy.deepcopy(v) for k, v in source.items() if k not in PRODUCT_FIELDS}
    package["schema_version"] = PACKAGE_SCHEMA_VERSION
    limitations = list(package.get("evidence_limitations", []))
    calc_by_target: dict[str | None, list[str]] = {}
    for ordinal, prohibition in enumerate(source.get("prohibitions", [])):
        if not _is_evidence_restriction(prohibition):
            continue
        target_id = prohibition.get("target_id")
        limitations.append(_limitation(prohibition, target_id=target_id, scope=prohibition.get("scope", "global"), ordinal=ordinal))
        if any(token in canonical_json(prohibition).lower() for token in CALCULATION_TOKENS):
            calc_by_target.setdefault(target_id, []).append("legacy_evidence_restriction:" + prohibition.get("code", "unknown"))
    for ordinal, target in enumerate(package["targets"]):
        legacy = {k: target.pop(k) for k in ("allowed_interpretations", "prohibited_inferences") if k in target}
        target["calculation_limitations"] = list(target.get("calculation_limitations", []))
        for item in legacy.get("prohibited_inferences", []):
            if _is_evidence_restriction(item):
                limitations.append(_limitation(item, target_id=target.get("target_id"), scope="target", ordinal=ordinal))
                if any(token in canonical_json(item).lower() for token in CALCULATION_TOKENS):
                    target["calculation_limitations"].append("legacy_evidence_restriction")
        target["calculation_limitations"].extend(calc_by_target.get(target.get("target_id"), []))
    package["evidence_limitations"] = limitations
    package.setdefault("source_lineage", {})["migration"] = {
        "from_schema_version": source["schema_version"],
        "strategy": "evidence_only_drop_product_policy_recompute_identity",
        "legacy_counts": {
            "target_count": len(source.get("targets", [])),
            "citation_count": len(source.get("citation_index", [])),
            "missing_evidence_count": len(source.get("missing_evidence", [])),
            "caveat_count": len(source.get("caveats", [])),
        },
        "v2_counts_verified": True,
    }
    _finalize(package)
    # Historical package alone carries lineage pointers, not every source artifact.
    # Schema validation is therefore the applicable self-contained v2 validation here.
    validate_schema(package, "m8r_watchlist_ai_context_package.v2.schema.json")
    if package["package_hash"] != artifact_hash_without(package, "package_hash"):
        raise ValueError("v1_to_v2_migration_hash_failed")
    return package
