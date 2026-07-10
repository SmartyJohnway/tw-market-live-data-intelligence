from __future__ import annotations

from copy import deepcopy
from typing import Any

ARTIFACT_SCHEMA_VERSION = "m7g_safe_context_artifact.v1"
MANIFEST_SCHEMA_VERSION = "m7g_safe_context_manifest.v1"
VALIDATION_RESULT_SCHEMA_VERSION = "m7g_safe_artifact_validation_result.v1"
SOURCE_HEALTH_SCHEMA_VERSION = "m7g_source_health.v1"
ALLOWED_SOURCE_HEALTH_STATUSES = {"artifact_reported", "unknown", "stale", "degraded", "unavailable"}

RAW_FORBIDDEN_KEYS = {
    "raw_payload",
    "twse_mis_rich_facts",
    "raw_rich_facts",
    "raw_unknown_facts",
    "full_ladder",
    "bid_prices",
    "ask_prices",
    "source_investigation_notes",
    "response_sample",
    "raw_fields_sample",
}

REQUIRED_GOVERNANCE_TRUE = {
    "not_trading_signal",
    "not_recommendation",
    "not_market_prediction",
    "not_capital_flow",
    "not_full_market_breadth",
}
REQUIRED_GOVERNANCE_FALSE = {"raw_payload_exposed", "raw_rich_facts_exposed", "raw_full_ladder_exposed"}
REQUIRED_CLOCK_FIELDS = {"currentness_label", "calendar_confidence", "session_state", "freshness_state"}
TRADING_CLAIM_KEYS = {
    "trading_advice", "recommendation", "trading_signal", "target_price", "support", "resistance",
    "capital_flow", "sector_rotation", "full_market_breadth", "bullish", "bearish",
}


def _detect_forbidden_keys(value: Any) -> list[str]:
    detected: set[str] = set()
    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key in RAW_FORBIDDEN_KEYS:
                    detected.add(key)
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(value)
    return sorted(detected)


def _has_positive_trading_claims(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    for key, child in value.items():
        lowered = str(key).lower()
        if lowered in TRADING_CLAIM_KEYS and child not in (False, None, "", "not_applicable"):
            return True
        if isinstance(child, dict) and _has_positive_trading_claims(child):
            return True
        if isinstance(child, list) and any(isinstance(item, dict) and _has_positive_trading_claims(item) for item in child):
            return True
    return False


def validate_m7g_safe_context_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    """
    Return a validation result dict.
    Must not mutate input artifact.
    Must not perform network calls.
    Must not read files.
    Must validate an already-loaded dict.
    """
    snapshot = deepcopy(artifact)
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    source_health_warnings: list[str] = []
    source_health_status = "unknown"
    source_health_schema_version = None

    def error(code: str, reason: str) -> None:
        errors.append({"code": code, "reason": reason})

    if not isinstance(artifact, dict):
        artifact = {}
        error("artifact_not_object", "Artifact must be a JSON object.")

    if artifact.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        error("invalid_schema_version", "Artifact schema_version is missing or unsupported.")
    for key in ("safe_for_frontend", "safe_for_ai_handoff"):
        if artifact.get(key) is not True:
            error(f"{key}_not_true", f"{key} must be true.")
    for key in ("raw_payload_exposed", "raw_rich_facts_exposed", "raw_full_ladder_exposed", "raw_forbidden_values_present"):
        if artifact.get(key) is not False:
            error(f"{key}_not_false", f"{key} must be false.")

    manifest = artifact.get("artifact_manifest")
    if not isinstance(manifest, dict) or manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        error("invalid_manifest", "artifact_manifest with supported schema_version is required.")

    governance = artifact.get("governance")
    if not isinstance(governance, dict):
        error("missing_governance", "governance object is required.")
    else:
        for key in REQUIRED_GOVERNANCE_TRUE:
            if governance.get(key) is not True:
                error(f"governance_{key}_not_true", f"governance.{key} must be true.")
        for key in REQUIRED_GOVERNANCE_FALSE:
            if governance.get(key) is not False:
                error(f"governance_{key}_not_false", f"governance.{key} must be false.")

    clock = artifact.get("market_clock_session_state")
    if not isinstance(clock, dict):
        error("missing_market_clock_session_state", "market_clock_session_state object is required.")
    else:
        for key in REQUIRED_CLOCK_FIELDS:
            if not clock.get(key):
                error(f"missing_clock_{key}", f"market_clock_session_state.{key} is required.")

    source_health = artifact.get("source_health")
    if source_health is None:
        source_health_warnings.append("missing_source_health_metadata")
    elif not isinstance(source_health, dict):
        error("invalid_source_health", "source_health must be an object when provided.")
    else:
        source_health_status = source_health.get("health_status") or "unknown"
        source_health_schema_version = source_health.get("schema_version")
        if source_health_status not in ALLOWED_SOURCE_HEALTH_STATUSES:
            error("invalid_source_health", "source_health.health_status is unsupported.")
        if source_health_schema_version != SOURCE_HEALTH_SCHEMA_VERSION:
            error("invalid_source_health", "source_health.schema_version is unsupported.")

    observations = artifact.get("observations")
    if not isinstance(observations, list):
        error("observations_not_list", "observations must be a list.")
        observation_count = 0
    else:
        observation_count = len(observations)
        for index, observation in enumerate(observations):
            if not isinstance(observation, dict):
                error("observation_not_object", f"observations[{index}] must be an object.")

    forbidden = _detect_forbidden_keys(artifact)
    if forbidden:
        error("raw_forbidden_keys_detected", "Raw forbidden key names were detected; values are not exposed.")
    if _has_positive_trading_claims(artifact):
        error("trading_claim_detected", "Trading advice or positive signal claim fields are not allowed.")

    accepted = not errors
    result = {
        "schema_version": VALIDATION_RESULT_SCHEMA_VERSION,
        "validation_status": "accepted" if accepted else "rejected",
        "safe_to_render": accepted,
        "safe_for_ai_handoff": accepted and artifact.get("safe_for_ai_handoff") is True,
        "errors": errors,
        "warnings": warnings,
        "artifact_id": artifact.get("artifact_id"),
        "artifact_schema_version": artifact.get("schema_version"),
        "observation_count": observation_count,
        "raw_forbidden_keys_detected": forbidden,
        "raw_payload_exposed": artifact.get("raw_payload_exposed") is True,
        "raw_rich_facts_exposed": artifact.get("raw_rich_facts_exposed") is True,
        "raw_full_ladder_exposed": artifact.get("raw_full_ladder_exposed") is True,
        "source_health_status": source_health_status,
        "source_health_schema_version": source_health_schema_version,
        "source_health_warnings": source_health_warnings,
    }
    assert snapshot == deepcopy(artifact)  # defensive no-mutation check, no user data returned
    return result


def build_m7g_safe_artifact_rejection_summary(validation_result: dict[str, Any]) -> dict[str, Any]:
    """
    Build a frontend/operator-safe rejection summary.
    Must not include raw values.
    """
    return {
        "schema_version": "m7g_safe_artifact_rejection_summary.v1",
        "validation_status": validation_result.get("validation_status"),
        "safe_to_render": False,
        "safe_for_ai_handoff": False,
        "error_codes": [item.get("code") for item in validation_result.get("errors", []) if isinstance(item, dict)],
        "reasons": [item.get("reason") for item in validation_result.get("errors", []) if isinstance(item, dict)],
        "raw_forbidden_keys_detected": list(validation_result.get("raw_forbidden_keys_detected", [])),
    }
