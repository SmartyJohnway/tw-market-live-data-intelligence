#!/usr/bin/env python3
"""Parse a complete TPEx company-delisting JSON response or legacy supplied HTML."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from common import normalize_date, normalize_text
from lifecycle_common import (
    LifecycleSchemaDrift,
    detect_calendar,
    make_event,
    parse_standard_table,
)

LANDING_URL = "https://www.tpex.org.tw/zh-tw/mainboard/listed/delisted.html"
API_URL = "https://www.tpex.org.tw/www/zh-tw/company/deListed"
API_FIELDS = ["股票代號", "公司名稱", "終止上櫃日期", "終止上櫃原因", "公司資料網址"]
API_ROOT_KEYS = {"tables", "date", "stat"}
API_TABLE_KEYS = {"fields", "data", "totalCount", "title", "notes"}
MAX_ALL_ROWS = 1000


def _drift(code: str, detail: dict[str, Any] | None = None) -> LifecycleSchemaDrift:
    return LifecycleSchemaDrift(code, detail or {})


def _parse_api(data: bytes, source_url: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _drift("tpex_api_invalid_json") from None

    if not isinstance(payload, dict):
        raise _drift("tpex_api_root_schema_drift")
    if payload.get("stat") != "ok":
        # Do not copy provider error text into long-lived evidence.
        raise _drift("tpex_api_application_error", {"stat_is_ok": False})
    if set(payload) != API_ROOT_KEYS:
        raise _drift("tpex_api_root_schema_drift")
    if payload.get("date") != "ALL":
        raise _drift("tpex_api_not_all_history", {"date_all": False})

    tables = payload.get("tables")
    if not isinstance(tables, list) or len(tables) != 1 or not isinstance(tables[0], dict):
        raise _drift("tpex_api_table_count_or_shape_drift")
    table = tables[0]
    if set(table) != API_TABLE_KEYS or table.get("fields") != API_FIELDS:
        raise _drift("tpex_api_table_schema_drift")
    if not isinstance(table.get("title"), str) or not isinstance(table.get("notes"), list):
        raise _drift("tpex_api_table_metadata_drift")

    rows = table.get("data")
    total = table.get("totalCount")
    if not isinstance(rows, list) or type(total) is not int or total < 0 or total > MAX_ALL_ROWS:
        raise _drift("tpex_api_count_or_data_type_drift")
    if len(rows) != total:
        raise _drift("tpex_api_incomplete_all_response", {
            "returned_row_count": len(rows), "total_count": total,
        })
    if total == 0:
        return []

    events: list[dict[str, Any]] = []
    identities: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(API_FIELDS):
            raise _drift("tpex_api_row_width_drift", {"row_index": index})
        if any(not isinstance(value, str) for value in row):
            raise _drift("tpex_api_row_value_type_drift", {"row_index": index})
        code, company, raw_date, reason, _company_url = row
        code = normalize_text(code)
        company = normalize_text(company)
        raw_date = normalize_text(raw_date)
        if not re.fullmatch(r"\d{4,6}", code) or not company or not raw_date:
            raise _drift("tpex_api_required_field_missing", {"row_index": index})
        calendar = detect_calendar(raw_date)
        effective_date = normalize_date(raw_date)
        if calendar != "ROC" or effective_date is None:
            raise _drift("tpex_api_invalid_roc_date", {"row_index": index})
        identity = (code, effective_date)
        if identity in identities:
            raise _drift("tpex_api_duplicate_lifecycle_identity", {"row_index": index})
        identities.add(identity)

        event = make_event(
            {
                "security_code": code,
                "security_name_zh": company,
                "effective_date": raw_date,
                "reason": normalize_text(reason),
            },
            event_type="tpex_delisted",
            source_family="tpex_company_delisted_api",
            source_url=source_url,
            evidence_status="official_explicit",
        )
        event["reason_raw"] = normalize_text(reason)
        event["provenance"].update({
            "response_contract": "tpex_company_deListed_all_v1",
            "row_index": index,
            "total_count": total,
        })
        events.append(event)
    return events


def parse(data: bytes, source_url: str) -> list[dict[str, Any]]:
    """Parse a captured TPEx JSON response; retain legacy HTML fixture support.

    A client-rendered landing shell is not an empty data response: it continues to
    fail through the legacy table parser with LifecycleSchemaDrift.
    """
    if source_url == API_URL:
        return _parse_api(data, source_url)
    if source_url == LANDING_URL:
        return parse_standard_table(
            data,
            event_type="tpex_delisted",
            source_family="tpex_termination_table",
            source_url=source_url,
        )
    raise _drift("tpex_source_url_not_governed")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--source-url", required=True)
    a = p.parse_args()
    try:
        events = parse(a.input.read_bytes(), a.source_url)
        result = {
            "acquisition_status": "data" if events else "empty_valid",
            "event_count": len(events), "events": events, "issues": [],
        }
        exit_code = 0
    except LifecycleSchemaDrift as exc:
        result = {
            "acquisition_status": "schema_drift", "event_count": 0,
            "events": [], "issues": [{"code": exc.issue_code, "detail": exc.detail}],
        }
        exit_code = 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(exit_code)
