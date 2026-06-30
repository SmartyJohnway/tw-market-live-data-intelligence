from pathlib import Path

from scripts.observation_contract import (
    FAILURE_SCHEMA_VERSION,
    OBSERVATION_SCHEMA_VERSION,
    normalize_failure,
    normalize_freshness,
    normalize_observation,
    normalize_timestamp,
)
from scripts.m5k_common import _parse_mis_item, _parse_taifex_tx_item


def test_unified_observation_contract_fields_are_source_neutral():
    obs = normalize_observation(symbol="2330", source="TWSE_MIS", adapter_id="twse_mis_equity_etf_quote", status="ok", retrieved_at_utc="2026-06-30T01:00:00Z")
    assert obs["schema_version"] == OBSERVATION_SCHEMA_VERSION
    for key in ["source", "adapter_id", "freshness_assessment", "delay_status", "contract", "reference_only", "price_like_value", "caveats"]:
        assert key in obs


def test_unified_failure_contract_fields_are_source_neutral():
    failure = normalize_failure(symbol="TX", source="TAIFEX", adapter_id="taifex_mis_tx_futures_quote", reason="timeout", retryable=True)
    assert failure["schema_version"] == FAILURE_SCHEMA_VERSION
    for key in ["source", "adapter_id", "status", "reason", "stage", "investigation_summary", "retryable", "caveats"]:
        assert key in failure


def test_shared_normalization_used_by_twse_mis_and_taifex():
    mis = _parse_mis_item({"z": "2460.0", "d": "20260630", "t": "09:31:15"}, {"symbol": "2330", "market": "twse", "instrument_type": "listed_equity"}, "2026-06-30T01:31:16Z")
    tx = _parse_taifex_tx_item({"CLastPrice": "22123", "CDate": "20260630", "CTime": "084500", "SymbolID": "TXF076-F", "DispEName": "TX076"}, {"symbol": "TX", "market": "taifex", "instrument_type": "futures"}, "2026-06-30T00:46:00Z")
    assert mis["schema_version"] == tx["schema_version"] == OBSERVATION_SCHEMA_VERSION
    assert mis["adapter_id"] == "twse_mis_equity_etf_quote"
    assert tx["adapter_id"] == "taifex_mis_tx_futures_quote"
    assert tx["contract_month"] == "202607"


def test_timestamp_and_freshness_helpers_are_single_contract():
    ts = normalize_timestamp("20260630 09:31:15", retrieved_at_utc="2026-06-30T01:31:16Z")
    assert ts["source_timestamp"] == "2026-06-30T09:31:15Z"
    assert normalize_freshness(1) == "fresh"
    assert normalize_freshness(None) == "unknown"


def test_readme_archive_and_product_links_exist():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Project Overview" in readme
    assert "docs/archive/readme/README_20260630_M5LRM_ARCHITECTURE_CONVERGENCE.md" in readme
    archive = Path("docs/archive/readme/README_20260630_M5LRM_ARCHITECTURE_CONVERGENCE.md").read_text(encoding="utf-8")
    assert "archive timestamp:" in archive
    assert "originating commit:" in archive


def test_architecture_docs_reference_single_contracts_and_no_competing_semantics():
    overview = Path("docs/architecture/architecture_overview.md").read_text(encoding="utf-8")
    level2 = Path("docs/architecture/level2_live_observation.md").read_text(encoding="utf-8")
    adapter = Path("docs/architecture/source_adapter_architecture.md").read_text(encoding="utf-8")
    assert "one observation model or one failure model" in overview
    assert "m5_live_observation.normalized.v1" in level2
    assert "scripts/observation_contract.py" in adapter


def test_forbidden_product_paths_not_written_by_m5lrm():
    changed = set(__import__("subprocess").check_output(["git", "diff", "--name-only"], text=True).splitlines())
    assert not any(path.startswith("frontend/public/") for path in changed)
    assert not any(path.startswith("research/generated/") for path in changed)
    assert not any(path.startswith("production/prod/") for path in changed)
