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

## 6. Source Contract Baseline Section
References the M2 baseline contract information mapping current source integrations.

## 7. Source Health Summary Section
Tracks whether a given source is passing offline capability checks, failing, or requires authentication/is blocked.

## 8. Latest Market Snapshot Reference & Summary
- `latest_snapshot_ref`: Points to `research/generated/latest_market_snapshot.json`.
- `latest_snapshot_summary`: A safe aggregation of market status without regurgitating raw data payloads.

## 9. Watchlist Observation Reference & Summary
- `watchlist_observations_ref`: Points to `research/generated/watchlist_observations.json`.
- `watchlist_observation_summary`: High-level count of observations derived from watchlist targets without generating new trading signals.

## 10. Failed Sources / Failed Targets Section
Maintains visibility of offline or inaccessible sources and target arrays. Prevents AI from hallucinating data for items that failed.

## 11. Freshness / Delay / Staleness Summary Section
Surfaces metadata surrounding source timeliness to accurately contextualize constraints on "real-time" data claims.

## 12. AI May-Say Section
Strict list of approved vocabulary for AI agents conveying market conditions.

## 13. AI Must-Not-Claim Section
Strict list prohibiting full-market coverage claims, signal generation, or assumptions regarding unstructured real-time updates.

## 14. Caveats Section
Required reading for AI, conveying limitations of unofficial APIs and delays in data sourcing.

## 15. Future Generator Notes
The v2 generator implementation (M3B-02) must maintain these strict structures deterministically and must operate entirely offline without conducting any live endpoint scans.
