import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))

from run_all_probes import generate_reports
import json

def test_markdown_table_escaping(tmp_path, monkeypatch):
    # Mock get_abs_path to write to a temp directory
    def mock_get_abs_path(path):
        return os.path.join(tmp_path, path)
    monkeypatch.setattr("run_all_probes.get_abs_path", mock_get_abs_path)

    # Fake probe result with a pipe character in the URL
    fake_results = [
        {
            "probe_id": "test_1",
            "source": "TWSE_MIS",
            "source_type": "unofficial_frontend_endpoint",
            "contract_status": "normalized_pass",
            "requires_auth": False,
            "requires_session": False,
            "is_usable_now": True,
            "http_status": 200,
            "parse_status": "success",
            "normalization_status": "success",
            "freshness_status": "realtime",
            "delay_status": "delayed",
            "risk_level": "high",
            "ai_suitability": "intraday",
            "unsupported_targets": [],
            "failed_targets": [],
            "risk_notes": ["Mock risk"],
            "retrieved_at_utc": "2024-01-01T00:00:00Z",
            "request": {
                "url": "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_1101.tw|tse_2330.tw",
                "method": "GET"
            }
        }
    ]

    generate_reports(fake_results)

    # Verify that the pipe is escaped in capability_matrix.md
    with open(os.path.join(tmp_path, "docs/capability_matrix.md"), "r") as f:
        content = f.read()
        assert "tse_1101.tw&#124;tse_2330.tw" in content
        assert "tse_1101.tw|tse_2330.tw" not in content

    # Verify that the pipe is UNESCAPED in the matrix.json to preserve original data
    with open(os.path.join(tmp_path, "frontend/public/matrix.json"), "r") as f:
        data = json.load(f)
        assert data["results"][0]["request"]["url"] == "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_1101.tw|tse_2330.tw"
