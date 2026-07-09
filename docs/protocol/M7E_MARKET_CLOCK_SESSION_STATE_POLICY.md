# M7E Market Clock and Session State Policy

Status:
- policy_and_pure_builder

Scope:
- market clock/session-state semantic layer
- TW market timezone handling
- supplied TWSE holiday schedule record classification
- observation freshness/currentness labeling
- AI language guardrails

Not in scope:
- controlled AI-safe promotion
- shared conversation context integration
- FastAPI integration
- MCP integration
- frontend UI changes
- live probes
- network fetching
- official full exchange calendar engine
- trading signals
- recommendations

## M7E sequence

1. M7E-00 policy/schema
2. M7E-01 pure builder
3. M7E-02 controlled promotion
4. M7E-03 shared context integration
5. M7E-04 final acceptance

## Future official calendar source candidate

TWSE OpenAPI holiday schedule endpoint is documented as a future official calendar source candidate:

- URL: `https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule`
- Source family: `TWSE_OpenAPI_holidaySchedule`
- Expected record shape includes `Name`, `Date`, `Weekday`, and `Description`.

M7E-00/01 does not fetch this endpoint. It only classifies supplied records. No runtime download, live probe, cached production data, or network dependency is added in this phase.

## ROC date conversion

The TWSE holiday schedule `Date` field uses ROC/Minguo `YYYMMDD`, not Gregorian `YYYYMMDD`.

- `1150101` means Gregorian `2026-01-01`.
- Conversion rule: Gregorian year = ROC year + 1911.
- Malformed, impossible, non-digit, wrong-length, or non-positive ROC-year values must be rejected by the parser.

## The `交易日` trap

The endpoint contains both non-trading dates and explicit trading-day labels. A record whose `Name` contains the exact substring `交易日` is an explicit trading-day label and must not be treated as an endpoint holiday closure solely because it appears in the endpoint.

Examples of explicit trading-day labels:

- `國曆新年開始交易日`
- `農曆春節前最後交易日`
- `農曆春節後開始交易日`

Names such as `市場無交易，僅辦理結算交割作業` do not contain `交易日` and are classified as endpoint non-trading dates.

## Non-trading rule

Initial M7E-00/01 policy uses:

1. all Saturdays and Sundays as non-trading by independent weekday rule; and
2. supplied endpoint records whose `Name` does not contain `交易日` as endpoint non-trading dates.

Endpoint records whose `Name` contains `交易日` are recorded as explicit trading-day labels and excluded from endpoint-holiday closure classification. Weekend closure remains independent unless future official evidence and policy explicitly support special Saturday/Sunday trading.

## Session-state terms

Timezone: `Asia/Taipei`.

Initial TWSE regular-session heuristics:

- `preopen`: `08:00 <= local time < 09:00`
- `regular_open`: `09:00 <= local time < 13:30`
- `postclose`: `13:30 <= local time < 14:30`
- `closed`: local time before `08:00` or at/after `14:30`
- `weekend_closed`: Saturday or Sunday
- `holiday_closed`: weekday date classified from supplied endpoint records as non-trading
- `unknown` / `holiday_or_unknown`: degraded or insufficient calendar evidence

This is a semantic guardrail layer, not a full official exchange calendar engine.

## Freshness and currentness terms

Timestamp fields may be read from `retrieved_at_utc`, `retrieved_at`, `observation_time_utc`, `generated_at_utc`, or `created_at_utc`.

Freshness thresholds:

- `fresh`: age <= 180 seconds
- `recent`: 180 < age <= 900 seconds
- `stale`: age > 900 seconds
- `future_timestamp`: timestamp more than 60 seconds after `now_utc`
- `no_observation`: no latest observation or no usable timestamp
- `invalid_timestamp`: unusable timestamp value

Currentness labels:

- `live_candidate`: regular-session candidate, trading-day candidate, and fresh observation
- `recent_but_unverified`: regular-session candidate, trading-day candidate, and recent observation
- `reference_only`: stale, post-close, or closed reference context
- `not_current`: preopen, weekend, or holiday closure context
- `degraded_unknown`: missing, invalid, future, or otherwise unknown evidence

## AI language guardrails

Allowed language examples:

- latest observed context
- latest retrieved observation
- reference-only context
- during regular-session candidate
- not verified as live
- session-state unknown
- weekday heuristic only
- holiday schedule records supplied

Blocked language examples:

- currently rising
- currently falling
- market is now moving
- live trading signal
- buy signal
- sell signal
- recommendation
- target price
- support
- resistance
- capital flow
- sector rotation
- full-market breadth

M7E-00/01 builder output remains `safe_for_ai_context = false` and `builder_output_safe_for_ai_context = false`. Controlled AI-safe promotion is deferred to M7E-02.

## M7E-02 Controlled Promotion

M7E-02 adds a controlled projection layer for market-clock/session-state output. The pure builder output remains **not** safe for direct AI conversation context: `safe_for_ai_context` remains `false` in the builder candidate and `builder_output_safe_for_ai_context` remains `false` in both builder and promoted outputs.

Only `promote_market_clock_session_state_for_controlled_context(...)` may convert a valid `m7e_market_clock_session_state.v1` candidate into the AI-safe `m7e_market_clock_session_state_controlled_context.v1` shape. The promoted shape includes bounded session/currentness semantics such as session state, freshness state, calendar confidence, currentness label, semantic caveats, and an AI currentness summary. It does not include raw market payloads, TWSE MIS rich facts, unknown raw facts, source response samples, bid/ask ladder arrays, or investigation notes.

Malformed candidates fail closed with `safe_for_ai_context=false`, `exposure_status=ai_safe_context_disabled`, and explicit non-exposure flags. Controlled promotion is descriptive governance context only; it does not create a trading signal, recommendation, market prediction, capital-flow claim, full-market breadth claim, target price, support/resistance level, or sector-rotation claim.

## M7E-03 Shared Context Integration

M7E-03 integrates only the promoted M7E controlled context into the shared M5N conversation package under `market_clock_session_state`. The conversation builder derives a pure M7E candidate from the latest observation timestamp fields already supplied to the package builder, then immediately promotes it and returns only the promoted safe projection.

The integration is pure and performs no network requests, no runtime TWSE `holidaySchedule` fetch, no live probe, no scheduler/polling, and no file writes from the helper. Supplied holiday-schedule records may be passed in by tests or deterministic callers; when absent, M7E preserves the weekday-heuristic caveat and does not claim official holiday correctness.

The shared `ai_guidance_summary` includes M7E currentness fields and a currentness-language guardrail so downstream AI can distinguish live-candidate, recent-but-unverified, reference-only, not-current, and degraded-unknown cases. Markdown handoff renders a Market Clock / Currentness section before the latest observation summary. M7E contextualizes whether latest observations may be discussed as live/current, but it never converts observations into trading signals or recommendations.

## M7E-04 Final Acceptance

M7E final acceptance is recorded in:

`docs/protocol/M7E_MARKET_CLOCK_SESSION_STATE_FINAL_ACCEPTANCE.md`

Final status: `pass_with_caveats`.

M7E is accepted as a governed market-clock/session-state semantic layer for AI conversation context. It remains descriptive only and does not implement trading signals, recommendations, official full exchange-calendar coverage, live probes, runtime holidaySchedule fetching, FastAPI/MCP/frontend changes, or M7F operator UI.

## M7E-05 TWSE Trading Calendar Authority

M7E-05 establishes a shared TWSE trading-calendar authority based on controlled normalization of TWSE OpenAPI holidaySchedule records. Runtime M7E consumers must not fetch holidaySchedule implicitly. Mode A / Mode B / Mode C should use the shared resolver for TWSE trading-day checks.
