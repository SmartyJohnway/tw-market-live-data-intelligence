"""Bounded DGPA closure authority parsing and adjudication for P0 R1/R2."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from html.parser import HTMLParser
import re
from typing import Any, Callable
from urllib.parse import parse_qs, urljoin, urlparse

DAILY_URL = "https://www.dgpa.gov.tw/typh/daily/nds.html?uid=31"
ARCHIVE_BASE = "https://www.dgpa.gov.tw/informationlist?uid=374&page="
OFFICIAL_HOST = "www.dgpa.gov.tw"
TARGET_DAILY = "2026-10-16"
TARGET_HISTORICAL = "2026-10-15"
MAX_DAILY, MAX_INDEX, MAX_DETAIL, MAX_TOTAL = 2, 6, 2, 10


class _DailyStatusError(ValueError):
    def __init__(self, code: str, diagnostics: dict[str, Any] | None = None) -> None:
        super().__init__(code)
        self.diagnostics = diagnostics


def parse_roc_date(text: str) -> str:
    patterns = [
        (r"(?<!\d)(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?", 1911),
        (r"(?<!\d)(\d{2,3})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{1,2})(?!\d)", 1911),
        (r"(?<!\d)(20\d{2})[-/.年]\s*(\d{1,2})[-/.月]\s*(\d{1,2})日?", 0),
    ]
    matches = [(m.start(), m, offset) for pattern, offset in patterns for m in re.finditer(pattern, text)]
    if matches:
        _, match, offset = min(matches, key=lambda item: item[0])
        year, month, day = map(int, match.groups())
        return date(year + offset, month, day).isoformat()
    raise ValueError("dgpa_target_date_unparseable")


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: list[str] = []
        self.text: list[str] = []
        self.semantic_text: list[str] = []
        self.rows: list[list[str]] = []
        # Structured companion to the legacy text-only rows view.  Daily status
        # adjudication needs cell roles; callers of ``rows`` remain compatible.
        self.row_records: list[dict[str, Any]] = []
        self.links: list[dict[str, str]] = []
        self.text_blocks: list[dict[str, Any]] = []
        self._heading = False
        self._cell = False
        self._row: list[str] | None = None
        self._row_cells: list[dict[str, str]] = []
        self._cell_tag: str | None = None
        self._row_links: list[dict[str, str]] = []
        self._cell_text: list[str] = []
        self._link: dict[str, str] | None = None
        self._excluded_depth = 0
        self._block_stack: list[dict[str, Any]] = []
        self._block_sequence = 0
        self._block_id = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = dict(attrs)
        if tag in {"nav", "footer", "script", "style", "noscript"}:
            self._excluded_depth += 1
        if self._excluded_depth == 0 and tag in {"div", "p", "section", "article", "aside", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th"}:
            ancestors = [item["node_id"] for item in self._block_stack]
            self._block_stack.append({"tag": tag, "parts": [], "depth": len(self._block_stack),
                "node_id": self._block_id, "ancestor_ids": ancestors})
            self._block_id += 1
        if tag in {"h1", "h2", "h3"}:
            self._heading = True
        elif tag == "tr":
            self._row = []
            self._row_cells = []
            self._row_links = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = True
            self._cell_tag = tag
            self._cell_text = []
        elif tag == "a" and attrs_d.get("href"):
            self._link = {"href": str(attrs_d["href"]), "text": "", "row_text": ""}
            if self._row is not None:
                self._row_links.append(self._link)

    def handle_endtag(self, tag: str) -> None:
        if self._block_stack and self._block_stack[-1]["tag"] == tag:
            block = self._block_stack.pop()
            value = " ".join("".join(block["parts"]).split())
            if value:
                self.text_blocks.append({"sequence": self._block_sequence, "depth": block["depth"], "tag": tag,
                    "text": value, "node_id": block["node_id"], "ancestor_ids": block["ancestor_ids"]})
                self._block_sequence += 1
        if tag in {"h1", "h2", "h3"}:
            self._heading = False
        elif tag in {"td", "th"} and self._cell and self._row is not None:
            cell_text = " ".join("".join(self._cell_text).split())
            self._row.append(cell_text)
            self._row_cells.append({"tag": self._cell_tag or "td", "text": cell_text})
            self._cell = False
            self._cell_tag = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
                self.row_records.append({"cells": self._row_cells})
            row_text = " ".join(self._row)
            for link in self._row_links:
                link["row_text"] = row_text
            self._row = None
        elif tag == "a" and self._link is not None:
            self.links.append(self._link)
            self._link = None
        if tag in {"nav", "footer", "script", "style", "noscript"} and self._excluded_depth:
            self._excluded_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._excluded_depth:
            return
        value = data.strip()
        if not value:
            return
        self.text.append(value)
        if self._link is None:
            self.semantic_text.append(value)
        if self._link is None:
            for block in self._block_stack:
                block["parts"].append(data)
        if self._heading:
            self.headings.append(value)
        if self._cell:
            self._cell_text.append(data)
        if self._link is not None:
            self._link["text"] += data


def parse_html(body: bytes, content_type: str | None = None) -> _Page:
    charset = "utf-8"
    if content_type:
        match = re.search(r"charset\s*=\s*['\"]?([^; '\"]+)", content_type, re.I)
        if match:
            charset = match.group(1)
    try:
        text = body.decode(charset, errors="strict")
    except (LookupError, UnicodeDecodeError) as exc:
        raise ValueError("dgpa_encoding_invalid") from exc
    parser = _Page()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:
        raise ValueError("dgpa_html_invalid") from exc
    return parser


def _page_status_signals(table_diagnostics: dict[str, Any], visible: str) -> list[str]:
    signals = []
    if any(phrase in visible for phrase in ("無停班停課訊息", "目前無停班停課訊息", "無停止上班上課訊息")):
        signals.append("NO_CLOSURE_NOTICE")
    for row in table_diagnostics["rows"]:
        semantic = row["normalized_status_semantics"]
        if semantic == "NO_CLOSURE_NOTICE":
            continue
        if row["classification"] == "LOCALITY_CLOSURE_STATUS":
            signals.append(semantic)
        elif row["locality"] in {"臺北市", "台北市"} and semantic not in {None, "UNRESOLVED"}:
            signals.append(semantic)
    return sorted(set(signals))


def daily_candidate_diagnostics(body: bytes, content_type: str | None = None) -> dict[str, Any]:
    """Return bounded subject-block diagnostics even when adjudication fails."""
    page = parse_html(body, content_type)
    pattern = re.compile(r"(?:天然災害\s*)?停止\s*(?:上班及上課|上班上課|辦公及上課|辦公上課)\s*情形")
    date_pattern = r"(?<!\d)(?:(?:\d{2,3}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?)|(?:\d{2,3}\s*[/.-]\s*\d{1,2}\s*[/.-]\s*\d{1,2})|(?:20\d{2}[-/.年]\s*\d{1,2}[-/.月]\s*\d{1,2}日?))"
    blocks = [item for item in page.text_blocks if pattern.search(item["text"])
              and not (item["tag"] == "th" and _is_table_schema_label(item["text"]))]
    visible = " ".join(page.semantic_text)
    table_diagnostics = _table_semantic_diagnostics(page)
    signals = _page_status_signals(table_diagnostics, visible)
    status_signal = signals[0] if len(signals) == 1 else "CONFLICTING_PAGE_STATUS" if len(signals) > 1 else "UNRESOLVED"
    candidates = []
    for index, item in enumerate(blocks):
        date_matches = list(re.finditer(date_pattern, item["text"]))
        dates = {parse_roc_date(match.group(0)) for match in date_matches}
        block_index = page.text_blocks.index(item)
        for neighbor_index in (block_index - 1, block_index + 1):
            if 0 <= neighbor_index < len(page.text_blocks):
                neighbor = page.text_blocks[neighbor_index]
                if abs(neighbor["depth"] - item["depth"]) <= 1 and not re.search(r"更新|資料|時間|行政院|人事行政|停班|上課", neighbor["text"]):
                    adjacent = list(re.finditer(date_pattern, neighbor["text"]))
                    if adjacent and not re.sub(date_pattern, "", neighbor["text"]).strip(" \t:：,，。|-"):
                        dates.update(parse_roc_date(match.group(0)) for match in adjacent)
        dates = sorted(dates)
        candidates.append({"candidate_id": f"subject-{index + 1}", "source_block_sequence": item["sequence"],
            "tag": item["tag"], "depth": item["depth"],
            "normalized_subject_identity": "natural_disaster_stop_work_school_status",
            "bound_date_candidates": dates, "normalized_status_semantics": status_signal,
            "link_content": False, "excluded_container": False,
            "is_excluded_container": False, "short_bounded_excerpt": item["text"][:300],
            "_node_id": item["node_id"], "_ancestor_ids": item["ancestor_ids"], "_text": item["text"]})
    excluded_ids = set()
    for item in candidates:
        item_text = " ".join(item["_text"].split())
        item_date = item["bound_date_candidates"][0] if len(item["bound_date_candidates"]) == 1 else None
        for other in candidates:
            if item is other:
                continue
            other_text = " ".join(other["_text"].split())
            other_date = other["bound_date_candidates"][0] if len(other["bound_date_candidates"]) == 1 else None
            if (item["_node_id"] in other["_ancestor_ids"] and item_date is not None
                    and item_date == other_date and other_text and other_text in item_text):
                excluded_ids.add(item["candidate_id"])
            elif (other["_node_id"] in item["_ancestor_ids"] and item_date is None
                    and other_date is not None and item_text and item_text in other_text):
                excluded_ids.add(item["candidate_id"])
    for item in candidates:
        if item["candidate_id"] in excluded_ids:
            item["is_excluded_container"] = True
            is_ancestor = any(item["_node_id"] in other["_ancestor_ids"] for other in candidates if other is not item)
            item["excluded_container_reason"] = ("ANCESTOR_PRESENTATION_CONTAINER" if is_ancestor
                                                   else "NESTED_PRESENTATION_FRAGMENT")
    active = [item for item in candidates if not item["is_excluded_container"]]
    canonical = {(item["normalized_subject_identity"], tuple(item["bound_date_candidates"]), item["normalized_status_semantics"])
                 for item in active}
    safe_candidates = [{key: value for key, value in item.items() if not key.startswith("_")} for item in candidates]
    return {"raw_subject_match_count": sum(len(list(pattern.finditer(text))) for text in page.semantic_text),
        "semantic_candidate_count": len(active), "canonical_candidate_count": len(canonical),
        "page_status_signals": signals, "candidates": safe_candidates,
        "table_semantic_diagnostics": table_diagnostics}


_SCHEMA_LABELS = ("是否停止上班上課情形", "停止上班上課查詢", "停止上班及上課資訊",
                  "天然災害停止上班上課說明", "縣市名稱", "縣市別")
_LOCALITY_NAMES = ("臺北市", "台北市", "新北市", "桃園市", "臺中市", "台中市", "臺南市", "台南市",
                   "高雄市", "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣", "南投縣",
                   "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "台東縣", "澎湖縣",
                   "金門縣", "連江縣")


def _is_table_schema_label(text: str) -> bool:
    normalized = "".join(text.split())
    return any(label in normalized for label in _SCHEMA_LABELS) or normalized.startswith("是否")


def _classify_table_row(record: dict[str, Any], index: int) -> dict[str, Any]:
    cells = record.get("cells", [])
    texts = [" ".join(str(cell.get("text", "")).split())[:200] for cell in cells]
    tags = [str(cell.get("tag", "td")) for cell in cells]
    joined = " ".join(texts)
    locality = next((name for name in _LOCALITY_NAMES if name in joined), None)
    no_notice = any(phrase in joined for phrase in ("無停班停課訊息", "目前無停班停課訊息", "無停止上班上課訊息"))
    decision_cells = [text for cell, text in zip(cells, texts)
                      if cell.get("tag") != "th" and text and not _is_table_schema_label(text)]
    decision_text = " ".join(decision_cells)
    if no_notice and not locality:
        classification, semantic = "NO_NOTICE_ROW", "NO_CLOSURE_NOTICE"
    elif not locality and ("th" in tags or any(_is_table_schema_label(text) for text in texts)):
        classification, semantic = "TABLE_SCHEMA_HEADER", None
    elif locality and decision_text:
        if any(phrase in decision_text for phrase in ("照常上班", "照常辦公", "照常上課", "正常上班", "正常辦公", "正常上課", "未停止")):
            classification, semantic = "LOCALITY_NORMAL_STATUS", "TAIPEI_NORMAL" if locality in {"臺北市", "台北市"} else "LOCALITY_NORMAL"
        elif any(phrase in decision_text for phrase in ("停止上班", "停止辦公", "停止上課", "停班停課")) and "是否" not in decision_text:
            scope = ("morning" if "上午" in decision_text
                     else "afternoon" if "下午" in decision_text
                     else "full_day" if any(term in decision_text for term in ("全天", "全日", "停止上班上課", "停止上班及上課"))
                     else None)
            semantic = ({"full_day": "TAIPEI_FULL_DAY_CLOSURE", "morning": "TAIPEI_MORNING_CLOSURE",
                         "afternoon": "TAIPEI_AFTERNOON_CLOSURE"}.get(scope, "TAIPEI_CLOSURE_SCOPE_UNRESOLVED")
                        if locality in {"臺北市", "台北市"}
                        else f"LOCALITY_{scope.upper()}_CLOSURE" if scope else "LOCALITY_CLOSURE_SCOPE_UNRESOLVED")
            classification = "LOCALITY_CLOSURE_STATUS"
        else:
            classification, semantic = "LOCALITY_UNRESOLVED_STATUS", "UNRESOLVED"
    else:
        classification, semantic = "NON_STATUS_ROW", None
    return {"row_index": index, "cell_tags": tags, "normalized_cell_texts": texts,
            "classification": classification, "locality": locality,
            "normalized_status_semantics": semantic}


def _table_semantic_diagnostics(page: _Page) -> dict[str, Any]:
    rows = [_classify_table_row(record, index) for index, record in enumerate(page.row_records)]
    return {"row_count": len(rows), "rows": rows,
            "schema_header_row_count": sum(row["classification"] == "TABLE_SCHEMA_HEADER" for row in rows),
            "locality_status_row_count": sum(row["classification"].startswith("LOCALITY_") for row in rows),
            "no_notice_row_count": sum(row["classification"] == "NO_NOTICE_ROW" for row in rows)}


def table_semantic_diagnostics(body: bytes, content_type: str | None = None) -> dict[str, Any]:
    return _table_semantic_diagnostics(parse_html(body, content_type))


def parse_daily_status(body: bytes, *, content_type: str | None, fetched_at: str) -> dict[str, Any]:
    fetched = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    cutoff = datetime.fromisoformat("2026-10-16T11:38:22+08:00")
    if fetched.tzinfo is None or fetched.utcoffset() is None or fetched < cutoff:
        raise ValueError("dgpa_daily_fetch_before_evaluation")
    page = parse_html(body, content_type)
    visible = " ".join(page.semantic_text)
    subject_pattern = re.compile(r"(?:天然災害\s*)?停止\s*(?:上班及上課|上班上課|辦公及上課|辦公上課)\s*情形")
    raw_candidates = [item for item in page.text_blocks if subject_pattern.search(item["text"])
                      and not (item["tag"] == "th" and _is_table_schema_label(item["text"]))]
    if not raw_candidates:
        raise ValueError("dgpa_daily_subject_missing")
    blocks = page.text_blocks
    date_pattern = r"(?<!\d)(?:(?:\d{2,3}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?)|(?:\d{2,3}\s*[/.-]\s*\d{1,2}\s*[/.-]\s*\d{1,2})|(?:20\d{2}[-/.年]\s*\d{1,2}[-/.月]\s*\d{1,2}日?))"
    table_diagnostics = _table_semantic_diagnostics(page)
    classified_rows = table_diagnostics["rows"]
    taipei_classified = [row for row in classified_rows if row["locality"] in {"臺北市", "台北市"}
                         and row["classification"].startswith("LOCALITY_")]
    taipei = [" ".join(row["normalized_cell_texts"]) for row in taipei_classified]
    locality_closures = [row for row in classified_rows if row["classification"] == "LOCALITY_CLOSURE_STATUS"]
    no_notice = any(phrase in visible for phrase in ("無停班停課訊息", "目前無停班停課訊息", "無停止上班上課訊息"))
    if no_notice and locality_closures:
        raise ValueError("dgpa_daily_status_conflict")
    if not no_notice and not taipei_classified:
        raise ValueError("dgpa_daily_status_missing")
    if no_notice:
        status_semantics = "NO_CLOSURE_NOTICE"
    else:
        row_states = []
        for classified in taipei_classified:
            row = " ".join(classified["normalized_cell_texts"])
            semantic = classified["normalized_status_semantics"]
            if semantic == "TAIPEI_NORMAL":
                row_states.append((semantic, row, None))
            elif semantic in {"TAIPEI_FULL_DAY_CLOSURE", "TAIPEI_MORNING_CLOSURE", "TAIPEI_AFTERNOON_CLOSURE"}:
                scope = {"TAIPEI_FULL_DAY_CLOSURE": "full_day", "TAIPEI_MORNING_CLOSURE": "morning",
                         "TAIPEI_AFTERNOON_CLOSURE": "afternoon"}[semantic]
                row_states.append((semantic, row, scope))
            else:
                raise ValueError("dgpa_daily_taipei_status_unresolved")
        if len({item[0] for item in row_states}) != 1:
            raise ValueError("dgpa_daily_semantic_conflict")
        status_semantics, _, scope = row_states[0]

    candidates: list[dict[str, Any]] = []
    for candidate_index, candidate in enumerate(raw_candidates):
        index = blocks.index(candidate)
        status_dates: set[str] = set()
        for match in re.finditer(date_pattern, candidate["text"]):
            status_dates.add(parse_roc_date(match.group(0)))
        for neighbor_index in (index - 1, index + 1):
            if 0 <= neighbor_index < len(blocks):
                neighbor = blocks[neighbor_index]
                if abs(neighbor["depth"] - candidate["depth"]) <= 1 and not re.search(r"更新|資料|時間|行政院|人事行政|停班|上課", neighbor["text"]):
                    adjacent_dates = list(re.finditer(date_pattern, neighbor["text"]))
                    remainder = re.sub(date_pattern, "", neighbor["text"])
                    if adjacent_dates and not remainder.strip(" \t:：,，。|-"):
                        status_dates.update(parse_roc_date(match.group(0)) for match in adjacent_dates)
        if len(status_dates) > 1:
            raise ValueError("dgpa_daily_date_ambiguous")
        candidate_date = next(iter(status_dates)) if status_dates else None
        candidates.append({"candidate_id": f"subject-{candidate_index + 1}", "source_block_sequence": candidate["sequence"],
            "tag": candidate["tag"], "depth": candidate["depth"],
            "normalized_subject_identity": "natural_disaster_stop_work_school_status",
            "bound_status_dates": sorted(status_dates), "status_signal": status_semantics,
            "taipei_status_if_any": status_semantics if status_semantics.startswith("TAIPEI_") else None,
            "is_link_content": False, "is_excluded_container": False,
            "short_bounded_excerpt": candidate["text"][:300], "_date": candidate_date, "_text": candidate["text"],
            "_node_id": candidate["node_id"], "_ancestor_ids": candidate["ancestor_ids"]})
    # Collapse duplicate presentations in both directions: discard a broad
    # ancestor when a descendant independently binds the same date, and
    # discard an unbound nested fragment when its bound ancestor contains it.
    remove_ids: set[str] = set()
    for item in candidates:
        item_text = " ".join(item["_text"].split())
        for other in candidates:
            if item is other:
                continue
            other_text = " ".join(other["_text"].split())
            if (item["_node_id"] in other["_ancestor_ids"]
                    and item["_date"] is not None and item["_date"] == other["_date"]
                    and other_text and other_text in item_text):
                remove_ids.add(item["candidate_id"])
            elif (other["_node_id"] in item["_ancestor_ids"] and item["_date"] is None
                    and other["_date"] is not None and item_text and item_text in other_text):
                remove_ids.add(item["candidate_id"])
    for item in candidates:
        if item["candidate_id"] in remove_ids:
            item["is_excluded_container"] = True
            item["excluded_container_reason"] = "ANCESTOR_PRESENTATION_CONTAINER"
    all_candidates = candidates
    candidates = [item for item in all_candidates if not item["is_excluded_container"]]
    def candidate_snapshot() -> dict[str, Any]:
        safe = [{key: value for key, value in item.items() if not key.startswith("_")} for item in all_candidates]
        return {"raw_subject_match_count": sum(len(list(subject_pattern.finditer(text))) for text in page.semantic_text),
            "semantic_candidate_count": len(candidates),
            "canonical_candidate_count": len({(item["normalized_subject_identity"], item["_date"], item["status_signal"]) for item in candidates}),
            "page_status_signals": _page_status_signals(table_diagnostics, visible),
            "table_semantic_diagnostics": table_diagnostics, "candidates": safe}
    for item in candidates:
        if item["_date"] is None:
            nested_match = any(other["_date"] is not None and other["_node_id"] in item["_ancestor_ids"]
                and " ".join(item["_text"].split()) in " ".join(other["_text"].split())
                for other in candidates)
            if any(other["_date"] is not None for other in candidates) and not nested_match:
                raise _DailyStatusError("dgpa_daily_semantic_ambiguity", candidate_snapshot())
    bound = {item["_date"] for item in candidates if item["_date"] is not None}
    if len(bound) > 1:
        raise _DailyStatusError("dgpa_daily_semantic_conflict", candidate_snapshot())
    if not bound:
        raise ValueError("dgpa_daily_displayed_date_mismatch")
    displayed_date = next(iter(bound))
    if displayed_date != TARGET_DAILY:
        raise ValueError("dgpa_daily_displayed_date_mismatch")
    # Repeated desktop/mobile/accessibility blocks are equivalent when their
    # independently bound date and normalized status agree. Nested text blocks
    # are treated as presentations of the same semantic fact, not as separate
    # provider facts.
    equivalence = {(item["normalized_subject_identity"], item["_date"], item["status_signal"]) for item in candidates}
    if len(equivalence) != 1:
        raise _DailyStatusError("dgpa_daily_semantic_conflict", candidate_snapshot())
    for item in candidates:
        item.pop("_date", None)
        item.pop("_text", None)
    diagnostics = {"raw_subject_match_count": sum(len(list(subject_pattern.finditer(text))) for text in page.semantic_text),
        "semantic_candidate_count": len(candidates), "canonical_candidate_count": len(equivalence),
        "candidates": [{key: value for key, value in item.items() if not key.startswith("_")} for item in all_candidates]}
    heading = " ".join(page.headings)
    update_match = re.search(r"(?:更新(?:時間|日期)?|資料更新)\s*[:：]?\s*((?:\d{2,3}年\s*)?\d{1,2}月\s*\d{1,2}日?\s*\d{1,2}[:：]\d{2}(?::\d{2})?)", visible)
    if not update_match:
        update_match = re.search(r"(?:更新(?:時間|日期)?|資料更新)\s*[:：]?\s*((?:\d{2,3}|20\d{2})[-/.]\d{1,2}[-/.]\d{1,2}\s+\d{1,2}[:：]\d{2}(?::\d{2})?)", visible)
    if not update_match or not ("行政院人事行政總處" in visible or "人事行政總處" in visible):
        raise ValueError("dgpa_daily_provenance_missing")
    if parse_roc_date(update_match.group(1)) != TARGET_DAILY:
        raise ValueError("dgpa_daily_update_date_mismatch")
    closure_event = None
    taipei_closures = [item for item in row_states if item[2] is not None] if not no_notice else []
    if taipei_closures:
        _, _, scope = taipei_closures[0]
        closure_event = {"status": "Actual", "area_name": "臺北市", "area_level": "municipality",
                         "work_status": "closed", "decision_status": "closure_confirmed",
                         "target_date": TARGET_DAILY, "closure_scope": scope}
    return {"target_date": TARGET_DAILY, "heading": heading, "status_semantics": status_semantics,
            "subject_candidate_diagnostics": diagnostics,
            "status_kind": "explicit_no_notice" if no_notice else "county_rows_present",
            "taipei_rows": taipei, "table_semantic_diagnostics": table_diagnostics,
            "source_attribution_present": "行政院人事行政總處" in visible or "人事行政總處" in visible,
            "page_update_timestamp": update_match.group(1), "closure_event": closure_event,
            "fetched_at": fetched.isoformat()}


def _detail_url(href: str, base: str) -> str:
    url = urljoin(base, href)
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    if parsed.scheme != "https" or parsed.hostname != OFFICIAL_HOST or parsed.path != "/information" or "pid" not in q or q.get("uid") != ["374"]:
        raise ValueError("dgpa_archive_detail_url_invalid")
    return url


def parse_archive_index(body: bytes, *, content_type: str | None, base_url: str) -> list[dict[str, Any]]:
    p = urlparse(base_url)
    q = parse_qs(p.query)
    if p.hostname != OFFICIAL_HOST or p.path != "/informationlist" or q.get("uid") != ["374"]:
        raise ValueError("dgpa_archive_identity_invalid")
    page = parse_html(body, content_type)
    visible = " ".join(page.text)
    if "歷次天然災害停止上班上課訊息" not in visible:
        raise ValueError("dgpa_archive_semantic_identity_missing")
    result = []
    for link in page.links:
        title = " ".join(link["text"].split())
        parsed_href = urlparse(urljoin(base_url, link["href"]))
        href_query = parse_qs(parsed_href.query)
        is_archive_detail = parsed_href.path == "/information" and href_query.get("uid") == ["374"] and bool(href_query.get("pid"))
        if not is_archive_detail:
            continue
        if "天然災害停止" not in title or "上課" not in title:
            raise ValueError("dgpa_archive_item_title_invalid")
        target = parse_roc_date(title)
        detail = _detail_url(link["href"], base_url)
        try:
            publication_date = parse_roc_date(link.get("row_text", ""))
        except ValueError as exc:
            raise ValueError("dgpa_archive_publication_date_missing") from exc
        result.append({"archive_publication_date": publication_date, "title": title,
                       "target_event_date": target, "detail_url": detail})
    if not result:
        raise ValueError("dgpa_archive_items_missing")
    return result


def adjudicate_archive_window(pages: list[dict[str, Any]], target_date: str) -> dict[str, Any]:
    if not pages:
        return {"historical_archive_target_entry_present": False, "historical_negative_evidence": False,
                "reason": "archive_window_empty", "coverage_dates": []}
    expected_page = 1
    all_items: list[dict[str, Any]] = []
    for page in pages:
        if page.get("page") != expected_page or not isinstance(page.get("items"), list) or not page["items"]:
            raise ValueError("dgpa_archive_pagination_gap")
        expected_page += 1
        all_items.extend(page["items"])
    dates = [date.fromisoformat(item["target_event_date"]) for item in all_items]
    if any(dates[i] < dates[i + 1] for i in range(len(dates) - 1)):
        raise ValueError("dgpa_archive_order_unresolved")
    matches = [x for x in all_items if x["target_event_date"] == target_date]
    if len({x["detail_url"] for x in matches}) > 1:
        raise ValueError("dgpa_archive_duplicate_target_conflict")
    crossed = dates[-1].isoformat() <= target_date
    negative = not matches and crossed
    return {"historical_archive_target_entry_present": bool(matches),
            "historical_negative_evidence": negative,
            "reason": "verified_chronological_window_crossed_target" if negative else "target_entry_requires_detail" if matches else "archive_window_not_crossed",
            "coverage_dates": [dates[0].isoformat(), dates[-1].isoformat()],
            "page_range": [1, pages[-1]["page"]], "matching_entries": matches}


def parse_detail_status(body: bytes, *, content_type: str | None, target_date: str) -> dict[str, Any]:
    page = parse_html(body, content_type)
    heading = " ".join(page.headings)
    if parse_roc_date(heading) != target_date:
        raise ValueError("dgpa_archive_detail_date_mismatch")
    taipei_rows = [" ".join(row) for row in page.rows if "臺北市" in " ".join(row) or "台北市" in " ".join(row)]
    if len(taipei_rows) != 1:
        raise ValueError("dgpa_archive_target_detail_unresolved")
    row = taipei_rows[0]
    if any(word in row for word in ("停止上班", "停止辦公", "停班停課")):
        scope = "full_day" if "全天" in row or "全日" in row else "morning" if "上午" in row else "afternoon" if "下午" in row else None
        if scope is None:
            raise ValueError("dgpa_archive_target_detail_unresolved")
        event = {"status": "Actual", "area_name": "臺北市", "area_level": "municipality",
                 "work_status": "closed", "decision_status": "closure_confirmed",
                 "target_date": target_date, "closure_scope": scope}
        return {"target_date": target_date, "taipei_status": "closed", "closure_scope": scope, "closure_event": event, "row_summary": row}
    if any(word in row for word in ("照常上班", "照常辦公", "未停止")):
        return {"target_date": target_date, "taipei_status": "normal", "closure_scope": None, "closure_event": None, "row_summary": row}
    raise ValueError("dgpa_archive_target_detail_unresolved")


@dataclass
class RequestBudget:
    daily: int = 0
    index: int = 0
    detail: int = 0

    @property
    def total(self) -> int:
        return self.daily + self.index + self.detail

    def reserve(self, kind: str) -> int:
        limits = {"daily": MAX_DAILY, "index": MAX_INDEX, "detail": MAX_DETAIL}
        if kind not in limits:
            raise ValueError("r1_unapproved_request_kind")
        if self.total >= MAX_TOTAL or getattr(self, kind) >= limits[kind]:
            raise ValueError("r1_request_budget_exceeded")
        setattr(self, kind, getattr(self, kind) + 1)
        return self.total

    def counts(self) -> dict[str, int]:
        return {"daily": self.daily, "archive_index": self.index, "archive_detail": self.detail, "total": self.total}


@dataclass
class R2RequestBudget:
    """Independent R2 ceilings; reserve before every authorized GET."""
    daily: int = 0
    index: int = 0
    detail: int = 0

    @property
    def total(self) -> int:
        return self.daily + self.index + self.detail

    def reserve(self, kind: str) -> int:
        limits = {"daily": 1, "index": 4, "detail": 1}
        if kind not in limits:
            raise ValueError("r2_unapproved_request_kind")
        if self.total >= 6 or getattr(self, kind) >= limits[kind]:
            raise ValueError("r2_request_budget_exceeded")
        setattr(self, kind, getattr(self, kind) + 1)
        return self.total

    def counts(self) -> dict[str, int]:
        return {"daily": self.daily, "archive_index": self.index, "archive_detail": self.detail, "total": self.total}


@dataclass
class R4RequestBudget:
    """Independent R4 ceilings; reserve each planned official DGPA GET first."""
    daily: int = 0
    index: int = 0
    detail: int = 0

    @property
    def total(self) -> int:
        return self.daily + self.index + self.detail

    def reserve(self, kind: str) -> int:
        limits = {"daily": 1, "index": 4, "detail": 1}
        if kind not in limits:
            raise ValueError("r4_unapproved_request_kind")
        if self.total >= 6 or getattr(self, kind) >= limits[kind]:
            raise ValueError("r4_request_budget_exceeded")
        setattr(self, kind, getattr(self, kind) + 1)
        return self.total

    def counts(self) -> dict[str, int]:
        return {"daily": self.daily, "archive_index": self.index, "archive_detail": self.detail, "total": self.total}


def validate_official_url(url: str) -> None:
    p = urlparse(url)
    if p.scheme != "https" or p.hostname != OFFICIAL_HOST or p.port not in (None, 443) or p.username or p.password:
        raise ValueError("r1_unapproved_domain")


def build_closure_events(daily: dict[str, Any], historical: dict[str, Any]) -> list[dict[str, Any]]:
    events = []
    for fact in (daily, historical):
        event = fact.get("closure_event")
        if event is not None:
            events.append(event)
    return events


def resolve_only_with_complete_authority(complete: bool, resolver: Callable[..., dict], **kwargs: Any) -> dict | None:
    """Keep the existing resolver unreachable until both scoped facts are adjudicated."""
    if complete is not True:
        return None
    return resolver(**kwargs)


def response_sha256(body: bytes) -> str:
    return sha256(body).hexdigest()
