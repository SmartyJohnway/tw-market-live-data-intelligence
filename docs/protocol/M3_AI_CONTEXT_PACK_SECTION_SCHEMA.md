# M3 AI Context Pack Section Schema

This document defines the detailed schema for each major section of the AI Market Context Pack.

## `pack_metadata`
- **Purpose**: Provides generation context and versioning.
- **Required fields**: `pack_version`, `generated_at_utc`, `generated_at_taipei`, `generation_mode`.
- **Optional fields**: None.
- **Allowed values**: `generation_mode` must be one of `["design_only", "offline_generation"]`.
- **Source documents**: N/A (Generated dynamically).
- **Future generator handling**: Populated automatically with current timestamps.
- **AI Agent treatment**: Authoritative for freshness of the context pack itself.

## `source_contract_baseline`
- **Purpose**: A summary representation of `docs/protocol/M2_SOURCE_CONTRACT_BASELINE.md`.
- **Required fields**: `baseline_version`, `total_sources`, `official_sources_count`, `unofficial_sources_count`.
- **Optional fields**: None.
- **Source documents**: `docs/protocol/M2_SOURCE_CONTRACT_BASELINE.md`.
- **Future generator handling**: Extracted and counted automatically from the baseline document.
- **AI Agent treatment**: Informational summary of the available source universe.

## `source_summaries`
- **Purpose**: Details capabilities, authority, and safety rules for each individual source.
- **Required fields**: `source_id`, `source_type`, `authority_level`, `freshness_status`, `delay_status`, `m3_eligibility`, `ai_safe_usage`, `must_show_caveats`, `prohibited_interpretations`.
- **Optional fields**: `access_status` (public, auth_required, doc_only) to provide finer granularity on current usability.
- **Allowed values**:
  - `source_type`: `official_openapi`, `unofficial_frontend_endpoint`, `unofficial_api`, `third_party_api`, `commercial_api`, `broker_api`, `doc_only`, `auth_required`.
  - `authority_level`: `official_public_exchange_eod`, `unofficial_frontend`, `third_party`, `third_party_commercial`, `authenticated_provider`, `broker_authenticated`, `doc_only`, `unknown`.
  - `freshness_status`: `eod_batch`, `realtime_candidate_or_stale`, `delayed`.
  - `m3_eligibility`: `allowed_as_official_eod_reference`, `allowed_only_with_caveats`, `not_eligible_current_repo`.
- **Source documents**: Protocol documents (e.g., `TWSE_MIS_PROTOCOL.md`), `docs/source_catalog.md`.
- **Future generator handling**: Populated by mapping source registry definitions.
- **AI Agent treatment**: **Authoritative.** AI agents must strictly obey `prohibited_interpretations` and surface `must_show_caveats`.

## `target_taxonomy_summary`
- **Purpose**: Lists recognized asset classes.
- **Required fields**: `asset_classes` (array of strings).
- **Source documents**: `docs/protocol/TARGET_TAXONOMY.md`.
- **Future generator handling**: Extracts keys from taxonomy definitions.
- **AI Agent treatment**: Authoritative list of supported market segments.

## `source_target_support_summary`
- **Purpose**: Maps which sources support which target classes.
- **Required fields**: A mapping of `source_id` to a nested object mapping `asset_class` to `support_status`.
- **Allowed values for `support_status`**: `supported_observed`, `supported_candidate`, `observed_unsupported`, `unsupported`, `auth_required`, `doc_only`, `unknown`, `deferred`.
- **Source documents**: `docs/protocol/SOURCE_TARGET_SUPPORT_MATRIX.md`.
- **Future generator handling**: Directly reflects the verified matrix.
- **AI Agent treatment**: Authoritative. AI must explicitly communicate when support is only "candidate" or "unknown".

## `freshness_and_delay_summary`
- **Purpose**: Explicitly maps source freshness.
- **Required fields**: A mapping of `source_id` to an object containing `freshness_category` and `known_delay_seconds`.
- **Source documents**: M2 baseline contracts, protocol definitions.
- **Future generator handling**: Parsed from source capability definitions.
- **AI Agent treatment**: Authoritative. AI must use this to explain data latency to users.

## `normalized_sample_summaries`
- **Purpose**: Provides AI agents with the expected shape of normalized data.
- **Required fields**: `contract_id`, `contract_version`, `expected_fields`, `always_present_fields`, `optional_fields`.
- **Source documents**: `docs/contracts/*`.
- **Future generator handling**: Extracts schema from v1 markdown contracts.
- **AI Agent treatment**: AI agents use this to understand data structure. They must assume optional fields might be missing or represented as empty lists.

## `ai_usage_guardrails`
- **Purpose**: Defines overarching global rules for AI behavior.
- **Required fields**: `global_rules` (array of strings), `strict_prohibitions` (array of strings).
- **Source documents**: `docs/protocol/M3_AI_CONTEXT_GUARDRAILS.md`.
- **Future generator handling**: Static injection from the guardrails document.
- **AI Agent treatment**: **Critical rules of engagement.** Must never be violated.

## `known_caveats`
- **Purpose**: Global or system-wide caveats not specific to a single source.
- **Required fields**: Array of caveat strings.
- **Future generator handling**: Aggregated from global documentation.
- **AI Agent treatment**: General warnings to consider during query resolution.

## `prohibited_uses`
- **Purpose**: Explicit global prohibitions (trading, signals, execution).
- **Required fields**: Array of prohibition strings.
- **Source documents**: `docs/protocol/M3_AI_CONTEXT_GUARDRAILS.md`.
- **Future generator handling**: Static injection.
- **AI Agent treatment**: **Critical.** Actions AI must refuse to perform.

## `next_actions` / `deferred_items`
- **Purpose**: Tracks missing capabilities or future work.
- **Optional fields**: Array of task strings or capability gaps.
- **AI Agent treatment**: Informational; useful for explaining why certain data is unavailable.