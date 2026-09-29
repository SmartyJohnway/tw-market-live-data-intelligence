---
title: "Phase I I0 — Evidence Value, Source, Identity & Timing Decision Record"
document_id: "PHASE_I_I0_EVIDENCE_VALUE_SOURCE_IDENTITY_TIMING_DECISION_RECORD_V1_0_0_FROZEN"
status: "FROZEN_PASS"
date: "2026-09-29"
timezone: "Asia/Taipei"
baseline_main: "a7b7f17df424229510fa6950f4cb5cb1b6b15f77"
phase: "I"
subphase: "I0"
implementation_authorized: true
live_activation_authorized: false
phase_i_implementation_started: false
---

# Phase I I0 — Evidence Value, Source, Identity & Timing Decision Record

## 0. Document Status

This document is the **Owner-approved frozen I0 pre-implementation decision contract** for Phase I.

Owner approval authority:

```text
OWNER_DECISION = OWNER_ACCEPTED_I0_AND_AUTHORIZED_I1_IMPLEMENTATION
OWNER_DECISION_REF = USER_CHAT_2026-09-29_PHASE_I_I0_OWNER_ACCEPTANCE
I0_STATUS = FROZEN / PASS
I1_IMPLEMENTATION_AUTHORIZED = true
I2_IMPLEMENTATION_AUTHORIZED = false
PHASE_I_LIVE_ACTIVATION_AUTHORIZED = false
PHASE_I_PRODUCTION_ROUTE_ACTIVATION_AUTHORIZED = false
```

It consolidates:

- Roadmap V3.2 Phase I intent and Evidence Value Gate;
- Phase G–M Deep Research Preflight findings;
- official TPEx and TAIFEX OpenAPI specifications downloaded on 2026-09-29;
- bounded manual live probes performed on 2026-09-29;
- architectural continuity from Phase G and Phase H.

This document is **FROZEN / PASS** as of 2026-09-29 after explicit Owner approval.

The authorization boundary is:

```text
PHASE_I_I0_FROZEN = true
PHASE_I_I1_IMPLEMENTATION_AUTHORIZED = true
PHASE_I_I2_IMPLEMENTATION_AUTHORIZED = false
PHASE_I_LIVE_ACTIVATION_AUTHORIZED = false
PHASE_I_PRODUCTION_ROUTE_ACTIVATION_AUTHORIZED = false
PHASE_I_MERGE_AUTHORIZED = false
```

Authorization permits the first bounded **I1 implementation tranche only**. It does not authorize I2 implementation, live activation, production route activation, merge, background acquisition, scheduler/polling, or Phase J.

---

# 1. Executive Decision

## 1.1 Phase I product definition

Phase I is not a general market-data expansion phase.

Phase I is:

> **Optional Interpretation Context — bounded, official market context loaded only when the current research question requires it.**

The purpose is to reduce situations in which an AI has correct target evidence but still lacks enough surrounding market context to interpret that evidence safely.

Phase I must not turn Unified Result into a market-data encyclopedia, investment analytics engine, sentiment engine, signal engine, strategy engine, backtester, or historical warehouse.

## 1.2 Recommended implementation sequence

```text
I0 — Context Contract & Source Decision

I1 — Market State Context
     TWSE + TPEx

I2 — TAIFEX TX Regular-Session Context

I3 — Selective Positioning Context
     separate future Evidence Value / Owner gate

I4 — Other Optional Relationships
     only when a concrete research use case proves value
```

Decision status:

```text
I1 Market State Context                  = ADD FIRST
I2 TX Regular-Session Context            = ADD NEXT
I3 Positioning Context                   = DEFER / SEPARATE GATE
Industry Performance Context             = DEFER
Options / PCR / Large-Trader Context     = DEFER
Day-Trading Context                      = DO NOT ADD IN V1
ETF Exact Holdings                       = DO NOT ADD IN V1
```

## 1.3 Existing invariants remain frozen

Phase I must preserve:

```text
Unified public Request / Result / Audit V3 remains preferred
exactly six MCP tools
installation-local Taiwan Market Identity Service
cash-security durable identity = ISIN
market + security_code remains routing identity
explicit bounded execution
execute-once semantics
missing / partial / failure remain distinct
citation + lineage + audit remain mandatory
no trading / order routing / broker credentials
no hidden background acquisition
no database-for-database's-sake
no silent source fallback
```

---

# 2. Continuity with Phase G and Phase H

Phase G addressed:

> **Do not let AI analyze without reliable official research facts.**

Phase H addressed:

> **Do not let AI misinterpret correct facts because market rules, corporate actions, or historical reference context are missing.**

Phase I extends the same philosophy:

> **Do not let AI mistake a local movement for a market-wide movement, or a market-wide movement for a target-specific event, merely because necessary surrounding context was absent.**

Therefore Phase I adds context, not conclusions.

TW-Market may provide observable facts such as benchmark state, breadth, turnover, futures contract state, session, volume, settlement, and open interest.

TW-Market must not canonically declare:

```text
bullish
bearish
leading
lagging
smart money
institutional sentiment
market manipulation
sector leader
outperformance signal
reversal signal
```

Those are interpretation layers for the AI/human conversation, not canonical evidence fields.

---

# 3. Evidence Basis and Deep-Probe Findings

## 3.1 Roadmap authority

Roadmap V3.2 requires every new Phase I evidence family to pass an Evidence Value Gate covering source authority, interpretation value, timing semantics, normalization, missing-state risk, default-vs-optional loading, over-interpretation risk, and resource cost.

Roadmap also requires Phase I context to remain explicit / AI-selected / bounded and forbids default loading of all derivatives, financing, institutional, ETF, and breadth data for every target.

## 3.2 Official OAS evidence

### TPEx OpenAPI

Official server:

```text
https://www.tpex.org.tw/openapi/v1
```

Relevant source contracts discovered:

```text
/tpex_mainborad_highlight
/tpex_trading_volume_ratio
/mopsfin_t187ap03_O
/tpex_3insti_daily_trading
/tpex_mainboard_margin_balance
/tpex_margin_sbl
/tpex_short_sell
```

### TAIFEX OpenAPI

Official server:

```text
https://openapi.taifex.com.tw/v1
```

Relevant source contracts discovered:

```text
/DailyMarketReportFut
/DailyMarketReportOpt
/PutCallRatio
/MarketDataOfMajorInstitutionalTradersDetailsOfFuturesContractsBytheDate
/OpenInterestOfLargeTradersFutures
/ContractAdj
/SSFLists
/FinalSettlementPrice*
```

## 3.3 Bounded live-probe observations — 2026-09-29

These values are probe observations, not permanent source-size guarantees.

| Source | Observed bytes | Observed rows | Observed date scope | Decision relevance |
|---|---:|---:|---|---|
| TPEx `/tpex_mainborad_highlight` | 430 | 1 | 1150924 | Ideal bounded market-state source |
| TPEx `/tpex_trading_volume_ratio` | 3,884 | 28 | 1150924 only | Sector turnover mix, not sector return |
| TPEx `/mopsfin_t187ap03_O` | 1,280,121 | 893 | 1150928 reference snapshot | Suitable reference enrichment; not per-request market evidence |
| TAIFEX `/DailyMarketReportFut` | 808,945 | 2,147 | 20260924 only | Full daily futures snapshot; bounded by one GET, local filtering required |
| TAIFEX `/PutCallRatio` | 2,923 | 19 | 20260831–20260924 | Technically easy, interpretation-risk high |
| TAIFEX institutional futures | 33,967 | 66 | 20260924 only | Product-level participant positioning, not expiry-series positioning |

Key findings:

1. TPEx market state is extremely compact and semantically clean.
2. TPEx company-to-industry metadata is a large reference snapshot and must not be treated as per-request live market context.
3. TPEx sector trading-weight data is turnover composition, not industry price performance.
4. TAIFEX daily futures is a single-day whole-market snapshot rather than an unbounded history feed.
5. TAIFEX `DailyMarketReportFut` contains both `一般` and `盤後` observations for the same product/series/date.
6. TAIFEX institutional futures data is product-level (`臺股期貨`, `電子期貨`, etc.) and participant-level (`自營商`, `投信`, `外資及陸資`), not contract-month level.
7. TAIFEX live transport returned `application/octet-stream` even though the OAS advertises JSON/CSV media types; the payload is UTF-8 JSON bytes and therefore requires explicit transport normalization.

---

# 4. Evidence Value Gate Decisions

| Evidence family | Source quality | Interpretation value | Timing / identity complexity | Misuse risk | I0 decision |
|---|---|---|---|---|---|
| Market benchmark state | High | Very High | Low | Low | **ADD I1** |
| Market breadth | High | Very High | Low | Low | **ADD I1** |
| Market turnover | High | High | Low | Low | **ADD I1** |
| Industry classification | High | Medium-High | Low-Medium | Low | **REFERENCE / DEFER** |
| Industry turnover mix | High | Medium | Low | Medium | **DEFER** |
| Industry price-performance context | Asymmetric | High | Medium | Low | **DEFER** |
| TX regular-session futures context | High | High | Medium | Medium | **ADD I2** |
| TX after-hours context | High | Medium-High | High | Medium | **DEFER** |
| Options market context | High | Medium | High | High | **DEFER** |
| Put/Call ratio | High | Medium | Low | Very High | **DEFER** |
| TAIFEX institutional positioning | High | Medium-High | Medium | Very High | **DEFER I3** |
| Cash-market institutional flow | Mixed symmetry | High | Medium | High | **DEFER I3** |
| Margin financing | High | Medium-High | Medium | High | **DEFER I3** |
| Short / SBL context | High / mixed surface terms | Medium-High | Medium | High | **DEFER I3** |
| Large-trader OI | Available | Medium | Medium | Very High | **DEFER** |
| Day-trading statistics | High | Low-Medium | Low | Medium | **DO NOT ADD V1** |
| ETF AUM / beneficiaries | Available | Low-Medium | Medium | Low | **DEFER** |
| ETF exact holdings / weights | Fragmented | Medium | High | Medium | **DO NOT ADD V1** |

`DEFER` does not mean permanently rejected. It means the family may not enter implementation merely because official data exists; it requires a separate evidence-value decision.

---

# 5. I1 Contract — Market State Context

## 5.1 Logical capability

Working logical evidence family:

```text
market_state_context
```

This is a conceptual contract name. Exact wire-schema field names/versioning are not frozen by I0 and must be added additively to the existing V3 architecture.

## 5.2 Supported v1 target scope

Initial scope:

```text
TWSE company_share / common_share
TPEx company_share / common_share
```

The market context is market-level evidence associated with the target's market. Multiple targets in the same market within one governed operation should share one normalized market-state fetch result rather than refetching per target.

## 5.3 Official source mapping

### TWSE

```text
/exchangeReport/FMTQIK
/opendata/twtazu_od
```

Rules:

- `FMTQIK` provides official benchmark / turnover evidence.
- `twtazu_od` breadth must select the official row whose `類型` is exactly `股票` for stock breadth semantics.
- Do not silently substitute `整體市場` breadth for stock breadth.

### TPEx

```text
/tpex_mainborad_highlight
```

This single source provides benchmark, breadth, trading value and trading volume.

## 5.4 Required normalized semantics

I1 evidence should expose only source-supported observable semantics, including as available:

```text
market
trade_date
benchmark_identifier
benchmark_close_or_index_value
benchmark_change
breadth_up
breadth_limit_up
breadth_down
breadth_limit_down
breadth_flat
breadth_unmatched_or_unavailable
turnover_value
turnover_volume
source_unit_metadata
retrieved_at
currentness_status
source_reference
citation / lineage
missing / partial state
```

Rules:

- Do not invent percentage change if the source does not provide it and no governed derivation contract exists.
- Do not normalize monetary/volume units unless the official source proves the unit.
- Different exchange transports may remain different internally; only semantic normalization is required.

## 5.5 I1 bounded execution contract

Initial bounded design:

```text
TWSE market context:
  <= 2 unique official source GETs per governed execution

TPEx market context:
  <= 1 unique official source GET per governed execution

same-market multi-target:
  reuse the same in-memory market context
  no per-target refetch

implicit retry:
  none in v1 unless an existing frozen global transport contract explicitly requires otherwise

raw full-response persistence:
  prohibited by default

allowed durable telemetry:
  source URL / source family
  retrieval timestamp
  response byte count
  response hash where governed
  normalized evidence
  citation / lineage
```

No background refresh, polling, scheduler, history DB, or market-wide archive is authorized.

## 5.6 Missing / partial semantics

I1 must distinguish at least:

```text
complete
partial
unavailable
source_failed
binding_failed / unsupported_market where applicable
```

Examples:

- benchmark succeeds but breadth fails => `partial`, not fabricated complete evidence;
- breadth source contains no exact stock-universe row => fail closed for breadth;
- unsupported target market => no executable I1 operation.

---

# 6. I2 Contract — TAIFEX TX Regular-Session Context

## 6.1 Logical capability

Working logical evidence family:

```text
index_futures_context
```

I2 v1 is deliberately narrow:

```text
venue = TAIFEX
product = TX
session = 一般
series = nearest available standard monthly outright series
```

No options, no after-hours, no participant positioning and no single-stock derivatives in I2 v1.

## 6.2 Official source

Primary source:

```text
https://openapi.taifex.com.tw/v1/DailyMarketReportFut
```

Official OAS fields include:

```text
Date
Contract
ContractMonth(Week)
Open
High
Low
Last
Change
%
Volume
SettlementPrice
OpenInterest
BestBid
BestAsk
TradingHalt
TradingSession
```

I2 v1 does not need every available source field in the normalized result.

## 6.3 Deterministic row selection

For the governed official futures trade date:

```text
1. Contract == "TX"
2. TradingSession == "一般"
3. ContractMonth(Week) matches exactly six decimal digits: ^[0-9]{6}$
4. exclude calendar spreads such as 202610/202611
5. choose the minimum valid YYYYMM contract period present in the official dataset
```

This uses actual official rows rather than maintaining an independent rollover calendar.

If no row satisfies the contract, return explicit unavailable / unsupported state; do not guess a contract.

## 6.4 Derivatives identity boundary

Cash identity remains unchanged and must not be polluted by derivatives identity.

### Cash security

```text
durable identity = ISIN
routing identity = market + security_code
```

### Derivative product identity

Conceptual identity:

```text
venue = TAIFEX
product_code = TX
```

### Derivative series identity

Conceptual identity:

```text
venue
product_code
contract_period
```

Example:

```text
TAIFEX / TX / 202610
```

### Observation identity / grain

Session belongs to the observation grain, not the durable product identity:

```text
product series
+ official trade_date
+ trading_session
```

This distinction is mandatory because the live dataset contains both `一般` and `盤後` rows for the same `TX + contract period + Date`.

## 6.5 Normalized I2 evidence

I2 v1 may expose:

```text
venue
product_code
contract_period
trade_date
trading_session
open
high
low
last
change
change_percent
volume
settlement_price
open_interest
retrieved_at
alignment_status
source_reference
citation / lineage
missing / partial state
```

Do not derive investment signals from these fields.

## 6.6 Spot–derivatives timing contract

The official trade date is not equivalent to simultaneous observation time.

I2 must expose timing honestly.

Minimum alignment semantics:

```text
same_trade_date_non_simultaneous_close
different_trade_date
not_comparable
unavailable
```

Rules:

- same official trade date may be used as descriptive market context;
- it must not be described as simultaneous spot/futures pricing;
- `盤後` rows are excluded from I2 v1;
- after-hours effective-date attribution is deferred to a later contract;
- if the source does not publish an exact observation timestamp, do not invent one; use official `trade_date` plus `retrieved_at`.

## 6.7 TAIFEX live transport normalization

Observed live behavior on 2026-09-29:

```text
HTTP status    = 200
Content-Type   = application/octet-stream
payload        = UTF-8 JSON bytes
observed bytes = 808,945
observed rows  = 2,147
observed date  = 20260924 only
```

The official OAS advertises JSON/CSV content, therefore the adapter must explicitly support the observed transport quirk:

```text
HTTP body bytes
→ bounded byte validation
→ UTF-8 decode
→ JSON parse
→ schema / required-field validation
```

Unexpected binary content, invalid UTF-8, invalid JSON, unexpected root shape, missing required fields, or resource-bound violation must fail closed.

Do not treat HTTP `Content-Type` alone as proof that payload semantics are valid JSON.

## 6.8 I2 bounded execution contract

Initial design:

```text
<= 1 DailyMarketReportFut GET per governed I2 execution
no implicit retry in v1
local in-memory deterministic filter only
no raw payload persistence by default
no historical backfill
no daily collector
no background polling
no scheduler
```

The 808,945-byte / 2,147-row live observation is an empirical baseline, not a permanent hard cap. A fail-closed maximum response size/row budget must be frozen before I2 production activation.

---

# 7. Grain Separation — Institutional Futures Must Not Be Joined to Expiry Series

TAIFEX institutional futures source:

```text
/MarketDataOfMajorInstitutionalTradersDetailsOfFuturesContractsBytheDate
```

Observed live grain:

```text
Date
ContractCode = product-level name such as 臺股期貨 / 電子期貨 / 小型臺指期貨
Item = 自營商 / 投信 / 外資及陸資
TradingVolume(Net)
OpenInterest(Net)
```

There is no contract-month field in the official OAS schema.

Therefore:

```text
DailyMarketReportFut grain
= product + expiry series + session + date

Institutional futures grain
= product + participant class + date
```

Forbidden example:

```text
"TX 202610 foreign institutional net OI = X"
```

unless a future official source proves that exact series-level relation.

Permitted evidence is product-level only, e.g. conceptually:

```text
"臺股期貨 product-level foreign/China institutional net OI = X"
```

This family is deferred to I3 and may not enter I2 by convenience join.

---

# 8. Reference Metadata Boundary — Industry Classification

TPEx official company basic data proves deterministic company-to-industry-code mapping, but the live probe shows the dataset is a large reference snapshot rather than small per-request evidence.

Decision:

```text
industry classification = reference enrichment
not I1 per-request market evidence
```

Requirements for any later implementation:

- do not create a parallel market identity authority;
- bind industry metadata subordinate to existing canonical cash identity;
- do not refetch a 1+ MB reference dataset per target request when an installation-local governed reference mechanism can safely serve the same role;
- source `Date` for reference metadata is not the same semantic as market observation `trade_date`;
- do not infer industry return from sector turnover weight.

Industry-performance context remains DEFER because TWSE and TPEx official surfaces are not currently symmetric enough to justify a single first-version semantic contract.

---

# 9. Currentness Contract

Phase I must preserve evidence-family-specific currentness.

Rules:

1. Capture the execution reference time once.
2. Preserve the official source date exactly.
3. Preserve `retrieved_at` separately.
4. Do not declare a source stale merely because `official_date != calendar_today`.
5. Weekends, holidays, publication lag and source-specific publication cadence must be respected.
6. Where governed trading-calendar evidence exists, classify currentness deterministically.
7. Where timing cannot be proven, return explicit caveat / unknown rather than guessing.
8. No global stale threshold may be applied to market state, futures, institutional positioning, PCR, reference metadata and research evidence as if they shared one publication cadence.

The 2026-09-29 probes returning 2026-09-24 market data are a concrete example of why calendar-date equality is not an acceptable currentness rule.

---

# 10. Source Authority & Usage Contract

For every new Phase I source family, three things must remain distinct:

```text
source authenticity
transport accessibility
usage / redistribution authority
```

Official endpoint returning HTTP 200 does not by itself prove redistribution or automation permission.

Before production activation, each source family must record:

```text
source owner
exact endpoint / surface
source contract identifier
usage / terms basis
provider automation permission status where relevant
retrieval bounds
raw-payload retention policy
```

No source may gain broader automated authority merely because it is technically reachable.

No unofficial fallback may silently replace an official source.

---

# 11. Request / Result Architecture Boundary

Phase I must extend the existing governed Unified Evidence architecture rather than create a competing stack.

Frozen principles:

```text
public Request / Result / Audit V3 remains preferred
six MCP tools remain exactly six
Phase I context is optional
AI explicitly selects the needed context
context is bounded by target / market / data_need / execution authorization
no default fetch of all Phase I families
```

I0 does **not** freeze exact wire-schema field names or version bumps.

Any schema change must be additive and must preserve current V3 compatibility unless a separately governed migration proves otherwise.

Conceptual families authorized for design consideration after I0 freeze:

```text
market_state_context
index_futures_context
```

The exact public request parameter names and result nesting must be decided by an implementation contract spike against the current repository schemas.

---

# 12. Explicit Non-Goals / Prohibitions

Phase I v1 must not become any of the following:

```text
technical-indicator engine
options analytics engine
volatility-surface engine
sentiment engine
institutional smart-money score
margin / short bullish-bearish score
PCR sentiment classifier
leading-signal engine
prediction engine
manipulation detector
strategy engine
backtester
historical derivatives warehouse
full-market archive
background collector
scheduled poller
unbounded crawler
news agent
seventh MCP tool
broker / trading integration
```

Also prohibited:

```text
automatic bullish / bearish labels
"foreign investors are bearish" derived solely from net position
"margin increase means retail bullish"
"SBL increase means foreign investors bearish"
series-level institutional claims when source grain is product-level
industry return inferred from sector turnover weight
same-date evidence described as simultaneous when close times differ
```

---

# 13. Intentionally Deferred Decisions

The following are not frozen by I0 and require later bounded decisions:

```text
exact Request/Result V3 additive schema shape
exact public data_need identifiers
hard maximum response-byte / row budgets
source-specific stale/currentness thresholds
I2 provider automation / usage authority closure
TWSE/TPEx industry-performance normalization
TAIFEX after-hours effective-date contract
options identity contract
PCR interpretation-safe contract
institutional / margin / short positioning contract
single-stock futures linkage and contract-adjustment semantics
ETF relationship / holdings semantics
```

Deferral is intentional scope control, not missing implementation work.

---

# 14. I0 Exit / Freeze Criteria

The Owner accepted the following I0 freeze criteria on 2026-09-29; all are now frozen baseline requirements:

```text
1. Phase I = Optional Interpretation Context, not data expansion for its own sake.
2. I1 = Market State Context first.
3. I1 includes benchmark + breadth + turnover only in v1.
4. Industry classification is reference enrichment, not I1 live evidence.
5. Industry performance remains deferred.
6. I2 = TAIFEX TX regular-session context second.
7. I2 uses DailyMarketReportFut only in its first vertical slice.
8. I2 excludes after-hours, options, institutional positioning and SSF.
9. Derivative product / series / observation grain is separate from cash identity.
10. Institutional futures data must remain product-level and cannot be joined to expiry series without official evidence.
11. All Phase I families remain optional / explicitly requested.
12. Source authenticity, access and usage authority remain separate gates.
13. Six MCP tools remain unchanged.
14. No history DB, scheduler, polling, trading signal or investment conclusion is introduced.
```

Owner freeze is complete. Codex may begin the first bounded Phase I implementation tranche, limited to I1 only, under the authorization boundary in this record.

---

# 14.1 Owner Freeze Decision

On 2026-09-29, the Owner explicitly accepted this I0 decision record and authorized progression into the first I1 implementation tranche.

The authorization is intentionally narrow:

```text
AUTHORIZED:
- preserve this document as the frozen I0 decision baseline;
- design and implement I1 Market State Context only;
- update/add additive V3 contracts required for I1;
- implement deterministic TWSE + TPEx I1 source adapters/routes under existing governance;
- add fixtures, validators, unit/integration/regression tests and non-live acceptance evidence;
- prepare a reviewable I1 implementation candidate.

NOT AUTHORIZED:
- I2 TAIFEX TX implementation;
- I3 positioning implementation;
- live activation of any new Phase I route;
- production route activation;
- merge to main;
- background acquisition, polling or scheduler;
- new MCP tools;
- trading signals, recommendations or broker integration;
- Phase J start.
```

Any boundary above requires a new explicit Owner authorization.

# 15. Future Codex Handoff Contract

The Owner has explicitly authorized Phase I implementation for the first tranche, which is limited to **I1 only**.

Codex should be instructed to:

```text
1. start from the then-current accepted main baseline;
2. inspect current V3 Request / Result / Audit contracts before designing fields;
3. implement an additive market_state_context contract only;
4. support TWSE + TPEx common-share targets only in v1;
5. use official sources only;
6. implement deterministic bounded fetch counts;
7. implement explicit complete / partial / unavailable / source_failed states;
8. preserve citation / lineage / audit semantics;
9. preserve six MCP tools;
10. add deterministic fixtures and current-state regression tests;
11. perform no I2 implementation in the same tranche;
12. perform no live activation without separate Owner authorization;
13. STOP after I1 implementation candidate + evidence review.
```

I2 must be a separate tranche after I1 acceptance.

---

# 16. Final I0 Decision Summary

```text
PHASE_I_PURPOSE = OPTIONAL_INTERPRETATION_CONTEXT

I1_MARKET_STATE_CONTEXT = ADD_FIRST
I1_BENCHMARK = ADD
I1_BREADTH = ADD
I1_TURNOVER = ADD
I1_INDUSTRY_CLASSIFICATION = REFERENCE_DEFER
I1_INDUSTRY_PERFORMANCE = DEFER

I2_TX_REGULAR_SESSION_CONTEXT = ADD_NEXT
I2_TX_AFTER_HOURS = DEFER
I2_OPTIONS = DEFER
I2_PCR = DEFER

I3_INSTITUTIONAL_POSITIONING = DEFER_SEPARATE_GATE
I3_MARGIN_SHORT_SBL = DEFER_SEPARATE_GATE

DAY_TRADING_CONTEXT_V1 = DO_NOT_ADD
ETF_EXACT_HOLDINGS_V1 = DO_NOT_ADD

PUBLIC_REQUEST_RESULT_AUDIT = V3_REMAINS_PREFERRED
MCP_TOOL_COUNT = 6
HISTORY_DATABASE = NO
BACKGROUND_COLLECTION = NO
SCHEDULER = NO
TRADING_SIGNAL = NO
INVESTMENT_CONCLUSION = NO

PHASE_I_IMPLEMENTATION_AUTHORIZED = true
PHASE_I_I1_IMPLEMENTATION_AUTHORIZED = true
PHASE_I_I2_IMPLEMENTATION_AUTHORIZED = false
PHASE_I_LIVE_ACTIVATION_AUTHORIZED = false
PHASE_I_PRODUCTION_ROUTE_ACTIVATION_AUTHORIZED = false
PHASE_I_MERGE_AUTHORIZED = false
```

North Star:

> **TW-Market does not add investment-analysis functionality in Phase I. It adds official, bounded, timing-safe context that an AI can request when it needs to understand the market environment surrounding a piece of evidence — without forcing the model to guess and without making the conclusion for the model.**
