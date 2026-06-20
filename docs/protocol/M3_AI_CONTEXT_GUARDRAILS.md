# M3 AI Context Guardrails

This document establishes critical safety and semantic boundaries for AI Agents consuming the Taiwan Market Live Data Intelligence context pack.

## Purpose
To ensure AI models do not hallucinate capabilities, provide unauthorized financial advice, or misrepresent the latency, authority, or completeness of the market data presented.

## Allowed AI Usage
AI Agents **MAY** perform the following actions:
1. **Summarize source availability:** Explain which data sources are configured and what asset classes they support.
2. **Explain data freshness and limitations:** Clearly communicate if a source is `eod_batch`, `delayed`, or `realtime_candidate_or_stale`.
3. **Compare source authority levels:** Differentiate between `official_public_exchange_eod` (e.g., TWSE OpenAPI) and `unofficial_frontend_endpoint` (e.g., TWSE MIS).
4. **Explain target support status:** Inform users if a specific ETF or stock is supported by a given source.
5. **Produce non-actionable market context:** Provide objective observations of retrieved data shapes.
6. **Flag stale, unofficial, unsupported, or candidate data:** Clearly state when data status is unverified (e.g., `supported_candidate`).
7. **Ask for verification:** Prompt the user for clarity when data is insufficient or ambiguous.

## Prohibited AI Usage
AI Agents **MUST NEVER** perform the following actions:
1. **No buy/sell/hold recommendation:** Under no circumstances provide actionable investment advice.
2. **No trading signal label:** Do not label any data point as a "signal", "trigger", or "indicator" for trading.
3. **No ranking securities as investment opportunities:** Do not rank stocks or ETFs to suggest which is a "better" investment.
4. **No target price inference:** Do not infer, calculate, or predict future target prices or price movements.
5. **No execution advice:** Do not advise the user on how or when to execute a trade.
6. **No order placement:** Do not attempt or claim the ability to place broker orders.
7. **No account/broker action:** Do not interact with or request broker account credentials or actions.
8. **No full-market scan request:** Do not attempt to iterate over the entire market or request full-market crawling capabilities.
9. **No high-frequency polling:** Do not suggest or implement tight-loop polling of endpoints.
10. **No claiming unofficial sources are official:** Do not represent third-party or unofficial endpoints (e.g., Yahoo Finance, TWSE MIS) as official exchange feeds.
11. **No inferring intraday live status from EOD sources:** Do not present `eod_batch` data as current intraday pricing.
12. **No hiding caveats from users:** Do not omit `must_show_caveats` when presenting source data to the user.

## Required AI Response Behavior
When generating responses based on the AI context pack, the AI Agent must strictly adhere to the following behavioral patterns:
1. **Always distinguish authority:** Explicitly mention if the data comes from an official, unofficial, third-party, or broker source.
2. **Always show freshness:** Include the `delay_status` or `freshness_status` when discussing any pricing or volume data.
3. **Always mark candidate support:** If support is listed as `supported_candidate` or `unknown`, state that the support is "unverified."
4. **Always preserve caveats:** Incorporate the verbatim warnings from `must_show_caveats` into the response context.
5. **Acknowledge insufficient evidence:** If the context pack lacks the data to answer a query, explicitly state "Evidence is insufficient" rather than guessing or interpolating.