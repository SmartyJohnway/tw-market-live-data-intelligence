import pytest
from scripts.run_m3g04_controlled_live_probe import PROHIBITED_SOURCES

def test_prohibited_sources_are_defined():
    assert "FinMind" in PROHIBITED_SOURCES
    assert "Fugle" in PROHIBITED_SOURCES
    assert "Fubon" in PROHIBITED_SOURCES
