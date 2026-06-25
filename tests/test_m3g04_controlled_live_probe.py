import pytest
from scripts.run_m3g04_controlled_live_probe import (
    PROHIBITED_SOURCES,
    map_targets_for_source,
    validate_targets,
    validate_sources,
    build_summary_entry
)
from pathlib import Path

import subprocess
import json
import os

def test_prohibited_sources_are_defined():
    assert "FinMind" in PROHIBITED_SOURCES
    assert "Fugle" in PROHIBITED_SOURCES
    assert "Fubon" in PROHIBITED_SOURCES

import sys

def get_env():
    env = os.environ.copy()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env["PYTHONPATH"] = f"{project_root}:{env.get('PYTHONPATH', '')}"
    return env

@pytest.mark.not_network
def test_max_targets_enforcement():
    cmd = [sys.executable, "scripts/run_m3g04_controlled_live_probe.py", "--targets", "2330", "0050", "00929", "8069", "TAIEX", "1435", "--sources", "TWSE_OpenAPI"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=get_env())
    assert result.returncode == 1
    assert "Error: Maximum of 5 targets allowed" in result.stderr

@pytest.mark.not_network
def test_prohibited_source_rejection():
    cmd = [sys.executable, "scripts/run_m3g04_controlled_live_probe.py", "--targets", "2330", "--sources", "FinMind"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=get_env())
    assert result.returncode == 1
    assert "Error: FinMind is strictly prohibited" in result.stderr

@pytest.mark.not_network
def test_empty_targets_rejection():
    cmd = [sys.executable, "scripts/run_m3g04_controlled_live_probe.py", "--targets", "--sources", "TWSE_OpenAPI"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=get_env())
    assert result.returncode == 2 # argparse catches empty nargs+

@pytest.mark.not_network
def test_unknown_source_rejection():
    cmd = [sys.executable, "scripts/run_m3g04_controlled_live_probe.py", "--targets", "2330", "--sources", "UNKNOWN_SOURCE"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=get_env())
    assert result.returncode == 1
    assert "Error: UNKNOWN_SOURCE is not in the allowed sources list" in result.stderr

def test_map_targets_for_source():
    targets = ["2330", "0050", "8069", "TAIEX", "t00"]

    yahoo_mapped = map_targets_for_source("Yahoo_Finance", targets)
    assert yahoo_mapped == ["2330.TW", "0050.TW", "8069.TWO", "^TWII", "^TWII"]

    mis_mapped = map_targets_for_source("TWSE_MIS", targets)
    assert mis_mapped == ["tse_2330.tw", "tse_0050.tw", "otc_8069.tw", "tse_t00.tw", "tse_t00.tw"]

    openapi_mapped = map_targets_for_source("TWSE_OpenAPI", targets)
    assert openapi_mapped == ["2330", "0050", "8069", "TAIEX", "t00"]

    tpex_mapped = map_targets_for_source("TPEx_OpenAPI", targets)
    assert tpex_mapped == ["2330", "0050", "8069", "TAIEX", "t00"]

def test_validate_targets():
    with pytest.raises(ValueError, match="Target list cannot be empty"):
        validate_targets([])
    with pytest.raises(ValueError, match="Maximum of 5 targets allowed"):
        validate_targets(["1", "2", "3", "4", "5", "6"])
    # Should not raise
    validate_targets(["2330", "0050"])

def test_validate_sources():
    with pytest.raises(ValueError, match="FinMind is strictly prohibited"):
        validate_sources(["FinMind"])
    with pytest.raises(ValueError, match="Unknown is not in the allowed sources list"):
        validate_sources(["Unknown"])
    # Should not raise
    validate_sources(["Yahoo_Finance", "TWSE_MIS"])

def test_build_summary_entry():
    mock_result = {
        "contract_status": "identity_mismatch",
        "http_ok": True,
        "parse_status": "success",
        "normalization_status": "success",
        "failed_targets": ["2330.TW"],
        "errors": ["Identity mismatch detected"]
    }
    mock_file = Path("dummy_output.json")

    summary = build_summary_entry("Yahoo_Finance", mock_result, mock_file, ["2330"])

    assert summary["status"] == "identity_mismatch"
    assert summary["contract_status"] == "identity_mismatch"
    assert summary["http_ok"] is True
    assert summary["parse_status"] == "success"
    assert summary["normalization_status"] == "success"
    assert summary["failed_targets"] == ["2330.TW"]
    assert summary["errors"] == ["Identity mismatch detected"]
    assert summary["output_file"] == "dummy_output.json"

def test_build_summary_entry_none_result():
    summary = build_summary_entry("Yahoo_Finance", None, Path("dummy.json"), ["2330"])

    assert summary["status"] == "failed"
    assert summary["contract_status"] == "failed"
    assert summary["http_ok"] is False
    assert summary["failed_targets"] == ["2330"]
    assert summary["errors"] == ["Result is None"]
