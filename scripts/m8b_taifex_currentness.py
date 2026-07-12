"""Source-specific TAIFEX official derivatives EOD currentness helpers."""
from __future__ import annotations
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
from scripts.m8a_market_day_currentness_resolver import resolve_market_day_currentness

TAIPEI = ZoneInfo("Asia/Taipei")
TAIFEX_OFFICIAL_CLOSURE_SOURCES = {"TAIFEX", "TAIFEX_OFFICIAL", "TAIFEX_SPECIAL_CLOSURE"}
CLOSURE_CONFIRMING_VALUES = {"closure_confirmed", "closed", "full_day_closed", "special_closure_confirmed", "confirmed"}
CLOSURE_NEGATING_VALUES = {"cancelled", "canceled", "normal_operations", "open", "draft", "test", "expired", "no_closure", "closure_cancelled", "closure_canceled"}


def _evaluation_target_date(value: str | datetime) -> str:
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TAIPEI)
    return dt.astimezone(TAIPEI).date().isoformat()


def _semantically_confirms_taifex_closure(event: dict, target_date: str) -> bool:
    if not isinstance(event, dict):
        return False
    if event.get("source_id") not in TAIFEX_OFFICIAL_CLOSURE_SOURCES:
        return False
    if event.get("target_date") != target_date:
        return False
    values = {str(event.get(k, "")).strip().lower() for k in ("decision_status", "status", "closure_status", "market_status", "publication_status", "lifecycle_status")}
    values.discard("")
    if values & CLOSURE_NEGATING_VALUES:
        return False
    if any(str(event.get(k, "")).strip().lower() in CLOSURE_NEGATING_VALUES for k in ("event_status", "state", "operation_status")):
        return False
    return bool(values & CLOSURE_CONFIRMING_VALUES)


def _has_target_specific_taifex_closure_evidence(*, target_date: str, closure_events: list | None, exchange_special_closures: list | None) -> bool:
    if target_date in {str(x) for x in (exchange_special_closures or [])}:
        return True
    return any(_semantically_confirms_taifex_closure(e, target_date) for e in (closure_events or []))

DAILY_CONTEXTS = {
    "futures_eod", "options_eod", "large_trader_oi_futures",
    "large_trader_oi_options", "put_call_ratio", "block_trade",
}


def evaluate_taifex_derivatives_currentness(*, reported_trade_date: str | None, evaluation_time_asia_taipei: str | datetime | None, session: str | None = None, calendar_artifact: dict | None = None, closure_events: list | None = None, closure_query_succeeded: bool | None = None, exchange_special_closures: list | None = None) -> dict:
    caveats: list[str] = []
    if not evaluation_time_asia_taipei:
        caveats.append("evaluation_time_asia_taipei_missing")
        return {"status": "unresolved_date_mismatch", "trade_date": reported_trade_date, "caveats": caveats, "source_specific": True}
    target_date = _evaluation_target_date(evaluation_time_asia_taipei)
    calendar_evidence = "provided_unverified" if calendar_artifact is not None else "incomplete"
    currentness_confidence = "provisional"
    taifex_specific_closure = _has_target_specific_taifex_closure_evidence(target_date=target_date, closure_events=closure_events, exchange_special_closures=exchange_special_closures)
    if calendar_artifact is None:
        caveats.append("taifex_trading_calendar_evidence_incomplete_weekend_rule_only")
    resolver_exchange_special_closures = list(dict.fromkeys(list(exchange_special_closures or []) + ([target_date] if taifex_specific_closure else [])))
    resolved = resolve_market_day_currentness(
        evaluation_time_asia_taipei=evaluation_time_asia_taipei,
        reported_trade_date=reported_trade_date,
        calendar_artifact=calendar_artifact,
        closure_events=closure_events,
        closure_query_succeeded=closure_query_succeeded,
        exchange_special_closures=resolver_exchange_special_closures,
    )
    mapping = {"current_official_eod": "current_official_derivatives_eod"}
    status = mapping.get(resolved.get("currentness_status"), resolved.get("currentness_status") or "unresolved_date_mismatch")
    if status == "matches_expected_latest_trade_date_after_emergency_closure" and not taifex_specific_closure:
        status = "unresolved_date_mismatch"
        currentness_confidence = "provisional"
        caveats.append("taifex_specific_closure_evidence_missing")
    if session == "unknown" and status != "unresolved_date_mismatch":
        status = "session_semantics_unresolved"
        caveats.append("session_semantics_unresolved")
    return {
        "status": status,
        "trade_date": reported_trade_date,
        "evaluation_time_asia_taipei": resolved.get("evaluation_time_asia_taipei"),
        "expected_latest_completed_trade_date": resolved.get("expected_latest_completed_trade_date"),
        "expected_latest_completed_trade_date_resolution_trace": resolved.get("expected_latest_completed_trade_date_resolution_trace", []),
        "emergency_closure_status": resolved.get("emergency_closure_status"),
        "exchange_market_status": resolved.get("exchange_market_status"),
        "source_specific": True,
        "calendar_evidence": calendar_evidence,
        "currentness_confidence": currentness_confidence,
        "caveats": caveats + resolved.get("caveats", []),
    }


def final_settlement_currentness(final_settlement_day: str | None, *, latest_reference_date: str | None = None) -> dict:
    status = "official_final_settlement_reference" if latest_reference_date is None or final_settlement_day == latest_reference_date else "historical_final_settlement_reference"
    return {"status": status, "trade_date": final_settlement_day, "caveats": ["final settlement reference is not latest daily market state"]}
