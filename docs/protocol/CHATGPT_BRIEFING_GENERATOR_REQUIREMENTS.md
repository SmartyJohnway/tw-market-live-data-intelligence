# ChatGPT Briefing Generator Requirements

This document outlines the strict behavioral and output requirements for the future `M3C-02` implementation of the ChatGPT Briefing Generator.

**Note:** This is a design specification only. M3C-01 strictly prohibits the implementation of this generator.

## 1. Required Inputs
The future generator must use the following generated artifacts as its source of truth:
- **Mandatory Input:** `research/generated/ai_context_pack.json`
- **Optional Reference Input:** `research/generated/ai_context_pack.md`

The future M3C-02 generator must treat the M3B-02 AI Context Pack v2 top-level structure as the source of truth. It must not assume alternative wrapper objects such as `metadata.*` or `scope.*` unless a future contract revision introduces them.

## 2. Required Outputs
The future generator must output exactly one artifact:
- `research/generated/chatgpt_briefing.md`

## 3. Required Behavior Constraints
The generator script must strictly adhere to the following behavioral rules:
1. **Offline Deterministic Generation:** The generation must be fully offline and deterministic.
2. **No Live Network Calls:** It must absolutely not make any HTTP requests to data providers (e.g., TWSE, Yahoo, Fugle, etc.).
3. **No Raw Endpoint Parsing:** It must not attempt to parse raw endpoint payloads directly. It must strictly depend on the heavily structured `ai_context_pack.json`.
4. **Immutability of Inputs:** It must not mutate, modify, or regenerate `ai_context_pack.json` or `ai_context_pack.md`.
5. **Preservation of Caveats:** It must faithfully preserve all mandatory caveats listed in the context pack.
6. **Preservation of Failures:** It must preserve visibility of failed sources and failed targets without masking them.
7. **Preservation of Scope:** It must preserve the "bounded watchlist scope" assertion (`full_market_coverage = false`).
8. **Preservation of Authority:** It must clearly document source authority distinctions as described in the context pack.
9. **Preservation of Freshness:** It must preserve freshness, delay, and staleness summaries.
10. **Observation vs Signal Boundary:** It must preserve the strict boundary that observation does not equal a signal.
11. **No Trading Advice:** It must strictly avoid synthesizing any form of trading advice (buy, sell, hold).
12. **No Prohibited Syntheses:** It must not generate rankings, target prices, trading signals, strategies, backtests, broker recommendations, or execution logic.
13. **Failure State:** The generator must fail clearly (e.g., `SystemExit(1)`) if `research/generated/ai_context_pack.json` is missing or unreadable.

## 4. Future Validation Requirements for M3C-02
The future PR that implements this generator must pass the following checks:
1. `chatgpt_briefing.md` is successfully generated on demand.
2. The briefing includes the `generated_metadata` section.
3. The briefing explicitly declares a bounded scope and `full_market_coverage=false`.
4. The briefing accurately lists source health and source authority classifications.
5. The briefing clearly states the total failed source count and failed target count.
6. The briefing accurately surfaces freshness, delay, and staleness caveats.
7. The briefing features the exact "What AI May Say" and "What AI Must Not Claim" sections.
8. All mandatory global caveats from the system are present.
9. The briefing suggests safe questions for LLM interactions.
10. The briefing contains absolutely no prohibited trading language outside of explicitly labeled prohibited examples.
11. The briefing does not falsely claim the market is live or that there is official realtime full-market coverage unless explicit future system configuration supports it.
12. The generator passes existing offline CI pipelines flawlessly without causing network-dependent test regressions.

**Strict Schema Parsing Validation:**
1. Generator reads top-level `pack_version`, `generated_at_utc`, `generated_at_taipei`, and `generation_mode` from `ai_context_pack.json`.
2. Generator reads scope from `target_support_summary`, not from a non-existent `scope` object.
3. Generator reads source health from `source_health_summary`, not from a non-existent `source_health` object.
4. Generator reads market session status from `latest_snapshot_summary.market_session_status`.
5. Generator fails clearly if required M3B-02 top-level sections are missing.
