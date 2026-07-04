import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import json, pytest
from tests.unit.test_controlled_refresh_staging_writer import payload
from scripts.build_frontend_readonly_context_package import build_frontend_readonly_context_package, write_frontend_readonly_context_package, validate_frontend_readonly_context_package, main

def test_stale_row_produces_stale_display_caveat(): assert "stale_source_row" in build_frontend_readonly_context_package(payload())["symbols"][0]["display_caveats"]
def test_delayed_row_produces_delayed_display_caveat(): assert "delayed_source_row" in build_frontend_readonly_context_package(payload(delay_status="delayed_candidate"))["symbols"][0]["display_caveats"]
def test_live_candidate_still_includes_not_realtime_guaranteed(): assert "not_realtime_guaranteed" in build_frontend_readonly_context_package(payload(freshness_status="live_candidate"))["symbols"][0]["display_caveats"]
def test_output_to_tmp_path_works(tmp_path): assert write_frontend_readonly_context_package(build_frontend_readonly_context_package(payload()), tmp_path).exists()
def test_output_to_frontend_public_fails_closed(tmp_path):
    with pytest.raises(ValueError): write_frontend_readonly_context_package(build_frontend_readonly_context_package(payload()), tmp_path/"frontend/public")
def test_buy_sell_hold_field_in_input_fails():
    with pytest.raises(ValueError): build_frontend_readonly_context_package(payload(normalized_sample_preview={"buy":True}))
def test_missing_caveats_fails():
    p=build_frontend_readonly_context_package(payload()); p["global_caveats"]=[]; assert validate_frontend_readonly_context_package(p)
def test_cli_missing_confirmation_fails(tmp_path):
    inp=tmp_path/"staging.json"; inp.write_text(json.dumps(payload()))
    with pytest.raises(SystemExit): main(["--input-staging-payload",str(inp),"--output-dir",str(tmp_path)])
