import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import json, pytest
from scripts.controlled_refresh_staging_writer import build_controlled_refresh_staging_payload, write_staging_payload, main

CONF=["confirm_controlled_refresh","confirm_staging_write_only","confirm_no_production_write","confirm_no_frontend_write","confirm_no_generated_artifact_write","confirm_no_trading_signal","confirm_bounded_targets"]

def run(**kw):
    base={"source_id":"TWSE_MIS","source_type":"unofficial_endpoint","authority_level":"unofficial","request_method":"LOCAL_FIXTURE","url_or_fixture":"fixture.json","http_status":200,"contract_status":"ok","retrieved_at_utc":"2026-06-26T00:00:00Z","source_timestamp":"2026-06-26T00:00:00Z","freshness_status":"stale","delay_status":"stale","staleness_seconds":1,"normalization_status":"ok","data_quality_flags":[],"source_risk_flags":["unofficial_endpoint"],"normalized_sample_preview":{"symbol":"2330","price":1},"raw_evidence_ref":"fixture","errors":[]}
    base.update(kw); return base

def payload(**kw): return build_controlled_refresh_staging_payload([run(**kw)], generated_at_utc="2026-06-26T00:00:00Z", target_universe={"symbols":["2330"]}, operator_confirmations=CONF)

def test_valid_fixture_backed_staging_payload(): assert payload()["validation"]["errors"] == []
def test_full_market_target_universe_fails_closed(): assert build_controlled_refresh_staging_payload([run()], generated_at_utc="x", target_universe={"scope":"full_market"}, operator_confirmations=CONF)["validation"]["errors"]
def test_output_path_under_research_generated_fails_closed(tmp_path):
    with pytest.raises(ValueError): write_staging_payload(payload(), tmp_path/"research/generated/x")
def test_output_path_under_frontend_public_fails_closed(tmp_path):
    with pytest.raises(ValueError): write_staging_payload(payload(), tmp_path/"frontend/public/x")
def test_production_looking_output_path_fails_closed(tmp_path):
    with pytest.raises(ValueError): write_staging_payload(payload(), tmp_path/"production/x")
def test_trading_signal_fields_rejected(): assert payload(**{"buy":"yes"})["validation"]["errors"]
def test_realtime_claim_rejected(): assert payload(**{"realtime_guaranteed":True})["validation"]["errors"]
def test_twse_mis_unofficial_source_risk_preserved(): assert "unofficial_endpoint" in payload()["source_runs"][0]["source_risk_flags"]
def test_stale_delayed_live_candidate_preserved():
    assert payload(freshness_status="live_candidate", delay_status="delayed_candidate")["source_runs"][0]["freshness_status"] == "live_candidate"
def test_tmp_path_write_success_with_explicit_confirmations(tmp_path): assert write_staging_payload(payload(), tmp_path).exists()
def test_missing_confirmation_flag_fails_closed(tmp_path):
    inp=tmp_path/"in.json"; inp.write_text(json.dumps({"generated_at_utc":"x","target_universe":{"symbols":["2330"]},"source_runs":[run()]}))
    with pytest.raises(SystemExit): main(["--input-fixture",str(inp),"--output-dir",str(tmp_path)])
