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

def canonicalize_target_class(group_name: str, symbol: str) -> str:
    mapping = {
        "twse_large_caps": "twse_common_stock",
        "tpex_stocks": "tpex_common_stock",
        "etfs": "twse_etf",
        "thinly_traded": "twse_tdr",
        "indices": "twse_index",
        "futures": "taifex_index_future",
        "funds": "mutual_fund"
    }
    return mapping.get(group_name, "unknown_or_unsupported")


def extract_all_targets(targets_config):
    all_targets = []
    for group_name, group_data in targets_config.items():
        standard_symbols = group_data.get("symbols", {}).get("standard", [])
        for sym in standard_symbols:
            all_targets.append({
                "symbol": sym,
                "target_class": canonicalize_target_class(group_name, sym),
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
    # Determine source order based on LATEST_MARKET_SNAPSHOT_SOURCE_PRIORITY_AND_FRESHNESS_POLICY.md
    priority_order = ["TWSE_MIS", "Yahoo_Finance", "TWSE_OpenAPI", "TPEx_OpenAPI"]

    selected_source = None
    for src in priority_order:
        if src in source_data:
            selected_source = src
            break

    if not selected_source:
        symbol_obj["data_quality_flags"].append("no_data_available")
        symbol_obj["caveats"].append("all_sources_failed")
        return symbol_obj

    data = source_data[selected_source]

    # Populate fields
    symbol_obj["source_used"] = selected_source
    symbol_obj["source_candidates"] = list(source_data.keys())

    for key in ["name", "last_price", "change", "change_pct", "open", "high", "low", "previous_close", "volume", "source_time", "retrieved_time", "price_semantics", "freshness_status", "delay_status", "staleness_seconds", "exchange"]:
        if key in data:
            symbol_obj[key] = data[key]

    if "bid_ask" in data:
        symbol_obj["bid_ask"].update(data["bid_ask"])

    # Determine authority and semantics
    if selected_source in ["TWSE_OpenAPI", "TPEx_OpenAPI"]:
        symbol_obj["source_authority"] = "official_public_exchange_eod"
        symbol_obj["price_semantics"] = "eod_reference"
        symbol_obj["official_eod_reference_available"] = True
    elif selected_source == "TWSE_MIS":
        symbol_obj["source_authority"] = "unofficial_frontend"
        if symbol_obj.get("price_semantics") in [None, "unknown"]:
            symbol_obj["price_semantics"] = "live_candidate"
        symbol_obj["live_candidate_available"] = symbol_obj.get("price_semantics") in ["live_candidate", "delayed_quote", "stale_quote"]
        symbol_obj["caveats"].append("unofficial_source_risk")
    elif selected_source == "Yahoo_Finance":
        symbol_obj["source_authority"] = "third_party"
        if symbol_obj.get("price_semantics") in [None, "unknown"]:
            symbol_obj["price_semantics"] = "live_candidate"
        symbol_obj["live_candidate_available"] = symbol_obj.get("price_semantics") in ["live_candidate", "delayed_quote", "stale_quote"]
        symbol_obj["caveats"].append("third_party_coverage_caveats")

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
        if symbol_obj["price_semantics"] != "eod_reference" and symbol_obj["price_semantics"] != "unknown":
             symbol_obj["data_quality_flags"].append("source_time_unavailable")

    # Enforce EOD restrictions
    if symbol_obj["price_semantics"] == "eod_reference":
        symbol_obj["freshness_status"] = "eod_batch"
        symbol_obj["delay_status"] = "eod"
    elif symbol_obj["price_semantics"] in ["live_candidate", "delayed_quote", "stale_quote"]:
        # Mark as stale if staleness is more than 300 seconds (5 minutes).
        # Otherwise preserve explicit delayed semantics supplied by the source adapter.
        if symbol_obj["staleness_seconds"] is not None and symbol_obj["staleness_seconds"] > 300:
            symbol_obj["freshness_status"] = "stale"
            symbol_obj["delay_status"] = "stale"
            symbol_obj["price_semantics"] = "stale_quote"
        elif symbol_obj["price_semantics"] == "delayed_quote" or symbol_obj.get("delay_status") == "delayed":
            symbol_obj["freshness_status"] = "delayed"
            symbol_obj["delay_status"] = "delayed"
            symbol_obj["price_semantics"] = "delayed_quote"
        elif symbol_obj["price_semantics"] == "stale_quote" or symbol_obj.get("delay_status") == "stale":
            symbol_obj["freshness_status"] = "stale"
            symbol_obj["delay_status"] = "stale"
            symbol_obj["price_semantics"] = "stale_quote"
        else:
            symbol_obj["freshness_status"] = "realtime_candidate"
            symbol_obj["delay_status"] = "realtime_candidate"

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
            "Yahoo_Finance (third_party_context)",
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

    all_canonical_sources = ["TWSE_MIS", "Yahoo_Finance", "TWSE_OpenAPI", "TPEx_OpenAPI", "FinMind", "Fugle", "Fubon"]

    # 1. Build initial source health entries
    for src in all_canonical_sources:
        if src in ["Fugle", "Fubon"]:
            snapshot["source_health"].append({
                "source_id": src,
                "source_type": "broker_api",
                "authority_level": "broker_authenticated",
                "http_ok": None,
                "parse_ok": None,
                "normalization_ok": None,
                "latency_ms": None,
                "retrieved_time": None,
                "error_type": "auth_required_doc_only_skipped",
                "caveats": ["broker_api_not_eligible_current_repo", "auth_required", "doc_only"]
            })
        elif src in ["TWSE_OpenAPI", "TPEx_OpenAPI"]:
            snapshot["source_health"].append({
                "source_id": src,
                "source_type": "official_openapi",
                "authority_level": "official_public_exchange_eod",
                "http_ok": None,
                "parse_ok": None,
                "normalization_ok": None,
                "latency_ms": None,
                "retrieved_time": None,
                "error_type": "not_attempted_offline_default",
                "caveats": ["offline_mode", "official_eod_reference_only", "not_live_intraday"]
            })
        elif src == "TWSE_MIS":
            snapshot["source_health"].append({
                "source_id": src,
                "source_type": "unofficial_frontend_endpoint",
                "authority_level": "unofficial_frontend",
                "http_ok": None,
                "parse_ok": None,
                "normalization_ok": None,
                "latency_ms": None,
                "retrieved_time": None,
                "error_type": "not_attempted_offline_default",
                "caveats": ["offline_mode", "unofficial_source_risk", "no_live_network_default"]
            })
        elif src == "Yahoo_Finance":
            snapshot["source_health"].append({
                "source_id": src,
                "source_type": "third_party_api",
                "authority_level": "third_party",
                "http_ok": None,
                "parse_ok": None,
                "normalization_ok": None,
                "latency_ms": None,
                "retrieved_time": None,
                "error_type": "not_attempted_offline_default",
                "caveats": ["offline_mode", "third_party_coverage_caveats"]
            })
        elif src == "FinMind":
            snapshot["source_health"].append({
                "source_id": src,
                "source_type": "third_party_api",
                "authority_level": "third_party",
                "http_ok": None,
                "parse_ok": None,
                "normalization_ok": None,
                "latency_ms": None,
                "retrieved_time": None,
                "error_type": "not_attempted_offline_default",
                "caveats": ["offline_mode", "historical_or_eod_candidate_with_auth_caveats"]
            })

    # 2. Process targets using mock inputs
    for target in all_targets:
        sym_obj = build_empty_symbol(target)
        if target["target_class"] == "unknown_or_unsupported":
             sym_obj["data_quality_flags"].append("target_class_mapping_unknown")

        source_data_for_sym = {}
        if mock_inputs:
            for src in all_canonical_sources:
                if src in mock_inputs and target["symbol"] in mock_inputs[src]:
                    source_data_for_sym[src] = mock_inputs[src][target["symbol"]]

        sym_obj = apply_source_priority_policy(sym_obj, source_data_for_sym)
        sym_obj = apply_freshness_policy(sym_obj)

        if sym_obj["source_used"]:
            snapshot["symbols"].append(sym_obj)
        else:
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
            if target["target_class"] == "unknown_or_unsupported":
                failed_sym["data_quality_flags"].append("target_class_mapping_unknown")
            snapshot["failed_symbols"].append(failed_sym)

    # 3. Mark sources without mock input as failed_sources offline if no inputs
    if not mock_inputs:
        for src in ["TWSE_MIS", "Yahoo_Finance", "TWSE_OpenAPI", "TPEx_OpenAPI"]:
            # Update source health error_type for missing local input
            for sh in snapshot["source_health"]:
                if sh["source_id"] == src:
                    sh["error_type"] = "offline_mode_no_local_input"
                    sh["retrieved_time"] = now_utc.isoformat()

            snapshot["failed_sources"].append({
                "source_id": src,
                "source_type": next((sh["source_type"] for sh in snapshot["source_health"] if sh["source_id"] == src), "unknown"),
                "http_ok": None,
                "error_type": "offline_mode_no_local_input",
                "retrieved_time": now_utc.isoformat(),
                "affected_symbols": [t["symbol"] for t in all_targets],
                "caveats": ["offline_mode", "no_live_network_default"]
            })

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


def build_snapshot_from_m5f_canonical(canonical):
    """Pure M5F convergence path: derive latest reviewed bounded evidence snapshot."""
    return {
        "schema_version": "m5f_latest_market_snapshot.v1",
        "snapshot_semantics": "latest reviewed bounded evidence",
        "source": canonical["source"],
        "source_date": canonical["source_date"],
        "symbols": [dict(s) for s in canonical.get("symbols", [])],
        "failed_targets": list(canonical.get("failed_targets", [])),
        "global_caveats": list(canonical.get("global_caveats", [])),
        "governance": dict(canonical.get("governance", {})),
    }
