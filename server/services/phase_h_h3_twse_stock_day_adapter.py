"""Dormant bounded adapter for the official TWSE STOCK_DAY HTML report.

One invocation requests one exact TWSE target and one explicit report month.
The adapter retains only normalized observations and bounded response
metadata; it does not persist or cache source HTML.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from email.message import Message
from hashlib import sha256
from html.parser import HTMLParser
import math
import re
import ssl
from typing import Callable, Literal, Mapping, Protocol
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener

from scripts.ssl_policy import (
    SSL_POLICY_COMPATIBILITY,
    SSL_POLICY_STRICT,
    SSL_POLICY_UNSAFE,
    build_ssl_context,
    validate_ssl_policy,
)
from scripts.twse_trading_calendar import parse_twse_roc_date


SOURCE_FAMILY = "TWSE_STOCK_DAY_OFFICIAL_WEB"
SOURCE_CONTRACT_ID = "TWSE_STOCK_DAY_HTML_MONTHLY_V1"
ENDPOINT = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
EXPECTED_HEADERS = (
    "日期", "成交股數", "成交金額", "開盤價", "最高價", "最低價", "收盤價",
    "漲跌價差", "成交筆數", "註記",
)
_REPORT_TITLE = re.compile(
    r"(?P<roc_year>\d{3})\s*年\s*(?P<month>\d{1,2})\s*月\s*"
    r"(?P<code>[0-9]{1,6})\s+(?P<name>.+?)\s*各日成交資訊"
)
_ROC_ROW_DATE = re.compile(r"(?P<year>\d{3})/(?P<month>\d{2})/(?P<day>\d{2})")
_VOLUME = re.compile(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)")
_CLOSE = re.compile(r"[0-9]+(?:\.[0-9]+)?")


class TWSEStockDayFormatError(ValueError):
    """Deterministic source-contract or target-binding rejection."""


@dataclass(frozen=True)
class TWSEStockDayResult:
    status: Literal["available", "no_evidence_in_covered_scope", "source_failed", "binding_failed"]
    source_contract_id: str = SOURCE_CONTRACT_ID
    requested_month: str | None = None
    requested_url: str | None = None
    effective_url: str | None = None
    http_status: int | None = None
    content_type: str | None = None
    retrieved_at: str | None = None
    response_byte_count: int = 0
    response_sha256: str | None = None
    observations: tuple[dict, ...] = ()
    unusable_observation_count: int = 0
    unusable_observations: tuple[dict[str, str], ...] = ()
    error_code: str | None = None


class _Response(Protocol):
    status: int
    headers: Mapping[str, str]

    def read(self, size: int = -1) -> bytes: ...
    def close(self) -> None: ...


HTTPGet = Callable[[Request, float], _Response]


class _NoRedirectHandler(HTTPRedirectHandler):
    """Do not follow unexpected provider redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _default_http_get(
    request: Request,
    timeout_seconds: float,
    *,
    ssl_context: ssl.SSLContext | None = None,
) -> _Response:
    handlers = [_NoRedirectHandler()]
    if ssl_context is not None:
        handlers.append(HTTPSHandler(context=ssl_context))
    opener = build_opener(*handlers)
    try:
        return opener.open(request, timeout=timeout_seconds)  # type: ignore[return-value]
    except HTTPError as response:
        # HTTPError carries the response, but the caller will reject its status.
        return response  # type: ignore[return-value]


def _fail(status: str, code: str, **metadata) -> TWSEStockDayResult:  # noqa: ANN003
    return TWSEStockDayResult(status=status, error_code=code, **metadata)


def _target_identity(
    target: Mapping[str, str], instrument_family: str, instrument_type: str
) -> tuple[str, str, str]:
    if not isinstance(target, Mapping) or set(target) != {
        "canonical_target_id", "market", "security_code"
    }:
        raise TWSEStockDayFormatError("binding_failed:invalid_target")
    canonical = target.get("canonical_target_id")
    market = target.get("market")
    code = target.get("security_code")
    if not all(isinstance(value, str) and value.strip() for value in (canonical, market, code)):
        raise TWSEStockDayFormatError("binding_failed:invalid_target")
    if market != "TWSE":
        raise TWSEStockDayFormatError("binding_failed:wrong_market")
    if canonical != f"TWSE:{code}":
        raise TWSEStockDayFormatError("binding_failed:target_identity_mismatch")
    if not (code.isascii() and code.isdigit() and 1 <= len(code) <= 6):
        raise TWSEStockDayFormatError("binding_failed:invalid_security_code")
    if instrument_family != "company_share" or instrument_type != "common_share":
        raise TWSEStockDayFormatError("binding_failed:unsupported_instrument_scope")
    return canonical, market, code


def _normalize_month(value: str) -> tuple[str, str]:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}", value):
        raise TWSEStockDayFormatError("source_failed:invalid_requested_month")
    year, month = (int(part) for part in value.split("-"))
    if year < 1912 or not 1 <= month <= 12:
        raise TWSEStockDayFormatError("source_failed:invalid_requested_month")
    return value, f"{year:04d}{month:02d}01"


def _validate_timestamp(value: str) -> None:
    if not isinstance(value, str):
        raise TWSEStockDayFormatError("source_failed:invalid_retrieved_at")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TWSEStockDayFormatError("source_failed:invalid_retrieved_at") from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise TWSEStockDayFormatError("source_failed:retrieved_at_timezone_required")


def _validate_bounds(timeout_seconds: float, max_response_bytes: int) -> None:
    try:
        timeout_is_finite = math.isfinite(timeout_seconds)
    except (OverflowError, TypeError):
        timeout_is_finite = False
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not timeout_is_finite
        or timeout_seconds <= 0
    ):
        raise TWSEStockDayFormatError("source_failed:invalid_timeout")
    if (
        isinstance(max_response_bytes, bool)
        or not isinstance(max_response_bytes, int)
        or max_response_bytes <= 0
    ):
        raise TWSEStockDayFormatError("source_failed:invalid_response_limit")


def _content_type(response: _Response) -> str | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    getter = getattr(headers, "get", None)
    value = getter("Content-Type") if getter else None
    return value if isinstance(value, str) else None


def _html_charset(content_type: str | None) -> str | None:
    if not content_type:
        return None
    try:
        header = Message()
        header["Content-Type"] = content_type
        if header.get_content_type().casefold() not in {"text/html", "application/xhtml+xml"}:
            return None
        return header.get_content_charset()
    except (TypeError, ValueError):
        return None


def _cell_text(value: str) -> str:
    value = value.replace("\u00a0", " ").replace("\u3000", " ")
    return " ".join(value.split())


class _ReportHTMLParser(HTMLParser):
    """Collect table rows structurally for same-table report binding."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table_depth = 0
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        if tag == "table":
            if self._table_depth == 0:
                self._current_table = []
            self._table_depth += 1
            return
        if self._table_depth == 1:
            if tag == "tr":
                self._current_row = []
            elif tag in {"td", "th"} and self._current_row is not None:
                self._current_cell = []
            elif tag == "br" and self._current_cell is not None:
                self._current_cell.append(" ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if self._table_depth == 1:
            if tag in {"td", "th"} and self._current_cell is not None:
                assert self._current_row is not None
                self._current_row.append("".join(self._current_cell))
                self._current_cell = None
            elif tag == "tr" and self._current_row is not None:
                assert self._current_table is not None
                self._current_table.append(self._current_row)
                self._current_row = None
        if tag == "table" and self._table_depth:
            self._table_depth -= 1
            if self._table_depth == 0:
                if self._current_table is not None:
                    self.tables.append(self._current_table)
                self._current_table = None

    def handle_data(self, data: str) -> None:
        if self._table_depth == 1 and self._current_cell is not None:
            self._current_cell.append(data)


def _normalize_header_label(value: str) -> str:
    """Remove display whitespace only when comparing semantic header labels."""
    return "".join(value.split())


def _normalize_title_text(value: str) -> str:
    """Collapse Unicode presentation whitespace without fuzzy title matching."""
    return _cell_text(value)


def _row_data_cells(row: list[str]) -> tuple[str, ...]:
    """Trim cell-edge layout whitespace while preserving internal data text."""
    return tuple(value.strip() for value in row)


def _parse_roc_date(value: str) -> str:
    match = _ROC_ROW_DATE.fullmatch(value)
    if match is None:
        raise TWSEStockDayFormatError("source_failed:invalid_row_date")
    try:
        return parse_twse_roc_date("".join(match.groups())).isoformat()
    except (TypeError, ValueError) as exc:
        raise TWSEStockDayFormatError("source_failed:invalid_row_date") from exc


def _parse_volume(value: str) -> int:
    if not _VOLUME.fullmatch(value):
        raise TWSEStockDayFormatError("source_failed:invalid_volume")
    return int(value.replace(",", ""))


def _parse_close(value: str) -> float:
    if not _CLOSE.fullmatch(value):
        raise TWSEStockDayFormatError("source_failed:invalid_close")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise TWSEStockDayFormatError("source_failed:invalid_close") from exc
    if not amount.is_finite() or amount < 0:
        raise TWSEStockDayFormatError("source_failed:invalid_close")
    try:
        result = float(amount)
    except OverflowError as exc:
        raise TWSEStockDayFormatError("source_failed:invalid_close") from exc
    if not math.isfinite(result):
        raise TWSEStockDayFormatError("source_failed:invalid_close")
    return result


def _normalize_html(
    payload: bytes,
    *,
    content_type: str | None,
    target: Mapping[str, str],
    instrument_family: str,
    instrument_type: str,
    requested_month: str,
    retrieved_at: str,
    requested_url: str,
    effective_url: str,
    http_status: int,
) -> TWSEStockDayResult:
    metadata = {
        "requested_month": requested_month,
        "requested_url": requested_url,
        "effective_url": effective_url,
        "http_status": http_status,
        "content_type": content_type,
        "retrieved_at": retrieved_at,
        "response_byte_count": len(payload),
        "response_sha256": sha256(payload).hexdigest(),
    }
    try:
        canonical, market, code = _target_identity(target, instrument_family, instrument_type)
    except TWSEStockDayFormatError as exc:
        return _fail("binding_failed", str(exc), **metadata)
    charset = _html_charset(content_type)
    if charset is None:
        return _fail("source_failed", "source_failed:invalid_html_content_type_or_charset", **metadata)
    try:
        html = payload.decode(charset)
    except (LookupError, UnicodeDecodeError):
        return _fail("source_failed", "source_failed:html_decode_failed", **metadata)

    parser = _ReportHTMLParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return _fail("source_failed", "source_failed:malformed_html", **metadata)

    report_tables: list[tuple[list[list[str]], int, re.Match[str]]] = []
    header_without_title = False
    ambiguous_title = False
    for candidate_table in parser.tables:
        header_indices = [
            index for index, row in enumerate(candidate_table)
            if len(row) == len(EXPECTED_HEADERS)
            and tuple(_normalize_header_label(cell) for cell in row) == EXPECTED_HEADERS
        ]
        for header_index in header_indices:
            title_matches = [
                match
                for row in candidate_table[:header_index]
                if len(row) == 1
                for match in [_REPORT_TITLE.fullmatch(_normalize_title_text(row[0]))]
                if match is not None
            ]
            if len(title_matches) == 1:
                report_tables.append((candidate_table, header_index, title_matches[0]))
            elif len(title_matches) > 1:
                ambiguous_title = True
            else:
                header_without_title = True

    if ambiguous_title:
        return _fail("source_failed", "source_failed:ambiguous_report_heading", **metadata)
    if not report_tables:
        if header_without_title:
            return _fail("source_failed", "source_failed:report_heading_missing", **metadata)
        return _fail("source_failed", "source_failed:report_table_contract_missing", **metadata)
    if len(report_tables) != 1:
        return _fail("source_failed", "source_failed:ambiguous_report_table_contract", **metadata)

    table, header_index, title = report_tables[0]
    roc_year = int(title.group("roc_year"))
    title_month = int(title.group("month"))
    title_code = title.group("code")
    requested_year, requested_month_number = (int(part) for part in requested_month.split("-"))
    if (
        title_code != code
        or roc_year + 1911 != requested_year
        or title_month != requested_month_number
    ):
        return _fail("binding_failed", "binding_failed:report_heading_target_or_month_mismatch", **metadata)

    by_date: dict[str, tuple[tuple[str, ...], dict | None, dict[str, str] | None]] = {}
    try:
        for source_row in table[header_index + 1 :]:
            row = _row_data_cells(source_row)
            if len(row) != len(EXPECTED_HEADERS):
                raise TWSEStockDayFormatError("source_failed:invalid_data_row_width")
            trade_date = _parse_roc_date(row[0])
            if trade_date[:7] != requested_month:
                raise TWSEStockDayFormatError("source_failed:row_outside_requested_month")
            volume = _parse_volume(row[1])
            signature = tuple(row)
            if row[6] == "--":
                observation = None
                unusable = {"trade_date": trade_date, "reason": "close_unavailable"}
            else:
                close = _parse_close(row[6])
                observation = {
                    "canonical_target_id": canonical,
                    "market": market,
                    "security_code": code,
                    "trade_date": trade_date,
                    "close": close,
                    "volume": volume,
                    "source_family": SOURCE_FAMILY,
                    "source_contract_id": SOURCE_CONTRACT_ID,
                    "retrieved_at": retrieved_at,
                    "citation_ids": [],
                }
                unusable = None
            previous = by_date.get(trade_date)
            if previous is not None and previous[0] != signature:
                raise TWSEStockDayFormatError("source_failed:conflicting_duplicate_trade_date")
            by_date.setdefault(trade_date, (signature, observation, unusable))
    except TWSEStockDayFormatError as exc:
        status = "binding_failed" if str(exc).startswith("binding_failed:") else "source_failed"
        return _fail(status, str(exc), **metadata)

    citation = (
        f"{SOURCE_FAMILY}|url={requested_url}|month={requested_month}|"
        f"retrieved_at={retrieved_at}|sha256={metadata['response_sha256']}"
    )
    observations = []
    unusable_observations = []
    for trade_date in sorted(by_date):
        _, observation, unusable = by_date[trade_date]
        if unusable is not None:
            unusable_observations.append(unusable)
            continue
        assert observation is not None
        observation["citation_ids"] = [citation]
        observations.append(observation)
    status = "available" if observations else "no_evidence_in_covered_scope"
    return TWSEStockDayResult(
        status=status,
        observations=tuple(observations),
        unusable_observation_count=len(unusable_observations),
        unusable_observations=tuple(unusable_observations),
        **metadata,
    )


def fetch_twse_stock_day_month(
    *,
    target: Mapping[str, str],
    instrument_family: str,
    instrument_type: str,
    requested_month: str,
    retrieved_at: str,
    timeout_seconds: float,
    max_response_bytes: int,
    http_get: HTTPGet | None = None,
    ssl_policy: str = SSL_POLICY_STRICT,
) -> TWSEStockDayResult:
    """Fetch and normalize one bounded HTML month for one exact TWSE target."""
    try:
        selected_ssl_policy = validate_ssl_policy(ssl_policy)
    except (AttributeError, ValueError):
        return _fail(
            "source_failed", "source_failed:invalid_ssl_policy",
            requested_month=requested_month if isinstance(requested_month, str) else None,
        )
    if selected_ssl_policy == SSL_POLICY_UNSAFE:
        return _fail(
            "source_failed", "source_failed:unsafe_ssl_policy_not_allowed",
            requested_month=requested_month if isinstance(requested_month, str) else None,
        )
    if selected_ssl_policy not in {SSL_POLICY_STRICT, SSL_POLICY_COMPATIBILITY}:
        return _fail(
            "source_failed", "source_failed:invalid_ssl_policy",
            requested_month=requested_month if isinstance(requested_month, str) else None,
        )

    try:
        canonical, market, code = _target_identity(target, instrument_family, instrument_type)
        month, date_parameter = _normalize_month(requested_month)
        _validate_timestamp(retrieved_at)
        _validate_bounds(timeout_seconds, max_response_bytes)
    except TWSEStockDayFormatError as exc:
        status = "binding_failed" if str(exc).startswith("binding_failed:") else "source_failed"
        return _fail(status, str(exc), requested_month=requested_month if isinstance(requested_month, str) else None)

    query = urlencode((
        ("response", "html"),
        ("date", date_parameter),
        ("stockNo", code),
    ))
    requested_url = f"{ENDPOINT}?{query}"
    request = Request(requested_url, headers={"User-Agent": "TW-Market official evidence client"}, method="GET")
    try:
        if http_get is None:
            ssl_context = build_ssl_context(selected_ssl_policy)
            if selected_ssl_policy == SSL_POLICY_COMPATIBILITY:
                if (
                    not isinstance(ssl_context, ssl.SSLContext)
                    or ssl_context.verify_mode != ssl.CERT_REQUIRED
                    or not ssl_context.check_hostname
                ):
                    return _fail(
                        "source_failed", "source_failed:verified_ssl_context_unavailable",
                        requested_month=month, requested_url=requested_url,
                        retrieved_at=retrieved_at,
                    )
            response = _default_http_get(
                request, float(timeout_seconds), ssl_context=ssl_context
            )
        else:
            response = http_get(request, float(timeout_seconds))
    except Exception:
        return _fail(
            "source_failed", "source_failed:transport_failure", requested_month=month,
            requested_url=requested_url, retrieved_at=retrieved_at,
        )

    try:
        status = getattr(response, "status", getattr(response, "code", None))
        content_type = _content_type(response)
        geturl = getattr(response, "geturl", None)
        effective_url = geturl() if callable(geturl) else requested_url
        body = response.read(max_response_bytes + 1)
    except Exception:
        return _fail(
            "source_failed", "source_failed:transport_failure", requested_month=month,
            requested_url=requested_url, retrieved_at=retrieved_at,
        )
    finally:
        try:
            response.close()
        except Exception:
            pass

    if not isinstance(body, bytes):
        return _fail(
            "source_failed", "source_failed:invalid_response_body", requested_month=month,
            requested_url=requested_url, http_status=status if isinstance(status, int) else None,
            retrieved_at=retrieved_at,
        )
    if len(body) > max_response_bytes:
        return _fail(
            "source_failed", "source_failed:response_too_large", requested_month=month,
            requested_url=requested_url, http_status=status if isinstance(status, int) else None,
            retrieved_at=retrieved_at, response_byte_count=len(body),
        )
    if not isinstance(status, int) or not 200 <= status < 300:
        return _fail(
            "source_failed", "source_failed:http_status_unaccepted", requested_month=month,
            requested_url=requested_url, http_status=status if isinstance(status, int) else None,
            retrieved_at=retrieved_at, response_byte_count=len(body),
        )
    return _normalize_html(
        body,
        content_type=content_type,
        target={"canonical_target_id": canonical, "market": market, "security_code": code},
        instrument_family=instrument_family,
        instrument_type=instrument_type,
        requested_month=month,
        retrieved_at=retrieved_at,
        requested_url=requested_url,
        effective_url=effective_url,
        http_status=status,
    )
