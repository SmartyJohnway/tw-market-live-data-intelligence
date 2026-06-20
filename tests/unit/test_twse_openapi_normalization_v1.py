import pytest
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))
from probe_twse_openapi import normalize_twse_openapi_row

def test_valid_twse_row():
    dt = datetime(2023, 10, 25, 12, 0, 0, tzinfo=timezone.utc)
    raw_row = {
        "Date": "1150618",
        "Code": "2330",
        "Name": "台積電",
        "TradeVolume": "49,982,610",
        "TradeValue": "120198889493",
        "OpeningPrice": "2395.00",
        "HighestPrice": "2415.00",
        "LowestPrice": "2385.00",
        "ClosingPrice": "2410.00",
        "Change": "25.0000",
        "Transaction": "103,190",
        "ExtraField": "123"
    }

    norm = normalize_twse_openapi_row(raw_row, dt)

    assert norm["symbol"] == "2330"
    assert norm["name"] == "台積電"
    assert norm["trade_date"] == "1150618"
    assert norm["open"] == 2395.0
    assert norm["high"] == 2415.0
    assert norm["low"] == 2385.0
    assert norm["close"] == 2410.0
    assert norm["change"] == 25.0
    assert norm["trade_volume"] == 49982610
    assert norm["trade_value"] == 120198889493.0
    assert norm["transaction_count"] == 103190
    assert "missing_close" not in norm["data_quality_flags"]
    assert "missing_trade_date" not in norm["data_quality_flags"]
    assert norm["unmapped_raw_fields"] == {"ExtraField": "123"}
    assert norm["raw_row"] == raw_row

def test_missing_close_does_not_crash():
    dt = datetime.now(timezone.utc)
    raw_row = {
        "Code": "2330",
        "ClosingPrice": "--",
        "OpeningPrice": "-"
    }
    norm = normalize_twse_openapi_row(raw_row, dt)
    assert norm["close"] is None
    assert norm["open"] is None
    assert "missing_close" in norm["data_quality_flags"]
    assert "missing_trade_date" in norm["data_quality_flags"]
    assert "missing_name" in norm["data_quality_flags"]

def test_malformed_close_does_not_crash():
    dt = datetime.now(timezone.utc)
    raw_row = {
        "Code": "2330",
        "Name": "台積電",
        "Date": "1150618",
        "ClosingPrice": "not_a_number"
    }
    norm = normalize_twse_openapi_row(raw_row, dt)
    assert norm["close"] is None
    assert "malformed_close" in norm["data_quality_flags"]

def test_missing_trade_date():
    dt = datetime.now(timezone.utc)
    raw_row = {
        "Code": "2330",
        "Name": "台積電",
        "ClosingPrice": "100.0"
    }
    norm = normalize_twse_openapi_row(raw_row, dt)
    assert norm["trade_date"] is None
    assert "missing_trade_date" in norm["data_quality_flags"]
