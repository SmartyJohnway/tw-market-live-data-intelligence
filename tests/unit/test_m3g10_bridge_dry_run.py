from pathlib import Path

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scripts.run_m3g10_bridge_dry_run import build_m3g10_dry_run_report

FIXTURE_DIR = Path("tests/fixtures/m3g_live_probe_evidence")


def _targets(symbols):
    return {
        "twse_large_caps": {"symbols": {"standard": symbols}},
    }


@pytest.mark.not_network
def test_m3g10_valid_fixture_builds_full_pipeline_in_memory():
    report = build_m3g10_dry_run_report(FIXTURE_DIR / "run_summary_valid.json", _targets(["2330", "8069"]))

    assert report["dry_run_status"] in {"pass", "partial"}
    assert report["network_calls_executed"] is False
    assert report["production_writes_executed"] is False
    assert report["frontend_writes_executed"] is False
    assert report["artifact_status"] == {
        "latest_market_snapshot": "built_in_memory",
        "watchlist_observations": "built_in_memory",
        "ai_context_pack": "built_in_memory",
        "chatgpt_briefing": "rendered_in_memory",
    }
    assert report["artifact_metrics"]["snapshot_symbols"] >= 1
    assert report["artifact_metrics"]["observations"] >= 1
    assert report["artifact_metrics"]["briefing_characters"] > 0
    assert report["semantic_checks"]["twse_mis_caveats_preserved"] is True
    assert report["semantic_checks"]["yahoo_caveats_preserved"] is True
    assert report["semantic_checks"]["failed_targets_preserved"] is True
    assert report["semantic_checks"]["unsupported_targets_preserved"] is True


@pytest.mark.not_network
def test_m3g10_identity_mismatch_fixture_blocks_source_without_writes():
    report = build_m3g10_dry_run_report(FIXTURE_DIR / "run_summary_identity_mismatch.json", _targets(["2330", "8069"]))

    assert report["dry_run_status"] == "blocked"
    assert report["adapter_status"] == "identity_mismatch_blocked"
    assert "Yahoo_Finance" in report["sources_blocked"]
    assert report["network_calls_executed"] is False
    assert report["production_writes_executed"] is False
    assert report["semantic_checks"]["identity_mismatch_blocked"] is True


@pytest.mark.not_network
def test_m3g10_official_eod_fixture_preserves_eod_semantics():
    report = build_m3g10_dry_run_report(FIXTURE_DIR / "run_summary_eod_openapi.json", _targets(["2330"]))

    assert report["dry_run_status"] == "pass"
    semantics = report["semantic_checks"]["symbol_semantics"]["2330"]
    assert semantics["source_used"] == "TWSE_OpenAPI"
    assert semantics["price_semantics"] == "eod_reference"
    assert semantics["freshness_status"] == "eod_batch"
    assert semantics["delay_status"] == "eod"
    assert report["semantic_checks"]["official_openapi_eod_only"] is True
