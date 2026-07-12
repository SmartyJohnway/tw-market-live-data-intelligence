"""Source-specific TAIFEX official derivatives EOD currentness helpers."""
from __future__ import annotations
from datetime import datetime
from typing import Any
from scripts.m8a_market_day_currentness_resolver import resolve_market_day_currentness

DAILY_CONTEXTS = {
    "futures_eod", "options_eod", "large_trader_oi_futures",
    "large_trader_oi_options", "put_call_ratio", "block_trade",
}


def evaluate_taifex_derivatives_currentness(*, reported_trade_date: str | None, evaluation_time_asia_taipei: str | datetime | None, session: str | None = None, calendar_artifact: dict | None = None, closure_events: list | None = None, closure_query_succeeded: bool | None = None, exchange_special_closures: list | None = None) -> dict:
    caveats: list[str] = []
    if not evaluation_time_asia_taipei:
        caveats.append("evaluation_time_asia_taipei_missing")
        return {"status": "unresolved_date_mismatch", "trade_date": reported_trade_date, "caveats": caveats, "source_specific": True}
    if calendar_artifact is None:
        caveats.append("taifex_trading_calendar_evidence_incomplete_weekend_rule_only")
    resolved = resolve_market_day_currentness(
        evaluation_time_asia_taipei=evaluation_time_asia_taipei,
        reported_trade_date=reported_trade_date,
        calendar_artifact=calendar_artifact,
        closure_events=closure_events,
        closure_query_succeeded=closure_query_succeeded,
        exchange_special_closures=exchange_special_closures,
    )
    mapping = {"current_official_eod": "current_official_derivatives_eod"}
    status = mapping.get(resolved.get("currentness_status"), resolved.get("currentness_status") or "unresolved_date_mismatch")
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
        "caveats": caveats + resolved.get("caveats", []),
    }


def final_settlement_currentness(final_settlement_day: str | None, *, latest_reference_date: str | None = None) -> dict:
    status = "official_final_settlement_reference" if latest_reference_date is None or final_settlement_day == latest_reference_date else "historical_final_settlement_reference"
    return {"status": status, "trade_date": final_settlement_day, "caveats": ["final settlement reference is not latest daily market state"]}
