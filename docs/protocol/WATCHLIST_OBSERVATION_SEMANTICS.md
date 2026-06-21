# Watchlist Observation Semantics

## 1. Purpose
This milestone defines and implements a conservative **watchlist observation semantics** layer on top of `latest_market_snapshot.json`. The goal is to let the system produce structured, AI-readable descriptive statements about available data quality or value relationships across bounded target scopes.

## 2. Intended Consumers
1. **M3B AI Context Pack Generator (Future):** Will consume these observations to build human/AI readable briefings.
2. **M3C ChatGPT Briefing Generator:** May consume this context to construct human-readable AI briefings.
3. **M4 Future Read-Only MCP Integration:** May expose these observations via the MCP protocol.

## 3. Explicit Non-Goals
1. Do not create buy/sell/hold recommendations.
2. Do not create trading signals.
3. Do not create target prices.
4. Do not create profit predictions.
5. Do not create ranking or scoring of securities as investment opportunities.
6. Do not create strategy logic.
7. Do not create backtests.
8. Do not create order execution logic.

## 4. Observation vs Signal Distinction
This milestone makes the distinction explicit:
* `observation != signal`
* `signal != trading instruction`
* `market context != investment recommendation`

**Important semantic rule:**
An observation is a descriptive statement about available data quality or value relationships. It is not a prediction, instruction, ranking, recommendation, or strategy.

## 5. Allowed Observation Vocabulary

| Observation Type | Meaning | Required Input Fields | Emission Rule | Severity | Required Caveats / Metadata | AI-Safe Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `price_changed` | Price differs from previous close | `last_price`, `previous_close` | `last_price != previous_close` (numeric) | `info` | Preserve snapshot caveats | "Price differs from previous close based on available data. Not a trading signal." |
| `volume_active` | Trading volume is greater than zero | `volume` | `volume > 0` (numeric) | `info` | Preserve snapshot caveats | "Trading volume observed. Not a liquidity guarantee." |
| `near_open` | Price is near the open price | `last_price`, `open` | Absolute % distance <= 0.5% | `info` | Preserve snapshot caveats | "Price is within 0.5% of open price. Descriptive observation only." |
| `near_high` | Price is near the high price | `last_price`, `high` | Absolute % distance <= 0.5% | `info` | Preserve snapshot caveats | "Price is within 0.5% of high price. Descriptive observation only." |
| `near_low` | Price is near the low price | `last_price`, `low` | Absolute % distance <= 0.5% | `info` | Preserve snapshot caveats | "Price is within 0.5% of low price. Descriptive observation only." |
| `above_previous_close` | Price is above previous close | `last_price`, `previous_close` | `last_price > previous_close` (numeric) | `info` | Preserve snapshot caveats | "Price is above previous close. Descriptive observation only." |
| `below_previous_close` | Price is below previous close | `last_price`, `previous_close` | `last_price < previous_close` (numeric) | `info` | Preserve snapshot caveats | "Price is below previous close. Descriptive observation only." |
| `spread_available` | Bid/Ask spread is available | `bid_ask` | `best_bid_price` and `best_ask_price` present | `info` | Preserve snapshot caveats | "Bid/Ask spread observed. Does not guarantee execution." |
| `bid_ask_missing` | Bid/Ask data is missing | `bid_ask` | `best_bid_price` or `best_ask_price` missing/null | `data_quality` | Preserve snapshot caveats | "Bid/Ask data is incomplete or unavailable." |
| `source_stale` | Source data is stale | `freshness_status` | `freshness_status` is `stale` | `source_risk` | Preserve snapshot caveats | "Available data is marked as stale. Exercise caution." |
| `source_failed` | Source failed to return data | `failed_symbols` | Symbol present in `failed_symbols` | `failed` | Failure reason | "Data source failed for this target." |
| `source_unavailable` | Source is unavailable | `failed_sources` | Target depends on failed source | `failed` | Failure reason | "Required data source is currently unavailable." |
| `eod_reference_only` | Data is EOD reference | `price_semantics` | `price_semantics` is `eod_reference` | `info` | `official_eod_reference_only` | "Data is End-of-Day reference. Do not treat as live intraday data." |
| `live_candidate_available` | Live data candidate exists | `price_semantics` | `price_semantics` is `live_candidate` | `info` | Preserve snapshot caveats | "Live data candidate observed. Not guaranteed to be authoritative." |
| `data_incomplete` | Missing required fields | Various | Cannot compute required metrics | `data_quality` | Preserve snapshot caveats | "Required data fields are missing or incomplete." |

*Note: The near-threshold for M3D-01 is deterministically hardcoded at 0.5% (e.g., `NEAR_THRESHOLD_PCT = 0.005`). Future milestones may make this configurable if there is a concrete need.*

## 6. Prohibited Vocabulary
The following vocabulary **MUST NOT** be generated or implied:
* buy
* sell
* hold
* target_price
* profit_prediction
* guaranteed_reversal
* automated_trade_signal
* trading_signal
* entry_point
* exit_point
* stop_loss
* take_profit
* strong_buy
* strong_sell
* rank
* top_pick
* best_stock

## 7. Observation Object Schema

**Top-level Artifact Schema:**
```json
{
  "observation_version": "watchlist_observations_v1",
  "generated_at_utc": "2023-10-01T00:00:00Z",
  "generated_at_taipei": "2023-10-01T08:00:00+08:00",
  "source_snapshot_ref": "research/generated/latest_market_snapshot.json",
  "generation_mode": "offline_snapshot_read",
  "watchlist_scope": {
    "target_count": 0,
    "full_market_scan": false
  },
  "observations": [],
  "failed_observations": [],
  "global_caveats": [],
  "prohibited_interpretations": []
}
```

**Observation Object Schema:**
```json
{
  "symbol": "2330",
  "exchange": "TWSE",
  "target_class": "twse_common_stock",
  "source_used": "TWSE_MIS",
  "source_authority": "unofficial_frontend",
  "freshness_status": "realtime_candidate",
  "delay_status": "realtime_candidate",
  "price_semantics": "live_candidate",
  "observation_type": "above_previous_close",
  "observation_label": "price above previous close",
  "observation_value": true,
  "evidence": {
    "last_price": 101.0,
    "previous_close": 100.0,
    "staleness_seconds": 60
  },
  "severity": "info",
  "caveats": [],
  "ai_safe_summary": "Price is above previous close based on available source data. This is an observation, not a trading signal."
}
```

## 8. Source Freshness / Staleness Dependency
Observations must never interpret a `last_price` without carrying over the `freshness_status`, `delay_status`, `source_authority`, and `price_semantics`. For example, a `price_changed` observation derived from EOD batch data must explicitly include `eod_reference_only` to ensure AI consumers cannot misread the observation as intraday/live.

## 9. Failure Handling
* If `latest_market_snapshot.json` lacks data for a symbol (e.g., symbol is in `failed_symbols`), a `source_failed` or `source_unavailable` observation must be emitted.
* If specific fields required for an observation are missing, the generator must either emit `data_incomplete` (if appropriate) or safely omit the dependent observation. Missing data must not be inferred.

## 10. AI Usage Rules
1. Observations are descriptive only.
2. Observations are not signals.
3. Observations are not trading instructions.
4. Observations must preserve source freshness and caveats.
5. Missing data must produce `data_incomplete` or no observation, not inferred values.

## 11. Future Generator Behavior
* The generator must act strictly offline and read from a generated snapshot.
* It must not execute network requests, full-market scans, or high-frequency polling.
* The near threshold logic may evolve to use a dynamically configurable `NEAR_THRESHOLD_PCT` setting instead of a hardcoded 0.5%.
