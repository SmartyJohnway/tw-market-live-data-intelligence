import os
import sys
import json
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from generate_ai_context_pack import (
    load_json,
    write_json,
    write_markdown,
    build_ai_context_pack,
    SOURCE_CONTRACT_BASELINE
)

@pytest.fixture
def mock_snapshot():
    return {
        "snapshot_version": "latest_market_snapshot_v1_draft",
        "generated_at_utc": "2026-06-21T09:44:55.792347+00:00",
        "generated_at_taipei": "2026-06-21T17:44:55.792347+00:00",
        "generation_mode": "bounded_watchlist_generation",
        "symbols": [
            {
                "symbol": "0050",
                "target_class": "twse_etf",
                "freshness_status": "realtime_candidate",
                "delay_status": "realtime_candidate"
            }
        ],
        "failed_symbols": [
            {
                "symbol": "2330",
                "target_class": "twse_common_stock",
                "failure_reason": "offline_mode",
                "source_attempts": [{"source_id": "TWSE_MIS", "error": "failed"}],
                "caveats": ["offline_mode"]
            }
        ],
        "failed_sources": [
            {
                "source_id": "TWSE_MIS",
                "affected_symbols": ["2330", "2317"]
            }
        ],
        "source_health": [
            {
                "source_id": "TWSE_MIS",
                "authority_level": "unofficial_frontend",
                "error_type": "offline_mode_no_local_input",
                "caveats": ["offline_mode"]
            }
        ]
    }

@pytest.fixture
def mock_observations():
    return {
        "observation_version": "watchlist_observations_v1",
        "observations": [
            {
                "symbol": "0050",
                "observation_type": "volume_active",
                "severity": "info"
            }
        ],
        "failed_observations": [
            {
                "symbol": "2330",
                "observation_type": "source_failed",
                "severity": "failed"
            }
        ]
    }

def test_missing_input_file_fails_clearly(tmp_path):
    with pytest.raises(FileNotFoundError, match="Required input file not found"):
        load_json(str(tmp_path / "missing.json"))

def test_json_output_has_required_top_level_keys(mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)

    expected_keys = [
        "pack_version", "generated_at_utc", "generated_at_taipei", "generation_mode",
        "source_contract_baseline", "source_health_summary", "source_authority_summary",
        "target_support_summary", "latest_snapshot_ref", "latest_snapshot_summary",
        "watchlist_observations_ref", "watchlist_observation_summary", "failed_sources",
        "failed_targets", "freshness_and_delay_summary", "ai_may_say", "ai_must_not_claim",
        "mandatory_caveats", "prohibited_interpretations", "next_actions"
    ]

    for key in expected_keys:
        assert key in pack

def test_source_contract_baseline_includes_all_canonical_sources(mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)
    scb = pack["source_contract_baseline"]

    expected_sources = ["TWSE_MIS", "Yahoo_Finance", "TWSE_OpenAPI", "TPEx_OpenAPI", "FinMind", "Fugle", "Fubon"]
    for source in expected_sources:
        assert source in scb["canonical_sources"]

def test_usable_live_sources_excludes_eod_and_broker_sources(mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)
    sas = pack["source_authority_summary"]

    assert "TWSE_OpenAPI" not in sas["usable_live_sources"]
    assert "TPEx_OpenAPI" not in sas["usable_live_sources"]
    assert "Fugle" not in sas["usable_live_sources"]
    assert "Fubon" not in sas["usable_live_sources"]

def test_target_support_summary_bounded_and_non_full_market(mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)
    tss = pack["target_support_summary"]

    assert tss["bounded_watchlist_only"] is True
    assert tss["full_market_coverage"] is False
    assert "twse_etf" in tss["target_classes_observed"]
    assert "twse_common_stock" in tss["target_classes_failed"]
    assert "twse_common_stock" in tss["target_classes_observed"]
    assert "target_classes_include_failed_bounded_watchlist_targets" in tss["target_support_caveats"]

def test_latest_snapshot_summary_preserves_failed_symbol_count(mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)
    lss = pack["latest_snapshot_summary"]

    assert lss["failed_symbol_count"] == 1

def test_watchlist_observation_summary_preserves_failed_observation_count(mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)
    wos = pack["watchlist_observation_summary"]

    assert wos["failed_observations_count"] == 1

def test_watchlist_observation_summary_preserves_failed_observation_count(mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)
    wos = pack["watchlist_observation_summary"]

    assert wos["failed_observations_count"] == 1
    assert wos["observations_count"] == 1
    assert wos["observation_type_counts"].get("source_failed") == 1
    assert wos["observation_type_counts"].get("volume_active") == 1
    assert wos["severity_counts"].get("failed") == 1
    assert wos["severity_counts"].get("info") == 1
    assert "source_failed" in wos["categories_present"]
    assert "volume_active" in wos["categories_present"]

def test_failed_sources_and_targets_preserved(mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)

    fs = pack["failed_sources"]
    assert len(fs) == 1
    assert fs[0]["source_id"] == "TWSE_MIS"
    assert fs[0]["affected_symbol_count"] == 2  # Pulled from failed_sources in snapshot

    ft = pack["failed_targets"]
    assert len(ft) == 1
    assert ft[0]["symbol"] == "2330"
    assert len(ft[0]["source_attempts"]) == 1

def test_freshness_and_delay_summary_handles_empty_successful_symbols_conservatively(mock_snapshot, mock_observations):
    # Empty symbols to test caveat path
    mock_snapshot["symbols"] = []

    pack = build_ai_context_pack(mock_snapshot, mock_observations)
    fds = pack["freshness_and_delay_summary"]

    assert "latest_snapshot_contains_no_successful_symbols" in fds["summary_caveats"]
    assert fds["unknown_freshness_count"] == 1
    assert fds["freshness_status_counts"].get("unknown") == 1
    assert fds["delay_status_counts"].get("unknown") == 1

def test_freshness_and_delay_summary_counts_successful_symbols(mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)
    fds = pack["freshness_and_delay_summary"]

    assert fds["freshness_status_counts"].get("realtime_candidate") == 1
    assert fds["delay_status_counts"].get("realtime_candidate") == 1
    assert fds["live_candidate_count"] == 1

def test_ai_may_say_and_must_not_claim_exist_and_non_empty(mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)

    assert len(pack["ai_may_say"]) > 0
    assert len(pack["ai_must_not_claim"]) > 0

def test_markdown_output_generation_and_caveats(tmp_path, mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)
    md_path = tmp_path / "ai_context_pack.md"

    write_markdown(pack, str(md_path))

    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")

    assert "## Mandatory Caveats" in content
    assert "bounded_watchlist_only" in content
    assert "observations_are_not_signals" in content

def test_prohibited_trading_vocabulary_absent_outside_policy_sections(tmp_path, mock_snapshot, mock_observations):
    pack = build_ai_context_pack(mock_snapshot, mock_observations)
    md_path = tmp_path / "ai_context_pack.md"
    write_markdown(pack, str(md_path))

    content = md_path.read_text(encoding="utf-8")

    # Split content by the Prohibited Interpretations section to only check areas before it
    # Note: Prohibited interpretations is not output in markdown by default but the arrays
    # are written in JSON. For the markdown, we check that bad vocabulary is constrained.
    # Because my generate script does not output "Prohibited Interpretations" to Markdown,
    # we just need to ensure no raw bad words appear outside of AI Must Not Claim.

    # Verify no execution signals were generated in summaries
    assert "strong sell signal" not in content
    assert "execute a trade" not in content
