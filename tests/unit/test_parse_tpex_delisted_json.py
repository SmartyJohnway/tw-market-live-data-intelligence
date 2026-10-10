"""Network-free tests for the qualified TPEx all-history JSON contract."""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills/tw-security-master-classifier/scripts"))
from lifecycle_common import LifecycleSchemaDrift  # noqa: E402
from parse_tpex_delisted import API_URL, LANDING_URL, parse  # noqa: E402


FIELDS = ["股票代號", "公司名稱", "終止上櫃日期", "終止上櫃原因", "公司資料網址"]


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*_args, **_kwargs):
        pytest.fail("TPEx lifecycle parser attempted network access")
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)


def payload(rows, *, total=None, stat="ok", date="ALL", fields=None):
    data = {
        "tables": [{
            "fields": FIELDS if fields is None else fields,
            "data": rows,
            "totalCount": len(rows) if total is None else total,
            "title": "公司終止上櫃",
            "notes": [],
        }],
        "date": date,
        "stat": stat,
    }
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def row(code="1234", company="測試公司", date="115-10-01", reason="終止上櫃"):
    return [code, company, date, reason, "https://www.tpex.org.tw/company/1234"]


def test_complete_all_response_maps_fields_and_roc_date():
    events = parse(payload([row(), row("5678", "另一公司", "001/01/02", "")]), API_URL)
    assert len(events) == 2
    first, second = events
    assert first["security_code"] == "1234"
    assert first["security_name_zh"] == "測試公司"
    assert first["effective_date"] == "2026-10-01"
    assert first["date_raw"] == "115-10-01"
    assert first["calendar"] == "ROC"
    assert first["reason_code"] == "終止上櫃"
    assert second["effective_date"] == "1912-01-02"
    assert second["reason_raw"] == ""
    assert "reason_code" not in second
    assert first["source_url"] == API_URL


def test_valid_empty_all_response_is_not_schema_drift():
    assert parse(payload([], total=0), API_URL) == []


@pytest.mark.parametrize("data,issue", [
    (b"not-json", "tpex_api_invalid_json"),
    ('{"stat":"參數輸入錯誤"}'.encode("utf-8"), "tpex_api_application_error"),
    (payload([row()], total=2), "tpex_api_incomplete_all_response"),
    (payload([], total=1001), "tpex_api_count_or_data_type_drift"),
    (payload([row(), row()], total=2), "tpex_api_duplicate_lifecycle_identity"),
    (payload([row(date="2026-10-01")]), "tpex_api_invalid_roc_date"),
    (payload([row(date="115-02-30")]), "tpex_api_invalid_roc_date"),
    (payload([["1234", "", "115-10-01", "", ""]]), "tpex_api_required_field_missing"),
    (payload([["1234", "公司", "115-10-01", "原因"]]), "tpex_api_row_width_drift"),
    (payload([row()], fields=FIELDS[:-1]), "tpex_api_table_schema_drift"),
    (payload([row()], date="2026"), "tpex_api_not_all_history"),
])
def test_contract_drift_fails_closed(data, issue):
    with pytest.raises(LifecycleSchemaDrift) as caught:
        parse(data, API_URL)
    assert caught.value.issue_code == issue


def test_landing_shell_is_not_a_valid_empty_dataset():
    with pytest.raises(LifecycleSchemaDrift, match="no_html_tables"):
        parse(b"<html><script>tables.init({action:'company/deListed'})</script></html>", LANDING_URL)


def test_legacy_governed_html_fixture_remains_supported():
    fixture = ROOT / "skills/tw-security-master-classifier/references/fixtures/tpex_delisted_excerpt.html"
    events = parse(fixture.read_bytes(), LANDING_URL)
    assert len(events) == 1
    assert events[0]["effective_date"] == "2026-06-01"


def test_unrecognized_url_is_not_assumed_to_be_a_source():
    with pytest.raises(LifecycleSchemaDrift, match="tpex_source_url_not_governed"):
        parse(payload([row()]), "https://www.tpex.org.tw/guessed")
