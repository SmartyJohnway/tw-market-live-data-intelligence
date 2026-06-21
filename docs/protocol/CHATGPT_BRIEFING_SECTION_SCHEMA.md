# ChatGPT Briefing Section Schema

This document defines the schema for each required section in the future `chatgpt_briefing.md` artifact.

## 1. generated_metadata
- **Purpose:** To provide timestamps and basic metadata regarding when the briefing was generated and from what context pack version.
- **Required Input Fields:**
  - `pack_version`
  - `generated_at_utc`
  - `generated_at_taipei`
  - `generation_mode`
- **Required Output Wording:** Must explicitly list the generation timestamp and schema version.
- **Optional Output Wording:** None.
- **AI-Safety Treatment:** Ensures the AI knows the exact timestamp of generation to anchor any time-sensitive queries.
- **Caveats:** Must state that the timestamp is the generation time of the briefing, not necessarily the freshness of the market data.
- **Future M3C-02 Generator Behavior:** Extract fields directly from the top-level keys in the JSON context pack.

## 2. current_scope
- **Purpose:** To define the bounding box of the data provided in the briefing.
- **Required Input Fields:**
  - `target_support_summary.bounded_watchlist_only`
  - `target_support_summary.full_market_coverage`
  - `target_support_summary.target_count`
  - `target_support_summary.failed_target_count`
  - `target_support_summary.target_classes_observed`
  - `target_support_summary.target_classes_failed`
  - `target_support_summary.target_support_caveats`
- **Required Output Wording:** Must state explicitly whether the scope is bounded or full-market. (e.g., "This briefing is bounded to the configured watchlist." and "Full market coverage: false").
- **Optional Output Wording:** Number of symbols in the watchlist scope.
- **AI-Safety Treatment:** Prevents the AI from hallucinating that it has a view of the entire market.
- **Caveats:** Emphasize that symbols outside the configured scope are fundamentally unobservable.
- **Future M3C-02 Generator Behavior:** Hard-check the `target_support_summary` boolean fields and generate explicit boolean-like statements.

## 3. source_health
- **Purpose:** To provide a high-level overview of which sources are functioning or failing.
- **Required Input Fields:**
  - `source_health_summary.total_sources`
  - `source_health_summary.source_ids`
  - `source_health_summary.unavailable_or_failed_sources`
  - `source_health_summary.offline_not_attempted_sources`
  - `source_health_summary.auth_required_sources`
  - `source_health_summary.doc_only_sources`
  - `source_health_summary.source_health_caveats`
- **Required Output Wording:** Must summarize the operational health of tracked sources.
- **Optional Output Wording:** None.
- **AI-Safety Treatment:** Establishes context that partial data or missing sources are due to system health, not zero-value data.
- **Caveats:** Mention if offline mode was active, which forces source failures.
- **Future M3C-02 Generator Behavior:** Summarize the operational status based on `source_health_summary`.

## 4. source_authority
- **Purpose:** To strictly distinguish the provenance and authority of the data.
- **Required Input Fields:**
  - `source_authority_summary.official_reference`
  - `source_authority_summary.unofficial_frontend`
  - `source_authority_summary.third_party`
  - `source_authority_summary.broker_authenticated`
  - `source_authority_summary.usable_live_sources`
  - `source_authority_summary.usable_eod_sources`
  - `source_authority_summary.doc_only_sources`
  - `source_authority_summary.auth_required_sources`
  - `source_authority_summary.source_authority_caveats`
- **Required Output Wording:** Must clearly classify sources into their respective authority levels.
- **Optional Output Wording:** Brief definitions of what "unofficial" means in this context.
- **AI-Safety Treatment:** Prevents the AI from treating third-party or unofficial data as a definitive source of truth equivalent to official Exchange endpoints.
- **Caveats:** Emphasize the lack of guarantees on unofficial sources.
- **Future M3C-02 Generator Behavior:** Group and list sources by their established authority classification from `source_authority_summary`.

## 5. market_session_status
- **Purpose:** To inform whether the market is open, closed, or in an unknown state.
- **Required Input Fields:**
  - `latest_snapshot_summary.market_session_status`
- **Required Output Wording:** Must clearly output the current session status.
- **Optional Output Wording:** Context on regular trading hours if applicable.
- **AI-Safety Treatment:** Ensures the AI knows if price action should be expected or if it's looking at static closing prices.
- **Caveats:** Session status might be unknown or inferred.
- **Future M3C-02 Generator Behavior:** Output the canonical session string.

## 6. latest_snapshot_summary
- **Purpose:** To provide an overview of the snapshot data volume.
- **Required Input Fields:**
  - `latest_snapshot_summary.target_count`
  - `latest_snapshot_summary.symbol_count`
  - `latest_snapshot_summary.failed_symbol_count`
  - `latest_snapshot_summary.failed_source_count`
  - `latest_snapshot_summary.global_caveats`
- **Required Output Wording:** Must output the total number of tracked symbols and the total number of failed symbols.
- **Optional Output Wording:** None.
- **AI-Safety Treatment:** Reinforces partial or failed states.
- **Caveats:** A high failure count means the snapshot is severely degraded.
- **Future M3C-02 Generator Behavior:** Parse the snapshot summary to extract and format these counts.

## 7. watchlist_observation_summary
- **Purpose:** To summarize the qualitative observations generated.
- **Required Input Fields:**
  - `watchlist_observation_summary.observations_count`
  - `watchlist_observation_summary.failed_observations_count`
  - `watchlist_observation_summary.observation_type_counts`
  - `watchlist_observation_summary.severity_counts`
  - `watchlist_observation_summary.categories_present`
  - `watchlist_observation_summary.global_caveats`
- **Required Output Wording:** Must include the number of successful observations and the number of failed observations.
- **Optional Output Wording:** None.
- **AI-Safety Treatment:** Explicitly uses the word "observation" to avoid "signal" semantics.
- **Caveats:** "The available observations are descriptive only and not trading signals."
- **Future M3C-02 Generator Behavior:** Extract observation counts from `watchlist_observation_summary`.

## 8. failed_sources
- **Purpose:** To detail exactly which sources are not functioning.
- **Required Input Fields:**
  - `failed_sources[].source_id`
  - `failed_sources[].source_type`
  - `failed_sources[].authority_level`
  - `failed_sources[].error_type`
  - `failed_sources[].affected_symbol_count`
  - `failed_sources[].caveats`
- **Required Output Wording:** Must summarize `source_id`, `error_type`, `affected_symbol_count`, and associated caveats for each.
- **Optional Output Wording:** None.
- **AI-Safety Treatment:** Explicitly highlights missing data.
- **Caveats:** Must note if the failure is due to offline execution.
- **Future M3C-02 Generator Behavior:** Iterate over `failed_sources` and render a list or table.

## 9. failed_targets
- **Purpose:** To detail exactly which symbols failed to resolve.
- **Required Input Fields:**
  - `failed_targets[].symbol`
  - `failed_targets[].target_class`
  - `failed_targets[].failure_reason`
  - `failed_targets[].source_attempts`
  - `failed_targets[].caveats`
- **Required Output Wording:** Must summarize `symbol`, `target_class`, `failure_reason`, `source_attempts`, and associated caveats for each.
- **Optional Output Wording:** None.
- **AI-Safety Treatment:** Exposes exactly what is unobservable.
- **Caveats:** None beyond the reason itself.
- **Future M3C-02 Generator Behavior:** Iterate over `failed_targets` and render a concise list.

## 10. freshness_delay_staleness
- **Purpose:** To provide critical context on the timing of the data.
- **Required Input Fields:**
  - `freshness_and_delay_summary.freshness_status_counts`
  - `freshness_and_delay_summary.delay_status_counts`
  - `freshness_and_delay_summary.stale_count`
  - `freshness_and_delay_summary.unknown_freshness_count`
  - `freshness_and_delay_summary.eod_reference_count`
  - `freshness_and_delay_summary.live_candidate_count`
  - `freshness_and_delay_summary.summary_caveats`
- **Required Output Wording:** Must include exact counts for stale, unknown freshness, EOD reference, and live candidates, plus summary caveats.
- **Optional Output Wording:** Definitions of staleness thresholds if defined.
- **AI-Safety Treatment:** Destroys the illusion of real-time trading capabilities for delayed data.
- **Caveats:** Emphasize that "live candidates" are not officially guaranteed realtime.
- **Future M3C-02 Generator Behavior:** Aggregate these metrics and print them distinctly.

## 11. ai_may_say
- **Purpose:** To guide the LLM on acceptable topics.
- **Required Input Fields:**
  - `ai_may_say[]`
- **Required Output Wording:** Direct copy of the array items as bullet points.
- **Optional Output Wording:** None.
- **AI-Safety Treatment:** Positive reinforcement of safe boundaries.
- **Caveats:** None.
- **Future M3C-02 Generator Behavior:** Iterate and format as a Markdown list.

## 12. ai_must_not_claim
- **Purpose:** To strictly forbid the LLM from making dangerous claims.
- **Required Input Fields:**
  - `ai_must_not_claim[]`
- **Required Output Wording:** Direct copy of the array items as bullet points.
- **Optional Output Wording:** None.
- **AI-Safety Treatment:** Hard guardrail against hallucinated signals and advice.
- **Caveats:** None.
- **Future M3C-02 Generator Behavior:** Iterate and format as a Markdown list.

## 13. mandatory_caveats
- **Purpose:** To enforce the global disclaimers of the project.
- **Required Input Fields:**
  - `mandatory_caveats[]`
- **Required Output Wording:** Direct copy of the array items as bullet points.
- **Optional Output Wording:** None.
- **AI-Safety Treatment:** Protects the consumer from misunderstanding the system's intent.
- **Caveats:** None.
- **Future M3C-02 Generator Behavior:** Iterate and format as a Markdown list.

## 14. suggested_safe_questions
- **Purpose:** To provide the consumer with examples of safe interactions.
- **Required Input Fields:**
  - static safe-question list from `CHATGPT_BRIEFING_POLICY.md`
- **Required Output Wording:** Must include examples that are purely informational (e.g., "Which sources failed?").
- **Optional Output Wording:** None.
- **AI-Safety Treatment:** Steers the user and AI away from signal-seeking behavior.
- **Caveats:** Suggested questions must not encourage trading decisions.
- **Future M3C-02 Generator Behavior:** Output a predefined list of safe questions aligned with the policy.
