# Latest Market Snapshot Contract

## 1. Purpose
This document defines the canonical, AI-readable `latest_market_snapshot` structure for the M3A snapshot layer. The snapshot acts as an intermediary layer between raw probe responses (M2) and the final AI Market Context Pack (M3). Its purpose is to present a clean, conservative, heavily-caveated view of the current market state across bounded target scopes, so that future AI agents do not consume raw endpoint payloads directly.

## 2. Intended Consumers
1. **M3A-02 Generator (Future):** Will parse config/targets, run probes, and synthesize this snapshot.
2. **M3B AI Context Pack Generator (Future):** Will consume this snapshot to build human/AI readable briefings.
3. **M3C ChatGPT Briefing Generator / Future AI consumers:** May consume this snapshot to create a human-readable AI briefing.
4. **M4 Future Read-Only MCP Integration:** Might expose this snapshot via the MCP protocol.

## 3. Explicit Non-Goals
1. This is **not** an execution-grade, high-frequency live feed.
2. It does **not** generate trading signals, alerts, rankings, buy/sell recommendations, or backtesting data.
3. It does **not** implement full-market crawling.
4. It does **not** pretend to be a single unified "truth" if multiple sources conflict; it prioritizes explicit source attribution and caveats.

## 4. Required Top-Level Object Structure
The top-level structure MUST adhere to the following schema.

```json
{
  "snapshot_version": "latest_market_snapshot_v1_draft",
  "generated_at_utc": null,
  "generated_at_taipei": null,
  "generation_mode": "design_only",
  "market_session_status": {
    "status": "unknown",
    "as_of_taipei": null,
    "source": "design_only",
    "caveats": []
  },
  "source_health": [],
  "source_priority": [],
  "watchlist_scope": {
    "scope_type": "bounded_config_watchlist",
    "target_count": 0,
    "target_source": "config/market_targets.json",
    "full_market_scan": false
  },
  "symbols": [],
  "failed_symbols": [],
  "failed_sources": [],
  "global_caveats": [],
  "prohibited_interpretations": []
}
```

## 5. Required Per-Symbol Structure
The snapshot uses a unified per-symbol structure to represent all targets, regardless of whether the populated data is derived from live candidates or EOD references. **Interpretation of values is strictly controlled by the metadata fields (e.g., `price_semantics`, `freshness_status`).**

```json
{
  "symbol": "2330",
  "exchange": "TWSE",
  "target_class": "twse_common_stock",
  "name": "台積電",
  "last_price": null,
  "change": null,
  "change_pct": null,
  "open": null,
  "high": null,
  "low": null,
  "previous_close": null,
  "volume": null,
  "bid_ask": {
    "best_bid_price": null,
    "best_bid_volume": null,
    "best_ask_price": null,
    "best_ask_volume": null,
    "spread": null,
    "bid_ask_status": "unknown"
  },
  "source_used": null,
  "source_candidates": [],
  "source_time": null,
  "retrieved_time": null,
  "staleness_seconds": null,
  "delay_status": "unknown",
  "freshness_status": "unknown",
  "source_authority": "unknown",
  "support_status": "unknown",
  "price_semantics": "unknown",
  "official_eod_reference_available": false,
  "live_candidate_available": false,
  "data_quality_flags": [],
  "caveats": [],
  "raw_payload_ref": null
}
```

### 5.1 Metadata-Driven Interpretation Rules
1. **Never Interpret Without Context:** The `last_price` field must never be interpreted without considering `freshness_status`, `delay_status`, `source_used`, `source_authority`, `staleness_seconds`, `price_semantics`, and `caveats`.
2. **`last_price` is a Display Reference:** It is a selected display/reference price, not automatically a live price.
3. **EOD as Reference:** EOD values may populate `last_price` only when `price_semantics` is set to `eod_reference` and `freshness_status` is `eod_batch`. They must never be treated as a live intraday quote.
4. **Staleness Tracking:** Stale live-candidate values must be marked stale (e.g., via `staleness_seconds` and `delay_status`) and must not be mixed into live-style summaries.
5. **Fallbacks:** If the future generator cannot determine freshness, use `freshness_status = unknown`, `price_semantics = unknown`, and keep caveats visible.

#### 5.1.1 Allowed Values for `price_semantics`
* `live_candidate`
* `delayed_quote`
* `stale_quote`
* `eod_reference`
* `chart_context`
* `unavailable`
* `unknown`

## 6. Source Health Block
A block defining the current operational status of the sources queried during snapshot generation. Each entry MUST adhere to the following schema:

```json
{
  "source_id": "TWSE_MIS",
  "source_type": "unofficial_frontend_endpoint",
  "authority_level": "unofficial_frontend",
  "http_ok": null,
  "parse_ok": null,
  "normalization_ok": null,
  "latency_ms": null,
  "retrieved_time": null,
  "error_type": null,
  "caveats": []
}
```

## 7. Source Priority Block
A block capturing the explicit precedence rules applied by the generator when selecting `source_used` for the symbols (e.g., favoring `TWSE_MIS` for live intraday fields, or `TWSE_OpenAPI` for EOD reference).

## 8. Market Session Status Block
A high-level view of the inferred market session (`unknown`, `pre_market`, `regular_trading`, `post_market`, `closed`, `holiday_or_no_session`, `source_time_inconsistent`). In M3A-01, this defaults to `unknown` and generation mode is `design_only`.

## 9. Freshness / Staleness / Delay Fields
Every symbol MUST declare its data freshness explicitly.
* `freshness_status`: Allowed values include `realtime_candidate`, `delayed`, `stale`, `eod_batch`, `unknown`.
* `delay_status`: Allowed values include `realtime_candidate`, `delayed`, `stale`, `eod`, `unknown`.
* `staleness_seconds`: An integer representing the elapsed time between `source_time` and `retrieved_time`. It is a mandatory field, but may be explicitly `null` when a source lacks a reliable `source_time` or when it represents EOD batch data.

### 9.1 Staleness Calculation Guidelines
1. If `source_time` exists, `staleness_seconds` = `retrieved_time` - `source_time`.
2. If `source_time` is unavailable, malformed, or only a trade date is provided, `staleness_seconds` may be `null`.
3. For official EOD references, use `freshness_status = eod_batch`, `delay_status = eod`, `price_semantics = eod_reference`.
4. Do not force intraday staleness calculations onto EOD batch rows.
5. If `staleness_seconds` is missing when it should be available for a live candidate, append `source_time_unavailable` to caveats or `data_quality_flags`.

## 10. Data Quality Flags
An array of strings describing schema anomalies, missing mappings, or suspect data (e.g., `["missing_trade_date", "malformed_volume"]`).

## 11. Caveats
An array of explicit disclaimers applied either globally (in `global_caveats`) or per symbol (in `caveats`). Unofficial live sources (e.g., TWSE MIS) MUST be accompanied by high-risk caveats.

## 12. Failure Preservation Rules
1. **Failed Symbols:** Symbols that could not be retrieved from any source must be explicitly listed in the `failed_symbols` array, preserving error metadata. They MUST NOT be silently omitted. Each entry MUST adhere to the following schema:

```json
{
  "symbol": "2330",
  "exchange": "TWSE",
  "target_class": "twse_common_stock",
  "source_attempts": [],
  "failure_reason": "all_sources_failed",
  "retrieved_time": null,
  "data_quality_flags": [],
  "caveats": []
}
```

2. **Failed Sources:** If a source fails globally, it MUST be noted in `failed_sources` and `source_health`. Each entry in `failed_sources` MUST adhere to the following schema:

```json
{
  "source_id": "TWSE_MIS",
  "source_type": "unofficial_frontend_endpoint",
  "http_ok": false,
  "error_type": "timeout",
  "retrieved_time": null,
  "affected_symbols": [],
  "caveats": []
}
```

3. **Isolation:** A source failure must not crash the entire snapshot generation process.

## 13. Future Generator Notes
The M3A-02 generator will be responsible for populating this contract. It must strictly adhere to bounded watchlist scope, deterministic execution, and never invent or impute missing data.
