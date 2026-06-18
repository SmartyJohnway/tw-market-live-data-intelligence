import pytest
import responses
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))

from probe_yahoo import probe, KNOWN_UNSUPPORTED_YAHOO_PLACEHOLDERS

@responses.activate
def test_valid_chart_response_parses_successfully():
    symbols = ["2330.TW"]
    responses.add(
        responses.GET,
        "https://query1.finance.yahoo.com/v8/finance/chart/2330.TW",
        json={
            "chart": {
                "result": [
                    {
                        "meta": {
                            "symbol": "2330.TW",
                            "regularMarketPrice": 2410.0,
                            "regularMarketTime": 1781760608,
                            "exchangeName": "TAI"
                        },
                        "timestamp": [1781744400],
                        "indicators": {
                            "quote": [{"close": [2410.0]}]
                        }
                    }
                ]
            }
        },
        status=200
    )

    result = probe(symbols=symbols)

    assert result["contract_status"] == "normalized_pass"
    assert result["normalized_sample"]["symbol"] == "2330.TW"
    assert result["normalized_sample"]["regular_market_price"] == 2410.0
    assert result["normalized_sample"]["series"]["close"] == [2410.0]
    assert len(result["failed_targets"]) == 0
    assert len(result["unsupported_targets"]) == 0
    assert len(result["errors"]) == 0

@responses.activate
def test_known_unsupported_placeholder_goes_to_unsupported():
    symbols = ["TX.TW"]
    responses.add(
        responses.GET,
        "https://query1.finance.yahoo.com/v8/finance/chart/TX.TW",
        json={"chart": {"error": {"code": "Not Found", "description": "No data found, symbol may be delisted"}}},
        status=404
    )

    result = probe(symbols=symbols)

    assert result["contract_status"] == "failed"
    assert "TX.TW" in result["unsupported_targets"]
    assert "TX.TW" not in result["failed_targets"]
    assert any("HTTP 404 for known unsupported placeholder" in w for w in result["warnings"])
    assert len(result["errors"]) == 0

@responses.activate
def test_expected_supported_symbol_404_goes_to_failed():
    symbols = ["EXPECTED.TW"]
    responses.add(
        responses.GET,
        "https://query1.finance.yahoo.com/v8/finance/chart/EXPECTED.TW",
        json={"chart": {"error": {"code": "Not Found"}}},
        status=404
    )

    result = probe(symbols=symbols)

    assert result["contract_status"] == "failed"
    assert "EXPECTED.TW" not in result["unsupported_targets"]
    assert "EXPECTED.TW" in result["failed_targets"]
    assert any("HTTP 404 for EXPECTED.TW" in e for e in result["errors"])


@responses.activate
def test_empty_chart_result_does_not_crash():
    symbols = ["EMPTY.TW"]
    responses.add(
        responses.GET,
        "https://query1.finance.yahoo.com/v8/finance/chart/EMPTY.TW",
        json={
            "chart": {
                "result": []
            }
        },
        status=200
    )

    result = probe(symbols=symbols)

    assert result["contract_status"] == "failed"
    assert "EMPTY.TW" in result["failed_targets"]
    assert any("Parse failed or empty result for EMPTY.TW" in e for e in result["errors"])

@responses.activate
def test_missing_quote_arrays_does_not_crash():
    symbols = ["NOQUOTE.TW"]
    responses.add(
        responses.GET,
        "https://query1.finance.yahoo.com/v8/finance/chart/NOQUOTE.TW",
        json={
            "chart": {
                "result": [
                    {
                        "meta": {
                            "symbol": "NOQUOTE.TW",
                            "regularMarketPrice": 100.0,
                            "regularMarketTime": 1781760608,
                            "exchangeName": "TAI"
                        }
                    }
                ]
            }
        },
        status=200
    )

    result = probe(symbols=symbols)

    assert result["contract_status"] == "normalized_pass"
    assert result["normalized_sample"]["symbol"] == "NOQUOTE.TW"

@responses.activate
def test_network_exception_is_classified_as_error():
    symbols = ["TIMEOUT.TW"]
    import requests
    responses.add(
        responses.GET,
        "https://query1.finance.yahoo.com/v8/finance/chart/TIMEOUT.TW",
        body=requests.exceptions.ConnectionError("Connection refused")
    )

    result = probe(symbols=symbols)

    assert result["contract_status"] == "failed"
    assert "TIMEOUT.TW" in result["failed_targets"]
    assert "TIMEOUT.TW" not in result["unsupported_targets"]
    assert any("Network exception for TIMEOUT.TW" in e for e in result["errors"])
