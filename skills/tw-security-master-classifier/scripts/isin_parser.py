#!/usr/bin/env python3
"""Parse TWSE ISIN HTML while preserving route and section evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from common import canonical_hash, file_sha256, isin_checksum_valid, normalize_date, normalize_text


PARSER_VERSION = "1.0.0"
ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
CFI_RE = re.compile(r"^[A-Z0-9]{6}$")
SECURITY_BLOCK_MARKERS = (
    "FOR SECURITY REASONS, THIS PAGE CAN NOT BE ACCESSED",
    "因為安全性考量，您所執行的頁面無法呈現",
    "THE PAGE CANNOT BE ACCESSED",
)


class TableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: list[str] = []
        self.tables: list[list[list[str]]] = []
        self._heading_tag: str | None = None
        self._heading_parts: list[str] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"h1", "h2", "h3", "h4"}:
            self._heading_tag = tag
            self._heading_parts = []
        elif tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell_parts = []
        elif tag == "br" and self._cell_parts is not None:
            self._cell_parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._heading_tag is not None:
            self._heading_parts.append(data)
        if self._cell_parts is not None:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == self._heading_tag:
            text = normalize_text("".join(self._heading_parts))
            if text:
                self.headings.append(text)
            self._heading_tag = None
            self._heading_parts = []
        elif tag in {"td", "th"} and self._cell_parts is not None and self._row is not None:
            self._row.append(normalize_text("".join(self._cell_parts)))
            self._cell_parts = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if any(self._row):
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None


def decode_html(data: bytes) -> tuple[str, str]:
    declared: list[str] = []
    prefix = data[:4096].decode("latin-1", errors="ignore")
    match = re.search(r"charset\s*=\s*['\"]?([A-Za-z0-9._-]+)", prefix, re.I)
    if match:
        declared.append(match.group(1))
    candidates = declared + ["utf-8-sig", "utf-8", "cp950", "big5", "big5hkscs"]
    seen: set[str] = set()
    for encoding in candidates:
        key = encoding.lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            return data.decode(encoding, errors="strict"), encoding
        except (UnicodeDecodeError, LookupError):
            continue
    raise UnicodeError("unable to decode HTML with controlled encodings")


def classify_payload(text: str) -> str:
    upper = text.upper()
    if any(marker.upper() in upper for marker in SECURITY_BLOCK_MARKERS):
        return "security_block"
    if "ISIN" not in upper:
        return "schema_drift"
    return "data"


def _header_key(value: str) -> str:
    text = normalize_text(value).casefold()
    if "isin" in text or "國際證券辨識號碼" in text:
        return "isin"
    if "cficode" in text.replace(" ", "") or text == "cfi code":
        return "cfi"
    if "備註" in text or "remark" in text:
        return "remarks"
    if "產業" in text or "industrial" in text:
        return "industry"
    if "市場" in text or text == "market":
        return "market"
    if "到期" in text or "maturity" in text:
        return "maturity_date"
    if "發布" in text or "announcement" in text:
        return "announcement_date"
    if "登錄" in text or "register" in text:
        return "registration_date"
    if "發行" in text or "issued" in text:
        return "issue_date"
    if "上市" in text or "掛牌" in text or "listed" in text:
        return "listing_date"
    if "代號" in text or "security code" in text or "security name" in text or "有價證券名稱" in text:
        return "code_name"
    return re.sub(r"\W+", "_", text).strip("_") or "unknown"


def _split_code_name(value: str) -> tuple[str | None, str]:
    text = normalize_text(value)
    parts = text.split(" ", 1)
    if len(parts) == 2 and re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{1,11}", parts[0], re.I):
        return parts[0].upper(), parts[1].strip()
    return None, text


def parse_html(
    data: bytes,
    *,
    lane: str,
    mode: int,
    source_url: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    text, encoding = decode_html(data)
    acquisition_status = classify_payload(text)
    base: dict[str, Any] = {
        "parser_version": PARSER_VERSION,
        "source_family": "twse_isin",
        "source_lane": lane,
        "source_url": source_url,
        "str_mode": mode,
        "observed_at": observed_at,
        "raw_payload_sha256": file_sha256(data),
        "encoding": encoding,
        "acquisition_status": acquisition_status,
        "records": [],
        "issues": [],
    }
    if acquisition_status != "data":
        base["issues"].append(f"payload_not_data:{acquisition_status}")
        return base

    parser = TableHTMLParser()
    parser.feed(text)
    headings = list(dict.fromkeys(parser.headings))
    page_title = next((h for h in headings if "更新日期" not in h and "updated" not in h.casefold()), "")
    update_text = next((h for h in headings if "更新日期" in h or "updated" in h.casefold()), "")
    update_match = re.search(r"(\d{2,4}[./-]\d{1,2}[./-]\d{1,2}|\d{7,8})", update_text)
    source_date_raw = update_match.group(1) if update_match else None
    source_date = normalize_date(source_date_raw)
    base.update(
        {
            "page_title": page_title,
            "headings": headings,
            "source_updated_date_raw": source_date_raw,
            "source_updated_date": source_date,
        }
    )

    for table in parser.tables:
        header_map: dict[int, str] = {}
        section_heading: str | None = None
        for cells in table:
            nonempty = [cell for cell in cells if cell]
            if not nonempty:
                continue
            if any("ISIN" in cell.upper() or "國際證券辨識號碼" in cell for cell in cells):
                header_map = {index: _header_key(cell) for index, cell in enumerate(cells)}
                continue
            isin_index = next((i for i, cell in enumerate(cells) if ISIN_RE.fullmatch(cell.upper())), None)
            if isin_index is None:
                if len(nonempty) == 1 and len(nonempty[0]) <= 120:
                    section_heading = nonempty[0]
                continue
            if not header_map:
                base["issues"].append("data_row_before_header")
                continue

            mapped: dict[str, Any] = {header_map.get(i, f"column_{i}"): cell for i, cell in enumerate(cells)}
            isin = cells[isin_index].upper()
            first = mapped.get("code_name", cells[0] if cells else "")
            code, name = _split_code_name(first)
            record: dict[str, Any] = {
                "source_family": "twse_isin",
                "source_lane": lane,
                "source_url": source_url,
                "str_mode": mode,
                "page_title": page_title,
                "section_heading": section_heading,
                "source_updated_date": source_date,
                "security_code": code,
                "isin": isin,
                "cfi": normalize_text(mapped.get("cfi", "")).upper() or None,
                "market": normalize_text(mapped.get("market", "")) or None,
                "industry": normalize_text(mapped.get("industry", "")) or None,
                "remarks": normalize_text(mapped.get("remarks", "")),
                "raw_cells": cells,
            }
            record["security_name_zh" if lane == "zh" else "security_name_en"] = name
            for date_key in ("issue_date", "listing_date", "registration_date", "maturity_date", "announcement_date"):
                if mapped.get(date_key):
                    record[f"{date_key}_raw"] = mapped[date_key]
                    record[date_key] = normalize_date(mapped[date_key])
            record["row_hash"] = canonical_hash(record)
            if not isin_checksum_valid(isin):
                record.setdefault("issues", []).append("invalid_isin_checksum")
            if record["cfi"] and not CFI_RE.fullmatch(record["cfi"]):
                record.setdefault("issues", []).append("invalid_cfi_format")
            if any("�" in normalize_text(record.get(key)) for key in ("security_code", "isin", "cfi")):
                record.setdefault("issues", []).append("replacement_character_in_identity")
            base["records"].append(record)

    if not base["records"]:
        base["issues"].append("no_data_rows")
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Saved official HTML payload")
    parser.add_argument("--lane", choices=("zh", "en"), required=True)
    parser.add_argument("--mode", type=int, choices=range(1, 13), required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--observed-at")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = parse_html(
        args.input.read_bytes(),
        lane=args.lane,
        mode=args.mode,
        source_url=args.source_url,
        observed_at=args.observed_at,
    )
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if result["acquisition_status"] == "data" and result["records"] else 1


if __name__ == "__main__":
    sys.exit(main())
