# M3 AI Context Pack v2 Generator Requirements

This document defines the requirements for the future **M3B-02** generator.
*Note: M3B-01 does not implement this generator.*

## 1. Future Inputs
The future v2 generator must consume the following inputs:
- `research/generated/latest_market_snapshot.json`
- `research/generated/watchlist_observations.json`
- `docs/protocol/M3_AI_CONTEXT_PACK_V2_CONTRACT.md`
- `docs/protocol/M3_AI_CONTEXT_PACK_V2_SECTION_SCHEMA.md`
- `docs/protocol/M3_AI_CONTEXT_PACK_V2_POLICY.md`
- `docs/protocol/M3_AI_CONTEXT_GUARDRAILS.md`
- `docs/protocol/M2_SOURCE_CONTRACT_BASELINE.md`
- `docs/protocol/SOURCE_TARGET_SUPPORT_MATRIX.md`
- `docs/protocol/SUPPORT_STATUS_SEMANTICS.md`

## 2. Future Outputs
The generator will produce:
- `research/generated/ai_context_pack.json`
- `research/generated/ai_context_pack.md`

## 3. Important Requirements
The generator implementation must strictly adhere to the following rules:
1. **Offline deterministic generation:** The generator must operate completely offline.
2. **No live network calls:** It must rely solely on the pre-generated snapshot and observations.
3. **No raw endpoint payloads:** It must summarize and synthesize the data, never directly dumping raw API responses.
4. **Must read `latest_market_snapshot.json`:** This is the primary data source.
5. **Must read `watchlist_observations.json`:** This provides the descriptive insights.
6. **Must preserve caveats:** All warnings about unofficial data, staleness, and scope must be maintained.
7. **Must preserve failed sources and failed targets:** Failures must be explicitly mapped to avoid AI hallucination.
8. **Must preserve observation != signal boundary:** Observations must never be transformed into buy/sell/hold execution signals.
9. **Must preserve source authority distinctions:** Clearly delineate between official reference, unofficial live, and third-party data.
10. **Must validate prohibited vocabulary:** The output must not contain terms implying financial advice or market execution.
11. **Must not mutate inputs:** `latest_market_snapshot.json` and `watchlist_observations.json` must remain unmodified.
12. **Must not create ChatGPT briefing:** The generator's output is an AI-readable context pack, not a human-readable chat summary.

## 4. Validation Requirements
The M3B-02 implementation will be validated against these criteria:
1. Required top-level keys exist in the generated JSON.
2. Required section keys exist in the generated JSON.
3. Snapshot reference and observation reference pointers exist and are accurate.
4. `source_contract_baseline` includes all seven canonical M2/M3 sources.
5. `official_eod_sources` includes `TWSE_OpenAPI` and `TPEx_OpenAPI` but they are excluded from `usable_live_sources`.
6. `auth_required_sources` / `doc_only_sources` include `Fugle` and `Fubon` and are excluded from `usable_live_sources`.
7. `target_support_summary` sets `bounded_watchlist_only = true`.
8. `target_support_summary` sets `full_market_coverage = false` unless a future explicit full-market milestone changes this.
9. `target_support_summary` does not contain ranking, investment-quality, or signal semantics.
10. Failed source counts are preserved or explainably summarized.
11. Failed target counts are preserved or explainably summarized.
12. Watchlist observation counts match `watchlist_observations.json`.
13. Unofficial sources preserve their necessary caveats.
14. Prohibited vocabulary is absent outside the `prohibited_interpretations` section.
15. No unsupported average-volume, momentum, ranking, or trend-strength language is generated unless future artifacts explicitly support it.
16. The script demonstrates full offline CI compatibility.
