# M3 AI Context Pack v2 Contract

## 1. Purpose
The AI Context Pack v2 contract is a formalized, AI-readable structure designed to replace the original source-oriented AI Context Pack (M3-01). The v2 contract integrates data seamlessly across:
- The source contract baseline.
- Source health and authority information.
- Latest market snapshot reference and summary.
- Watchlist observation reference and summary.
- Freshness, delay, and staleness policies.
- Failed sources and failed targets context.
- Strict AI may-say and must-not-claim rules, preventing unverified interpretations.

## 2. Intended Consumers
- AI Agents reading market data.
- System maintainers debugging agent reasoning contexts.

## 3. Explicit Non-Goals
- It does **not** implement or contain raw endpoint payloads.
- It does **not** generate new signals, ranks, or buy/sell execution logic.
- It is **not** an open, real-time live trading feed.

## 4. Relationship to M3-01 v1 Contract
The v1 contract organized AI data as direct translations of source capabilities and raw responses. The v2 contract shifts to an abstraction layer utilizing outputs from `latest_market_snapshot.json` and `watchlist_observations.json`, effectively sandboxing raw source variations away from the final AI briefing.

## 5. Required Top-Level Object Structure

The canonical draft structure for the M3 AI Context Pack v2 is as follows:

```json
{
  "pack_version": "m3_ai_context_pack_v2_draft",
  "generated_at_utc": null,
  "generated_at_taipei": null,
  "generation_mode": "design_only",
  "source_contract_baseline": {},
  "source_health_summary": {},
  "source_authority_summary": {},
  "target_support_summary": {},
  "latest_snapshot_ref": "research/generated/latest_market_snapshot.json",
  "latest_snapshot_summary": {},
  "watchlist_observations_ref": "research/generated/watchlist_observations.json",
  "watchlist_observation_summary": {},
  "failed_sources": [],
  "failed_targets": [],
  "freshness_and_delay_summary": {},
  "ai_may_say": [],
  "ai_must_not_claim": [],
  "mandatory_caveats": [],
  "prohibited_interpretations": [],
  "next_actions": []
}
```

## 6. Contract Rules
1. AI Context Pack v2 must not include raw endpoint payloads.
2. `latest_snapshot_summary` must be derived from `latest_market_snapshot.json`.
3. `watchlist_observation_summary` must be derived from `watchlist_observations.json`.
4. EOD-only OpenAPI sources must never be listed as usable live sources.
5. doc_only / auth_required sources must never be listed as usable live sources.
6. TWSE MIS must remain `unofficial_frontend` and must carry caveats.
7. Yahoo Finance must remain `third_party` and must carry caveats.
8. Watchlist observations must not be converted into signals.
9. Failed sources and failed targets must remain visible.
10. Bounded watchlist scope must be explicit; do not claim full-market coverage.
11. Mandatory caveats must not be hidden or dropped.
12. `source_contract_baseline` must classify sources by authority and usability, not by investment quality.
13. `source_contract_baseline` must not imply live availability from EOD, doc_only, or auth_required sources.
14. `target_support_summary` must be bounded to configured watchlist scope unless future evidence proves broader coverage.
15. `target_support_summary` must not claim full-market coverage.
16. `target_support_summary` must not rank target classes or securities.

## 7. Source Contract Baseline Section
References the M2 baseline contract information mapping current source integrations.

## 8. Source Health Summary Section
Tracks whether a given source is passing offline capability checks, failing, or requires authentication/is blocked.

## 9. Source Authority Summary Section
Explicitly designates sources as `official_reference`, `unofficial_frontend`, or `third_party` to prevent AI from inflating the authority or reliability of the data retrieved from unofficial channels.

## 10. Target Support Summary Section
Summarizes system support for requested target classes (e.g. `twse_common_stock`, `twse_etf`) to provide boundaries on what asset types are included.

## 11. Latest Market Snapshot Reference & Summary
- `latest_snapshot_ref`: Points to `research/generated/latest_market_snapshot.json`.
- `latest_snapshot_summary`: A safe aggregation of market status without regurgitating raw data payloads.

## 12. Watchlist Observation Reference & Summary
- `watchlist_observations_ref`: Points to `research/generated/watchlist_observations.json`.
- `watchlist_observation_summary`: High-level count of observations derived from watchlist targets without generating new trading signals.

## 13. Failed Sources / Failed Targets Section
Maintains visibility of offline or inaccessible sources and target arrays. Prevents AI from hallucinating data for items that failed.

## 14. Freshness / Delay / Staleness Summary Section
Surfaces metadata surrounding source timeliness to accurately contextualize constraints on "real-time" data claims.

## 15. AI May-Say Section
Strict list of approved vocabulary for AI agents conveying market conditions.

## 16. AI Must-Not-Claim Section
Strict list prohibiting full-market coverage claims, signal generation, or assumptions regarding unstructured real-time updates.

## 17. Mandatory Caveats Section
Lists fundamental warnings about unofficial APIs, third-party data, and data staleness. These mandatory reading items convey strict system limitations and must be displayed by the AI when summarizing data, unable to be hidden in footnotes.

## 18. Prohibited Interpretations Section
Provides explicit examples of bad interpretations of data to ensure AI understands what constitutes a signal violation or hallucination.

## 19. Next Actions Section
Outlines recommended next tasks for the agent or user, such as verifying source endpoints or investigating failing sources.

## 20. Future Generator Notes
The v2 generator implementation (M3B-02) must maintain these strict structures deterministically and must operate entirely offline without conducting any live endpoint scans.
