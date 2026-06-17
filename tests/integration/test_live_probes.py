import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

@pytest.mark.network
def test_probe_yahoo():
    from probe_yahoo import probe
    result = probe(symbols=["2330.TW"])
    assert result["source"] == "Yahoo_Finance"
    assert result["status"] == "pass"
    assert result["contract_status"] in ["normalized_pass", "http_pass"]
    assert "2330.TW" not in result.get("failed_targets", [])

@pytest.mark.network
def test_probe_twse_openapi():
    from probe_twse_openapi import probe
    result = probe()
    assert result["source"] == "TWSE_OpenAPI"
    assert result["status"] == "pass"
    assert result["contract_status"] in ["normalized_pass", "http_pass"]
    assert "tpex_stocks" in result.get("unsupported_targets", [])
