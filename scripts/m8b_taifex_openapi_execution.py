from __future__ import annotations
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from scripts.m8b_taifex_derivatives_observation import utc_now, apply_currentness_to_observation
from scripts.m8b_taifex_currentness import evaluate_taifex_derivatives_currentness
from scripts.m8b_taifex_openapi_futures_adapter import normalize_taifex_futures_eod
from scripts.m8b_taifex_openapi_options_adapter import normalize_taifex_options_eod
from scripts.m8b_taifex_openapi_final_settlement_adapter import normalize_taifex_final_settlement
from scripts.m8b_taifex_openapi_large_trader_oi_adapter import normalize_taifex_large_trader_oi
from scripts.m8b_taifex_openapi_put_call_ratio_adapter import normalize_taifex_put_call_ratio
from scripts.m8b_taifex_openapi_block_trade_adapter import normalize_taifex_block_trade

ALLOWED = {"futures_eod", "options_eod", "final_settlement", "large_trader_oi_futures", "large_trader_oi_options", "put_call_ratio", "block_trade"}
DAILY_CONTEXTS = ALLOWED - {"final_settlement"}


def _selectors(requested_contracts):
    out = {"months": [], "strikes": [], "option_types": [], "delivery_months": [], "trader_types": []}
    for c in requested_contracts or []:
        if not isinstance(c, dict):
            continue
        for src, dst in [("contract_month", "months"), ("contract_month_or_week", "months"), ("settlement_month", "months"), ("delivery_month", "delivery_months"), ("strike_price", "strikes"), ("option_type", "option_types"), ("type_of_traders", "trader_types")]:
            if c.get(src) is not None and str(c.get(src)) not in out[dst]:
                out[dst].append(str(c.get(src)))
    return out


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)



def _finish_execution_result(result: dict, started: str, overall_status: str) -> dict:
    completed = utc_now()
    result.update(overall_status=overall_status, completed_at_utc=completed, duration_ms=max(0, int((_parse_utc(completed) - _parse_utc(started)).total_seconds() * 1000)))
    return result

def _error_result(context: str, endpoint: str, exc: Exception) -> dict:
    ts = utc_now()
    return {
        "schema_version": "m8b_taifex_openapi_adapter_result.v1",
        "source_id": "TAIFEX_OPENAPI",
        "endpoint_contract_id": endpoint,
        "context": context,
        "requested_at_utc": ts,
        "completed_at_utc": ts,
        "source_status": "source_error",
        "batch_status": "source_error",
        "row_count_received": 0,
        "row_count_retained": 0,
        "observations": [],
        "rejected_rows": [],
        "caveats": ["unexpected adapter exception captured without raw payload"],
        "provenance": {"error_type": type(exc).__name__, "endpoint": endpoint, "context": context, "raw_payload_retained": False},
    }


def _apply_currentness(context: str, result: dict, *, evaluation_time_asia_taipei, calendar_artifact, closure_events, closure_query_succeeded, exchange_special_closures) -> None:
    if context == "final_settlement":
        return
    if context not in DAILY_CONTEXTS:
        return
    for obs in result.get("observations", []):
        cur = evaluate_taifex_derivatives_currentness(
            reported_trade_date=obs.get("trade_date"),
            evaluation_time_asia_taipei=evaluation_time_asia_taipei,
            session=obs.get("session"),
            calendar_artifact=calendar_artifact,
            closure_events=closure_events,
            closure_query_succeeded=closure_query_succeeded,
            exchange_special_closures=exchange_special_closures,
        )
        apply_currentness_to_observation(obs, cur)


def execute_taifex_openapi_refresh(*, operator_confirmed: bool, requested_contexts: list[str], requested_products: list[str], requested_contracts: list[dict] | None = None, requested_sessions: list[str] | None = None, evaluation_time_asia_taipei: str | None = None, fetchers: dict | None = None, calendar_artifact: dict | None = None, closure_events: list | None = None, closure_query_succeeded: bool | None = None, exchange_special_closures: list | None = None, requested_trade_dates: list[str] | None = None, put_call_ratio_latest_n: int = 1, max_put_call_ratio_rows: int = 20, requested_delivery_months: list[str] | None = None, final_settlement_latest_n_per_product: int = 1, max_final_settlement_rows: int = 50) -> dict:
    started = utc_now()
    evaluation_time_source = "caller_supplied" if evaluation_time_asia_taipei is not None else "runtime_clock"
    if evaluation_time_asia_taipei is None:
        evaluation_time_asia_taipei = datetime.now(ZoneInfo("Asia/Taipei")).replace(microsecond=0).isoformat()
    result = {"schema_version": "m8b_taifex_openapi_execution_result.v1", "source_id": "TAIFEX_OPENAPI", "requested_contexts": requested_contexts, "requested_products": requested_products, "requested_contracts": requested_contracts or [], "operator_confirmed": operator_confirmed, "started_at_utc": started, "completed_at_utc": None, "duration_ms": None, "overall_status": "not_started", "endpoint_results": {}, "observations": [], "raw_payload_retained": False, "scheduler_added": False, "polling_added": False, "startup_fetch_added": False, "db_write_added": False, "evaluation_time_asia_taipei": evaluation_time_asia_taipei, "evaluation_time_source": evaluation_time_source, "evaluation_timezone": "Asia/Taipei"}
    if not operator_confirmed:
        return _finish_execution_result(result, started, "operator_confirmation_required")
    if not requested_contexts or any(c not in ALLOWED for c in requested_contexts):
        return _finish_execution_result(result, started, "rejected_invalid_scope")
    if not requested_products and any(c != "put_call_ratio" for c in requested_contexts):
        return _finish_execution_result(result, started, "rejected_invalid_scope")
    selectors = _selectors(requested_contracts)
    fetchers = fetchers or {}
    calls = {
        "futures_eod": ("DailyMarketReportFut", lambda: normalize_taifex_futures_eod(requested_products=requested_products, requested_contract_months=selectors["months"], requested_sessions=requested_sessions, fetcher=fetchers.get("DailyMarketReportFut"))),
        "options_eod": ("DailyMarketReportOpt", lambda: normalize_taifex_options_eod(requested_products=requested_products, requested_contract_months=selectors["months"], requested_strikes=selectors["strikes"], requested_option_types=selectors["option_types"], requested_sessions=requested_sessions, fetcher=fetchers.get("DailyMarketReportOpt"))),
        "final_settlement": ("FinalSettlementPrice", lambda: normalize_taifex_final_settlement(requested_products=requested_products, requested_delivery_months=requested_delivery_months or selectors["delivery_months"] or selectors["months"], latest_n_per_product=final_settlement_latest_n_per_product, max_retained_rows=max_final_settlement_rows, fetcher=fetchers.get("FinalSettlementPrice"))),
        "large_trader_oi_futures": ("OpenInterestOfLargeTradersFutures", lambda: normalize_taifex_large_trader_oi(endpoint="OpenInterestOfLargeTradersFutures", requested_products=requested_products, requested_settlement_months=selectors["months"], requested_trader_types=selectors["trader_types"], fetcher=fetchers.get("OpenInterestOfLargeTradersFutures"))),
        "large_trader_oi_options": ("OpenInterestOfLargeTradersOptions", lambda: normalize_taifex_large_trader_oi(endpoint="OpenInterestOfLargeTradersOptions", requested_products=requested_products, requested_settlement_months=selectors["months"], requested_option_types=selectors["option_types"], requested_trader_types=selectors["trader_types"], fetcher=fetchers.get("OpenInterestOfLargeTradersOptions"))),
        "put_call_ratio": ("PutCallRatio", lambda: normalize_taifex_put_call_ratio(fetcher=fetchers.get("PutCallRatio"), requested_trade_dates=requested_trade_dates, latest_n=put_call_ratio_latest_n, max_retained_rows=max_put_call_ratio_rows)),
        "block_trade": ("BlockTrade", lambda: normalize_taifex_block_trade(requested_products=requested_products, requested_contract_months=selectors["months"], requested_strikes=selectors["strikes"], requested_option_types=selectors["option_types"], requested_sessions=requested_sessions, fetcher=fetchers.get("BlockTrade"))),
    }
    statuses = []
    for context in requested_contexts:
        endpoint, call = calls[context]
        try:
            endpoint_result = call()
            _apply_currentness(context, endpoint_result, evaluation_time_asia_taipei=evaluation_time_asia_taipei, calendar_artifact=calendar_artifact, closure_events=closure_events, closure_query_succeeded=closure_query_succeeded, exchange_special_closures=exchange_special_closures)
        except Exception as exc:  # deliberately compact, endpoint-isolated metadata
            endpoint_result = _error_result(context, endpoint, exc)
        result["endpoint_results"][context] = endpoint_result
        result["observations"].extend(endpoint_result.get("observations", []))
        statuses.append(endpoint_result.get("batch_status"))
    ok = {"successful_derivatives_eod_batch", "empty_non_trading_day", "no_matching_bounded_scope"}
    result["overall_status"] = "successful_derivatives_eod_batch" if all(status in ok for status in statuses) else ("partial_source_success" if any(status in ok for status in statuses) else statuses[0])
    completed = utc_now()
    result["completed_at_utc"] = completed
    result["duration_ms"] = int((_parse_utc(completed) - _parse_utc(started)).total_seconds() * 1000)
    return result
