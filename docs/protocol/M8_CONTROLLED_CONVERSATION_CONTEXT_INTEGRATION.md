# M8 Controlled Conversation Context Integration

Status: `m8_00_06_controlled_conversation_context_integration_defined`

## 1. Purpose

Define a pure projection from the M8 multi-source market context into a controlled AI-readable conversation context. The projection preserves useful caveated context while preventing realtime, authority, and trading-interpretation mistakes.

## 2. Input: `m8_00_multi_source_market_context.v1`

The input is the already-built M8-00-05 multi-source context payload. This integration does not fetch, parse, poll, schedule, or adapt any source.

## 3. Output: `m8_controlled_conversation_context.v1`

The output schema is produced by `scripts/m8_controlled_conversation_context.py` and contains schema versions, status, one M8 section, source summaries, projected instrument contexts, caveats, markdown, and guardrail booleans.

## 4. Projection rules

- Include freshness summary, source summaries, cross-source caveats, forbidden interpretations, and safety booleans.
- Include instrument `safe_fields` only when top-level policy and per-source policy allow it.
- Scrub forbidden raw fields from projected safe fields and markdown.
- Preserve EOD/reference, stale, manual, validation-only, credential-gated, unknown, and live-ish caveats.

## 5. Safe-to-include vs metadata-only vs blocked

- `ready`: policy allows context and no caveats are required.
- `ready_with_caveats`: policy allows context and caveats are required.
- `metadata_only`: instrument values are withheld, but safe metadata/caveats are useful.
- `blocked`: schema is wrong, no useful safe metadata exists, or forbidden raw fields are detected after projection.

## 6. Unknown source safe_fields withholding

Unknown source IDs or unknown freshness assessments do not project instrument safe fields into conversation context. They may appear only as source/instrument metadata with the caveat `unknown source safe_fields withheld from conversation context`.

## 7. Caveat propagation

Projection carries builder cross-source caveats and adds compatibility caveats for EOD not realtime, retrieved-at not exchange timestamp, stale not current, manual not official, validation-only not primary, credential-gated not runtime dependency, and live-ish not guaranteed streaming/realtime.

## 8. Markdown rendering policy

Markdown is deterministic and concise. It includes status, freshness summary, source caveats, instrument contexts, and the guardrail line: `This context is not trading advice, not a recommendation, and not a trading signal.` It must not render raw payloads, bid/ask ladders, recommendations, target prices, support/resistance, rankings, or bullish/bearish labels.

## 9. Non-goals

- no network
- no adapter
- no runtime endpoint
- no frontend
- no MCP
- no M8A

## 10. Next task

`M8-00-08-FINAL-ACCEPTANCE-AND-CLOSURE`
