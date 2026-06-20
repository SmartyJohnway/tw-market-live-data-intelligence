import pytest
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))
from probe_tpex_openapi import normalize_tpex_openapi_row

def test_valid_tpex_row():
    dt = datetime(2023, 10, 25, 12, 0, 0, tzinfo=timezone.utc)
    raw_row = {
        "Date": "1150618",
        "SecuritiesCompanyCode": "3105",
        "CompanyName": "穩懋",
        "Close": "528.00",
        "Change": "+9.00",
        "Open": "522.00",
        "High": "557.00",
        "Low": "521.00",
        "TradingShares": "40,139,349",
        "TransactionAmount": "21613642453",
        "TransactionNumber": "47240",
        "Average": "538.47"
    }

    norm = normalize_tpex_openapi_row(raw_row, dt)

    assert norm["symbol"] == "3105"
    assert norm["name"] == "穩懋"
    assert norm["trade_date"] == "1150618"
    assert norm["open"] == 522.0
    assert norm["high"] == 557.0
    assert norm["low"] == 521.0
    assert norm["close"] == 528.0
    assert norm["change"] == 9.0
    assert norm["trade_volume"] == 40139349
    assert norm["trade_value"] == 21613642453.0
    assert norm["transaction_count"] == 47240
    assert "missing_close" not in norm["data_quality_flags"]
    assert "missing_trade_date" not in norm["data_quality_flags"]
    assert norm["unmapped_raw_fields"] == {"Average": "538.47"}
    assert norm["raw_row"] == raw_row

def test_missing_close_does_not_crash():
    dt = datetime.now(timezone.utc)
    raw_row = {
        "SecuritiesCompanyCode": "3105",
        "Close": "---",
        "Open": ""
    }
    norm = normalize_tpex_openapi_row(raw_row, dt)
    assert norm["close"] is None
    assert norm["open"] is None
    assert "missing_close" in norm["data_quality_flags"]
    assert "missing_trade_date" in norm["data_quality_flags"]
    assert "missing_name" in norm["data_quality_flags"]

def test_malformed_close_does_not_crash():
    dt = datetime.now(timezone.utc)
    raw_row = {
        "SecuritiesCompanyCode": "3105",
        "CompanyName": "穩懋",
        "Date": "1150618",
        "Close": "N/A"
    }
    norm = normalize_tpex_openapi_row(raw_row, dt)
    assert norm["close"] is None
    assert "malformed_close" in norm["data_quality_flags"]

def test_tpex_legacy_aliases():
    dt = datetime(2023, 10, 25, 12, 0, 0, tzinfo=timezone.utc)
    raw_row = {
        "Date": "1150618",
        "SecuritiesCompanyCode": "3105",
        "CompanyName": "穩懋",
        "Close": "528.00",
        "TradingVolume": "50000",
        "TradingAmount": "250000",
        "Transaction": "123"
    }

    norm = normalize_tpex_openapi_row(raw_row, dt)

    assert norm["trade_volume"] == 50000
    assert norm["trade_value"] == 250000.0
    assert norm["transaction_count"] == 123
    assert norm["unmapped_raw_fields"] == {}


def test_missing_trade_date():
    dt = datetime.now(timezone.utc)
    raw_row = {
        "SecuritiesCompanyCode": "3105",
        "CompanyName": "穩懋",
        "Close": "100.0"
    }
    norm = normalize_tpex_openapi_row(raw_row, dt)
    assert norm["trade_date"] is None
    assert "missing_trade_date" in norm["data_quality_flags"]
