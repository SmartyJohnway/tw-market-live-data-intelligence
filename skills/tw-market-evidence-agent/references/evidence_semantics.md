# Evidence Semantics (Unified Version)

This document defines the timing taxonomy, source authority rules, and calculation semantics used to interpret results returned by the Unified Market Evidence workbench.

---

## 1. Timing Taxonomy

Every piece of evidence returned in the `unified_market_evidence_result.v1` envelope carries a specific `timing_class` that governs its freshness and description semantics:

- **`liveish_intraday_snapshot`**: Current intraday quote or state. AI must describe this in present tense but disclose that it is **not guaranteed to be real-time zero-latency data**.
- **`official_eod`**: Official End-of-Day cash-market OHLCV completed session metrics. AI must describe this in past tense as a completed session.
- **`official_statistics_eod`**: Official EOD derivatives reports, large-trader open interest, or statistical aggregates. AI must describe this in past tense.
- **`request_session_context`**: Structural clock and calendar state used to assert currentness.

---

## 2. Source Authority Classes

Citations in the result contain source attribution that defines the legal and operational trust level of the data:
- **`official_exchange_current`**: Live-ish data from official exchange query lines (e.g. TWSE MIS).
- **`official_exchange_eod`**: Official completed EOD reference APIs (e.g. TWSE OpenAPI).
- **`official_government` / `official_dynamic_event`**: Official announcements (e.g. NCDR closure declarations).
- **`derived_calculation`**: Metrics calculated deterministically by the workbench (e.g. price change percentages). AI must label these as calculated derived metrics, not exchange-reported figures.

---

## 3. Timestamp Semantics

AI must strictly enforce the following timestamp distinctions:
- **`retrieved_at`**: The timestamp when the workbench fetched the data. **This is not the exchange event time.** AI must say: *"Retrieved at [retrieved_at]"*, not *"Market price as of [retrieved_at]"*.
- **`effective_trade_date`**: The trade date to which the data legally belongs. 
- **`stale` or `reference_only`**: If the currentness evaluator marks data as stale (e.g. market closed but query run during weekend), AI must describe all price facts in past tense.

---

## 4. Calculation Semantics

- **Unadjusted Returns**: Price movements calculated under `recent_performance` are unadjusted returns. AI must warn that splits, dividends, or ex-right events are not accounted for.
- **No Zero Dividends**: If dividend adjustment data is missing, AI must not assume dividend yield is zero. It must state that dividend data was omitted from the evidence.
