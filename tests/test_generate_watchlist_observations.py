import os
import sys
import pytest

# Append scripts path to sys.path to prevent ModuleNotFoundError
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from generate_watchlist_observations import (
    build_watchlist_observations,
    generate_symbol_observations,
    generate_failed_observations,
    NEAR_THRESHOLD_PCT
)

def test_generate_failed_observations():
    failed_sym = {
        "symbol": "2330",
        "failure_reason": "all_sources_failed"
    }
    obs = generate_failed_observations(failed_sym)
    assert len(obs) == 1
    assert obs[0]["observation_type"] == "source_failed"
    assert obs[0]["severity"] == "failed"
    assert obs[0]["evidence"]["failure_reason"] == "all_sources_failed"

def test_generate_symbol_observations_stale_and_eod():
    sym = {
        "symbol": "2330",
        "freshness_status": "stale",
        "price_semantics": "eod_reference",
        "staleness_seconds": 600
    }
    obs = generate_symbol_observations(sym)
    obs_types = [o["observation_type"] for o in obs]
    assert "source_stale" in obs_types
    assert "eod_reference_only" in obs_types
    assert "bid_ask_missing" in obs_types

def test_generate_symbol_observations_live_and_spread():
    sym = {
        "symbol": "2330",
        "price_semantics": "live_candidate",
        "bid_ask": {
            "best_bid_price": 100.0,
            "best_ask_price": 101.0
        }
    }
    obs = generate_symbol_observations(sym)
    obs_types = [o["observation_type"] for o in obs]
    assert "live_candidate_available" in obs_types
    assert "spread_available" in obs_types
    assert "bid_ask_missing" not in obs_types

def test_generate_symbol_observations_price_above_prev_close():
    sym = {
        "symbol": "2330",
        "last_price": 105.0,
        "previous_close": 100.0
    }
    obs = generate_symbol_observations(sym)
    obs_types = [o["observation_type"] for o in obs]
    assert "price_changed" in obs_types
    assert "above_previous_close" in obs_types
    assert "below_previous_close" not in obs_types

def test_generate_symbol_observations_price_below_prev_close():
    sym = {
        "symbol": "2330",
        "last_price": 95.0,
        "previous_close": 100.0
    }
    obs = generate_symbol_observations(sym)
    obs_types = [o["observation_type"] for o in obs]
    assert "price_changed" in obs_types
    assert "below_previous_close" in obs_types
    assert "above_previous_close" not in obs_types

def test_generate_symbol_observations_near_thresholds():
    sym = {
        "symbol": "2330",
        "last_price": 100.2, # Distance to open is 0.2%, which is <= 0.5%
        "open": 100.0,
        "high": 105.0,
        "low": 100.0
    }
    obs = generate_symbol_observations(sym)
    obs_types = [o["observation_type"] for o in obs]
    assert "near_open" in obs_types
    assert "near_low" in obs_types
    assert "near_high" not in obs_types # 105.0 vs 100.2 is ~4.5% distance

def test_generate_symbol_observations_volume_active():
    sym = {
        "symbol": "2330",
        "volume": 1000
    }
    obs = generate_symbol_observations(sym)
    obs_types = [o["observation_type"] for o in obs]
    assert "volume_active" in obs_types

def test_build_watchlist_observations_structure():
    mock_snapshot = {
        "watchlist_scope": {
            "target_count": 2
        },
        "symbols": [
            {
                "symbol": "2330",
                "last_price": 105.0,
                "previous_close": 100.0
            }
        ],
        "failed_symbols": [
            {
                "symbol": "1435",
                "failure_reason": "network_error"
            }
        ],
        "global_caveats": ["test_caveat"],
        "prohibited_interpretations": ["buy", "sell"]
    }

    artifact = build_watchlist_observations(mock_snapshot)

    assert artifact["observation_version"] == "watchlist_observations_v1"
    assert "generated_at_utc" in artifact
    assert "generated_at_taipei" in artifact
    assert artifact["watchlist_scope"]["target_count"] == 2
    assert artifact["watchlist_scope"]["full_market_scan"] is False
    assert len(artifact["observations"]) > 0
    assert len(artifact["failed_observations"]) == 1
    assert artifact["global_caveats"] == ["test_caveat"]
    assert artifact["prohibited_interpretations"] == ["buy", "sell"]
