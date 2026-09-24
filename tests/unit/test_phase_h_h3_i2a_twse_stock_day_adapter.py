"""Synthetic, fixture-only contract tests for the dormant TWSE STOCK_DAY adapter."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from server.services.phase_h_h3_twse_stock_day_adapter import (
    SOURCE_CONTRACT_ID,
    SOURCE_FAMILY,
    fetch_twse_stock_day_month,
)
from server.services.phase_h_recent_performance import build_recent_performance_evidence


ROOT = Path(__file__).resolve().parents[2]
TARGET = {"canonical_target_id": "TWSE:1423", "market": "TWSE", "security_code": "1423"}
RETRIEVED = "2026-09-24T10:15:00+08:00"
TIMEOUT = 4.0
MAX_BYTES = 16_384
HEADERS = "<tr>" + "".join(f"<th>{value}</th>" for value in (
    "日期", "成交股數", "成交金額", "開盤價", "最高價", "最低價", "收盤價", "漲跌價差", "成交筆數", "註記"
)) + "</tr>"


def _row(date: str, volume: str = "240,011", close: str = "15.80", *, note: str = "") -> str:
    return "<tr>" + "".join(f"<td>{value}</td>" for value in (
        date, volume, "3,792,173", "15.70", "16.00", "15.60", close, "0.10", "412", note
    )) + "</tr>"


def _html(*rows: str, title: str = "110年02月 1423 利華 各日成交資訊", include_table: bool = True) -> bytes:
    table = f"<table><thead>{HEADERS}</thead><tbody>{''.join(rows)}</tbody></table>" if include_table else ""
    # A non-report table precedes the report to prove semantic table selection.
    return (
        "<!doctype html><html><head><meta charset='utf-8'></head><body>"
        f"<table><tr><td>navigation</td></tr></table><h2>{title}</h2>{table}</body></html>"
    ).encode("utf-8")


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "text/html; charset=utf-8"):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.read_sizes: list[int] = []
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        return self.body if size < 0 else self.body[:size]

    def close(self) -> None:
        self.closed = True


class FakeHTTPGet:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls = []

    def __call__(self, request, timeout_seconds: float) -> FakeResponse:
        self.calls.append((request, timeout_seconds))
        return self.response


def _fetch(fake, **overrides):
    args = {
        "target": TARGET,
        "instrument_family": "company_share",
        "instrument_type": "common_share",
        "requested_month": "2021-02",
        "retrieved_at": RETRIEVED,
        "timeout_seconds": TIMEOUT,
        "max_response_bytes": MAX_BYTES,
        "http_get": fake,
    }
    args.update(overrides)
    return fetch_twse_stock_day_month(**args)


def test_exact_one_get_for_exact_target_and_month_with_timeout_and_byte_bound() -> None:
    response = FakeResponse(_html(_row("110/02/02")))
    fake = FakeHTTPGet(response)
    result = _fetch(fake)

    assert result.status == "available"
    assert result.requested_month == "2021-02"
    assert result.source_contract_id == SOURCE_CONTRACT_ID
    assert result.response_sha256 == sha256(response.body).hexdigest()
    assert result.response_byte_count == len(response.body)
    assert len(fake.calls) == 1
    request, timeout = fake.calls[0]
    assert request.method == "GET"
    assert urlsplit(request.full_url).scheme == "https"
    assert urlsplit(request.full_url).path == "/exchangeReport/STOCK_DAY"
    assert urlsplit(request.full_url).netloc == "www.twse.com.tw"
    assert parse_qs(urlsplit(request.full_url).query) == {
        "response": ["html"], "date": ["20210201"], "stockNo": ["1423"]
    }
    assert timeout == TIMEOUT
    assert response.read_sizes == [MAX_BYTES + 1]
    assert response.closed


def test_observation_normalization_roc_dates_volume_close_order_and_citation() -> None:
    result = _fetch(FakeHTTPGet(FakeResponse(_html(
        _row("110/02/03", "303,806", "16.45"),
        _row("110/02/01", "240,011", "15.80"),
    ))))
    assert result.status == "available"
    assert [item["trade_date"] for item in result.observations] == ["2021-02-01", "2021-02-03"]
    assert [item["volume"] for item in result.observations] == [240011, 303806]
    assert [item["close"] for item in result.observations] == [15.8, 16.45]
    assert all(item["source_family"] == SOURCE_FAMILY for item in result.observations)
    assert all(item["source_contract_id"] == SOURCE_CONTRACT_ID for item in result.observations)
    assert result.observations[0]["citation_ids"] == [
        f"{SOURCE_FAMILY}|url={result.requested_url}|month=2021-02|retrieved_at={RETRIEVED}|sha256={result.response_sha256}"
    ]


@pytest.mark.parametrize(
    ("target", "family", "kind"),
    [
        ({"canonical_target_id": "TPEX:1423", "market": "TPEX", "security_code": "1423"}, "company_share", "common_share"),
        (TARGET, "fund", "etf"),
    ],
)
def test_wrong_market_or_instrument_scope_rejected_before_network(target, family, kind) -> None:
    fake = FakeHTTPGet(FakeResponse(_html(_row("110/02/01"))))
    result = _fetch(fake, target=target, instrument_family=family, instrument_type=kind)
    assert result.status == "binding_failed"
    assert fake.calls == []


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("110年02月 2330 台積電 各日成交資訊", "binding_failed:report_heading_target_or_month_mismatch"),
        ("110年03月 1423 利華 各日成交資訊", "binding_failed:report_heading_target_or_month_mismatch"),
        ("110年02月 14230 利華 各日成交資訊", "binding_failed:report_heading_target_or_month_mismatch"),
    ],
)
def test_heading_must_bind_exact_code_and_requested_month(title: str, expected: str) -> None:
    result = _fetch(FakeHTTPGet(FakeResponse(_html(_row("110/02/01"), title=title))))
    assert result.status == "binding_failed"
    assert result.error_code == expected
    assert result.observations == ()


def test_report_table_is_selected_by_complete_semantic_header() -> None:
    html = _html(_row("110/02/01")).decode("utf-8")
    html = html.replace("<th>收盤價</th>", "<th>收盤</th>")
    result = _fetch(FakeHTTPGet(FakeResponse(html.encode("utf-8"))))
    assert result.status == "source_failed"
    assert result.error_code == "source_failed:report_table_contract_missing"


@pytest.mark.parametrize(
    ("row", "code"),
    [
        (_row("110/03/01"), "source_failed:row_outside_requested_month"),
        (_row("110/02/xx"), "source_failed:invalid_row_date"),
        (_row("110/02/01", "24x,011"), "source_failed:invalid_volume"),
        (_row("110/02/01", "240,011", "ABC"), "source_failed:invalid_close"),
        (_row("110/02/01", "240,011", "9" * 400), "source_failed:invalid_close"),
        ("<tr><td>110/02/01</td><td>1</td></tr>", "source_failed:invalid_data_row_width"),
    ],
)
def test_malformed_or_out_of_month_data_fails_closed(row: str, code: str) -> None:
    result = _fetch(FakeHTTPGet(FakeResponse(_html(row))))
    assert result.status == "source_failed"
    assert result.error_code == code


def test_identical_duplicate_row_is_deduplicated_but_conflict_fails_closed() -> None:
    row = _row("110/02/01")
    identical = _fetch(FakeHTTPGet(FakeResponse(_html(row, row))))
    assert identical.status == "available"
    assert len(identical.observations) == 1

    conflicting = _fetch(FakeHTTPGet(FakeResponse(_html(row, _row("110/02/01", close="15.81")))))
    assert conflicting.status == "source_failed"
    assert conflicting.error_code == "source_failed:conflicting_duplicate_trade_date"


def test_verified_unavailable_close_is_excluded_with_source_provenance_in_mixed_month() -> None:
    result = _fetch(FakeHTTPGet(FakeResponse(_html(
        _row("114/02/03", "120", "36.80"),
        _row("114/02/04", "90", "36.40"),
        _row("114/02/05", "75", "37.30"),
        _row("114/02/06", "49", "--"),
        _row("114/02/07", "63", "36.95"),
        title="114年02月 1423 利華 各日成交資訊",
    ))), requested_month="2025-02")

    assert result.status == "available"
    assert [row["trade_date"] for row in result.observations] == [
        "2025-02-03", "2025-02-04", "2025-02-05", "2025-02-07"
    ]
    assert [row["close"] for row in result.observations] == [36.8, 36.4, 37.3, 36.95]
    assert result.unusable_observation_count == 1
    assert result.unusable_observations == ({
        "trade_date": "2025-02-06", "reason": "close_unavailable"
    },)


def test_month_with_only_verified_unavailable_closes_is_no_usable_h3_evidence() -> None:
    result = _fetch(FakeHTTPGet(FakeResponse(_html(
        _row("114/02/06", "49", "--"),
        _row("114/02/07", "63", "--"),
        title="114年02月 1423 利華 各日成交資訊",
    ))), requested_month="2025-02")

    assert result.status == "no_evidence_in_covered_scope"
    assert result.observations == ()
    assert result.unusable_observation_count == 2
    assert result.unusable_observations == (
        {"trade_date": "2025-02-06", "reason": "close_unavailable"},
        {"trade_date": "2025-02-07", "reason": "close_unavailable"},
    )


def test_valid_bound_empty_table_is_no_evidence_but_missing_table_is_source_failure() -> None:
    empty = _fetch(FakeHTTPGet(FakeResponse(_html())))
    assert empty.status == "no_evidence_in_covered_scope"
    assert empty.observations == ()

    missing = _fetch(FakeHTTPGet(FakeResponse(_html(include_table=False))))
    assert missing.status == "source_failed"
    assert missing.error_code == "source_failed:report_table_contract_missing"


@pytest.mark.parametrize(
    ("status", "content_type", "body", "code"),
    [
        (403, "text/html; charset=utf-8", b"blocked", "source_failed:http_status_unaccepted"),
        (200, "text/html; charset=utf-8", b"<html><body>captcha challenge</body></html>", "source_failed:report_heading_missing"),
        (200, "application/json", b"{}", "source_failed:invalid_html_content_type_or_charset"),
        (200, "text/html; charset=utf-8", b"\xff", "source_failed:html_decode_failed"),
    ],
)
def test_http_provider_challenge_or_non_html_response_fails_closed(status, content_type, body, code) -> None:
    result = _fetch(FakeHTTPGet(FakeResponse(body, status=status, content_type=content_type)))
    assert result.status == "source_failed"
    assert result.error_code == code


def test_network_failure_and_oversized_response_fail_without_retry() -> None:
    calls = []

    def failing(request, timeout_seconds):
        calls.append((request, timeout_seconds))
        raise RuntimeError("network fixture failure")

    failed = _fetch(failing)
    assert failed.status == "source_failed"
    assert failed.error_code == "source_failed:transport_failure"
    assert len(calls) == 1

    response = FakeResponse(b"x" * (MAX_BYTES + 10))
    oversized = _fetch(FakeHTTPGet(response))
    assert oversized.status == "source_failed"
    assert oversized.error_code == "source_failed:response_too_large"
    assert response.read_sizes == [MAX_BYTES + 1]


def test_invalid_timeout_and_response_limit_are_rejected_before_dispatch() -> None:
    fake = FakeHTTPGet(FakeResponse(_html(_row("110/02/01"))))
    for overrides, error_code in (
        ({"timeout_seconds": 10**10000}, "source_failed:invalid_timeout"),
        ({"max_response_bytes": 0}, "source_failed:invalid_response_limit"),
    ):
        result = _fetch(fake, **overrides)
        assert result.status == "source_failed"
        assert result.error_code == error_code
    assert fake.calls == []


def test_response_without_report_heading_or_ambiguous_contract_fails_closed() -> None:
    no_heading = _html(_row("110/02/01"), title="個股日成交資訊")
    result = _fetch(FakeHTTPGet(FakeResponse(no_heading)))
    assert result.status == "source_failed"
    assert result.error_code == "source_failed:report_heading_missing"

    repeated_heading = _html(_row("110/02/01"), title="110年02月 1423 利華 各日成交資訊 110年02月 1423 利華 各日成交資訊")
    result = _fetch(FakeHTTPGet(FakeResponse(repeated_heading)))
    assert result.status == "source_failed"
    assert result.error_code == "source_failed:ambiguous_report_heading"


def test_no_raw_monthly_payload_is_persisted_and_h3_i0_consumes_observations(tmp_path: Path) -> None:
    body = _html(
        _row("110/02/02", "303,806", "16.45"),
        _row("110/02/01", "240,011", "15.80"),
    )
    result = _fetch(FakeHTTPGet(FakeResponse(body)))
    assert list(tmp_path.iterdir()) == []

    evidence = build_recent_performance_evidence(
        target=TARGET,
        observations=[result.observations[0]],
        governed_end_observation=result.observations[1],
        requested_observations=1,
        baseline_lookbacks=[1],
        current_volume_basis="completed_session",
        schema=json.loads((ROOT / "schemas/recent_performance_evidence.v1.schema.json").read_text(encoding="utf-8")),
    )
    assert evidence["coverage_status"] == "complete"
    assert evidence["baselines"][0]["start_observation_date"] == "2021-02-01"
    assert evidence["baselines"][0]["end_observation_date"] == "2021-02-02"
    assert evidence["observations"][0]["source_family"] == SOURCE_FAMILY
