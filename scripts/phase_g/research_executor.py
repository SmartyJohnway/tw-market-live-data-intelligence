"""Dependency-injected, target-bounded Phase G research execution primitives."""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Any, Callable, Iterable

EXECUTOR_ID = "phase_g_official_research_executor"

ROUTES = {
    ("material_disclosures", "TWSE"): {"contract": "t187ap04_L", "csv_url": "https://mopsfin.twse.com.tw/opendata/t187ap04_L.csv", "json_url": "https://openapi.twse.com.tw/v1/opendata/t187ap04_L"},
    ("material_disclosures", "TPEX"): {"contract": "t187ap04_O", "csv_url": "https://mopsfin.twse.com.tw/opendata/t187ap04_O.csv", "json_url": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap04_O"},
    ("monthly_revenue", "TWSE"): {"contract": "t187ap05_L", "csv_url": "https://mopsfin.twse.com.tw/opendata/t187ap05_L.csv", "json_url": "https://openapi.twse.com.tw/v1/opendata/t187ap05_L"},
    ("monthly_revenue", "TPEX"): {"contract": "t187ap05_O", "csv_url": "https://mopsfin.twse.com.tw/opendata/t187ap05_O.csv", "json_url": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O"},
}

Fetcher = Callable[[str], str | bytes | list[dict[str, Any]]]

class SourceFailure(Exception):
    def __init__(self, code: str, attempts: list[dict[str, str]] | None = None):
        super().__init__(code); self.code=code; self.attempts=attempts or []

@dataclass(frozen=True)
class TransportResult:
    rows: list[dict[str, Any]]
    transport: str
    fallback_attempted: bool
    attempt_failures: list[dict[str, str]]

def parse_csv(payload: str | bytes) -> list[dict[str, str]]:
    text = payload.decode("utf-8-sig") if isinstance(payload, bytes) else payload
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or not rows[0] or not any(rows[0].keys()): raise SourceFailure("empty_or_unverifiable_source")
    return [{str(k).strip(): (v or "").strip() for k, v in row.items() if k is not None} for row in rows]

def parse_json(payload: str | bytes | list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(payload, list): rows = payload
    else:
        text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        rows = json.loads(text)
    if not isinstance(rows, list) or not rows or not all(isinstance(x, dict) for x in rows): raise SourceFailure("empty_or_unverifiable_source")
    return rows

def fetch_once(route: dict[str, str], csv_fetcher: Fetcher, json_fetcher: Fetcher) -> TransportResult:
    try:
        return TransportResult(parse_csv(csv_fetcher(route["csv_url"])), "official_csv", False, [])
    except Exception as primary:
        attempts=[{"transport":"official_csv","failure":type(primary).__name__}]
        try:
            return TransportResult(parse_json(json_fetcher(route["json_url"])), "official_json_openapi", True, attempts)
        except Exception as fallback:
            raise SourceFailure("all_governed_transports_failed", attempts+[{"transport":"official_json_openapi","failure":type(fallback).__name__}]) from fallback

def failed_provenance(result: TransportResult | None, failure: SourceFailure) -> tuple[str, bool, bool, list[dict[str, str]]]:
    """Retain transport state when parse/normalization fails after a fetch."""
    if result is None:
        attempts=failure.attempts
        attempted=any(x["transport"] == "official_json_openapi" for x in attempts)
        transport="official_json_openapi" if attempted else "official_csv"
        return transport, False, attempted, attempts
    attempts=result.attempt_failures + [{"transport":result.transport,"failure":failure.code}]
    return result.transport, False, result.fallback_attempted, attempts

SOURCE_FIELD_MAPPINGS: dict[tuple[str, str], dict[str, tuple[str, ...]]] = {
    # TWSE Open Data keeps its established Chinese column names in both transports.
    **{(contract, transport): {
        "company_code": ("公司代號",), "company_name": ("公司名稱",),
        "source_report_date": ("出表日期",), "publication_date": ("發言日期",),
        "publication_time": ("發言時間",),
    } for contract in ("t187ap04_L", "t187ap04_O") for transport in ("official_csv", "official_json_openapi")},
    # TPEx's saved material-disclosure JSON probe has a distinct English envelope.
    ("t187ap04_O", "official_json_openapi"): {
        "company_code": ("SecuritiesCompanyCode",), "company_name": ("CompanyName",),
        "source_report_date": ("Date",), "publication_date": ("發言日期",),
        "publication_time": ("發言時間",),
    },
    **{(contract, transport): {
        "company_code": ("公司代號",), "company_name": ("公司名稱",),
        "source_report_date": ("出表日期",), "reporting_period": ("資料年月",),
        "current_month_revenue": ("營業收入-當月營收",),
        "previous_month_revenue": ("營業收入-上月營收",),
        "previous_year_same_month_revenue": ("營業收入-去年當月營收",),
        "mom_pct": ("營業收入-上月比較增減(%)",), "yoy_pct": ("營業收入-去年同月增減(%)",),
        "ytd_revenue": ("累計營業收入-當月累計營收",),
        "previous_year_ytd_revenue": ("累計營業收入-去年累計營收",),
        "ytd_yoy_pct": ("累計營業收入-前期比較增減(%)",), "note": ("備註",),
    } for contract in ("t187ap05_L", "t187ap05_O") for transport in ("official_csv", "official_json_openapi")},
}

def normalize_source_rows(route: dict[str, str], transport: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map a governed route/transport shape into canonical binding concepts."""
    contract=route["contract"]
    aliases=SOURCE_FIELD_MAPPINGS.get((contract, transport))
    if aliases is None: raise SourceFailure("unsupported_governed_source_contract")
    required=("company_code","publication_date","publication_time") if contract.startswith("t187ap04") else tuple(aliases)
    result=[]
    for row in rows:
        item=dict(row)
        for canonical,names in aliases.items():
            value=field(row,*names)
            if value is not None: item[canonical]=value
        # Empty percentages and notes are source-faithful nullable values.  Their
        # columns must still exist so an upstream renamed field fails closed.
        if any(not any(name in row for name in aliases[key]) for key in required):
            raise SourceFailure("source_contract_required_field_missing")
        if any(key not in item for key in required if key not in {"mom_pct", "yoy_pct", "ytd_yoy_pct", "note"}):
            raise SourceFailure("source_contract_required_value_missing")
        result.append(item)
    return result

def field(row: dict[str, Any], *names: str) -> str | None:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "": return str(value).strip()
    return None

def bind_rows(rows: Iterable[dict[str, Any]], target: dict[str, Any]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    code = str(target["security_code"])
    name = target.get("security_name_zh")
    matches=[]; name_mismatch=[]
    for row in rows:
        row_code=field(row, "company_code")
        if row_code == code: matches.append(row)
        elif name and field(row, "company_name") == name: name_mismatch.append(row)
    if name_mismatch and not matches: return "binding_failed", [], name_mismatch
    return "matched" if matches else "missing", matches, []
