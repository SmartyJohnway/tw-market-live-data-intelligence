import json
import os
import argparse
from datetime import datetime, timezone, timedelta

def get_abs_path(relative_path):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)

def load_targets():
    targets_path = get_abs_path("config/market_targets.json")
    try:
        with open(targets_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load targets from {targets_path}. Error: {e}")
        return {}

def extract_all_targets(targets_config):
    all_targets = []
    for class_name, group_data in targets_config.items():
        standard_symbols = group_data.get("symbols", {}).get("standard", [])
        for sym in standard_symbols:
            all_targets.append({
                "symbol": sym,
                "target_class": class_name,
            })
    return all_targets

def build_empty_symbol(target):
    return {
        "symbol": target["symbol"],
        "exchange": "unknown", # will be filled if source resolves
        "target_class": target["target_class"],
        "name": None,
        "last_price": None,
        "change": None,
        "change_pct": None,
        "open": None,
        "high": None,
        "low": None,
        "previous_close": None,
        "volume": None,
        "bid_ask": {
            "best_bid_price": None,
            "best_bid_volume": None,
            "best_ask_price": None,
            "best_ask_volume": None,
            "spread": None,
            "bid_ask_status": "unknown"
        },
        "source_used": None,
        "source_candidates": [],
        "source_time": None,
        "retrieved_time": None,
        "staleness_seconds": None,
        "delay_status": "unknown",
        "freshness_status": "unknown",
        "source_authority": "unknown",
        "support_status": "unknown",
        "price_semantics": "unknown",
        "official_eod_reference_available": False,
        "live_candidate_available": False,
        "data_quality_flags": [],
        "caveats": [],
        "raw_payload_ref": None
    }

def apply_source_priority_policy(symbol_obj, source_data):
    # This function would take the available data for a symbol from multiple sources
    # and decide which to use based on LATEST_MARKET_SNAPSHOT_SOURCE_PRIORITY_AND_FRESHNESS_POLICY.md

    # If no data is available from any source:
    if not source_data:
        symbol_obj["data_quality_flags"].append("no_data_available")
        symbol_obj["caveats"].append("all_sources_failed")
        return symbol_obj

    # Implement mock evaluation for now
    return symbol_obj

def apply_freshness_policy(symbol_obj):
    # Calculate staleness_seconds
    if symbol_obj["source_time"] and symbol_obj["retrieved_time"]:
        try:
            source_dt = datetime.fromisoformat(symbol_obj["source_time"].replace('Z', '+00:00'))
            retrieved_dt = datetime.fromisoformat(symbol_obj["retrieved_time"].replace('Z', '+00:00'))
            staleness = (retrieved_dt - source_dt).total_seconds()
            symbol_obj["staleness_seconds"] = int(staleness)
        except ValueError:
            symbol_obj["staleness_seconds"] = None
            symbol_obj["data_quality_flags"].append("source_time_unavailable")
    else:
        symbol_obj["staleness_seconds"] = None
        if symbol_obj["price_semantics"] != "eod_reference":
             symbol_obj["data_quality_flags"].append("source_time_unavailable")

    # Enforce EOD restrictions
    if symbol_obj["price_semantics"] == "eod_reference":
        symbol_obj["freshness_status"] = "eod_batch"
        symbol_obj["delay_status"] = "eod"

    return symbol_obj

def build_snapshot(targets_config, mock_inputs=None):
    now_utc = datetime.now(timezone.utc)
    now_taipei = now_utc + timedelta(hours=8)

    snapshot = {
        "snapshot_version": "latest_market_snapshot_v1_draft",
        "generated_at_utc": now_utc.isoformat(),
        "generated_at_taipei": now_taipei.isoformat(),
        "generation_mode": "bounded_watchlist_generation",
        "market_session_status": {
            "status": "unknown",
            "as_of_taipei": None,
            "source": "generator_default",
            "evidence": [],
            "caveats": [
                "session_detection_not_implemented_in_m3a_02"
            ]
        },
        "source_health": [],
        "source_priority": [
            "TWSE_MIS (live_candidate)",
            "Yahoo Finance (third_party_context)",
            "TWSE_OpenAPI (eod_reference)",
            "TPEx_OpenAPI (eod_reference)"
        ],
        "watchlist_scope": {
            "scope_type": "bounded_config_watchlist",
            "target_count": 0,
            "target_source": "config/market_targets.json",
            "full_market_scan": False
        },
        "symbols": [],
        "failed_symbols": [],
        "failed_sources": [],
        "global_caveats": [
            "This snapshot is not a live execution feed.",
            "Do not use for automated trading."
        ],
        "prohibited_interpretations": [
            "buy", "sell", "hold", "target_price", "profit_prediction",
            "guaranteed_reversal", "automated_trade_signal", "trading_signal"
        ]
    }

    all_targets = extract_all_targets(targets_config)
    snapshot["watchlist_scope"]["target_count"] = len(all_targets)

    # Process inputs (mocked offline inputs for M3A-02)
    # If no inputs, all sources fail

    if mock_inputs:
        # Evaluate sources and targets based on inputs
        # For this test, we just pass the mock inputs if provided appropriately
        pass
    else:
        # Default Offline mode: All sources fail, all symbols fail
        # Record failed sources
        snapshot["failed_sources"] = [
            {
                "source_id": "TWSE_MIS",
                "source_type": "unofficial_frontend_endpoint",
                "http_ok": False,
                "error_type": "offline_mode_no_data",
                "retrieved_time": now_utc.isoformat(),
                "affected_symbols": [t["symbol"] for t in all_targets],
                "caveats": ["offline_mode"]
            },
            {
                "source_id": "Yahoo_Finance",
                "source_type": "third_party",
                "http_ok": False,
                "error_type": "offline_mode_no_data",
                "retrieved_time": now_utc.isoformat(),
                "affected_symbols": [t["symbol"] for t in all_targets],
                "caveats": ["offline_mode"]
            }
        ]

        # Add broker API skipped to source_health
        snapshot["source_health"].append({
            "source_id": "Fugle",
            "source_type": "broker_api",
            "authority_level": "broker_authenticated",
            "http_ok": None,
            "parse_ok": None,
            "normalization_ok": None,
            "latency_ms": None,
            "retrieved_time": None,
            "error_type": "auth_required_doc_only_skipped",
            "caveats": [
                "broker_api_not_eligible_current_repo",
                "auth_required",
                "doc_only"
            ]
        })

        snapshot["source_health"].extend([
            {
                "source_id": "TWSE_MIS",
                "source_type": "unofficial_frontend_endpoint",
                "authority_level": "unofficial_frontend",
                "http_ok": False,
                "parse_ok": False,
                "normalization_ok": False,
                "latency_ms": None,
                "retrieved_time": now_utc.isoformat(),
                "error_type": "offline_mode_no_data",
                "caveats": ["offline_mode"]
            }
        ])

        for target in all_targets:
            failed_sym = {
                "symbol": target["symbol"],
                "exchange": "unknown",
                "target_class": target["target_class"],
                "source_attempts": ["TWSE_MIS", "Yahoo_Finance", "TWSE_OpenAPI", "TPEx_OpenAPI"],
                "failure_reason": "all_sources_failed",
                "retrieved_time": now_utc.isoformat(),
                "data_quality_flags": ["offline_mode_no_data"],
                "caveats": ["offline_mode"]
            }
            snapshot["failed_symbols"].append(failed_sym)

    return snapshot

def validate_snapshot_contract(snapshot):
    # Very basic validation, actual validation is in tests
    assert "snapshot_version" in snapshot
    assert "symbols" in snapshot
    assert "failed_symbols" in snapshot
    assert "failed_sources" in snapshot
    assert snapshot["watchlist_scope"]["full_market_scan"] is False

def generate_snapshot():
    targets = load_targets()
    snapshot = build_snapshot(targets)
    validate_snapshot_contract(snapshot)

    out_dir = get_abs_path("research/generated")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "latest_market_snapshot.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"Generated snapshot at {out_path}")

if __name__ == "__main__":
    generate_snapshot()
