import json
import os
from datetime import datetime, timezone, timedelta

NEAR_THRESHOLD_PCT = 0.005

def get_abs_path(relative_path):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)

def build_observation(sym_obj, obs_type, obs_label, obs_value, evidence, severity, ai_summary):
    return {
        "symbol": sym_obj.get("symbol"),
        "exchange": sym_obj.get("exchange", "unknown"),
        "target_class": sym_obj.get("target_class", "unknown"),
        "source_used": sym_obj.get("source_used") or "unknown",
        "source_authority": sym_obj.get("source_authority", "unknown"),
        "freshness_status": sym_obj.get("freshness_status", "unknown"),
        "delay_status": sym_obj.get("delay_status", "unknown"),
        "price_semantics": sym_obj.get("price_semantics", "unknown"),
        "observation_type": obs_type,
        "observation_label": obs_label,
        "observation_value": obs_value,
        "evidence": evidence,
        "severity": severity,
        "caveats": sym_obj.get("caveats", []),
        "ai_safe_summary": ai_summary
    }

def generate_symbol_observations(sym_obj):
    observations = []

    last_price = sym_obj.get("last_price")
    prev_close = sym_obj.get("previous_close")
    open_price = sym_obj.get("open")
    high_price = sym_obj.get("high")
    low_price = sym_obj.get("low")
    volume = sym_obj.get("volume")
    bid_ask = sym_obj.get("bid_ask", {})
    staleness = sym_obj.get("staleness_seconds")

    freshness = sym_obj.get("freshness_status")
    price_sem = sym_obj.get("price_semantics")

    # Source / Freshness observations
    if freshness == "stale":
        observations.append(build_observation(
            sym_obj, "source_stale", "source data is stale", True, {"staleness_seconds": staleness}, "source_risk",
            "Available data is marked as stale. Exercise caution."
        ))

    if price_sem == "eod_reference":
        observations.append(build_observation(
            sym_obj, "eod_reference_only", "data is EOD reference", True, {"price_semantics": "eod_reference"}, "info",
            "Data is End-of-Day reference. Do not treat as live intraday data."
        ))
    elif price_sem == "delayed_quote":
        observations.append(build_observation(
            sym_obj, "delayed_quote_available", "delayed quote available", True, {"price_semantics": "delayed_quote"}, "source_risk",
            "Available quote is explicitly delayed. Do not treat as realtime."
        ))
    elif price_sem == "live_candidate":
        observations.append(build_observation(
            sym_obj, "live_candidate_available", "live data candidate available", True, {"price_semantics": "live_candidate"}, "info",
            "Live data candidate observed. Not guaranteed to be authoritative."
        ))

    # Bid/Ask
    if bid_ask:
        best_bid = bid_ask.get("best_bid_price")
        best_ask = bid_ask.get("best_ask_price")
        if best_bid is None or best_ask is None:
            observations.append(build_observation(
                sym_obj, "bid_ask_missing", "bid/ask data missing", True, {"best_bid_price": best_bid, "best_ask_price": best_ask}, "data_quality",
                "Bid/Ask data is incomplete or unavailable."
            ))
        else:
            observations.append(build_observation(
                sym_obj, "spread_available", "bid/ask spread available", True, {"best_bid_price": best_bid, "best_ask_price": best_ask}, "info",
                "Bid/Ask spread observed. Does not guarantee execution."
            ))
    else:
        observations.append(build_observation(
            sym_obj, "bid_ask_missing", "bid/ask data missing", True, {}, "data_quality",
            "Bid/Ask data is incomplete or unavailable."
        ))

    # Volume
    if isinstance(volume, (int, float)) and volume > 0:
        observations.append(build_observation(
            sym_obj, "volume_active", "trading volume active", True, {"volume": volume}, "info",
            "Trading volume observed. Not a liquidity guarantee."
        ))

    # Price comparisons
    if isinstance(last_price, (int, float)):
        if isinstance(prev_close, (int, float)):
            if last_price != prev_close:
                observations.append(build_observation(
                    sym_obj, "price_changed", "price changed from previous close", True, {"last_price": last_price, "previous_close": prev_close}, "info",
                    "Price differs from previous close based on available data. Not a trading signal."
                ))
            if last_price > prev_close:
                observations.append(build_observation(
                    sym_obj, "above_previous_close", "price above previous close", True, {"last_price": last_price, "previous_close": prev_close}, "info",
                    "Price is above previous close. Descriptive observation only."
                ))
            elif last_price < prev_close:
                observations.append(build_observation(
                    sym_obj, "below_previous_close", "price below previous close", True, {"last_price": last_price, "previous_close": prev_close}, "info",
                    "Price is below previous close. Descriptive observation only."
                ))

        # Near thresholds
        for field, price, label in [("open", open_price, "near_open"), ("high", high_price, "near_high"), ("low", low_price, "near_low")]:
            if isinstance(price, (int, float)) and price != 0:
                dist = abs((last_price - price) / price)
                if dist <= NEAR_THRESHOLD_PCT:
                    observations.append(build_observation(
                        sym_obj, label, f"price near {field}", True, {"last_price": last_price, field: price, "distance_pct": dist}, "info",
                        f"Price is within 0.5% of {field} price. Descriptive observation only."
                    ))

    return observations

def generate_failed_observations(failed_sym):
    return [build_observation(
        failed_sym, "source_failed", "source failed to return data", True, {"failure_reason": failed_sym.get("failure_reason")}, "failed",
        "Data source failed for this target."
    )]

def build_watchlist_observations(snapshot):
    now_utc = datetime.now(timezone.utc)
    now_taipei = now_utc + timedelta(hours=8)

    artifact = {
        "observation_version": "watchlist_observations_v1",
        "generated_at_utc": now_utc.isoformat(),
        "generated_at_taipei": now_taipei.isoformat(),
        "source_snapshot_ref": "research/generated/latest_market_snapshot.json",
        "generation_mode": "offline_snapshot_read",
        "watchlist_scope": {
            "target_count": snapshot.get("watchlist_scope", {}).get("target_count", 0),
            "full_market_scan": False
        },
        "observations": [],
        "failed_observations": [],
        "global_caveats": snapshot.get("global_caveats", []),
        "prohibited_interpretations": snapshot.get("prohibited_interpretations", [])
    }

    symbols = snapshot.get("symbols", [])
    for sym in symbols:
        artifact["observations"].extend(generate_symbol_observations(sym))

    failed_symbols = snapshot.get("failed_symbols", [])
    for fs in failed_symbols:
        artifact["failed_observations"].extend(generate_failed_observations(fs))

    return artifact

def generate_observations():
    snapshot_path = get_abs_path("research/generated/latest_market_snapshot.json")
    if not os.path.exists(snapshot_path):
        print(f"Error: Snapshot not found at {snapshot_path}")
        return

    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    observations_artifact = build_watchlist_observations(snapshot)

    out_path = get_abs_path("research/generated/watchlist_observations.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(observations_artifact, f, ensure_ascii=False, indent=2)

    print(f"Generated watchlist observations at {out_path}")

if __name__ == "__main__":
    generate_observations()


def build_watchlist_observations_from_m5f_canonical(canonical):
    """Pure M5F convergence path: descriptive observations only."""
    gov = dict(canonical.get("governance", {}))
    source = canonical.get("source", "unknown")
    source_date = canonical.get("source_date", "unknown")
    return {
        "schema_version": "m5f_watchlist_observations.v1",
        "observations": [
            {
                "symbol": s["symbol"],
                "observation": (
                    f"{s['symbol']} has reviewed historical {source} price-like value "
                    f"{s['price_like_value']} from {source_date}; "
                    f"{s.get('freshness_status', gov.get('stale_status', 'unknown'))}/historical only."
                ),
                "source": source,
                "source_date": source_date,
                "freshness_status": s.get("freshness_status"),
                "caveats": list(s.get("display_caveats", [])),
            }
            for s in canonical.get("symbols", [])
        ],
        "failed_targets": list(canonical.get("failed_targets", [])),
        "governance": gov,
    }
