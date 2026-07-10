from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from scripts.m5k_common import execute_live_observation
from scripts.m7g_refresh_request_package import validate_m7g_controlled_refresh_request_package
from scripts.m7g_safe_artifact_validator import validate_m7g_safe_context_artifact

EXECUTION_RESULT_SCHEMA_VERSION = "m7g_controlled_refresh_execution_result.v1"
EXECUTION_CONFIRMATION_PHRASE = "EXECUTE_CONTROLLED_REFRESH_ONCE"
EXECUTION_SUPPORTED_SOURCE_FAMILIES = {"TWSE_MIS"}
DECLARED_BUT_NOT_YET_EXECUTABLE_SOURCE_FAMILIES = {"TWSE_OPENAPI", "TAIFEX_OPENAPI"}
_NETWORK_FETCH_SCOPE = "explicit_operator_controlled_refresh_only"

_FORBIDDEN_RESULT_KEYS = {
    "raw_payload", "twse_mis_rich_facts", "raw_rich_facts", "raw_unknown_facts",
    "full_ladder", "bid_prices", "ask_prices", "source_investigation_notes",
    "response_sample", "raw_fields_sample",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _base_result(status: str, errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": EXECUTION_RESULT_SCHEMA_VERSION,
        "execution_status": status,
        "execution_mode": "controlled_manual_once",
        "execution_authorized": False,
        "execution_performed": False,
        "auto_refresh": False,
        "scheduler": False,
        "hidden_fetch": False,
        "requested_symbols": [],
        "executed_symbols": [],
        "requested_source_families": [],
        "executed_source_families": [],
        "unsupported_source_families": [],
        "refresh_scope": "bounded_watchlist",
        "bounded_watchlist_only": True,
        "mode_abc_unchanged": True,
        "level_1_2_unchanged": True,
        "mode_d_added": False,
        "level_3_added": False,
        "level2_output_only": True,
        "m5f_mutated": False,
        "level1_mutated": False,
        "safe_artifact_returned": False,
        "safe_artifact_validation_status": "not_run",
        "raw_payload_exposed": False,
        "raw_forbidden_values_returned": False,
        "trading_advice_generated": False,
        "ai_model_call_performed": False,
        "network_fetch_performed": False,
        "network_fetch_scope": _NETWORK_FETCH_SCOPE,
        "execution_caveats": [
            "Controlled manual refresh only.",
            "Level 2 temporary safe artifact only.",
            "Not trading advice.",
            "Not a recommendation.",
            "Not a trading signal.",
        ],
        "errors": errors or [],
    }


def _validate_execution_request(package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validation = validate_m7g_controlled_refresh_request_package(package)
    errors.extend(validation.get("errors", []))
    required = {
        "package_status": "prepared_not_executed",
        "execution_eligible_for_m7g09": True,
        "execution_authorized": False,
        "execution_performed": False,
        "requires_m7g09_execution_gate": True,
        "refresh_scope": "bounded_watchlist",
        "bounded_watchlist_only": True,
        "raw_payload_requested": False,
        "raw_forbidden_values_requested": False,
        "ai_model_call_requested": False,
        "trading_advice_requested": False,
    }
    for key, expected in required.items():
        if package.get(key) != expected:
            errors.append(f"{key}_invalid")
    confirmation = package.get("operator_confirmation")
    if not isinstance(confirmation, dict):
        errors.append("operator_confirmation_required")
    else:
        if confirmation.get("confirmed") is not True:
            errors.append("operator_confirmation_confirmed_required")
        if confirmation.get("confirmation_phrase_matched") is not True:
            errors.append("operator_confirmation_phrase_matched_required")
    if not isinstance(package.get("requested_symbols"), list) or not package.get("requested_symbols"):
        errors.append("requested_symbols_required")
    if not isinstance(package.get("requested_source_families"), list) or not package.get("requested_source_families"):
        errors.append("requested_source_families_required")
    return sorted(set(errors))


def _watchlist_from_package(package: dict[str, Any]) -> dict[str, Any]:
    markets = package.get("requested_markets") if isinstance(package.get("requested_markets"), list) else []
    items = []
    for index, symbol in enumerate(package.get("requested_symbols", []), start=1):
        market = str(markets[index - 1]).lower() if index - 1 < len(markets) and markets[index - 1] else "twse"
        if market.upper() == "TWSE":
            market = "twse"
        items.append({
            "id": f"m7g09:{symbol}",
            "symbol": str(symbol),
            "display_name": str(symbol),
            "market": market,
            "instrument_type": "equity",
            "adapter": "twse_mis_equity_etf_quote",
            "preferred_sources": ["TWSE_MIS"],
            "category": "m7g09_controlled_refresh",
            "enabled": True,
            "display_order": index,
            "tags": ["m7g09", "bounded_watchlist"],
            "notes": "M7G-09 controlled manual refresh bounded target.",
        })
    return {
        "schema_version": "m5n_watchlist.v1",
        "watchlist_id": "m7g09_controlled_manual_refresh",
        "name": "M7G-09 controlled manual refresh watchlist",
        "description": "Bounded operator-requested watchlist for one controlled manual refresh.",
        "items": items,
        "governance": {"trading_signal": False, "recommendations_allowed": False},
    }


def _safe_observation(row: dict[str, Any], fallback_clock: dict[str, Any]) -> dict[str, Any]:
    caveats = list(row.get("semantic_caveats") or row.get("caveats") or [])
    caveats.extend(["Safe projected observation only.", "Not trading advice.", "No realtime SLA."])
    return {
        "symbol": str(row.get("symbol") or ""),
        "display_name": str(row.get("display_name") or row.get("name") or row.get("symbol") or ""),
        "market": str(row.get("market") or "TWSE").upper(),
        "source": str(row.get("source") or "TWSE_MIS"),
        "retrieved_at_utc": row.get("retrieved_at_utc") or row.get("retrieved_at") or fallback_clock.get("retrieved_at_utc"),
        "price_like_value": row.get("price_like_value") if row.get("price_like_value") is not None else row.get("value"),
        "change_percent": row.get("change_percent"),
        "volume_candidate": row.get("volume_candidate") or row.get("volume"),
        "best_bid_candidate": row.get("best_bid_candidate"),
        "best_ask_candidate": row.get("best_ask_candidate"),
        "session_state": row.get("session_state") or fallback_clock.get("session_state"),
        "freshness_state": row.get("freshness_state") or fallback_clock.get("freshness_state"),
        "currentness_label": row.get("currentness_label") or fallback_clock.get("currentness_label"),
        "calendar_confidence": row.get("calendar_confidence") or fallback_clock.get("calendar_confidence"),
        "trading_day_status": row.get("trading_day_status") or fallback_clock.get("trading_day_status"),
        "semantic_caveats": sorted(set(str(c) for c in caveats if c)),
    }


def _source_health(executed: list[str], timestamp: str) -> dict[str, Any]:
    return {
        "schema_version": "m7g_source_health.v1",
        "source_family": "TWSE_MIS",
        "health_status": "artifact_reported",
        "source_mode": "controlled_manual_refresh_execution",
        "last_success_at_utc": timestamp if executed else None,
        "last_error_at_utc": None if executed else timestamp,
        "last_error_code": None if executed else "no_safe_observations",
        "staleness_status": "artifact_currentness_labeled",
        "operator_action_required": False,
        "caveats": [
            "Source health is execution-reported metadata, not a continuous live probe.",
            "No realtime SLA.",
        ],
    }


def build_m7g_refreshed_safe_context_artifact(*, request_package: dict[str, Any], observation_result: dict[str, Any], execution_metadata: dict[str, Any]) -> dict[str, Any]:
    generated_at = observation_result.get("generated_at_utc") or execution_metadata.get("executed_at_utc") or _utc_now()
    clock = {
        "session_state": "unknown",
        "freshness_state": "degraded_unknown",
        "currentness_label": "recent_but_unverified" if observation_result.get("observations") else "degraded_unknown",
        "calendar_confidence": "weekday_heuristic_only",
        "trading_day_status": "unknown",
        "calendar_authority_caveats": ["not_full_exchange_calendar_engine", "no_realtime_sla", "not_trading_advice"],
        "semantic_caveats": ["Controlled manual refresh Level 2 temporary safe artifact only.", "Not trading advice.", "No realtime SLA."],
        "retrieved_at_utc": generated_at,
    }
    observations = [_safe_observation(row, clock) for row in observation_result.get("observations", []) if isinstance(row, dict)]
    executed_symbols = [row["symbol"] for row in observations if row.get("symbol")]
    return {
        "schema_version": "m7g_safe_context_artifact.v1",
        "artifact_id": f"m7g09-controlled-refresh-{generated_at.replace(':', '').replace('-', '')}",
        "artifact_type": "safe_context_projection",
        "created_at_utc": generated_at,
        "generated_by": "m7g_controlled_refresh_executor",
        "source_scope": "bounded_watchlist",
        "market": "TW",
        "timezone": "Asia/Taipei",
        "safe_for_frontend": True,
        "safe_for_ai_handoff": True,
        "raw_payload_exposed": False,
        "raw_rich_facts_exposed": False,
        "raw_full_ladder_exposed": False,
        "raw_forbidden_values_present": False,
        "artifact_manifest": {
            "schema_version": "m7g_safe_context_manifest.v1",
            "source": "controlled_manual_refresh_execution",
            "operator_selected": False,
            "loaded_at_utc": None,
            "validation_status": "server_validated_before_return",
            "validation_errors": [],
        },
        "market_clock_session_state": {k: v for k, v in clock.items() if k != "retrieved_at_utc"},
        "governance": {
            "not_trading_signal": True,
            "not_recommendation": True,
            "not_market_prediction": True,
            "not_capital_flow": True,
            "not_full_market_breadth": True,
            "raw_payload_exposed": False,
            "raw_rich_facts_exposed": False,
            "raw_full_ladder_exposed": False,
        },
        "observations": observations,
        "source_health": _source_health(executed_symbols, generated_at),
    }


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in _FORBIDDEN_RESULT_KEYS or _contains_forbidden_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(child) for child in value)
    return False


def validate_m7g_controlled_refresh_execution_result(result: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if result.get("schema_version") != EXECUTION_RESULT_SCHEMA_VERSION:
        errors.append("invalid_schema_version")
    for key in ["auto_refresh", "scheduler", "hidden_fetch", "m5f_mutated", "level1_mutated", "raw_payload_exposed", "raw_forbidden_values_returned", "trading_advice_generated", "ai_model_call_performed"]:
        if result.get(key) is not False:
            errors.append(f"{key}_must_be_false")
    for key in ["mode_abc_unchanged", "level_1_2_unchanged", "level2_output_only"]:
        if result.get(key) is not True:
            errors.append(f"{key}_must_be_true")
    if _contains_forbidden_key(result):
        errors.append("raw_forbidden_keys_detected")
    return {"validation_status": "accepted" if not errors else "rejected", "errors": errors}


def execute_m7g_controlled_manual_refresh(*, request_package: dict[str, Any], operator_execution_confirmation_phrase: str, observation_runner: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> dict[str, Any]:
    if not isinstance(request_package, dict):
        return _base_result("rejected_invalid_request_package", ["request_package_missing"])
    requested_families = [str(f) for f in request_package.get("requested_source_families", [])] if isinstance(request_package.get("requested_source_families"), list) else []
    requested_symbols = [str(s) for s in request_package.get("requested_symbols", [])] if isinstance(request_package.get("requested_symbols"), list) else []
    unsupported = [f for f in requested_families if f not in EXECUTION_SUPPORTED_SOURCE_FAMILIES]
    supported = [f for f in requested_families if f in EXECUTION_SUPPORTED_SOURCE_FAMILIES]
    if operator_execution_confirmation_phrase != EXECUTION_CONFIRMATION_PHRASE:
        result = _base_result("rejected_missing_execution_confirmation")
        result.update({"requested_symbols": requested_symbols, "requested_source_families": requested_families, "unsupported_source_families": unsupported})
        return result
    if requested_families and not supported:
        result = _base_result("rejected_unsupported_source_family")
        result.update({"requested_symbols": requested_symbols, "requested_source_families": requested_families, "unsupported_source_families": unsupported})
        return result
    errors = _validate_execution_request(request_package)
    if errors:
        result = _base_result("rejected_invalid_request_package", errors)
        result.update({"requested_symbols": requested_symbols, "requested_source_families": requested_families, "unsupported_source_families": unsupported})
        return result

    runner = observation_runner or (lambda watchlist: execute_live_observation(watchlist, write_latest=False))
    watchlist = _watchlist_from_package(request_package)
    observation_result = runner(watchlist)
    metadata = {"executed_at_utc": observation_result.get("generated_at_utc") or _utc_now()}
    artifact = build_m7g_refreshed_safe_context_artifact(request_package=request_package, observation_result=observation_result, execution_metadata=metadata)
    validation = validate_m7g_safe_context_artifact(artifact)
    if validation.get("validation_status") != "accepted":
        result = _base_result("execution_failed_safe_artifact_rejected", [e.get("code", "artifact_rejected") for e in validation.get("errors", [])])
    elif not artifact.get("observations"):
        result = _base_result("execution_failed_no_safe_artifact", ["no_safe_observations"])
    else:
        result = _base_result("executed_safe_artifact_ready")
        result["safe_context_artifact"] = artifact
        result["safe_artifact_returned"] = True
    executed_symbols = [str(o.get("symbol")) for o in artifact.get("observations", []) if isinstance(o, dict) and o.get("symbol")]
    result.update({
        "execution_authorized": True,
        "execution_performed": True,
        "requested_symbols": requested_symbols,
        "executed_symbols": executed_symbols,
        "requested_source_families": requested_families,
        "executed_source_families": ["TWSE_MIS"] if "TWSE_MIS" in supported else [],
        "unsupported_source_families": unsupported,
        "safe_artifact_validation_status": validation.get("validation_status"),
        "network_fetch_performed": True,
        "source_health_after_refresh": _source_health(executed_symbols, metadata["executed_at_utc"]),
    })
    shape_validation = validate_m7g_controlled_refresh_execution_result(result)
    if shape_validation.get("validation_status") != "accepted":
        safe = _base_result("execution_failed_safe_artifact_rejected", shape_validation.get("errors", []))
        safe.update({"requested_symbols": requested_symbols, "requested_source_families": requested_families, "network_fetch_performed": True})
        return safe
    return result
