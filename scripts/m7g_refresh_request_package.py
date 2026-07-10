from __future__ import annotations

from typing import Any

REFRESH_REQUEST_PACKAGE_SCHEMA_VERSION = "m7g_controlled_refresh_request_package.v1"
CONFIRMATION_PHRASE = "PREPARE_REFRESH_REQUEST_ONLY"
ALLOWED_SOURCE_FAMILIES = {"TWSE_MIS", "TWSE_OPENAPI", "TAIFEX_OPENAPI"}
_ALLOWED_CONTEXT_MODES = {"static_demo", "loaded_safe_artifact"}
_RAW_FORBIDDEN_KEYS = {
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


def _observation_symbols(active_context: dict[str, Any]) -> set[str]:
    observations = active_context.get("observations")
    if not isinstance(observations, list):
        return set()
    return {str(item.get("symbol")) for item in observations if isinstance(item, dict) and item.get("symbol")}


def _observation_markets(active_context: dict[str, Any], symbols: list[str]) -> list[str]:
    observations = active_context.get("observations") if isinstance(active_context.get("observations"), list) else []
    values = []
    for item in observations:
        if isinstance(item, dict) and str(item.get("symbol")) in symbols:
            values.append(str(item.get("market") or active_context.get("market") or "TWSE"))
    return sorted(set(values))


def _contains_raw_forbidden_key(value: Any) -> list[str]:
    found: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key in _RAW_FORBIDDEN_KEYS:
                    found.add(key)
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return sorted(found)


def build_m7g_controlled_refresh_request_package(
    *,
    active_context: dict[str, Any],
    active_context_mode: str,
    validation_result: dict[str, Any] | None,
    requested_symbols: list[str],
    requested_source_families: list[str],
    operator_confirmation_phrase: str,
) -> dict[str, Any]:
    """
    Build a safe controlled refresh request package.

    Must not execute refresh, perform network calls, read files, call backend/API,
    call AI systems, write a database, or mutate active_context.
    """
    if active_context_mode not in _ALLOWED_CONTEXT_MODES:
        raise ValueError("active_context_mode must be static_demo or loaded_safe_artifact")

    active_symbols = _observation_symbols(active_context)
    normalized_symbols = [str(symbol) for symbol in requested_symbols]
    if not normalized_symbols or not set(normalized_symbols).issubset(active_symbols):
        raise ValueError("requested_symbols must be a non-empty subset of active context observations")

    normalized_families = [str(family) for family in requested_source_families]
    if not normalized_families or not set(normalized_families).issubset(ALLOWED_SOURCE_FAMILIES):
        raise ValueError("requested_source_families must use the fixed allowlist")

    validation_status = (validation_result or {}).get("validation_status") or ("static_demo" if active_context_mode == "static_demo" else None)
    safe_to_render = (validation_result or {}).get("safe_to_render") is True
    loaded_accepted = active_context_mode == "loaded_safe_artifact" and validation_status == "accepted" and safe_to_render
    confirmation_matched = operator_confirmation_phrase == CONFIRMATION_PHRASE
    clock = active_context.get("market_clock_session_state") if isinstance(active_context.get("market_clock_session_state"), dict) else {}
    health = active_context.get("source_health") if isinstance(active_context.get("source_health"), dict) else {}

    return {
        "schema_version": REFRESH_REQUEST_PACKAGE_SCHEMA_VERSION,
        "package_type": "controlled_manual_refresh_request",
        "package_status": "prepared_not_executed" if confirmation_matched else "preflight_failed",
        "created_at_utc": "operator_action_runtime",
        "created_by": "operator_explicit_preflight",
        "active_context_mode": active_context_mode,
        "source_artifact_id": active_context.get("artifact_id") if loaded_accepted else "static_demo",
        "source_artifact_schema_version": active_context.get("schema_version") if loaded_accepted else "static_demo",
        "source_validation_status": validation_status,
        "source_observation_count": len(active_symbols),
        "requested_symbols": normalized_symbols,
        "requested_markets": _observation_markets(active_context, normalized_symbols),
        "requested_source_families": normalized_families,
        "refresh_scope": "bounded_watchlist",
        "bounded_watchlist_only": True,
        "execution_eligible_for_m7g09": loaded_accepted and confirmation_matched,
        "execution_authorized": False,
        "execution_performed": False,
        "requires_m7g09_execution_gate": True,
        "network_intent": "declared_for_future_m7g09_only",
        "raw_payload_requested": False,
        "raw_forbidden_values_requested": False,
        "ai_model_call_requested": False,
        "trading_advice_requested": False,
        "currentness_before_refresh": {
            "currentness_label": clock.get("currentness_label"),
            "calendar_confidence": clock.get("calendar_confidence"),
            "trading_day_status": clock.get("trading_day_status"),
        },
        "source_health_before_refresh": {
            "source_health_status": health.get("health_status", "artifact_reported" if loaded_accepted else "static_demo"),
            "source_health_schema_version": health.get("schema_version"),
        },
        "operator_confirmation": {
            "required": True,
            "confirmation_phrase_required": CONFIRMATION_PHRASE,
            "confirmed": confirmation_matched,
            "confirmation_phrase_matched": confirmation_matched,
        },
        "governance_guardrails": {
            "not_trading_signal": True,
            "not_recommendation": True,
            "not_market_prediction": True,
            "not_capital_flow": True,
            "not_full_market_breadth": True,
            "raw_payload_exposed": False,
            "raw_rich_facts_exposed": False,
            "raw_full_ladder_exposed": False,
        },
    }


def validate_m7g_controlled_refresh_request_package(package: dict[str, Any]) -> dict[str, Any]:
    """Validate request package shape and safety flags. Must not execute refresh."""
    errors: list[str] = []
    if package.get("schema_version") != REFRESH_REQUEST_PACKAGE_SCHEMA_VERSION:
        errors.append("invalid_schema_version")
    for key in ["execution_authorized", "execution_performed", "raw_payload_requested", "raw_forbidden_values_requested", "ai_model_call_requested", "trading_advice_requested"]:
        if package.get(key) is not False:
            errors.append(f"{key}_must_be_false")
    if package.get("requires_m7g09_execution_gate") is not True:
        errors.append("requires_m7g09_execution_gate_required")
    if not package.get("requested_symbols"):
        errors.append("requested_symbols_required")
    families = package.get("requested_source_families")
    if not families or not set(families).issubset(ALLOWED_SOURCE_FAMILIES):
        errors.append("requested_source_families_invalid")
    raw_keys = _contains_raw_forbidden_key(package)
    if raw_keys:
        errors.append("raw_forbidden_keys_detected")
    return {"validation_status": "accepted" if not errors else "rejected", "errors": errors, "raw_forbidden_keys_detected": raw_keys}
