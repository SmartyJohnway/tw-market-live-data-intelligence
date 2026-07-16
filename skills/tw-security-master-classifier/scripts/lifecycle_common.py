#!/usr/bin/env python3
"""Shared deterministic helpers for supplied official lifecycle captures."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

from common import canonical_hash, normalize_date, normalize_text


class LifecycleSchemaDrift(ValueError):
    """Raised when an official capture has no recognizable lifecycle table contract."""

    def __init__(self, issue_code: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(issue_code)
        self.issue_code = issue_code
        self.detail = detail or {}


class Tables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.table: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table": self.table = []
        elif tag == "tr" and self.table is not None: self.row = []
        elif tag in {"td", "th"} and self.row is not None: self.cell = []
        elif tag == "br" and self.cell is not None: self.cell.append(" ")

    def handle_data(self, data: str) -> None:
        if self.cell is not None: self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.cell is not None and self.row is not None:
            self.row.append(normalize_text("".join(self.cell))); self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            if any(self.row): self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            if self.table: self.tables.append(self.table)
            self.table = None


def parse_tables(data: bytes) -> list[list[list[str]]]:
    text = data.decode("utf-8-sig", errors="strict")
    parser = Tables(); parser.feed(text)
    return parser.tables


def header_key(value: str) -> str:
    text = normalize_text(value).casefold()
    if any(term in text for term in ("代號", "代碼", "code", "上市編號", "上櫃編號", "證券編號")): return "security_code"
    if any(term in text for term in ("名稱", "name")): return "security_name_zh"
    if any(term in text for term in ("終止上市", "終止上櫃", "終止日", "effective", "delisting")): return "effective_date"
    if any(term in text for term in ("最後交易", "last trading")): return "last_trading_date"
    if any(term in text for term in ("到期", "maturity")): return "maturity_date"
    if any(term in text for term in ("公告日", "announcement")): return "announcement_date"
    if any(term in text for term in ("原因", "reason")): return "reason"
    return "unknown"


def rows_as_dicts(data: bytes) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    tables = parse_tables(data)
    if not tables:
        raise LifecycleSchemaDrift("no_html_tables")
    recognized_headers = 0
    observed_header_candidates: list[list[str]] = []
    for table in tables:
        headers: dict[int, str] | None = None
        for row in table:
            mapped = {index: header_key(cell) for index, cell in enumerate(row)}
            if "security_code" in mapped.values() and any(key in mapped.values() for key in ("effective_date", "announcement_date", "maturity_date")):
                headers = mapped; recognized_headers += 1; continue
            if headers is None and len(observed_header_candidates) < 5:
                observed_header_candidates.append(row)
            if headers:
                item = {headers[index]: cell for index, cell in enumerate(row) if index in headers and headers[index] != "unknown" and cell}
                if item.get("security_code"): output.append(item)
    if recognized_headers == 0:
        raise LifecycleSchemaDrift("unrecognized_lifecycle_header", {"observed_header_candidates": observed_header_candidates})
    return output


def detect_calendar(value: str | None) -> str:
    raw = normalize_text(value)
    if not raw:
        return "unknown"
    if re.fullmatch(r"\d{2,3}年\d{1,2}月\d{1,2}日", raw):
        return "ROC"
    if re.fullmatch(r"\d{2,3}[-/.]\d{1,2}[-/.]\d{1,2}", raw) or re.fullmatch(r"\d{7}", raw):
        return "ROC"
    if re.fullmatch(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", raw) or re.fullmatch(r"\d{8}", raw):
        return "Gregorian"
    return "unknown"


def make_event(row: dict[str, str], *, event_type: str, source_family: str, source_url: str, evidence_status: str = "official_table") -> dict[str, Any]:
    raw_effective = row.get("effective_date")
    raw_evidence_date = raw_effective or row.get("announcement_date") or row.get("maturity_date")
    event: dict[str, Any] = {
        "source_family": source_family,
        "source_url": source_url,
        "security_code": row["security_code"],
        "security_name_zh": row.get("security_name_zh", ""),
        "event_type": event_type,
        "effective_date": normalize_date(raw_effective) or "unknown",
        "date_raw": raw_evidence_date or "",
        "calendar": detect_calendar(raw_evidence_date),
        "evidence_status": evidence_status,
        "provenance": {"adapter": source_family, "supplied_capture": True},
    }
    for key in ("announcement_date", "maturity_date", "last_trading_date"):
        if row.get(key): event[key] = normalize_date(row[key]) or "unknown"
    if row.get("reason"): event["reason_code"] = normalize_text(row["reason"])
    event["event_key"] = canonical_hash({key: event.get(key) for key in ("security_code", "event_type", "effective_date", "source_url")})
    return event


def parse_standard_table(data: bytes, *, event_type: str, source_family: str, source_url: str, evidence_status: str = "official_table") -> list[dict[str, Any]]:
    return [make_event(row, event_type=event_type, source_family=source_family, source_url=source_url, evidence_status=evidence_status) for row in rows_as_dicts(data)]
