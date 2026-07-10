# M7G Safe Context Artifact Schema and Manifest

Status: `m7g_safe_context_artifact.v1` / `m7g_safe_context_manifest.v1`

Schema version: `m7g_safe_context_artifact.v1`. Manifest version: `m7g_safe_context_manifest.v1`.

A valid artifact contains safe projection metadata, `safe_for_frontend: true`, `safe_for_ai_handoff: true`, all raw exposure flags set to false, an `artifact_manifest`, `market_clock_session_state`, `governance`, and `observations`.

Each observation is a safe projection only, for example symbol, display name, market, source, retrieval timestamp, price-like value, change percent, volume candidate, best bid candidate, best ask candidate, and semantic caveats.

Forbidden keys in artifact, observation, and handoff: `raw_payload`, `twse_mis_rich_facts`, `raw_rich_facts`, `raw_unknown_facts`, `full_ladder`, `bid_prices`, `ask_prices`, `source_investigation_notes`, `response_sample`, `raw_fields_sample`.

These keys may appear only in catalog metadata, omission notice, and test assertions. They must not appear as values in loaded artifact observations.
