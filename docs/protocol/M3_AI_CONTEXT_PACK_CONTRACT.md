# M3 AI Context Pack Contract

## 1. Purpose

The purpose of the AI Market Context Pack is to provide a standardized, AI-readable, offline-generated snapshot of Taiwan equity market data capabilities. It bridges the gap between raw source protocol documentation (e.g., TWSE, TPEx, Yahoo Finance) and AI agents (e.g., ChatGPT, Claude) that need to answer user queries safely and reliably without hallcuinating capabilities, data freshness, or source authority.

This contract defines the structured format that the future context pack generator must produce and that AI agents must strictly consume as a trusted baseline.

## 2. Intended Consumers

1. **AI Agents / LLMs:** To understand what market data is supported, whether it is live/delayed/stale, and what risks or caveats exist for specific data sources.
2. **Developers / Reviewers:** To rapidly verify the current baseline capability matrix without needing to run network probes or read complex test outputs.
3. **Future AI Tools:** As a foundational, low-latency reference schema for dynamic watchlist resolution and context-injection.

## 3. Explicit Non-Goals

The AI context pack and its contract explicitly **DO NOT** aim to:
1. Provide a live intraday trading feed.
2. Provide full-market crawling or high-frequency polling data.
3. Recommend, endorse, rank, or provide investment/trading advice (buy/sell/hold).
4. Implement automated execution or order placement semantics.
5. Hide unofficial, third-party, or broker sources as "official."
6. Compute, synthesize, or infer missing pricing data.

## 4. Required Top-Level Sections

The AI Context Pack JSON artifact must conform to the following top-level structure:

```json
{
  "pack_version": "string",
  "generated_at_utc": "ISO-8601 string",
  "generated_at_taipei": "ISO-8601 string",
  "generation_mode": "string",
  "source_contract_baseline": {},
  "source_summaries": [],
  "target_taxonomy_summary": {},
  "source_target_support_summary": {},
  "freshness_and_delay_summary": {},
  "normalized_sample_summaries": [],
  "ai_usage_guardrails": {},
  "known_caveats": [],
  "prohibited_uses": [],
  "next_actions": []
}
```

## 5. Source Attribution Requirements

Every piece of data must be attributable to a registered source. The contract requires:
- `source_id`: The canonical identifier (e.g., `TWSE_MIS`, `TWSE_OpenAPI`).
- `source_type`: Must distinguish between `official_openapi`, `unofficial_frontend_endpoint`, `third_party_api`, `broker_api`, etc.
- `authority_level`: Explicit categorization (e.g., `official_public_exchange_eod`, `unofficial`).

## 6. Freshness and Staleness Requirements

The context pack must explicitly state the temporal reliability of the data:
- `freshness_status`: (e.g., `eod_batch`, `realtime_candidate_or_stale`).
- `delay_status`: Must be clearly defined (e.g., `eod`, `20m_delayed`, `realtime`).
- EOD (End of Day) sources must not be misrepresented as intraday feeds.

## 7. Target Taxonomy Requirements

Target markets and assets must be explicitly modeled based on `docs/protocol/TARGET_TAXONOMY.md`:
- Distinguish between explicit target classes (e.g., TWSE large caps, TPEx stocks, ETFs, Options).
- Use canonical taxonomy keys (e.g., `twse_stock`, `tpex_stock`, `twse_etf`).

## 8. Support Status Requirements

The context pack must reflect the strict matrix defined in `docs/protocol/SOURCE_TARGET_SUPPORT_MATRIX.md`:
- Allowed status labels: `supported_observed`, `supported_candidate`, `observed_unsupported`, `unsupported`, `auth_required`, `doc_only`, `unknown`, `deferred`.
- Unverified or inferred support must remain visibly unverified (e.g., `supported_candidate`).
- Multiple combined statuses per cell are prohibited (e.g., no "unknown/auth_required").

## 9. Source Caveat Requirements

Caveats are mandatory and must be preserved verbatim in AI summaries:
- `must_show_caveats`: An array of explicit warnings (e.g., `unofficial_endpoint`, `rate_limit_risk`, `not_intraday_live_feed`, `schema_drift_possible`).
- AI Agents must surface these caveats to users if quoting data from these sources.

## 10. Normalized Sample Summary Requirements

To assist AI Agents in understanding the data shape:
- The pack may include summarized, standardized JSON data contracts.
- Missing optional arrays must not be omitted from the schema; they must be represented as `[]` with a corresponding warning in `data_quality_flags`.

## 11. Guardrail Requirements

A mandatory block defining what AI Agents cannot do:
- Explicit enumeration of `prohibited_interpretations` and `ai_safe_usage` per source.
- Refer to `docs/protocol/M3_AI_CONTEXT_GUARDRAILS.md` for the full set of usage guardrails.

## 12. Future Generator Requirements

The future generator that produces this JSON artifact (in M3-02) must:
- Be entirely deterministic based on offline input documents.
- Run without active network probing by default.
- Fail validation if mandatory caveats or guardrails are missing.
- Refer to `docs/protocol/M3_AI_CONTEXT_PACK_GENERATOR_REQUIREMENTS.md` for specific validation logic.