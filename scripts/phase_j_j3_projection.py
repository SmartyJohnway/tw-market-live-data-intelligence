"""Closed, deterministic projection helpers for the J1 -> J3 acceptance contract."""
from __future__ import annotations

import hashlib
import json
from collections import Counter

EXPECTATION_PROJECTIONS = {
    "identity_expectation": ("identity", "identity_expectation"),
    "source_expectation": ("source", "source_expectation"),
    "coverage_expectation": ("source", "coverage_expectation"),
    "period_expectation": ("period", "period_expectation"),
    "timing_expectation": ("period", "timing_expectation"),
    "currentness_expectation": ("currentness", "currentness_expectation"),
    "missing_expectation": ("missing", "missing_expectation"),
    "partial_expectation": ("partial", "partial_expectation"),
    "corporate_action_expectation": ("corporate_action", "corporate_action_expectation"),
    "interpretation_guard_expectation": ("corporate_action", "interpretation_guard_expectation"),
    "authorization_expectation": ("authorization", "authorization_expectation"),
    "resource_bound_expectation": ("bounded_execution", "resource_bound_expectation"),
    "citation_expectation": ("citations_lineage", "citation_expectation"),
    "lineage_expectation": ("citations_lineage", "lineage_expectation"),
}
ASSERTION_OPERATORS = {
    "equals": ("equals", lambda assertion: assertion["value"]),
    "is_true": ("equals", lambda assertion: True),
}
FORBIDDEN_CONTENT_FIELDS = ("claim_id", "description", "semantic_class", "handoff_text_marker")


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_hash(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_assertion(scenario_id: str, assertion: dict) -> dict:
    required_fields = {"assertion_id", "context", "path", "operator"}
    allowed_fields = required_fields | {"value"}
    if not required_fields <= set(assertion) or not set(assertion) <= allowed_fields:
        raise ValueError(f"J1 assertion has unmapped semantic fields: {sorted(set(assertion) - allowed_fields)}")
    operator = assertion.get("operator")
    if operator not in ASSERTION_OPERATORS:
        raise ValueError(f"PHASE_J_J3_R1_UNMAPPABLE_J1_ASSERTION_OPERATOR: {operator!r}")
    if operator == "equals" and "value" not in assertion:
        raise ValueError("J1 equals assertion is missing its expected value")
    if operator == "is_true" and "value" in assertion:
        raise ValueError("J1 is_true assertion contains an unmapped explicit value")
    predicate, expected = ASSERTION_OPERATORS[operator]
    return {
        "scenario_id": scenario_id,
        "assertion_id": assertion["assertion_id"],
        "context": assertion["context"],
        "path": assertion["path"],
        "predicate": predicate,
        "expected": expected(assertion),
    }


def forbidden_content(claim: dict) -> dict:
    # J1 omits optional classification/marker fields for some claims. Null is
    # the explicit, stable representation of that absence in J3.
    unknown = set(claim) - set(FORBIDDEN_CONTENT_FIELDS)
    if unknown:
        raise ValueError(f"J1 forbidden claim has unmapped semantic fields: {sorted(unknown)}")
    return {field: claim.get(field) for field in FORBIDDEN_CONTENT_FIELDS}


def source_pointer(scenario_index: int, family: str, suffix: str = "") -> str:
    base = f"/scenarios/{scenario_index}/{family}"
    return f"{base}/{suffix}" if suffix else base


def target_pointer(scenario_index: int, dimension: str, key: str, suffix: str = "") -> str:
    base = f"/scenarios/{scenario_index}/dimensions/{dimension}/expectations/{key}"
    return f"{base}/{suffix}" if suffix else base


def mapping(source_value, target_value, *, scenario_id, source, target):
    source_hash, target_hash = canonical_hash(source_value), canonical_hash(target_value)
    return {
        "scenario_id": scenario_id,
        "source_pointer": source,
        "target_pointer": target,
        "source_canonical_sha256": source_hash,
        "target_canonical_sha256": target_hash,
        "match": source_hash == target_hash and source_value == target_value,
    }


def build_content_trace(registry: dict, golden: dict) -> dict:
    by_id = {row["scenario_id"]: row for row in golden["scenarios"]}
    assertion_maps, family_maps, forbidden_maps, outcome_maps, readiness_maps = [], [], [], [], []
    for scenario_index, source_row in enumerate(registry["scenarios"]):
        sid = source_row["scenario_id"]
        target_row = by_id[sid]
        source_assertions = source_row["expected_semantic_assertions"]
        target_assertions = {row["assertion_id"]: (index, row) for index, row in enumerate(target_row["assertions"])}
        for assertion_index, assertion in enumerate(source_assertions):
            normalized = normalize_assertion(sid, assertion)
            target_index, target = target_assertions[assertion["assertion_id"]]
            target_semantics = {key: target[key] for key in ("scenario_id", "assertion_id", "context", "path", "predicate", "expected")}
            assertion_maps.append(mapping(
                normalized, target_semantics, scenario_id=sid,
                source=source_pointer(scenario_index, "expected_semantic_assertions", str(assertion_index)),
                target=f"/scenarios/{scenario_index}/assertions/{target_index}",
            ))
        for family, (dimension, key) in EXPECTATION_PROJECTIONS.items():
            source_value = source_row.get(family)
            target_value = target_row["dimensions"][dimension]["expectations"].get(key)
            family_maps.append(mapping(
                source_value, target_value, scenario_id=sid,
                source=source_pointer(scenario_index, family), target=target_pointer(scenario_index, dimension, key),
            ))
        source_claims = {claim["claim_id"]: claim for claim in source_row["forbidden_claims"]}
        target_claims = {claim["claim_id"]: (index, claim) for index, claim in enumerate(target_row["forbidden_claims"])}
        for claim_id, claim in source_claims.items():
            source_claim_index = next(i for i, item in enumerate(source_row["forbidden_claims"]) if item["claim_id"] == claim_id)
            target_claim_index, target = target_claims[claim_id]
            target_content = {field: target.get(field) for field in FORBIDDEN_CONTENT_FIELDS}
            forbidden_maps.append(mapping(
                forbidden_content(claim), target_content, scenario_id=sid,
                source=source_pointer(scenario_index, "forbidden_claims", str(source_claim_index)),
                target=f"/scenarios/{scenario_index}/forbidden_claims/{target_claim_index}",
            ))
        outcomes = source_row["accepted_fail_closed_outcomes"]
        target_outcomes = target_row["accepted_fail_closed_outcomes"]
        outcome_maps.append(mapping(
            outcomes, target_outcomes, scenario_id=sid,
            source=source_pointer(scenario_index, "accepted_fail_closed_outcomes"),
            target=f"/scenarios/{scenario_index}/accepted_fail_closed_outcomes",
        ))
        readiness_maps.append(mapping(
            source_row["current_readiness_status"], target_row["readiness_status"], scenario_id=sid,
            source=source_pointer(scenario_index, "current_readiness_status"),
            target=f"/scenarios/{scenario_index}/readiness_status",
        ))
    return {
        "assertion_content_mappings": assertion_maps,
        "expectation_family_mappings": family_maps,
        "forbidden_claim_content_mappings": forbidden_maps,
        "accepted_fail_closed_mappings": outcome_maps,
        "readiness_status_mappings": readiness_maps,
    }


def operator_inventory(registry: dict) -> dict[str, int]:
    return dict(sorted(Counter(
        assertion["operator"]
        for scenario in registry["scenarios"]
        for assertion in scenario["expected_semantic_assertions"]
    ).items()))


def project_golden(registry: dict, golden: dict) -> dict:
    """Refresh only J1-derived content; retain J3 dimension and evidence metadata."""
    by_id = {row["scenario_id"]: row for row in golden["scenarios"]}
    for source_row in registry["scenarios"]:
        sid = source_row["scenario_id"]
        target = by_id[sid]
        target["readiness_status"] = source_row["current_readiness_status"]
        existing_dimensions = {
            assertion["assertion_id"]: assertion.get("dimension")
            for assertion in target["assertions"]
        }
        existing_refs = {
            assertion["assertion_id"]: assertion.get("authority_ref")
            for assertion in target["assertions"]
        }
        projected = []
        for assertion in source_row["expected_semantic_assertions"]:
            normalized = normalize_assertion(sid, assertion)
            normalized["dimension"] = existing_dimensions.get(assertion["assertion_id"], "citations_lineage")
            normalized["authority_ref"] = existing_refs.get(assertion["assertion_id"])
            projected.append(normalized)
        target["assertions"] = projected
        for family, (dimension, key) in EXPECTATION_PROJECTIONS.items():
            target["dimensions"][dimension].setdefault("expectations", {})[key] = source_row.get(family)
        target["accepted_fail_closed_outcomes"] = source_row["accepted_fail_closed_outcomes"]
        existing_claims = {claim["claim_id"]: claim for claim in target["forbidden_claims"]}
        projected_claims = []
        for source_claim in source_row["forbidden_claims"]:
            claim = dict(existing_claims.get(source_claim["claim_id"], {}))
            claim.update(forbidden_content(source_claim))
            claim.setdefault("dimensions", ["no_trading"])
            claim["authority_ref"] = f"phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json#{sid}/forbidden_claims/{source_claim['claim_id']}"
            projected_claims.append(claim)
        target["forbidden_claims"] = projected_claims
    golden["authority_status"] = "J3_R1_FROZEN_ACCEPTANCE_CANDIDATE_PENDING_REVIEW"
    golden["baseline_binding"].update({
        "head": "2d1b51e531f36f5f032971ad7916d805c9af1276",
        "tree": "ed2d1c4ee6c3f9c1a198fd3c792a5f0ccc6afdec",
        "owner_authorization_sha256": "8c3e497debe7329f4051a2d0f4884cbe2505dace97395f1beca46ab1d3f2d047",
    })
    golden["authority_reviews"].update({"r1_review": "5481919568"})
    golden["phase_state"]["J3"] = "R1_FROZEN_ACCEPTANCE_CANDIDATE_PENDING_REVIEW"
    return golden
