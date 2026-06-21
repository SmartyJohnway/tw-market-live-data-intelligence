# Latest Market Snapshot Generator Requirements

## 1. Purpose
This document outlines the strict functional requirements and guardrails for the future M3A-02 generator. The generator's responsibility is to read configuration, execute probes, and output a compliant `latest_market_snapshot.json` artifact based on the M3A-01 contract design. **This document does not implement the generator.**

## 2. Inputs
The future generator should accept or read from the following inputs:
* `config/market_targets.json` (defines the bounded watchlist scope)
* `docs/protocol/M2_SOURCE_CONTRACT_BASELINE.md`
* `docs/protocol/LATEST_MARKET_SNAPSHOT_SOURCE_PRIORITY_AND_FRESHNESS_POLICY.md`
* `docs/protocol/MARKET_SESSION_STATUS_SEMANTICS.md`
* `docs/source_catalog.md` and `docs/capability_matrix.md`

## 3. Outputs
The generator must produce a single, deterministic artifact:
* `research/generated/latest_market_snapshot.json`

*(Note: Creating this file is strictly prohibited in M3A-01.)*

## 4. Deterministic Behavior
The generator must be deterministic given the same external source responses. It must not rely on randomized fallbacks, machine-learning imputations, or probabilistic gap-filling for missing data. If data is missing, it must remain explicitly `null` or an empty array `[]`.

## 5. Bounded Watchlist Scope
The generator MUST restrict its execution strictly to the symbols defined in `config/market_targets.json`. It MUST NOT implement full-market crawling, discovery, or recursive scraping. The `watchlist_scope` block in the snapshot must reflect this restriction.

## 6. Source Selection Policy
The generator must strictly adhere to the `LATEST_MARKET_SNAPSHOT_SOURCE_PRIORITY_AND_FRESHNESS_POLICY.md`. It must evaluate targets against authorized sources, correctly attributing `source_used` and populating `price_semantics` to clearly distinguish EOD references from live candidates.

## 7. Freshness and Staleness Calculation Requirements
1. **Timestamping:** Every fetched symbol must capture `source_time` (from the API payload, if available) and `retrieved_time` (the local system execution time).
2. **Staleness Metric:** The generator must calculate `staleness_seconds` = `retrieved_time` - `source_time`.
3. **Thresholding:** Based on `staleness_seconds` and the source authority, the generator must correctly categorize `freshness_status` (e.g., `realtime_candidate`, `stale`, `eod_batch`).

## 8. Source Failure Behavior
If a source API fails entirely (e.g., HTTP 5xx, timeout, or schema drift):
1. The source must be appended to `failed_sources`.
2. The error must be logged in `source_health`.
3. The generator MUST NOT crash. It should gracefully degrade by falling back to lower-priority sources or marking the affected symbols as failed.

## 9. Symbol Failure Behavior
If a symbol cannot be resolved by any authorized source:
1. It MUST NOT be silently omitted from the snapshot.
2. It MUST be appended to the `failed_symbols` array.
3. Appropriate `data_quality_flags` and `caveats` must be attached indicating the failure reason.

## 10. Data Quality Flag Requirements
The generator must aggressively flag malformed, suspect, or missing data by appending standard string codes to the `data_quality_flags` array (e.g., `missing_trade_date`, `malformed_volume`, `unmapped_raw_fields_present`).

## 11. No Live-Probe-By-Default Policy
If the generator is designed to run in a continuous/UI context, it must not execute live network probes automatically or aggressively polling loops. Probes should be user-initiated or triggered by a single batch run. **High-frequency polling is strictly prohibited.**

## 12. Optional Explicit Live Refresh Policy
Future scope (M3A-03+) may introduce an explicit, authenticated refresh mechanism for live data. The M3A-02 generator must lay the groundwork by ensuring its architecture separates the "read snapshot" action from the "execute network refresh" action.

## 13. Validation Requirements
Before writing the final `latest_market_snapshot.json`, the generator MUST validate the output against the following strict constraints:
1. **JSON Schema:** The output must be valid, parseable JSON.
2. **Required Keys:** All top-level keys defined in the contract must exist.
3. **Per-Symbol Keys:** Every symbol object must contain all required keys.
4. **Freshness Mandate:** Every symbol must include `freshness_status`, `delay_status`, `staleness_seconds`, `price_semantics`, and `caveats`.
5. **Stale Data Isolation:** Stale symbols must be visibly marked via metadata.
6. **Failure Preservation:** Failed sources and symbols must exist in their respective arrays, not dropped.
7. **EOD Restriction:** Official EOD sources must never be tagged with `price_semantics = live_candidate`.
8. **Caveat Enforcement:** Unofficial live candidates must always preserve explicit caveats.
9. **Broker Exclusion:** Broker APIs must not be included as usable sources.
10. **Semantic Purity:** No trading-signal, buy/sell, or ranking vocabulary may appear anywhere in the output.
11. **Offline CI:** The generator's underlying logic must be testable via offline unit tests (e.g., `pytest -m "not network"`).

## 14. Versioning
The generator must stamp the output with the corresponding `snapshot_version` defined in the contract (e.g., `latest_market_snapshot_v1_draft`).

## 15. Future Output Paths
The generated artifact will reside at `research/generated/latest_market_snapshot.json` and serve as the foundational input for the M3B AI Context Pack generator.
