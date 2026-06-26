import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from tests.unit.test_controlled_refresh_staging_writer import payload, run
from scripts.controlled_refresh_staging_writer import build_controlled_refresh_staging_payload
from scripts.controlled_refresh_staging_validator import validate_controlled_refresh_staging_payload

def errs(p): return validate_controlled_refresh_staging_payload(p)
def test_valid_schema_pass(): assert errs(payload()) == []
def test_missing_top_level_field_fail(): p=payload(); del p["schema_version"]; assert errs(p)
def test_missing_source_run_field_fail(): p=payload(); del p["source_runs"][0]["source_id"]; assert errs(p)
def test_invalid_freshness_enum_fail(): assert payload(freshness_status="fresh")["validation"]["errors"]
def test_invalid_delay_enum_fail(): assert payload(delay_status="now")["validation"]["errors"]
def test_production_write_true_fail(): p=payload(); p["validation"]["production_write"]=True; assert errs(p)
def test_frontend_write_true_fail(): p=payload(); p["validation"]["frontend_write"]=True; assert errs(p)
def test_generated_artifact_write_true_fail(): p=payload(); p["validation"]["generated_artifact_write"]=True; assert errs(p)
def test_trading_signal_true_fail(): p=payload(); p["validation"]["trading_signal"]=True; assert errs(p)
def test_source_id_outside_allowlist_fail(): assert payload(source_id="FinMind")["validation"]["errors"]
def test_buy_sell_hold_nested_field_fail(): assert payload(normalized_sample_preview={"symbol":"2330","hold":True})["validation"]["errors"]
def test_realtime_guarantee_nested_field_fail(): assert payload(normalized_sample_preview={"official_realtime":True})["validation"]["errors"]


def test_target_universe_mode_full_market_fails():
    p=payload(); p["target_universe"]={"mode":"full_market"}; assert errs(p)

def test_target_universe_mode_all_fails():
    p=payload(); p["target_universe"]={"mode":"all"}; assert errs(p)

def test_target_universe_mode_star_fails():
    p=payload(); p["target_universe"]={"mode":"*"}; assert errs(p)

def test_target_universe_bounded_mode_passes():
    p=payload(); p["target_universe"]={"mode":"bounded","symbols":["2330"]}; assert errs(p) == []

def test_twse_mis_unofficial_source_risk_passes():
    assert payload(source_risk_flags=["unofficial_source_risk"])["validation"]["errors"] == []

def test_twse_mis_unofficial_endpoint_legacy_alias_passes():
    assert payload(source_risk_flags=["unofficial_endpoint"])["validation"]["errors"] == []

def test_twse_mis_without_unofficial_source_risk_fails():
    assert payload(source_risk_flags=["fragile_frontend_contract"])["validation"]["errors"]
