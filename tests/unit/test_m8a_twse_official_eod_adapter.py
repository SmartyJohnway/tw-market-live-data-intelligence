import json
from pathlib import Path
from scripts.m8a_twse_official_eod_adapter import parse_twse_official_eod_rows
FIX=Path(__file__).resolve().parents[1]/"fixtures/m8a_official_eod"
def load(n): return json.loads((FIX/n).read_text())
def test_twse_parse_normal_preserves_identity_and_derives_previous_close():
    r=parse_twse_official_eod_rows(load("twse_normal_rows.json"), requested_symbols=["2330","0050"], retrieved_at_utc="2026-07-10T00:00:00Z")
    assert r["batch_status"] == "successful_eod_batch"
    assert {o["symbol"] for o in r["observations"]} == {"2330","0050"}
    o=r["observations"][0]
    assert o["trade_date"] == "2026-07-09" and o["price"]["previous_close"] == "1000.00"
    assert "raw_payload" not in str(r)
def test_twse_duplicate_mixed_schema_and_partial():
    assert parse_twse_official_eod_rows(load("twse_duplicate_identity.json"), requested_symbols=["2330"])["row_count_rejected"] == 1
    assert parse_twse_official_eod_rows(load("twse_mixed_date.json"), requested_symbols=["2330","0050"])["batch_status"] == "date_mismatch"
    assert parse_twse_official_eod_rows(load("twse_schema_drift.json"), requested_symbols=["2330"])["row_count_rejected"] == 1
    assert parse_twse_official_eod_rows(load("twse_partial_rows.json"), requested_symbols=["2330"])["observations"][0]["observation_status"] == "complete"
