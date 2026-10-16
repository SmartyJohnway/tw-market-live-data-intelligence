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
        self.links: list[dict[str, str]] = []
        self.text_blocks: list[dict[str, Any]] = []
        self._heading = False
        self._cell = False
        self._row: list[str] | None = None
        self._row_links: list[dict[str, str]] = []
        self._cell_text: list[str] = []
        self._link: dict[str, str] | None = None
        self._excluded_depth = 0
        self._block_stack: list[dict[str, Any]] = []
        self._block_sequence = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = dict(attrs)
        if tag in {"nav", "footer", "script", "style", "noscript"}:
            self._excluded_depth += 1
        if self._excluded_depth == 0 and tag in {"div", "p", "section", "article", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th"}:
            self._block_stack.append({"tag": tag, "parts": [], "depth": len(self._block_stack)})
        if tag in {"h1", "h2", "h3"}:
            self._heading = True
        elif tag == "tr":
            self._row = []
            self._row_links = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = True
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
                self.text_blocks.append({"sequence": self._block_sequence, "depth": block["depth"], "tag": tag, "text": value})
                self._block_sequence += 1
        if tag in {"h1", "h2", "h3"}:
            self._heading = False
        elif tag in {"td", "th"} and self._cell and self._row is not None:
            self._row.append(" ".join("".join(self._cell_text).split()))
            self._cell = False
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
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


def parse_daily_status(body: bytes, *, content_type: str | None, fetched_at: str) -> dict[str, Any]:
    fetched = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    cutoff = datetime.fromisoformat("2026-10-16T11:38:22+08:00")
    if fetched.tzinfo is None or fetched.utcoffset() is None or fetched < cutoff:
        raise ValueError("dgpa_daily_fetch_before_evaluation")
    page = parse_html(body, content_type)
    visible = " ".join(page.semantic_text)
    subject_pattern = re.compile(r"(?:天然災害\s*)?停止\s*(?:上班及上課|上班上課|辦公及上課|辦公上課)\s*情形")
    semantic_blocks = [item for item in page.text_blocks if subject_pattern.search(item["text"])]
    # Nested containers can repeat the same visible subject. Keep the smallest
    # semantic container(s), rather than searching dates across the whole page.
    if semantic_blocks:
        shortest = min(len(item["text"]) for item in semantic_blocks)
        semantic_blocks = [item for item in semantic_blocks if len(item["text"]) == shortest]
    if not semantic_blocks:
        raise ValueError("dgpa_daily_subject_missing")
    subject_positions = [m.start() for m in subject_pattern.finditer(visible)]
    if len(subject_positions) != 1:
        raise ValueError("dgpa_daily_subject_ambiguous")
    chosen = semantic_blocks[0]
    blocks = page.text_blocks
    index = next(i for i, item in enumerate(blocks) if item is chosen)
    date_pattern = r"(?<!\d)(?:(?:\d{2,3}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?)|(?:\d{2,3}\s*[/.-]\s*\d{1,2}\s*[/.-]\s*\d{1,2})|(?:20\d{2}[-/.年]\s*\d{1,2}[-/.月]\s*\d{1,2}日?))"
    status_dates = set()
    for match in re.finditer(date_pattern, chosen["text"]):
        status_dates.add(parse_roc_date(match.group(0)))
    for neighbor_index in (index - 1, index + 1):
        if 0 <= neighbor_index < len(blocks):
            neighbor = blocks[neighbor_index]
            if abs(neighbor["depth"] - chosen["depth"]) <= 1 and not re.search(r"更新|資料|時間|行政院|人事行政|停班|上課", neighbor["text"]):
                adjacent_dates = list(re.finditer(date_pattern, neighbor["text"]))
                # Only date-only neighboring blocks are semantically adjacent
                # status-date candidates; timestamp and surrounding page text
                # cannot leak into this binding.
                remainder = re.sub(date_pattern, "", neighbor["text"])
                if adjacent_dates and not remainder.strip(" \t:：,，。|-"):
                    for match in adjacent_dates:
                        status_dates.add(parse_roc_date(match.group(0)))
    if len(status_dates) > 1:
        raise ValueError("dgpa_daily_date_ambiguous")
    if not status_dates:
        raise ValueError("dgpa_daily_displayed_date_mismatch")
    displayed_date = next(iter(status_dates))
    if displayed_date != TARGET_DAILY:
        raise ValueError("dgpa_daily_displayed_date_mismatch")
    heading = " ".join(page.headings)
    update_match = re.search(r"(?:更新(?:時間|日期)?|資料更新)\s*[:：]?\s*((?:\d{2,3}年\s*)?\d{1,2}月\s*\d{1,2}日?\s*\d{1,2}[:：]\d{2}(?::\d{2})?)", visible)
    if not update_match:
        update_match = re.search(r"(?:更新(?:時間|日期)?|資料更新)\s*[:：]?\s*((?:\d{2,3}|20\d{2})[-/.]\d{1,2}[-/.]\d{1,2}\s+\d{1,2}[:：]\d{2}(?::\d{2})?)", visible)
    no_notice = any(phrase in visible for phrase in ("無停班停課訊息", "目前無停班停課訊息", "無停止上班上課訊息"))
    taipei = []
    for row in page.rows:
        joined = " ".join(row)
        if "臺北市" in joined or "台北市" in joined:
            taipei.append(joined)
    rows_with_closure = [" ".join(row) for row in page.rows if any(term in " ".join(row) for term in ("停止上班", "停止辦公", "停班停課"))]
    if no_notice and rows_with_closure:
        raise ValueError("dgpa_daily_status_conflict")
    if not no_notice and len(taipei) != 1:
        raise ValueError("dgpa_daily_status_missing")
    if not update_match or not ("行政院人事行政總處" in visible or "人事行政總處" in visible):
        raise ValueError("dgpa_daily_provenance_missing")
    if parse_roc_date(update_match.group(1)) != TARGET_DAILY:
        raise ValueError("dgpa_daily_update_date_mismatch")
    closure_event = None
    if taipei:
        row = taipei[0]
        if any(word in row for word in ("停止上班", "停止辦公", "停班停課")):
            scope = "full_day" if "全天" in row or "全日" in row else "morning" if "上午" in row else "afternoon" if "下午" in row else None
            if scope is None:
                raise ValueError("dgpa_daily_taipei_status_unresolved")
            closure_event = {"status": "Actual", "area_name": "臺北市", "area_level": "municipality",
                             "work_status": "closed", "decision_status": "closure_confirmed",
                             "target_date": TARGET_DAILY, "closure_scope": scope}
        elif not any(word in row for word in ("照常上班", "照常辦公", "未停止")):
            raise ValueError("dgpa_daily_taipei_status_unresolved")
    return {"target_date": TARGET_DAILY, "heading": heading,
            "status_kind": "explicit_no_notice" if no_notice else "county_rows_present",
            "taipei_rows": taipei, "source_attribution_present": "行政院人事行政總處" in visible or "人事行政總處" in visible,
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
