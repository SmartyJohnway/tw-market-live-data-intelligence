import pytest
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))
from probe_yahoo import normalize_yahoo_chart_result

def test_valid_chart_normalization():
    # Mock retrieved_at time
    retrieved_dt = datetime(2026, 6, 18, 13, 14, 0, tzinfo=timezone.utc)

    result_data = {
        "meta": {
            "symbol": "2330.TW",
            "currency": "TWD",
            "exchangeName": "TAI",
            "timezone": "Asia/Taipei",
            "gmtoffset": 28800,
            "regularMarketPrice": 950.0,
            "regularMarketTime": 1781788408, # ~2026-06-18 13:13:28 UTC
            "range": "1d",
            "dataGranularity": "1m",
            "validRanges": ["1d", "5d"],
            "firstTradeDate": 946944000
        },
        "timestamp": [1781744400, 1781744460],
        "indicators": {
            "quote": [
                {
                    "open": [945.0, 946.0],
                    "high": [948.0, 946.0],
                    "low": [945.0, 945.0],
                    "close": [948.0, 945.0],
                    "volume": [123000, 50000]
                }
            ],
            "adjclose": [
                {
                    "adjclose": [948.0, 945.0]
                }
            ]
        }
    }

    normalized = normalize_yahoo_chart_result(result_data, "2330.TW", retrieved_dt)

    assert normalized["symbol"] == "2330.TW"
    assert normalized["requested_symbol"] == "2330.TW"
    assert normalized["regular_market_price"] == 950.0
    assert normalized["staleness_seconds"] == 32
    assert normalized["delay_status"] == "realtime"
    assert normalized["series"]["open"] == [945.0, 946.0]
    assert normalized["series"]["adjclose"] == [948.0, 945.0]
    assert len(normalized["series"]["timestamps"]) == 2
    assert normalized["series"]["timestamps_utc"][0] == "2026-06-18T01:00:00+00:00"
    assert normalized["series"]["timestamps_local"][0] == "2026-06-18T09:00:00+08:00"
    assert "data_quality_flags" in normalized
    assert len(normalized["data_quality_flags"]) == 0
    assert normalized["coverage_status"] == "observed_supported"
    assert "unofficial_source" in normalized["source_risk_flags"]


def test_missing_adjclose_adds_flag_and_empty_list():
    retrieved_dt = datetime(2026, 6, 18, 13, 14, 0, tzinfo=timezone.utc)

    result_data = {
        "meta": {
            "symbol": "NOADJ.TW",
            "gmtoffset": 28800,
            "regularMarketTime": 1781760608
        },
        "timestamp": [1781744400],
        "indicators": {
            "quote": [
                {
                    "open": [945.0],
                    "high": [948.0],
                    "low": [945.0],
                    "close": [948.0],
                    "volume": [123000]
                }
            ]
        }
    }

    normalized = normalize_yahoo_chart_result(result_data, "NOADJ.TW", retrieved_dt)
    assert normalized["series"]["adjclose"] == []
    assert "missing_adjclose_array" in normalized["data_quality_flags"]

def test_missing_volume_array():
    retrieved_dt = datetime(2026, 6, 18, 13, 14, 0, tzinfo=timezone.utc)

    result_data = {
        "meta": {
            "symbol": "NOVOL.TW",
            "gmtoffset": 28800,
            "regularMarketTime": 1781760608
        },
        "timestamp": [1781744400],
        "indicators": {
            "quote": [
                {
                    "open": [945.0],
                    "high": [948.0],
                    "low": [945.0],
                    "close": [948.0]
                }
            ]
        }
    }

    normalized = normalize_yahoo_chart_result(result_data, "NOVOL.TW", retrieved_dt)
    assert normalized["series"]["volume"] == []
    assert "missing_volume_array" in normalized["data_quality_flags"]


def test_array_length_mismatch():
    retrieved_dt = datetime(2026, 6, 18, 13, 14, 0, tzinfo=timezone.utc)

    result_data = {
        "meta": {
            "symbol": "MISMATCH.TW",
            "gmtoffset": 28800,
            "regularMarketTime": 1781760608
        },
        "timestamp": [1781744400, 1781744460],
        "indicators": {
            "quote": [
                {
                    "open": [945.0], # 1 item instead of 2
                    "high": [948.0, 946.0],
                    "low": [945.0, 945.0],
                    "close": [948.0, 945.0],
                    "volume": [123000, 50000]
                }
            ],
            "adjclose": [
                {
                    "adjclose": [948.0] # 1 item instead of 2
                }
            ]
        }
    }

    normalized = normalize_yahoo_chart_result(result_data, "MISMATCH.TW", retrieved_dt)
    assert "timestamp_quote_length_mismatch" in normalized["data_quality_flags"]
    assert "timestamp_adjclose_length_mismatch" in normalized["data_quality_flags"]

def test_preserves_none_values():
    retrieved_dt = datetime(2026, 6, 18, 13, 14, 0, tzinfo=timezone.utc)

    result_data = {
        "meta": {
            "symbol": "NONEVALS.TW",
            "gmtoffset": 28800,
            "regularMarketTime": 1781760608
        },
        "timestamp": [1781744400, 1781744460],
        "indicators": {
            "quote": [
                {
                    "open": [945.0, None],
                    "high": [948.0, None],
                    "low": [945.0, None],
                    "close": [948.0, None],
                    "volume": [123000, None]
                }
            ]
        }
    }

    normalized = normalize_yahoo_chart_result(result_data, "NONEVALS.TW", retrieved_dt)
    assert normalized["series"]["close"] == [948.0, None]
    assert normalized["series"]["volume"] == [123000, None]

def test_empty_chart_result():
    retrieved_dt = datetime(2026, 6, 18, 13, 14, 0, tzinfo=timezone.utc)
    normalized = normalize_yahoo_chart_result({}, "EMPTY.TW", retrieved_dt)
    assert normalized["symbol"] == "EMPTY.TW"
    assert "empty_chart_result" in normalized["data_quality_flags"]

def test_exchange_timezone_name_preference():
    retrieved_dt = datetime(2026, 6, 18, 13, 14, 0, tzinfo=timezone.utc)

    result_data = {
        "meta": {
            "symbol": "TZ.TW",
            "timezone": "CST",
            "exchangeTimezoneName": "Asia/Taipei",
            "regularMarketTime": 1781760608
        }
    }
    normalized = normalize_yahoo_chart_result(result_data, "TZ.TW", retrieved_dt)
    assert normalized["exchange_timezone_name"] == "Asia/Taipei"

def test_malformed_timestamp_flag():
    retrieved_dt = datetime(2026, 6, 18, 13, 14, 0, tzinfo=timezone.utc)

    result_data = {
        "meta": {
            "symbol": "MALFORMED.TW",
            "gmtoffset": 28800,
            "regularMarketTime": 1781760608
        },
        "timestamp": [1781744400, "invalid"],
        "indicators": {
            "quote": [
                {
                    "open": [945.0, 946.0],
                    "high": [948.0, 946.0],
                    "low": [945.0, 945.0],
                    "close": [948.0, 945.0],
                    "volume": [123000, 50000]
                }
            ]
        }
    }

    normalized = normalize_yahoo_chart_result(result_data, "MALFORMED.TW", retrieved_dt)
    assert "malformed_timestamp" in normalized["data_quality_flags"]
    assert normalized["series"]["timestamps_utc"][1] is None
