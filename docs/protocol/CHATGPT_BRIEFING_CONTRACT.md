# ChatGPT Briefing Contract

## 1. Purpose
This document defines the contract for the future ChatGPT Market Briefing generator (M3C-02). The briefing is designed to be a human-readable and AI-copyable Markdown output that summarizes the conservative AI context pack. The goal is to provide a safe, bounded, and clear snapshot of the market based purely on the generated `ai_context_pack.json`, without claiming to be a live trading feed or offering market advice.

## 2. Intended Consumers
The primary intended consumers of the output `chatgpt_briefing.md` are:
- Human researchers or users copying the text.
- Large Language Models (LLMs) such as ChatGPT, Gemini, or Claude when the briefing is pasted as context.
- Future read-only MCP integrations.

## 3. Explicit Non-Goals
The briefing generation process and the generated artifact explicitly do **not**:
- Act as a live trading signal.
- Provide buy, sell, or hold recommendations, target prices, or rankings.
- Represent an official real-time quote feed.
- Hide or mask missing, stale, or failed source capabilities.
- Encourage execution of any trades.
- Act as a full-market coverage indicator.

## 4. Relationship to AI Context Pack v2
The ChatGPT briefing is strictly a projection of the `research/generated/ai_context_pack.json`. It takes the heavily structured JSON fields (such as scope, source health, and mandatory caveats) and translates them into a simple Markdown representation optimized for language models to read efficiently.

## 5. Required Input Artifacts
The future generator must strictly rely on the following existing artifacts:
- **Mandatory Input:** `research/generated/ai_context_pack.json`
- **Optional Reference Input:** `research/generated/ai_context_pack.md`

The generator must **not** parse raw endpoints, run live network calls, or fetch any raw payloads. It relies solely on the context pack.

## 6. Required Output Artifact
The future generator must produce:
`research/generated/chatgpt_briefing.md`

*(Note: Do not generate this artifact as part of M3C-01. This is for the future M3C-02 generator).*

## 7. Required Briefing Sections
The generated briefing must contain the following sections:
- Generated Metadata
- Current Scope
- Source Health
- Source Authority
- Market Session Status
- Latest Snapshot Summary
- Watchlist Observation Summary
- Failed Sources
- Failed Targets
- Freshness / Delay / Staleness
- What AI May Say
- What AI Must Not Claim
- Mandatory Caveats
- Suggested Safe Questions

## 8. Mandatory Caveat Propagation
Any mandatory caveats found in `ai_context_pack.json` must be faithfully propagated to the ChatGPT briefing. The generator must ensure that the briefing clearly emphasizes that it does not serve as financial advice or an official live feed. If the generated context is an offline failure envelope, the briefing must state this unambiguously:

*Example formulation:*
"The current generated context is bounded to the configured watchlist. The latest snapshot contains no successful symbols and all tracked targets are failed/offline. No live market movement summary can be safely produced from this artifact."

## 9. Source Authority and Freshness Propagation
The briefing must preserve source authority distinctions (e.g., distinguishing between official EOD reference batches, unofficial/third-party sources, and document-only categories). Freshness, staleness, and delay statuses must also be distinctly stated so the consumer knows if the data is stale or real-time.

## 10. Failed Source / Failed Target Visibility
Errors, missing fields, failed sources, and failed targets must be prominently displayed. The briefing must summarize counts and list failures so the LLM understands what data is missing from the snapshot.

## 11. Observation vs Signal Boundary
The briefing must enforce a strict boundary between an observation and a signal. Observations are descriptive ("The close was X"). Signals are prescriptive ("X is undervalued, buy"). The briefing is explicitly limited to descriptive observations.

## 12. AI-Copyable Wording Constraints
The briefing must use plain, simple language that is clear for AI models to interpret without hallucinating additional context. The structure must be direct, avoiding ambiguous phrasing that could lead an AI to infer a trading signal.

## 13. Prohibited Claims
The briefing must strictly avoid making the following claims:
- "The market is live" (unless strictly verified).
- "This data is an official real-time feed."
- "There is a strong signal for [Symbol]."
- "The entire market is covered."
- Any claim suggesting that trading or execution should be based on this data.

## 14. Future Generator Behavior
The future generator script (in M3C-02) must operate deterministically in an offline manner. It must read the `ai_context_pack.json` and output the `chatgpt_briefing.md` without any network calls, raw payload interactions, or mutation of upstream artifacts.

## 15. Acceptance Criteria for M3C-02
For the future generator implementation:
- `chatgpt_briefing.md` is successfully generated.
- All required sections (metadata, scope, source health, etc.) are present.
- Mandatory caveats, failures, and freshness metrics are explicitly visible.
- No trading advice or prohibited claims are present.
- The generator runs completely offline, performing no network operations.
- The generator fails clearly if `ai_context_pack.json` is missing.
- Tests confirm adherence to these policies.
