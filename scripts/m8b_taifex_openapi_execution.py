from __future__ import annotations
from scripts.m8b_taifex_derivatives_observation import utc_now
from scripts.m8b_taifex_openapi_futures_adapter import normalize_taifex_futures_eod
from scripts.m8b_taifex_openapi_options_adapter import normalize_taifex_options_eod
from scripts.m8b_taifex_openapi_final_settlement_adapter import normalize_taifex_final_settlement
from scripts.m8b_taifex_openapi_large_trader_oi_adapter import normalize_taifex_large_trader_oi
from scripts.m8b_taifex_openapi_put_call_ratio_adapter import normalize_taifex_put_call_ratio
from scripts.m8b_taifex_openapi_block_trade_adapter import normalize_taifex_block_trade
ALLOWED={"futures_eod","options_eod","final_settlement","large_trader_oi_futures","large_trader_oi_options","put_call_ratio","block_trade"}
def _selectors(requested_contracts):
    out={"months":[],"strikes":[],"option_types":[],"delivery_months":[],"trader_types":[]}
    for c in requested_contracts or []:
        if not isinstance(c,dict): continue
        for src,dst in [("contract_month","months"),("contract_month_or_week","months"),("settlement_month","months"),("delivery_month","delivery_months"),("strike_price","strikes"),("option_type","option_types"),("type_of_traders","trader_types")]:
            if c.get(src) is not None and c.get(src) not in out[dst]: out[dst].append(str(c.get(src)))
    return out
def execute_taifex_openapi_refresh(*, operator_confirmed: bool, requested_contexts: list[str], requested_products: list[str], requested_contracts: list[dict] | None = None, requested_sessions: list[str] | None = None, evaluation_time_asia_taipei: str | None = None, fetchers: dict | None = None) -> dict:
    ts=utc_now(); result={"schema_version":"m8b_taifex_openapi_execution_result.v1","source_id":"TAIFEX_OPENAPI","requested_contexts":requested_contexts,"requested_products":requested_products,"requested_contracts":requested_contracts or [],"operator_confirmed":operator_confirmed,"started_at_utc":ts,"completed_at_utc":ts,"overall_status":"not_started","endpoint_results":{},"observations":[],"raw_payload_retained":False,"scheduler_added":False,"polling_added":False,"startup_fetch_added":False,"db_write_added":False}
    if not operator_confirmed: result["overall_status"]="operator_confirmation_required"; return result
    if not requested_contexts or any(c not in ALLOWED for c in requested_contexts): result["overall_status"]="rejected_invalid_scope"; return result
    if not requested_products and any(c!="put_call_ratio" for c in requested_contexts): result["overall_status"]="rejected_invalid_scope"; return result
    s=_selectors(requested_contracts); fetchers=fetchers or {}
    calls={
      "futures_eod": lambda: normalize_taifex_futures_eod(requested_products=requested_products, requested_contract_months=s["months"], requested_sessions=requested_sessions, fetcher=fetchers.get("DailyMarketReportFut")),
      "options_eod": lambda: normalize_taifex_options_eod(requested_products=requested_products, requested_contract_months=s["months"], requested_strikes=s["strikes"], requested_option_types=s["option_types"], requested_sessions=requested_sessions, fetcher=fetchers.get("DailyMarketReportOpt")),
      "final_settlement": lambda: normalize_taifex_final_settlement(requested_products=requested_products, requested_delivery_months=s["delivery_months"] or s["months"], fetcher=fetchers.get("FinalSettlementPrice")),
      "large_trader_oi_futures": lambda: normalize_taifex_large_trader_oi(endpoint="OpenInterestOfLargeTradersFutures", requested_products=requested_products, requested_settlement_months=s["months"], requested_trader_types=s["trader_types"], fetcher=fetchers.get("OpenInterestOfLargeTradersFutures")),
      "large_trader_oi_options": lambda: normalize_taifex_large_trader_oi(endpoint="OpenInterestOfLargeTradersOptions", requested_products=requested_products, requested_settlement_months=s["months"], requested_option_types=s["option_types"], requested_trader_types=s["trader_types"], fetcher=fetchers.get("OpenInterestOfLargeTradersOptions")),
      "put_call_ratio": lambda: normalize_taifex_put_call_ratio(fetcher=fetchers.get("PutCallRatio")),
      "block_trade": lambda: normalize_taifex_block_trade(requested_products=requested_products, requested_contract_months=s["months"], requested_strikes=s["strikes"], requested_option_types=s["option_types"], requested_sessions=requested_sessions, fetcher=fetchers.get("BlockTrade")),
    }
    statuses=[]
    for c in requested_contexts:
        r=calls[c](); result["endpoint_results"][c]=r; result["observations"].extend(r.get("observations",[])); statuses.append(r.get("batch_status"))
    ok={"successful_derivatives_eod_batch","empty_non_trading_day"}; result["overall_status"]="successful_derivatives_eod_batch" if all(x in ok for x in statuses) else ("partial_source_success" if any(x in ok for x in statuses) else statuses[0]); return result
