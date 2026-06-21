# M3 AI Context Pack v2 Section Schema

This document defines the schema and purpose of each section within the AI Context Pack v2.

## `pack_metadata`
- **Purpose:** Identifies the current context pack generation event.
- **Required fields:** `pack_version`, `generated_at_utc`, `generated_at_taipei`, `generation_mode`
- **Allowed values:** `pack_version` must be `m3_ai_context_pack_v2_draft` (or stable version in the future), `generation_mode` handles `design_only` for current phase.
- **Future M3B-02 Behavior:** Generated entirely offline.

## `source_contract_baseline`
- **Purpose:** Informs AI about current canonical sources mapped in the system.
- **Derived from:** M2 / M3 source contract documents.
- **Future M3B-02 Behavior:** Will pull statically from source protocols.
- **Caveats:** Must not imply that sources currently blocked or requiring authentication are accessible.

## `source_health_summary`
- **Purpose:** Describes the availability of the sources based on offline probes.
- **Optional fields:** Status counts.
- **Future M3B-02 Behavior:** Derives from baseline data capabilities.

## `source_authority_summary`
- **Purpose:** Designates official vs third-party vs unofficial sources.
- **Future M3B-02 Behavior:** Strictly segregates TWSE MIS (unofficial) from EOD OpenAPI (official).

## `target_support_summary`
- **Purpose:** Describes support for targets (e.g. `twse_common_stock`, `twse_etf`).

## `latest_snapshot_ref`
- **Purpose:** Strict reference pointer.
- **Required fields:** Set exactly to `"research/generated/latest_market_snapshot.json"`.

## `latest_snapshot_summary`
- **Purpose:** Aggregates a summary of the snapshot.
- **Derived from:** `research/generated/latest_market_snapshot.json`
- **Future M3B-02 Behavior:** Aggregates top-level snapshot metadata (e.g., total symbols, time generated) but strictly excludes all raw market data records.

## `watchlist_observations_ref`
- **Purpose:** Strict reference pointer.
- **Required fields:** Set exactly to `"research/generated/watchlist_observations.json"`.

## `watchlist_observation_summary`
- **Purpose:** Provides a count and high-level categorization of watchlist observations.
- **Derived from:** `research/generated/watchlist_observations.json`
- **Future M3B-02 Behavior:** Aggregates counts.
- **AI Treatment:** AI must read this as descriptive and non-actionable (no trading signals).

## `failed_sources`
- **Purpose:** Provides visibility into sources that are offline or failing.
- **Required fields:** List of source identifiers.

## `failed_targets`
- **Purpose:** Lists specific symbols/targets that failed retrieval.

## `freshness_and_delay_summary`
- **Purpose:** Details `delay_status` and `staleness_seconds` mapped from the snapshot.
- **AI Treatment:** Prevents AI from assuming data is universally real-time.

## `ai_may_say`
- **Purpose:** Lists exactly what claims the AI is allowed to make.
- **Derived from:** M3 guardrails and v2 policy.
- **AI Treatment:** Strict whitelist for generative AI outputs.

## `ai_must_not_claim`
- **Purpose:** Lists prohibited claims.
- **Derived from:** M3 guardrails and v2 policy.
- **AI Treatment:** Strict blacklist for generative AI outputs.

## `mandatory_caveats`
- **Purpose:** Lists fundamental warnings about unofficial APIs, third-party data, and data staleness.
- **AI Treatment:** These must be displayed whenever summarizing data.

## `prohibited_interpretations`
- **Purpose:** Examples of bad interpretations of data to ensure AI understands what constitutes a signal violation.

## `next_actions`
- **Purpose:** Recommended next tasks for the agent or user, such as verifying source endpoints or resolving failures.
