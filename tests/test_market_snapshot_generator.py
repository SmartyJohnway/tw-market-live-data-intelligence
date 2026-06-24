import pytest
import os
import json
from datetime import datetime, timezone
import sys

# Ensure scripts can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
from generate_latest_market_snapshot import build_snapshot
from tests.helpers.mock_fixtures import build_mock_inputs_from_fixtures

# Mock targets config for offline testing
MOCK_TARGETS_CONFIG = {
  "twse_large_caps": {
    "description": "TWSE Large Cap Equities",
    "symbols": {
      "standard": ["2330", "1435"],
      "yahoo": ["2330.TW", "1435.TW"],
      "twse_mis": ["tse_2330.tw", "tse_1435.tw"]
    }
  },
  "tpex_stocks": {
    "description": "TPEx Mid/Small Cap Equities",
    "symbols": {
      "standard": ["8069", "5347"],
      "yahoo": ["8069.TWO", "5347.TWO"],
      "twse_mis": ["otc_8069.tw", "otc_5347.tw"]
    }
  },
  "indices": {
    "description": "Market Indices",
    "symbols": {
      "standard": ["TAIEX"],
      "yahoo": ["^TWII"],
      "twse_mis": ["tse_t00.tw"]
    }
  }
}

@pytest.mark.offline
def test_mock_fixtures_can_be_loaded():
    mock_inputs = build_mock_inputs_from_fixtures()
    assert "TWSE_MIS" in mock_inputs
    assert "2330" in mock_inputs["TWSE_MIS"]
    assert mock_inputs["TWSE_MIS"]["2330"]["last_price"] == 1015.0

    assert "TWSE_OpenAPI" in mock_inputs
    assert "2330" in mock_inputs["TWSE_OpenAPI"]
    assert mock_inputs["TWSE_OpenAPI"]["2330"]["close"] == 1005.0

    assert "TPEx_OpenAPI" in mock_inputs
    assert "8069" in mock_inputs["TPEx_OpenAPI"]
    assert mock_inputs["TPEx_OpenAPI"]["8069"]["close"] == 250.0

    assert "Yahoo_Finance" in mock_inputs
    assert "2330" in mock_inputs["Yahoo_Finance"]
    assert mock_inputs["Yahoo_Finance"]["2330"]["regular_market_price"] == 1015.0

@pytest.mark.offline
def test_parsed_labeling():
    mock_inputs = build_mock_inputs_from_fixtures()

    # 6. Parsed TWSE_MIS data is labeled correctly (Note: generator determines price_semantics for TWSE_MIS as live_candidate)
    # The source label in snapshot is built in generator based on raw fields, let's verify generator output later
    # The raw parsed TWSE_MIS doesn't have source_authority field, it's mapped in apply_source_priority_policy.

    # 7. Parsed TWSE_OpenAPI / TPEx_OpenAPI
    twse_open = mock_inputs["TWSE_OpenAPI"]["2330"]
    assert twse_open["source_type"] == "official_openapi"
    assert twse_open["freshness_status"] == "eod_batch"

    # 8. Parsed Yahoo
    yahoo = mock_inputs["Yahoo_Finance"]["2330"]
    assert yahoo["source_type"] == "unofficial_api"

@pytest.mark.offline
def test_build_snapshot_with_mock_success():
    retrieved_at_utc_dt = datetime.now(timezone.utc)
    mock_inputs = build_mock_inputs_from_fixtures(retrieved_at_utc_dt)
    snapshot = build_snapshot(MOCK_TARGETS_CONFIG, mock_inputs=mock_inputs)

    # 9. Mock inputs can produce at least one non-empty symbols entry
    assert len(snapshot["symbols"]) > 0

    symbols_map = {s["symbol"]: s for s in snapshot["symbols"]}
    assert "2330" in symbols_map

    sym_2330 = symbols_map["2330"]

    # Check that TWSE_MIS took priority for 2330 since it's the highest live candidate
    assert sym_2330["source_used"] == "TWSE_MIS"
    assert sym_2330["source_authority"] == "unofficial_frontend"
    assert sym_2330["price_semantics"] == "live_candidate" or sym_2330["price_semantics"] == "stale_quote" # It will be stale if staleness > 300s. Since the mock uses a fixed source time and current retrieved time, it will be stale.

    # Check TPEx OpenAPI for 8069 (TPEx OpenAPI is eod_reference)
    # Note: 8069 has no TWSE_MIS or Yahoo in our mock fixture output, only TPEx OpenAPI
    assert "8069" in symbols_map
    sym_8069 = symbols_map["8069"]
    assert sym_8069["source_used"] == "TPEx_OpenAPI"
    assert sym_8069["source_authority"] == "official_public_exchange_eod"
    assert sym_8069["price_semantics"] == "eod_reference"

    # 11. Generated mock snapshot has: watchlist_scope.full_market_scan = false
    assert snapshot["watchlist_scope"]["full_market_scan"] is False

    # 12. Generated mock context does not contain investment semantics
    prohibited = ["buy", "sell", "hold", "target_price", "profit_prediction", "guaranteed_reversal", "automated_trade_signal", "trading_signal"]
    for p in prohibited:
        assert p in snapshot["prohibited_interpretations"]

    # Verify we don't have investment keys in the top level
    snapshot_str = json.dumps(snapshot).lower()
    assert "recommendation" not in snapshot_str

@pytest.mark.offline
def test_build_snapshot_with_mock_empty():
    # 10. Mock inputs preserve failed-symbol handling for unsupported or missing targets.
    empty_mock_inputs = {
        "TWSE_MIS": {},
        "TWSE_OpenAPI": {},
        "TPEx_OpenAPI": {},
        "Yahoo_Finance": {}
    }
    snapshot = build_snapshot(MOCK_TARGETS_CONFIG, mock_inputs=empty_mock_inputs)

    # Everything should fail
    assert len(snapshot["symbols"]) == 0
    assert len(snapshot["failed_symbols"]) == 5 # 2330, 1435, 8069, 5347, TAIEX

    failed_sym_2330 = next(s for s in snapshot["failed_symbols"] if s["symbol"] == "2330")
    assert failed_sym_2330["failure_reason"] == "all_sources_failed"
    assert "offline_mode_no_data" in failed_sym_2330["data_quality_flags"]

@pytest.mark.offline
def test_build_snapshot_artifact_compatibility():
    # 1. ai_context_pack.json / market_snapshot mock shape includes expected top-level groups
    mock_inputs = build_mock_inputs_from_fixtures()
    snapshot = build_snapshot(MOCK_TARGETS_CONFIG, mock_inputs=mock_inputs)

    assert "snapshot_version" in snapshot
    assert "source_health" in snapshot
    assert "watchlist_scope" in snapshot
    assert "symbols" in snapshot
    assert "failed_symbols" in snapshot
    assert "failed_sources" in snapshot

    # 2. failed sources / failed targets remain arrays
    assert isinstance(snapshot["failed_sources"], list)
    assert isinstance(snapshot["failed_symbols"], list)

    # 3. source health summary remains present
    assert isinstance(snapshot["source_health"], list)

    # 4. mandatory caveats remain present
    assert "global_caveats" in snapshot
    assert len(snapshot["global_caveats"]) > 0

    # 5. AI must-not-claim remains present
    assert "prohibited_interpretations" in snapshot
    assert len(snapshot["prohibited_interpretations"]) > 0

    # 6. bounded watchlist / full_market_coverage=false remains present
    assert snapshot["watchlist_scope"]["full_market_scan"] is False
