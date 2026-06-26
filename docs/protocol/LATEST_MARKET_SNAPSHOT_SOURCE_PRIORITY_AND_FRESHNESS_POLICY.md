# Latest Market Snapshot Source Priority and Freshness Policy

## 1. Purpose
This document defines how the future M3A-02 generator should evaluate, prioritize, and select data sources when populating the Latest Market Snapshot. Priority in this context does **not** mean "best investment source". It solely dictates data suitability for specific fields (e.g., live vs. EOD) and freshness contexts.

## 2. Source Classes and Roles

### TWSE OpenAPI
* **Role:** Official EOD/reference source.
* **May Provide:** EOD price/volume reference for TWSE targets.
* **Must Not Provide:** Live intraday price.
* **M3A Usage:** `official_eod_reference` only.

### TPEx OpenAPI
* **Role:** Official EOD/reference source.
* **May Provide:** EOD price/volume reference for TPEx targets.
* **Must Not Provide:** Live intraday price.
* **M3A Usage:** `official_eod_reference` only.

### TWSE MIS
* **Role:** Unofficial frontend endpoint / live candidate.
* **May Provide:** Bounded low-frequency watchlist-style latest quote fields when fresh enough.
* **Must Not Provide:** Official quote authority, full-market scan, high-frequency feed.
* **M3A Usage:** `live_candidate_with_high_risk_caveats`.

### Yahoo Finance
* **Role:** Third-party chart/watchlist context.
* **May Provide:** Chart and low-frequency context when supported.
* **Must Not Provide:** Official exchange authority.
* **M3A Usage:** `third_party_context_with_coverage_caveats`.

### FinMind
* **Role:** Third-party/commercial historical/EOD source.
* **May Provide:** EOD/historical context depending on dataset/auth availability.
* **Must Not Provide:** Official exchange authority or live intraday unless future evidence proves it.
* **M3A Usage:** `historical_or_eod_candidate_with_auth_caveats`.

### Fugle / Fubon
* **Role:** Authenticated provider / broker API.
* **Current Repo Status:** `doc_only` / `auth_required`.
* **M3A Usage:** Not eligible for generated snapshot until explicit future authenticated scope is implemented.

## 3. Source Priority for Intraday Watchlist Fields (`live_candidate_priority`)
When populating fields designated for intraday / latest snapshot usage (such as `last_price` with `price_semantics = live_candidate`), the generator must use the following precedence:
1. **TWSE MIS:** For bounded TWSE/TPEx watchlist quote fields. MUST include high-risk caveats.
2. **Yahoo Finance:** As a third-party context fallback. MUST include coverage caveats.
3. **Official OpenAPI:** Only permissible as EOD reference, **never** as a live candidate.

## 4. Source Priority for Official EOD Reference Fields (`official_eod_reference_priority`)
When populating definitive EOD data (where `price_semantics = eod_reference`):
1. **TWSE OpenAPI:** For TWSE target EOD reference.
2. **TPEx OpenAPI:** For TPEx target EOD reference.
3. **FinMind:** As third-party/commercial fallback with necessary caveats.

## 5. Broker Priority
None in the current repository scope. All broker APIs (Fugle, Fubon) are `auth_required` or `doc_only` and are prohibited from being used in the snapshot generation currently.

## 6. Source Authority Rules
Sources must be explicitly labeled with an authority level reflecting their standing:
* `official_public_exchange_eod` (TWSE OpenAPI, TPEx OpenAPI)
* `unofficial_frontend` (TWSE MIS)
* `third_party` (Yahoo Finance, FinMind)

## 7. Staleness Policy
1. Data freshness must be explicitly tracked using `staleness_seconds`, calculated as the difference between `retrieved_time` and `source_time`.
2. If a live candidate source is deemed stale (e.g., crossing a pre-defined threshold), mark the symbol's `freshness_status` as `stale` or `delayed` and `price_semantics` as `stale_quote`.
3. If a source is both explicitly delayed and exceeds the stale threshold, staleness takes precedence: classify it as `stale_quote` with `freshness_status = stale` and `delay_status = stale`, because conservative degradation is safer than preserving a merely delayed label.
4. **Do not silently replace** a stale live candidate with EOD official data while presenting it as a live price. Stale quotes must remain visible as stale.

## 8. Fallback Policy
1. If the primary live candidate source fails or is excessively stale, the generator may fall back to the secondary source in the priority list (e.g., Yahoo Finance).
2. If an official EOD source is used, set `freshness_status = eod_batch` and `delay_status = eod`.
3. If all sources fail for a given symbol, the symbol must be explicitly included in the `failed_symbols` array with error metadata attached. It MUST NOT be dropped silently.

## 9. Conflict Policy
If multiple sources are queried and they disagree (e.g., volume differences between TWSE MIS and Yahoo Finance), the snapshot must preserve source attribution via `source_used` and `source_candidates`. The generator must adhere strictly to the established priority lists and **must not synthesize a single “truth”** unless explicitly documented by policy.

## 10. Caveat Preservation Policy
All unverified, unofficial, or third-party sources MUST inject explicit caveat strings into the `caveats` array for the given symbol, describing the risk profile of the data (e.g., `unofficial_source_risk`, `third_party_coverage_gap`).

## 11. Prohibited Source Combinations
1. Do not merge live intraday price from an unofficial source with EOD volume from an official source under the pretense that they form a single coherent quote.
2. Official EOD batch data and live intraday candidates must always be segregated semantically via the `price_semantics` and `freshness_status` fields.
