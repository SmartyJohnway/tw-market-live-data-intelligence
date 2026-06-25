import pytest
from pathlib import Path
from scripts.m3g_live_probe_to_snapshot_adapter import (
    build_adapter_report,
    build_mock_inputs_from_live_probe_run,
    standardize_symbol
)
from scripts.generate_latest_market_snapshot import build_snapshot

FIXTURE_DIR = Path("tests/fixtures/m3g_live_probe_evidence")

def test_standardize_symbol():
    assert standardize_symbol("Yahoo_Finance", "2330.TW") == "2330"
    assert standardize_symbol("Yahoo_Finance", "8069.TWO") == "8069"
    assert standardize_symbol("Yahoo_Finance", "^TWII") == "TAIEX"
    assert standardize_symbol("TWSE_MIS", "tse_2330.tw") == "2330"
    assert standardize_symbol("TWSE_MIS", "otc_8069.tw") == "8069"
    assert standardize_symbol("TWSE_MIS", "tse_t00.tw") == "TAIEX"
    assert standardize_symbol("TWSE_OpenAPI", "2330") == "2330"
    assert standardize_symbol("Yahoo_Finance", "invalid_format") == "invalid_format"
    assert standardize_symbol("TWSE_MIS", "invalid_format") is None

@pytest.mark.not_network
def test_valid_run_summary_mapping():
    summary_path = FIXTURE_DIR / "run_summary_valid.json"
    report = build_adapter_report(summary_path)

    assert report["adapter_status"] == "mapping_pass"
    assert "TWSE_MIS" in report["sources_mapped"]
    assert "Yahoo_Finance" in report["sources_mapped"]

    mock_inputs = report["mock_inputs_preview"]
    assert "TWSE_MIS" in mock_inputs
    assert "2330" in mock_inputs["TWSE_MIS"]
    assert mock_inputs["TWSE_MIS"]["2330"]["last_price"] == 500.0
    assert mock_inputs["TWSE_MIS"]["2330"]["price_semantics"] == "live_candidate"
    assert "unofficial_source_risk" in mock_inputs["TWSE_MIS"]["2330"]["caveats"]

    assert "Yahoo_Finance" in mock_inputs
    assert "2330" in mock_inputs["Yahoo_Finance"]
    assert mock_inputs["Yahoo_Finance"]["2330"]["last_price"] == 500.0
    assert mock_inputs["Yahoo_Finance"]["2330"]["price_semantics"] == "stale_candidate"
    assert "third_party_coverage_caveats" in mock_inputs["Yahoo_Finance"]["2330"]["caveats"]

@pytest.mark.not_network
def test_yahoo_identity_mismatch_blocks_mapping():
    summary_path = FIXTURE_DIR / "run_summary_identity_mismatch.json"
    report = build_adapter_report(summary_path)

    assert report["adapter_status"] == "identity_mismatch_blocked"
    assert "Yahoo_Finance" in report["sources_blocked"]
    assert "Yahoo_Finance" not in report["mock_inputs_preview"]
    assert any("identity mismatch" in e.lower() for e in report["errors"])

@pytest.mark.not_network
def test_official_openapi_mapping():
    summary_path = FIXTURE_DIR / "run_summary_eod_openapi.json"
    report = build_adapter_report(summary_path)

    assert report["adapter_status"] == "mapping_pass"
    mock_inputs = report["mock_inputs_preview"]
    assert "TWSE_OpenAPI" in mock_inputs
    assert "2330" in mock_inputs["TWSE_OpenAPI"]
    assert mock_inputs["TWSE_OpenAPI"]["2330"]["price_semantics"] == "official_eod_reference_only"
    assert "official_eod_reference_only" in mock_inputs["TWSE_OpenAPI"]["2330"]["caveats"]

@pytest.mark.not_network
def test_missing_output_file_fails_closed():
    summary_path = FIXTURE_DIR / "run_summary_missing_output_file.json"
    report = build_adapter_report(summary_path)

    assert report["adapter_status"] == "partial_mapping"
    assert "Yahoo_Finance" in report["sources_blocked"]
    assert "TWSE_MIS" in report["sources_mapped"]
    assert "Yahoo_Finance" not in report["mock_inputs_preview"]

@pytest.mark.not_network
def test_malformed_run_summary_fails_closed():
    summary_path = FIXTURE_DIR / "run_summary_malformed.json"
    report = build_adapter_report(summary_path)

    assert report["adapter_status"] == "malformed_input"
    assert not report["mock_inputs_preview"]

@pytest.mark.not_network
def test_failed_targets_preserved():
    summary_path = FIXTURE_DIR / "run_summary_failed_source.json"
    report = build_adapter_report(summary_path)

    assert report["adapter_status"] == "partial_mapping"
    assert "2330" in report["failed_targets"].get("Yahoo_Finance", [])
    assert "8069" in report["failed_targets"].get("Yahoo_Finance", [])
    assert "8069" in report["unsupported_targets"].get("TWSE_MIS", [])

@pytest.mark.not_network
def test_snapshot_generator_integration_in_memory():
    """
    Test that the generated mock_inputs can be passed directly to build_snapshot
    in memory without crashing, and produces a valid output structure.
    """
    summary_path = FIXTURE_DIR / "run_summary_valid.json"
    mock_inputs = build_mock_inputs_from_live_probe_run(summary_path)

    # Minimal mocked targets_config based on TARGET_TAXONOMY.md
    mock_targets_config = {
        "twse_common_stock": {
            "symbols": {
                "standard": ["2330"]
            }
        },
        "tpex_common_stock": {
            "symbols": {
                "standard": ["8069"]
            }
        }
    }

    snapshot_output = build_snapshot(mock_targets_config, mock_inputs=mock_inputs)

    assert "generated_at_utc" in snapshot_output
    assert "symbols" in snapshot_output

    symbols = snapshot_output["symbols"]
    assert len(symbols) == 2

    tsmc_target = next(t for t in symbols if t["symbol"] == "2330")
    assert "TWSE_MIS" in tsmc_target["source_candidates"]
    assert "Yahoo_Finance" in tsmc_target["source_candidates"]

    eink_target = next(t for t in symbols if t["symbol"] == "8069")
    assert "Yahoo_Finance" in eink_target["source_candidates"]
