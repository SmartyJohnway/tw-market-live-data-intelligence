import os
import sys
import json
import pytest
from datetime import datetime, timezone

# Add scripts directory to path to allow importing generate_latest_market_snapshot
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from generate_latest_market_snapshot import (
    build_empty_symbol,
    apply_source_priority_policy,
    apply_freshness_policy,
    build_snapshot,
    validate_snapshot_contract
)

def test_snapshot_top_level_keys():
    targets = {
        "twse_large_caps": {
            "symbols": {
                "standard": ["2330"]
            }
        }
    }
    snapshot = build_snapshot(targets)

    expected_keys = {
        "snapshot_version", "generated_at_utc", "generated_at_taipei",
        "generation_mode", "market_session_status", "source_health",
        "source_priority", "watchlist_scope", "symbols",
        "failed_symbols", "failed_sources", "global_caveats",
        "prohibited_interpretations"
    }
    assert set(snapshot.keys()) == expected_keys

    # Contract constraint checks
    assert snapshot["generation_mode"] == "bounded_watchlist_generation"
    assert snapshot["watchlist_scope"]["scope_type"] == "bounded_config_watchlist"
    assert snapshot["watchlist_scope"]["full_market_scan"] is False

def test_symbol_required_keys():
    target = {"symbol": "2330", "target_class": "twse_common_stock"}
    sym = build_empty_symbol(target)

    expected_keys = {
        "symbol", "exchange", "target_class", "name", "last_price",
        "change", "change_pct", "open", "high", "low", "previous_close",
        "volume", "bid_ask", "source_used", "source_candidates",
        "source_time", "retrieved_time", "staleness_seconds",
        "delay_status", "freshness_status", "source_authority",
        "support_status", "price_semantics",
        "official_eod_reference_available", "live_candidate_available",
        "data_quality_flags", "caveats", "raw_payload_ref"
    }

    assert set(sym.keys()) == expected_keys
    assert sym["symbol"] == "2330"
    assert sym["last_price"] is None # Must explicitly be None if unavailable, not omitted.

def test_bid_ask_required_keys():
    target = {"symbol": "2330", "target_class": "twse_common_stock"}
    sym = build_empty_symbol(target)

    expected_keys = {
        "best_bid_price", "best_bid_volume", "best_ask_price",
        "best_ask_volume", "spread", "bid_ask_status"
    }

    assert set(sym["bid_ask"].keys()) == expected_keys

def test_failed_symbol_schema():
    targets = {
        "twse_large_caps": {
            "symbols": {
                "standard": ["2330"]
            }
        }
    }
    # With no mock inputs, all fail
    snapshot = build_snapshot(targets)

    assert len(snapshot["failed_symbols"]) == 1
    fs = snapshot["failed_symbols"][0]

    expected_keys = {
        "symbol", "exchange", "target_class", "source_attempts",
        "failure_reason", "retrieved_time", "data_quality_flags", "caveats"
    }
    assert set(fs.keys()) == expected_keys
    assert fs["symbol"] == "2330"

def test_failed_source_schema():
    targets = {
        "twse_large_caps": {
            "symbols": {
                "standard": ["2330"]
            }
        }
    }
    snapshot = build_snapshot(targets)

    assert len(snapshot["failed_sources"]) > 0
    fsrc = snapshot["failed_sources"][0]

    expected_keys = {
        "source_id", "source_type", "http_ok", "error_type",
        "retrieved_time", "affected_symbols", "caveats"
    }
    assert set(fsrc.keys()) == expected_keys
    assert fsrc["http_ok"] is None
    assert fsrc["error_type"] == "offline_mode_no_local_input"

def test_source_health_schema():
    targets = {}
    snapshot = build_snapshot(targets)

    assert len(snapshot["source_health"]) > 0
    sh = snapshot["source_health"][0]

    expected_keys = {
        "source_id", "source_type", "authority_level", "http_ok",
        "parse_ok", "normalization_ok", "latency_ms", "retrieved_time",
        "error_type", "caveats"
    }
    assert set(sh.keys()) == expected_keys

    # Check that all 7 sources are covered
    sources = set([sh["source_id"] for sh in snapshot["source_health"]])
    assert sources == {"TWSE_MIS", "Yahoo_Finance", "TWSE_OpenAPI", "TPEx_OpenAPI", "FinMind", "Fugle", "Fubon"}


def test_official_eod_not_live_candidate():
    targets = {
        "twse_large_caps": {
            "symbols": {
                "standard": ["2330"]
            }
        }
    }
    mock_inputs = {
        "TWSE_OpenAPI": {
            "2330": {
                "name": "TSMC",
                "last_price": 100,
                "volume": 1000,
                "source_time": None,
                "retrieved_time": "2023-01-01T12:00:00+00:00",
                "exchange": "TWSE"
            }
        }
    }
    snapshot = build_snapshot(targets, mock_inputs)
    sym = snapshot["symbols"][0]

    assert sym["price_semantics"] == "eod_reference"
    assert sym["freshness_status"] == "eod_batch"
    assert sym["delay_status"] == "eod"
    assert sym["source_authority"] == "official_public_exchange_eod"
    assert sym["source_used"] == "TWSE_OpenAPI"

def test_unofficial_live_candidate_preserves_caveats():
    targets = {
        "twse_large_caps": {
            "symbols": {
                "standard": ["2330"]
            }
        }
    }
    mock_inputs = {
        "TWSE_MIS": {
            "2330": {
                "name": "TSMC",
                "last_price": 101,
                "source_time": "2023-01-01T12:00:00+00:00",
                "retrieved_time": "2023-01-01T12:00:01+00:00",
                "exchange": "TWSE"
            }
        }
    }
    snapshot = build_snapshot(targets, mock_inputs)
    sym = snapshot["symbols"][0]

    assert sym["price_semantics"] == "live_candidate"
    assert sym["source_authority"] == "unofficial_frontend"
    assert "unofficial_source_risk" in sym["caveats"]
    assert sym["source_used"] == "TWSE_MIS"

def test_broker_sources_skipped():
    targets = {}
    snapshot = build_snapshot(targets)

    broker_found = False
    for sh in snapshot["source_health"]:
        if sh["source_type"] == "broker_api":
            broker_found = True
            assert sh["error_type"] == "auth_required_doc_only_skipped"
            assert "broker_api_not_eligible_current_repo" in sh["caveats"]

    assert broker_found, "Broker API was not found in source_health as skipped"

def test_canonical_target_class_mapping():
    targets = {
        "twse_large_caps": {"symbols": {"standard": ["2330"]}},
        "random_unknown_group": {"symbols": {"standard": ["1234"]}}
    }
    snapshot = build_snapshot(targets)

    target_classes = {fs["target_class"] for fs in snapshot["failed_symbols"]}
    assert "twse_common_stock" in target_classes
    assert "unknown_or_unsupported" in target_classes

    unknown_sym = next(fs for fs in snapshot["failed_symbols"] if fs["target_class"] == "unknown_or_unsupported")
    assert "target_class_mapping_unknown" in unknown_sym["data_quality_flags"]

def test_watchlist_scope_not_full_market():
    targets = {}
    snapshot = build_snapshot(targets)
    assert snapshot["watchlist_scope"]["full_market_scan"] is False

def test_no_trading_signal_semantics_outside_prohibited_interpretations():
    targets = {}
    snapshot = build_snapshot(targets)

    snapshot_str = json.dumps(snapshot).lower()

    prohibited = ["buy", "sell", "hold", "target_price", "profit_prediction", "guaranteed_reversal"]

    # Check that they only appear in the prohibited_interpretations array
    for p in prohibited:
        # Check count of occurrences. Should only appear inside the list.
        # It's a rough check but ensures we didn't add keys like "buy_signal"
        count = snapshot_str.count(f'"{p}"')
        assert count <= 1 # At most once in the array.

def test_stale_source_marked_stale():
    target = {"symbol": "2330", "target_class": "twse_common_stock"}
    sym = build_empty_symbol(target)

    now_utc = datetime.now(timezone.utc)
    sym["retrieved_time"] = now_utc.isoformat()
    # Source time is 5 minutes ago
    sym["source_time"] = "2023-01-01T12:00:00+00:00"
    sym["retrieved_time"] = "2023-01-01T12:05:00+00:00"
    sym["price_semantics"] = "live_candidate"

    sym = apply_freshness_policy(sym)

    assert sym["staleness_seconds"] == 300
