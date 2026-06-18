import pytest
from datetime import datetime, timezone, timedelta
from scripts.probe_twse_mis import normalize_twse_mis_row, _parse_ladder, _safe_float

@pytest.fixture
def mock_retrieved_at_utc():
    return datetime(2024, 10, 25, 5, 30, 5, tzinfo=timezone.utc)

def test_safe_float_dash_handling():
    flags = []
    assert _safe_float("-", flags, "test_field") is None
    assert len(flags) == 0

def test_safe_float_empty_handling():
    flags = []
    assert _safe_float("", flags, "test_field") is None
    assert len(flags) == 0

def test_parse_ladder_trailing_underscore():
    flags = []
    prices, volumes = _parse_ladder("10.5_10.4_10.3_10.2_10.1_", "100_200_300_400_500_", flags, "bid")
    assert prices == [10.5, 10.4, 10.3, 10.2, 10.1]
    assert volumes == [100, 200, 300, 400, 500]
    assert len(flags) == 0

def test_parse_ladder_invalid_placeholders():
    flags = []
    prices, volumes = _parse_ladder("10.5_0.0000_10.3_0_-_", "100_200_300_400_500_", flags, "bid")
    assert prices == [10.5, None, 10.3, None, None]
    assert volumes == [100, None, 300, None, None]
    assert "invalid_bid_price_level" in flags

def test_parse_ladder_mismatched_length():
    flags = []
    prices, volumes = _parse_ladder("10.5_10.4_", "100_", flags, "ask")
    assert prices == [10.5, 10.4]
    assert volumes == [100, None]
    assert "mismatched_ask_ladder_length" in flags

def test_intraday_stock_like_row(mock_retrieved_at_utc):
    raw_row = {
        "c": "2330",
        "ex": "tse",
        "n": "台積電",
        "ch": "2330.tw",
        "z": "-",
        "y": "1040.00",
        "o": "-",
        "h": "-",
        "l": "-",
        "v": "15000",
        "tv": "-",
        "s": "-",
        "a": "1055.00_1060.00_1065.00_1070.00_1075.00_",
        "f": "100_200_300_400_500_",
        "b": "1050.00_1045.00_1040.00_1035.00_1030.00_",
        "g": "150_250_350_450_550_",
        "u": "1140.00",
        "w": "936.00",
        "d": "20241025",
        "t": "09:00:00",
        "tlong": "1729818000000"
    }

    normalized = normalize_twse_mis_row(raw_row, mock_retrieved_at_utc)

    assert normalized["symbol"] == "2330"
    assert normalized["exchange"] == "tse"
    assert normalized["asset_type_candidate"] == "stock_like"
    assert normalized["last_price"] is None
    assert normalized["open"] is None
    assert normalized["high"] is None
    assert normalized["low"] is None
    assert normalized["current_volume"] is None
    assert normalized["change"] is None
    assert normalized["change_pct"] is None
    assert "missing_last_price" in normalized["data_quality_flags"]
    assert "s" in normalized["unmapped_raw_fields"]
    assert normalized["unmapped_raw_fields"]["s"] == "-"

def test_post_market_stock_like_row(mock_retrieved_at_utc):
    raw_row = {
        "c": "2330",
        "ex": "tse",
        "n": "台積電",
        "ch": "2330.tw",
        "z": "1050.00",
        "y": "1040.00",
        "o": "1045.00",
        "h": "1055.00",
        "l": "1040.00",
        "v": "20000",
        "tv": "500",
        "oa": "1055.00",
        "ob": "1050.00",
        "oz": "1050.00",
        "ov": "1000",
        "ot": "14:30:00",
        "fv": "50",
        "a": "1055.00_1060.00_1065.00_1070.00_1075.00_",
        "f": "100_200_300_400_500_",
        "b": "1050.00_1045.00_1040.00_1035.00_1030.00_",
        "g": "150_250_350_450_550_",
        "u": "1140.00",
        "w": "936.00",
        "d": "20241025",
        "t": "13:30:00",
        "tlong": "1729834200000"
    }

    normalized = normalize_twse_mis_row(raw_row, mock_retrieved_at_utc)

    assert normalized["last_price"] == 1050.0
    assert normalized["current_volume"] == 500
    assert normalized["alternate_session_time"] == "14:30:00"
    assert normalized["change"] == 10.0

    # Check post market fields preserved
    unmapped = normalized["unmapped_raw_fields"]
    assert "oa" in unmapped
    assert "ob" in unmapped
    assert "oz" in unmapped
    assert "ov" in unmapped
    assert "fv" in unmapped

def test_etf_row(mock_retrieved_at_utc):
    raw_row = {
        "c": "0050",
        "ex": "tse",
        "it": "02",
        "nu": "http://example.com/nav",
        "a": "100.00_",
        "f": "10_",
        "b": "99.00_",
        "g": "20_"
    }

    normalized = normalize_twse_mis_row(raw_row, mock_retrieved_at_utc)

    assert normalized["asset_type_candidate"] == "etf"
    assert "nu" in normalized["unmapped_raw_fields"]
    assert normalized["bid_prices"] == [99.0]

def test_tdr_row(mock_retrieved_at_utc):
    raw_row = {
        "c": "9103",
        "ex": "tse",
        "it": "13",
        "a": "10.00_",
        "f": "10_",
        "b": "9.00_",
        "g": "20_"
    }

    normalized = normalize_twse_mis_row(raw_row, mock_retrieved_at_utc)

    assert normalized["asset_type_candidate"] == "tdr"

def test_index_row_no_crash_and_no_fake_bid_ask(mock_retrieved_at_utc):
    raw_row = {
        "c": "t00",
        "ex": "tse",
        "it": "t",
        "n": "發行量加權股價指數",
        "ch": "t00.tw",
        "z": "23300.00",
        "y": "23200.00",
        "d": "20241025",
        "t": "13:30:00"
    }

    normalized = normalize_twse_mis_row(raw_row, mock_retrieved_at_utc)

    assert normalized["asset_type_candidate"] == "index"
    assert normalized["bid_prices"] == []
    assert normalized["ask_prices"] == []
    assert normalized["bid_volumes"] == []
    assert normalized["ask_volumes"] == []
    assert normalized["limit_up"] is None
    assert normalized["limit_down"] is None

    # Verify no flag generated for missing bid/ask on index
    assert "missing_bid_ask" not in normalized["data_quality_flags"]

def test_malformed_numeric_values(mock_retrieved_at_utc):
    raw_row = {
        "c": "2330",
        "ex": "tse",
        "z": "abc",
        "v": "def"
    }

    normalized = normalize_twse_mis_row(raw_row, mock_retrieved_at_utc)
    assert normalized["last_price"] is None
    assert normalized["cumulative_volume"] is None
    assert "malformed_last_price" in normalized["data_quality_flags"]
    assert "malformed_cumulative_volume" in normalized["data_quality_flags"]
