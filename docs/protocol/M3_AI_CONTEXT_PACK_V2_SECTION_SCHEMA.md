# M3 AI Context Pack v2 Section Schema

This document defines the schema and purpose of each section within the AI Context Pack v2. Every section is concrete enough to guide the M3B-02 generator implementation and validation.

## `pack_metadata`
1. **Purpose:** Identifies the current context pack generation event.
2. **Required fields:** `pack_version`, `generated_at_utc`, `generated_at_taipei`, `generation_mode`.
3. **Optional fields:** None.
4. **Allowed values:** `pack_version` must be `m3_ai_context_pack_v2_draft` (or stable version), `generation_mode` is `design_only`.
5. **Source documents:** Generated internally by the script.
6. **Future M3B-02 Behavior:** Generated entirely offline without network calls.
7. **AI agent treatment:** Read to understand the timestamp context.
8. **Caveats:** None.

## `source_contract_baseline`
1. **Purpose:** Informs AI about current canonical sources mapped in the system.
2. **Required fields:** `canonical_sources`, `official_eod_sources`, `unofficial_live_candidate_sources`, `third_party_context_sources`, `auth_required_sources`, `doc_only_sources`, `unsupported_or_deferred_sources`, `source_contract_caveats`.
3. **Optional fields:** None.
4. **Allowed values:** Example shape:
```json
{
  "source_contract_baseline": {
    "canonical_sources": [
      "TWSE_MIS",
      "Yahoo_Finance",
      "TWSE_OpenAPI",
      "TPEx_OpenAPI",
      "FinMind",
      "Fugle",
      "Fubon"
    ],
    "official_eod_sources": [
      "TWSE_OpenAPI",
      "TPEx_OpenAPI"
    ],
    "unofficial_live_candidate_sources": [
      "TWSE_MIS"
    ],
    "third_party_context_sources": [
      "Yahoo_Finance",
      "FinMind"
    ],
    "auth_required_sources": [
      "Fugle",
      "Fubon"
    ],
    "doc_only_sources": [
      "Fugle",
      "Fubon"
    ],
    "unsupported_or_deferred_sources": [],
    "source_contract_caveats": [
      "official_openapi_sources_are_eod_reference_only",
      "twse_mis_is_unofficial_frontend_candidate",
      "third_party_sources_require_caveats",
      "broker_sources_are_auth_required_or_doc_only"
    ]
  }
}
```
5. **Source documents:** Derived from M2/M3 source contract documents.
6. **Future M3B-02 Behavior:** Will pull statically and summarize this from existing source-contract documents, not from live probes.
7. **AI agent treatment:** Used to understand system capability scope.
8. **Caveats:** Must not imply that sources currently blocked or requiring authentication are accessible.

## `source_health_summary`
1. **Purpose:** Describes the availability of the sources based on offline probes.
2. **Required fields:** `passing_sources`, `failing_sources`, `auth_required_sources`, `blocked_sources`.
3. **Optional fields:** Status counts.
4. **Allowed values:** Numeric counts and arrays of source identifiers.
5. **Source documents:** Derived from M2 source baseline data capabilities.
6. **Future M3B-02 Behavior:** Derives cleanly from the pre-generated capabilities matrix.
7. **AI agent treatment:** Must strictly acknowledge if sources are failing.
8. **Caveats:** Does not imply real-time live health in this offline-generated context.

## `source_authority_summary`
1. **Purpose:** Designates official vs third-party vs unofficial sources to prevent AI from inflating data authority.
2. **Required fields:** `official_reference`, `unofficial_frontend`, `third_party`.
3. **Optional fields:** None.
4. **Allowed values:** Lists of source identifiers mapped to these categories.
5. **Source documents:** M2 Source Contract Baseline.
6. **Future M3B-02 Behavior:** Strictly segregates TWSE MIS (unofficial) from EOD OpenAPI (official) systematically.
7. **AI agent treatment:** AI must never elevate unofficial or third-party sources to official realtime authority.
8. **Caveats:** Must carry caveats when dealing with unofficial APIs like TWSE MIS.

## `target_support_summary`
1. **Purpose:** Describes support coverage and scope for specific target classes. It must describe support and scope, not market movement and not investment quality.
2. **Required fields:** `target_classes_observed`, `target_classes_supported_candidate`, `target_classes_unsupported`, `target_classes_unknown`, `bounded_watchlist_only`, `full_market_coverage`, `target_support_caveats`.
3. **Optional fields:** None.
4. **Allowed values:** Example shape:
```json
{
  "target_support_summary": {
    "target_classes_observed": [
      "twse_common_stock",
      "tpex_common_stock",
      "twse_etf",
      "twse_tdr",
      "twse_index",
      "taifex_index_future",
      "mutual_fund"
    ],
    "target_classes_supported_candidate": [],
    "target_classes_unsupported": [],
    "target_classes_unknown": [],
    "bounded_watchlist_only": true,
    "full_market_coverage": false,
    "target_support_caveats": [
      "support_summary_describes_configured_watchlist_scope_only",
      "does_not_claim_full_market_coverage",
      "some_target_classes_may_have_failed_or_offline_observations"
    ]
  }
}
```
5. **Source documents:** TARGET_TAXONOMY.md and SOURCE_TARGET_SUPPORT_MATRIX.md.
6. **Future M3B-02 Behavior:** Extracted directly from protocol docs.
7. **AI agent treatment:** Sets the context of what asset types the AI can speak about safely.
8. **Caveats:** Does not claim full-market support if the target is observed but bounded by the watchlist.

## `latest_snapshot_ref`
1. **Purpose:** Strict reference pointer to the snapshot file.
2. **Required fields:** `path`.
3. **Optional fields:** None.
4. **Allowed values:** Set exactly to `"research/generated/latest_market_snapshot.json"`.
5. **Source documents:** Static pointer.
6. **Future M3B-02 Behavior:** Output as a static string.
7. **AI agent treatment:** Used as a reference link.
8. **Caveats:** AI must not attempt to fetch this file via network tools if it is meant to be offline.

## `latest_snapshot_summary`
1. **Purpose:** Aggregates a summary of the snapshot without exposing raw payloads.
2. **Required fields:** `total_symbols_tracked`, `snapshot_generated_at`.
3. **Optional fields:** `snapshot_generation_mode`.
4. **Allowed values:** Integers and ISO-8601 timestamps.
5. **Source documents:** `research/generated/latest_market_snapshot.json`
6. **Future M3B-02 Behavior:** Aggregates top-level snapshot metadata strictly excluding all raw market data records.
7. **AI agent treatment:** Used to establish the current bounding of the snapshot data.
8. **Caveats:** This summary does not contain trade data; it only establishes bounds.

## `watchlist_observations_ref`
1. **Purpose:** Strict reference pointer.
2. **Required fields:** `path`.
3. **Optional fields:** None.
4. **Allowed values:** Set exactly to `"research/generated/watchlist_observations.json"`.
5. **Source documents:** Static pointer.
6. **Future M3B-02 Behavior:** Output as a static string.
7. **AI agent treatment:** Reference link only.
8. **Caveats:** None.

## `watchlist_observation_summary`
1. **Purpose:** Provides a count and high-level categorization of watchlist observations.
2. **Required fields:** `total_observations`, `categories_present`.
3. **Optional fields:** Detailed counts per category.
4. **Allowed values:** Integers and arrays of defined observation categories.
5. **Source documents:** `research/generated/watchlist_observations.json`
6. **Future M3B-02 Behavior:** Aggregates counts offline deterministically.
7. **AI agent treatment:** AI must read this as descriptive and non-actionable.
8. **Caveats:** Does not provide signals; descriptive only.

## `failed_sources`
1. **Purpose:** Preserves enough information about failing sources for AI safety to avoid hallucinations.
2. **Required fields:** `source_id`, `source_type`, `authority_level`, `error_type`, `affected_symbol_count`, `caveats`.
3. **Optional fields:** None.
4. **Allowed values:** Mapped source details and strict error categorizations.
5. **Source documents:** `research/generated/latest_market_snapshot.json` (failed_sources block).
6. **Future M3B-02 Behavior:** Maps and summarizes from the snapshot.
7. **AI agent treatment:** Must explicitly state that data is unavailable for these sources.
8. **Caveats:** If a source fails, no data from it should be assumed or imputed.

## `failed_targets`
1. **Purpose:** Lists specific symbols/targets that failed retrieval safely.
2. **Required fields:** `symbol`, `target_class`, `failure_reason`, `source_attempts`, `caveats`.
3. **Optional fields:** None.
4. **Allowed values:** Mapped symbols and reasons (e.g. `unsupported_target`, `network_error`).
5. **Source documents:** `research/generated/latest_market_snapshot.json`.
6. **Future M3B-02 Behavior:** Mapped systematically from snapshot.
7. **AI agent treatment:** AI must explicitly note unavailability for these specific targets.
8. **Caveats:** No data should be forward-filled for failed targets.

## `freshness_and_delay_summary`
1. **Purpose:** Details delay and staleness to accurately contextualize constraints on "real-time" data claims.
2. **Required fields:** `freshness_status_counts`, `delay_status_counts`, `stale_count`, `unknown_freshness_count`, `eod_reference_count`, `live_candidate_count`, `summary_caveats`.
3. **Optional fields:** None.
4. **Allowed values:** Integers and mapping dictionaries.
5. **Source documents:** `research/generated/latest_market_snapshot.json` metadata fields.
6. **Future M3B-02 Behavior:** Aggregates freshness fields deterministically.
7. **AI agent treatment:** Prevents AI from assuming data is universally real-time.
8. **Caveats:** Crucial for bounding AI claims about market activity.

## `ai_may_say`
1. **Purpose:** Lists exactly what claims the AI is allowed to make.
2. **Required fields:** Array of strings outlining allowed statements.
3. **Optional fields:** None.
4. **Allowed values:** String constraints from v2 policy.
5. **Source documents:** M3 guardrails and v2 policy.
6. **Future M3B-02 Behavior:** Extracted statically.
7. **AI agent treatment:** Strict whitelist for generative AI outputs.
8. **Caveats:** Statements outside this whitelist risk hallucination.

## `ai_must_not_claim`
1. **Purpose:** Lists prohibited claims to prevent signal generation.
2. **Required fields:** Array of strings outlining prohibited claims.
3. **Optional fields:** None.
4. **Allowed values:** String constraints from v2 policy.
5. **Source documents:** M3 guardrails and v2 policy.
6. **Future M3B-02 Behavior:** Extracted statically.
7. **AI agent treatment:** Strict blacklist for generative AI outputs.
8. **Caveats:** Must not be ignored under any circumstances.

## `mandatory_caveats`
1. **Purpose:** Lists fundamental warnings about unofficial APIs, third-party data, and data staleness that must be presented.
2. **Required fields:** Array of caveat strings.
3. **Optional fields:** None.
4. **Allowed values:** Static caveat strings.
5. **Source documents:** Defined globally across M3 protocols.
6. **Future M3B-02 Behavior:** Included consistently in all output packs.
7. **AI agent treatment:** These must be displayed whenever summarizing data.
8. **Caveats:** Cannot be hidden in footnotes.

## `prohibited_interpretations`
1. **Purpose:** Examples of bad interpretations of data to ensure AI understands what constitutes a signal violation.
2. **Required fields:** Array of bad example strings.
3. **Optional fields:** None.
4. **Allowed values:** Predefined examples of prohibited interpretations.
5. **Source documents:** V2 policy.
6. **Future M3B-02 Behavior:** Extracted statically.
7. **AI agent treatment:** Uses as negative few-shot examples for reasoning boundaries.
8. **Caveats:** None.

## `next_actions`
1. **Purpose:** Recommended next tasks for the agent or user, such as verifying source endpoints or resolving failures.
2. **Required fields:** Array of strings for next steps.
3. **Optional fields:** None.
4. **Allowed values:** Descriptive tasks.
5. **Source documents:** Determined dynamically based on failures, or statically defined.
6. **Future M3B-02 Behavior:** Generated based on the presence of failed sources or targets.
7. **AI agent treatment:** Provides structured follow-up guidance.
8. **Caveats:** None.
