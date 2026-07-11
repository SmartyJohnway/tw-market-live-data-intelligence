import json
from pathlib import Path
from scripts.m8a_tpex_official_eod_adapter import parse_tpex_official_eod_rows
FIX=Path(__file__).resolve().parents[1]/"fixtures/m8a_official_eod"
def load(n): return json.loads((FIX/n).read_text())
def test_tpex_parse_normal_classifies_and_omits_extension_fields():
    r=parse_tpex_official_eod_rows(load("tpex_normal_rows.json"), requested_symbols=["8069","006201"], retrieved_at_utc="2026-07-10T00:00:00Z")
    assert r["batch_status"] == "successful_eod_batch"
    assert {o["instrument_type"] for o in r["observations"]} == {"equity","etf"}
    assert "Average" in r["observations"][0]["omitted_source_fields"]
    assert "raw_payload" not in str(r)
def test_tpex_unclassified_and_signed_change_and_duplicate():
    r=parse_tpex_official_eod_rows(load("tpex_mixed_instruments.json"), requested_symbols=["9999"])
    assert r["observations"][0]["instrument_type"] == "unknown"
    assert "unclassified" in " ".join(r["observations"][0]["caveats"])
    assert parse_tpex_official_eod_rows(load("tpex_signed_change.json"), requested_symbols=["8069"])["observations"][0]["price"]["change"] == "1.5"
    assert parse_tpex_official_eod_rows(load("tpex_duplicate_identity.json"), requested_symbols=["8069"])["row_count_rejected"] == 1
