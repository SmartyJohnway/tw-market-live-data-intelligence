import pytest
from scripts.run_m3g04_controlled_live_probe import PROHIBITED_SOURCES

import subprocess
import json
import os

def test_prohibited_sources_are_defined():
    assert "FinMind" in PROHIBITED_SOURCES
    assert "Fugle" in PROHIBITED_SOURCES
    assert "Fubon" in PROHIBITED_SOURCES

@pytest.mark.not_network
def test_max_targets_enforcement():
    cmd = ["python", "scripts/run_m3g04_controlled_live_probe.py", "--targets", "2330", "0050", "00929", "8069", "TAIEX", "1435", "--sources", "TWSE_OpenAPI"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "Error: Maximum of 5 targets allowed" in result.stderr

@pytest.mark.not_network
def test_prohibited_source_rejection():
    cmd = ["python", "scripts/run_m3g04_controlled_live_probe.py", "--targets", "2330", "--sources", "FinMind"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "Error: FinMind is strictly prohibited" in result.stderr
