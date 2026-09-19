"""G2 normalization using supplied official monthly-revenue source payloads only."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .research_executor import ROUTES, SourceFailure, bind_rows, fetch_once, field, normalize_source_rows

SOURCE_FAMILY = "MOPS_MONTHLY_REVENUE_OPEN_DATA"

def _roc_date(value: str | None) -> str | None:
    if not value: return None
    digits=value.replace("/", "").replace("-", "").strip()
    if not digits.isdigit() or len(digits) not in {5, 6, 7}: return None
    year=int(digits[:-2])+1911; month=int(digits[-2:])
    return f"{year:04d}-{month:02d}" if 1 <= month <= 12 else None

def _report_date(value: str | None) -> str | None:
    if not value: return None
    digits=value.replace("/", "").replace("-", "").strip()
    if not digits.isdigit() or len(digits) not in {7, 8}: return None
    year=int(digits[:-4])+1911; month=int(digits[-4:-2]); day=int(digits[-2:])
    if not (1 <= month <= 12 and 1 <= day <= 31): return None
    return f"{year:04d}-{month:02d}-{day:02d}"

def _integer(row: dict[str, Any], *names: str) -> int | None:
    value=field(row,*names)
    if value is None: return None
    try: return int(value.replace(",", ""))
    except ValueError: raise SourceFailure("invalid_monetary_value")

def _number(row: dict[str, Any], *names: str) -> float | None:
    value=field(row,*names)
    if value is None: return None
    try: return float(value.replace(",", ""))
    except ValueError: raise SourceFailure("invalid_percentage_value")

def _value(row: dict[str, Any]) -> dict[str, Any]:
    return {"currency":"TWD","unit":"thousand",
        "current_month_revenue":_integer(row,"營業收入-當月營收","current_month_revenue"),
        "previous_month_revenue":_integer(row,"營業收入-上月營收","previous_month_revenue"),
        "previous_year_same_month_revenue":_integer(row,"營業收入-去年當月營收","previous_year_same_month_revenue"),
        "mom_pct":_number(row,"營業收入-上月比較增減(%)","mom_pct"),
        "yoy_pct":_number(row,"營業收入-去年同月增減(%)","yoy_pct"),
        "ytd_revenue":_integer(row,"累計營業收入-當月累計營收","ytd_revenue"),
        "previous_year_ytd_revenue":_integer(row,"累計營業收入-去年累計營收","previous_year_ytd_revenue"),
        "ytd_yoy_pct":_number(row,"累計營業收入-前期比較增減(%)","ytd_yoy_pct"),
        "note":field(row,"備註","note")}

def execute(targets: list[dict[str, Any]], market: str, *, observed_at: str, csv_fetcher, json_fetcher) -> list[dict[str, Any]]:
    route=ROUTES[("monthly_revenue", market)]
    if any(target.get("market") != market for target in targets): return [_result(target,"binding_failed",None,observed_at,route,"official_csv",False,["route_target_market_mismatch"]) for target in targets]
    try:
        rows, transport, fallback, attempts=fetch_once(route,csv_fetcher,json_fetcher)
        rows=normalize_source_rows(route,transport,rows)
    except SourceFailure as exc: return [_result(t,"source_failed",None,observed_at,route,"official_json_openapi" if exc.attempts else "official_csv",bool(exc.attempts),[str(exc)],[],None,None,exc.attempts) for t in targets]
    periods={_roc_date(field(row,"reporting_period")) for row in rows}; periods.discard(None)
    report_dates={_report_date(field(row,"source_report_date")) for row in rows}; report_dates.discard(None)
    period=next(iter(periods)) if len(periods)==1 else None; report_date=next(iter(report_dates)) if len(report_dates)==1 else None
    out=[]
    for target in targets:
        status,matches,diagnostics=bind_rows(rows,target)
        if status=="binding_failed": out.append(_result(target,"binding_failed",None,observed_at,route,transport,fallback,["exact_company_code_binding_failed"],_binding_diagnostics(diagnostics),period,report_date,attempts)); continue
        if not matches: out.append(_result(target,"not_yet_available",None,observed_at,route,transport,fallback,[],[],period,report_date,attempts)); continue
        normalized=[]
        try:
            for row in matches: normalized.append((_value(row), hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True).encode()).hexdigest()))
        except SourceFailure as exc: out.append(_result(target,"source_failed",None,observed_at,route,transport,fallback,[str(exc)],[],period,report_date,attempts)); continue
        if len({h for _,h in normalized}) != 1: out.append(_result(target,"binding_failed",None,observed_at,route,transport,fallback,["conflicting_duplicate_normalized_source_rows"],[{"kind":"binding_conflict","normalized_record_hashes":sorted(h for _,h in normalized)}],period,report_date,attempts)); continue
        out.append(_result(target,"available",normalized[0][0],observed_at,route,transport,fallback,[],[],period,report_date,attempts))
    return out

def _binding_diagnostics(rows):
    return [] if not rows else [{"kind":"company_name_mismatch","source_company_codes":sorted({str(x.get("company_code", "")) for x in rows})}]
def _result(target,status,value,observed_at,route,transport,fallback,caveats,diagnostics=None,period=None,report_date=None,attempts=None):
    return {"schema_version":"phase_g_monthly_revenue_operation_evidence.v1","executor_id":"phase_g_official_research_executor","capability_id":"monthly_revenue","target":{k:target[k] for k in ("canonical_target_id","market","security_code")},"status":status,"source":{"source_family":SOURCE_FAMILY,"source_contract_id":route["contract"],"transport":transport,"fallback_used":fallback,"fallback_attempted":fallback or bool(attempts),"attempt_failures":attempts or []},"observed_at":observed_at,"coverage":{"mode":"latest_available_reporting_period","reporting_period":period,"source_report_date":report_date},"value":value,"diagnostics":diagnostics or [],"caveats":caveats}
