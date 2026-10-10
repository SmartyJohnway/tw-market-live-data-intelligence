from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills/tw-security-master-classifier/scripts"))
from lifecycle_common import LifecycleSchemaDrift  # noqa: E402
from parse_etn_termination import parse_twse_expired_json  # noqa: E402


FIELDS = ["終止上市日期", "證券代號", "證券簡稱", "發行證券商", "終止上市理由"]
URL = "https://www.twse.com.tw/rwd/zh/ETN/expireEnd?response=json"


def row(index: int) -> list[str]:
    return [f"2026/05/{index:02d}", f"0200{index:02d}", f"ETN {index}", "Example Issuer", "Maturity"]


def payload(rows: list[list[str]] | None = None) -> dict:
    return {"stat": "ok", "title": "到期或終止上市資訊", "data": [row(i) for i in range(1, 14)] if rows is None else rows, "fields": FIELDS.copy()}


def encoded(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def test_qualified_thirteen_row_response_maps_to_schema_valid_events():
    events = parse_twse_expired_json(encoded(payload()), URL)
    assert len(events) == 13
    first = events[0]
    assert first["security_code"] == "020001"
    assert first["security_name_zh"] == "ETN 1"
    assert first["issuer_name"] == "Example Issuer"
    assert first["effective_date"] == "2026-05-01"
    assert first["date_raw"] == "2026/05/01"
    assert first["calendar"] == "Gregorian"
    assert first["event_type"] == "twse_delisted"
    assert first["evidence_status"] == "official_explicit"
    assert first["reason_code"] == "Maturity"
    assert "maturity_date" not in first and "last_trading_date" not in first
    assert all(event["source_url"] == URL for event in events)
    assert len({(e["security_code"], e["effective_date"], e["event_type"]) for e in events}) == 13


def test_exact_schema_empty_data_is_a_valid_empty_result():
    assert parse_twse_expired_json(encoded(payload([])), URL) == []


@pytest.mark.parametrize(
    ("body", "issue"),
    [
        (b"not-json", "twse_etn_json_malformed_json"),
        (encoded({"stat": "ok", "data": [], "fields": FIELDS}), "twse_etn_json_root_drift"),
        (encoded({**payload([]), "stat": "error"}), "twse_etn_json_non_ok_stat"),
        (encoded({**payload([]), "fields": list(reversed(FIELDS))}), "twse_etn_json_fields_drift"),
        (encoded({**payload([]), "data": [["2026/05/01", "020001"]]}), "twse_etn_json_row_width_drift"),
        (encoded({**payload([]), "data": [["2026/05/01", 20001, "n", "i", "r"]]}), "twse_etn_json_row_value_type_drift"),
        (encoded({**payload([]), "data": [["2026/05/01", "", "n", "i", "r"]]}), "twse_etn_json_missing_security_code"),
        (encoded({**payload([]), "data": [["2026/05/01", "020001", "", "i", "r"]]}), "twse_etn_json_missing_security_name"),
        (encoded({**payload([]), "data": [["2026/02/30", "020001", "n", "i", "r"]]}), "twse_etn_json_invalid_date"),
        (encoded({**payload([]), "data": [["115-05-01", "020001", "n", "i", "r"]]}), "twse_etn_json_date_shape_drift"),
        (encoded({**payload([]), "data": [row(1), row(1)]}), "twse_etn_json_duplicate_lifecycle_identity"),
        (b"<html><form id='form' data-api='/ETN/expireEnd'></form></html>", "twse_etn_json_malformed_json"),
    ],
)
def test_contract_drift_fails_closed(body: bytes, issue: str):
    with pytest.raises(LifecycleSchemaDrift) as exc:
        parse_twse_expired_json(body, URL)
    assert exc.value.issue_code == issue
