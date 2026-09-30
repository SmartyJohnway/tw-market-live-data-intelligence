# Phase I I2-A1 — TX Regular-Session Source & Evidence Contract

Status: `FROZEN_PASS`

Owner decision reference: `USER_CHAT_2026-09-30_PHASE_I_I2_A1_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_FREEZE`

Authoritative JSON: [PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json](PHASE_I_I2_TX_REGULAR_SESSION_SOURCE_EVIDENCE_CONTRACT_2026-09-30_FROZEN.json)
JSON SHA-256: `6d535e34defb1e82947f64ceec6df5e1859888fb3550e36e6ded1b6a7573d4fb`

## Scope and authority

I2 v1 freezes the optional `index_futures_context` evidence contract for the
TAIFEX TX standard monthly outright, regular-session series. It is descriptive
market context, not a trading signal. This freeze does not authorize A2 runtime
implementation, an I2 route/source activation, live acquisition, merge, I3 or
Phase J.

The sole source is TAIFEX OAS `DailyMarketReportFut` at
`https://openapi.taifex.com.tw/v1/DailyMarketReportFut`, under the official OAS
authority at `https://openapi.taifex.com.tw/swagger.json`. Its government
open-data association is dataset 11319, **期貨每日交易行情**, published by the
Financial Supervisory Commission Securities and Futures Bureau under Open
Government Data License v1.0; attribution is required. That authority applies
only to this dataset and endpoint, not to other TAIFEX services, realtime feeds,
paid historical products, or all TAIFEX website content.

## Product and identity

Eligible context association is limited to TWSE `company_share/common_share`.
TPEx is unsupported because TX's stated underlying is TAIEX and an equivalent
direct relationship to TPEx instruments is not established. Cash instruments
retain ISIN durable identity and `market + security_code` routing identity.
The derivative product is `TAIFEX/TX`; a derivative series is
`TAIFEX/TX/YYYYMM`; observations are at series, official trade date, and
trading-session grain. Futures series are not Security Master cash identities.

Only source `TradingSession == 一般` is eligible and normalizes to `regular`.
Select the maximum valid Gregorian compact `Date` first, without ROC conversion
or fallback to an older date. On that date select exact `Contract == TX`,
`TradingSession == 一般`, and `ContractMonth(Week)` full-matching
`^[0-9]{6}$` with month `01..12`; exclude weekly and slash-containing spread
values, then choose the minimum valid `YYYYMM`. The final binding must be unique.
No rollover calendar, execution-clock guess, volume/OI inference, or product
fallback is permitted.

## Transport and evidence

Future A2 transport is one GET per governed execution, zero retries, 30-second
timeout, HTTP 200 only, 2 MiB response cap, 5,000 root-row cap, redirects
rejected, and no raw payload persistence, cache/history, polling, scheduler,
or background refresh. Accept UTF-8 JSON arrays (UTF-8-SIG only where existing
transport convention permits), including the observed `application/octet-stream`
media type and normal JSON media type. Do not support CSV. Validate bytes,
decode, JSON, root type, row bound, deterministic selection, selected fields,
then normalized evidence; fail closed at every invalid stage.

The evidence schema is
`schemas/index_futures_context_evidence.v1.schema.json`. It distinguishes
`complete`, `partial`, `unavailable`, `source_failed`, and `binding_failed`.
Complete requires a unique selection, valid date and all required market
observations. Best bid/ask may be absent or null. Partial may carry explicit
missing fields; malformed numeric input is never silently converted to missing.
Units remain explicit: prices and point change are `index_point`, percent is
percentage-scale `percent` (e.g. `-0.74%` becomes `-0.74`, not `-0.0074`), and
volume/open interest are `contract_count`. `-`, `NULL`, and permitted empty
markers mean missing, never zero.

Currentness remains `unknown`. Capture one governed execution/acquisition
reference timestamp for normalized `retrieved_at`; preserve the individual HTTP
retrieval timestamp in transport telemetry. Alignment is descriptive against
the TWSE FMTQIK benchmark trade date only: same date means
`same_trade_date_non_simultaneous_close`, different date means
`different_trade_date`, absent benchmark means `not_comparable`, and unusable
I2 evidence means `unavailable`. Equal dates do not mean simultaneous closes.

No bullish/bearish, leading/lagging, sentiment, manipulation, basis,
premium/discount, or target-specific causation interpretation is allowed.
No notional, leverage, implied-return, continuous-contract, or historical
high/low interpretation is defined by this contract.

## A0 preflight observation

The Owner-executed bounded A0 probe is recorded in
`PHASE_I_I2_A0_TX_REGULAR_SESSION_GO_NO_GO_PREFLIGHT_2026-09-30.json`.
It observed HTTP 200, `application/octet-stream`, 813057 bytes, SHA-256
`7a35adfc030aba52378dcc5e68a1bcfd90082d4a065b3fff891a365e9fa9370b`, 2156
rows, source Date `20260929`, both `一般` and `盤後`, one GET and zero retries.
The selected TX regular row was `202610` with the original source values retained
in the A0 record. The payload included calendar-spread rows such as
`202610/202611`, confirming the six-digit outright selector requirement. The
raw response is not included in the repository.

## Dormant boundary

At A1 close: I1 remains active with three sources; I2 has zero active sources,
zero normal production routes, and no executor; `index_futures_context` remains
non-executable. MCP remains six tools. I3 is not started and broader Phase I is
incomplete. Compatible future A2 requests are intended to batch as `same_source`
and share one source acquisition, but this A1 does not implement that route.
