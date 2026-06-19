import pytest
import os
import sys

# Ensure scripts directory can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from probe_twse_openapi import probe as probe_twse
from probe_yahoo import probe as probe_yahoo

def test_twse_openapi_offline(mocker):
    # Mock requests.get
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"Code": "2330", "Name": "TSMC", "ClosingPrice": "1000", "Change": "10"}]
    mocker.patch('requests.get', return_value=mock_response)

    result = probe_twse()
    assert result["is_usable_now"] is True
    assert result["contract_status"] == "normalized_pass"
    assert result["normalized_sample"]["symbol"] == "2330"
    assert result["normalized_sample"]["close"] == 1000.0

def test_twse_openapi_failure(mocker):
    # Mock requests.get to throw exception
    mocker.patch('requests.get', side_effect=Exception("Connection Timeout"))

    result = probe_twse()
    assert result["is_usable_now"] is False
    assert result["contract_status"] == "failed"
    assert result["http_status"] == "Error"
    assert "Connection Timeout" in result["errors"][0]

def test_yahoo_probe_offline(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "chart": {
            "result": [
                {"meta": {"symbol": "2330.TW", "regularMarketPrice": 1000, "regularMarketTime": 1700000000, "exchangeName": "TAI"}}
            ]
        }
    }
    mocker.patch('requests.get', return_value=mock_response)
    mocker.patch('time.sleep', return_value=None) # Don't sleep in tests

    result = probe_yahoo(symbols=["2330.TW"])
    assert result["is_usable_now"] is True
    assert result["contract_status"] == "normalized_pass"
    assert result["normalized_sample"]["symbol"] == "2330.TW"
