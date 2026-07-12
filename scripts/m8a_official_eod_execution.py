"""Controlled explicit M8A official EOD execution."""
from __future__ import annotations
from scripts.m8a_official_eod_observation import observation_to_context_observation, utc_now
from scripts.m8a_twse_official_eod_adapter import execute_twse_official_eod_adapter
from scripts.m8a_tpex_official_eod_adapter import execute_tpex_official_eod_adapter
from datetime import datetime
from zoneinfo import ZoneInfo
from scripts.m8a_market_day_currentness_resolver import resolve_market_day_currentness
ALLOWED={"TWSE_OPENAPI","TPEX_OPENAPI"}
def _valid_symbols(symbols): return sorted({str(s).strip() for s in symbols or [] if str(s).strip()})
def execute_official_eod_refresh(requested_symbols, requested_sources, operator_confirmed, requested_trade_date=None, *, twse_adapter=execute_twse_official_eod_adapter, tpex_adapter=execute_tpex_official_eod_adapter, closure_fetcher=None, evaluation_time_asia_taipei=None, calendar_artifact=None):
    started=utc_now(); syms=_valid_symbols(requested_symbols); sources=list(requested_sources or []); evaluation_time_asia_taipei=evaluation_time_asia_taipei or datetime.now(ZoneInfo("Asia/Taipei")).replace(microsecond=0).isoformat()
    base={"schema_version":"m8a_official_eod_execution_result.v1","requested_sources":sources,"requested_symbols":syms,"requested_trade_date":requested_trade_date,"operator_confirmed":bool(operator_confirmed),"started_at_utc":started,"completed_at_utc":started,"source_results":[],"normalized_observations":[],"calendar_resolution":{},"safe_projection_scope":{"network_scope":"whole_market","retained_scope":"bounded_requested_symbols"},"overall_status":"failed","caveats":[]}
    if not operator_confirmed: base["overall_status"]="rejected_not_confirmed"; return base
    if not syms or not sources or any(s not in ALLOWED for s in sources): base["overall_status"]="rejected_invalid_scope"; return base
    for s in sources:
        r=twse_adapter(syms) if s=="TWSE_OPENAPI" else tpex_adapter(syms); base["source_results"].append(r); base["normalized_observations"].extend(r.get("observations",[]))
    statuses=[r.get("source_status") for r in base["source_results"]]
    reported=next((d for r in base["source_results"] for d in r.get("reported_trade_dates",[]) if d), None)
    closures=None; closure_query_succeeded=False
    tentative=resolve_market_day_currentness(evaluation_time_asia_taipei=evaluation_time_asia_taipei,reported_trade_date=reported,target_date=requested_trade_date,calendar_artifact=calendar_artifact)
    if closure_fetcher and reported and tentative["currentness_status"] not in {"current_official_eod"}:
        closure_target=tentative.get("expected_latest_completed_trade_date") or tentative["target_date"]
        closure_result=closure_fetcher(closure_target); closures=closure_result.get("events",[]); closure_query_succeeded=bool(closure_result.get("closure_query_succeeded", True))
    base["calendar_resolution"]=resolve_market_day_currentness(evaluation_time_asia_taipei=evaluation_time_asia_taipei,reported_trade_date=reported,closure_events=closures,closure_query_succeeded=closure_query_succeeded,target_date=requested_trade_date,calendar_artifact=calendar_artifact)
    cur=base["calendar_resolution"].get("currentness_status")
    base["context_observations"]=[observation_to_context_observation(o,currentness_status=cur) for o in base["normalized_observations"]]
    for ctx in base["context_observations"]:
        if ctx.get("safe_fields"):
            ctx["safe_fields"]["currentness_resolution_reason"] = base["calendar_resolution"].get("expected_latest_completed_trade_date_resolution_reason")
            ctx["safe_fields"]["currentness_resolution_trace"] = base["calendar_resolution"].get("expected_latest_completed_trade_date_resolution_trace", [])
            ctx["safe_fields"]["emergency_closure_evidence"] = base["calendar_resolution"].get("evidence", [])
    if statuses and all(x=="success" for x in statuses): base["overall_status"]="success"
    elif any(x=="success" for x in statuses): base["overall_status"]="partial_success"
    else: base["overall_status"]="failed"
    base["completed_at_utc"]=utc_now(); return base
