import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from tests.unit.test_controlled_refresh_staging_writer import payload, run
from scripts.controlled_refresh_staging_writer import build_controlled_refresh_staging_payload
from scripts.controlled_refresh_staging_validator import validate_controlled_refresh_staging_payload

def errs(p): return validate_controlled_refresh_staging_payload(p)
def test_valid_schema_pass(): assert errs(payload()) == []
def test_invalid_payload_mutations_fail():
    mutations = [
        lambda p: p.pop("schema_version"),
        lambda p: p["source_runs"][0].pop("source_id"),
        lambda p: p["validation"].__setitem__("production_write", True),
        lambda p: p["validation"].__setitem__("trading_signal", True),
        lambda p: p.__setitem__("target_universe", {"mode": "full_market"}),
        lambda p: p.__setitem__("target_universe", {"scope": "Full_Market"}),
    ]
    for mutate in mutations:
        p = payload()
        mutate(p)
        assert errs(p)


def test_invalid_payload_builder_cases_record_validation_errors():
    invalid_kwargs = [
        {"freshness_status": "fresh"},
        {"delay_status": "now"},
        {"source_id": "FinMind"},
        {"normalized_sample_preview": {"symbol": "2330", "hold": True}},
        {"normalized_sample_preview": {"official_realtime": True}},
    ]
    for kwargs in invalid_kwargs:
        assert payload(**kwargs)["validation"]["errors"]


def test_allowed_target_universe_cases_pass():
    allowed_cases = [
        {"mode": "bounded", "symbols": ["2330"]},
        {"mode": " bounded ", "symbols": ["2330"]},
        {"mode": None, "symbols": ["2330"]},
    ]
    for target_universe in allowed_cases:
        p = payload()
        p["target_universe"] = target_universe
        assert errs(p) == []


def test_twse_mis_unofficial_source_risk_passes():
    assert payload(source_risk_flags=["unofficial_source_risk"])["validation"]["errors"] == []

def test_twse_mis_unofficial_endpoint_legacy_alias_passes():
    assert payload(source_risk_flags=["unofficial_endpoint"])["validation"]["errors"] == []

def test_twse_mis_without_unofficial_source_risk_fails():
    assert payload(source_risk_flags=["fragile_frontend_contract"])["validation"]["errors"]
