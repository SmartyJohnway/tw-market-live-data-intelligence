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

class SourceFailure(Exception): pass

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

def fetch_once(route: dict[str, str], csv_fetcher: Fetcher, json_fetcher: Fetcher) -> tuple[list[dict[str, Any]], str, bool]:
    try:
        return parse_csv(csv_fetcher(route["csv_url"])), "official_csv", False
    except Exception as primary:
        try:
            return parse_json(json_fetcher(route["json_url"])), "official_json_openapi", True
        except Exception as fallback:
            raise SourceFailure(f"primary={type(primary).__name__};fallback={type(fallback).__name__}") from fallback

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
        row_code=field(row, "公司代號", "公司代碼", "company_code")
        if row_code == code: matches.append(row)
        elif name and field(row, "公司名稱", "公司簡稱", "company_name") == name: name_mismatch.append(row)
    if name_mismatch and not matches: return "binding_failed", [], name_mismatch
    return "matched" if matches else "missing", matches, []
