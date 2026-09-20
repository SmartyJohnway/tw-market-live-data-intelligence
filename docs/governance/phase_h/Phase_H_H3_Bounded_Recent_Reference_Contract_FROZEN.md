# Phase H H3 Bounded Recent Reference Contract

Status: **FROZEN**
Freeze date: 2026-09-21
Capability: `recent_performance`
Repository baseline: `85a61cd8dc14c37832f7702c9e0a529b3f27ee0f`
Upstream H0-A–H0-D merge: `85a61cd8dc14c37832f7702c9e0a529b3f27ee0f`
Owner instruction: `H0-02B FORMAL CONTRACT FREEZE`

## 1. Purpose and product boundary

`recent_performance` means **bounded descriptive recent-market reference evidence** needed for the current authorized AI conversation.

It MUST NOT become a historical-market-data product, performance analytics engine, technical-analysis engine, backtester, screener, ranking system, investment-performance engine, or source of investment recommendations.

Recent historical evidence is a bounded execution input, not a persistent historical-data product.

H3 MUST NOT introduce a historical database, OHLCV warehouse, rolling cache, daily collector, automatic accumulation, automatic history backfill, market-wide archive, startup preload, background refresh, scheduler, polling, unofficial fallback, or browser-CSV scraping workaround.

## 2. Existing capability authority is reused

H3 MUST reuse the existing `recent_performance` capability. It MUST NOT introduce competing capabilities such as `historical_baseline`, `price_history`, `recent_history`, or `market_history`.

Existing Phase G authority remains true:

- support status is `contract_supported`;
- TWSE and TPEx are supported markets at the contract level;
- `lookback_trading_days` is required and bounded to integer values from 1 through 20;
- the current route is `plan_only` and `runtime_executable=false`;
- no executor is selected;
- `recent_return_pct` is a raw, unadjusted metric;
- missing dividend or event evidence is not zero.

This semantic freeze does not modify the current Catalog, Routing Matrix, request contract, runtime route, or activation state.

## 3. Lookback and completed-session semantics

`lookback_trading_days=N` means the requested count of recent valid **completed official trading-session lookback observations before the governed end observation**. It does not mean calendar days, retention duration, collection frequency, or permission to acquire an unbounded history.

This definition preserves the existing governed M8R-03C formula:

```text
return_Nd = latest_valid_close / close_N_trading_rows_ago - 1
```

An N-day raw return therefore requires N lookback observations plus one governed end observation: N+1 distinct valid closes. The end observation MAY be supplied inside one self-contained governed H3 artifact or by separately bound current/EOD evidence. It MUST be counted and identified separately from `requested_observations`.

A request for 20 trading days means up to 20 valid completed-session lookback observations plus the governed end observation. The result MUST distinguish:

- requested observation count;
- valid governed observations actually obtained;
- the calendar span containing those observations;
- missing governed trading-session observations.

It MUST also identify the end observation and the total distinct close count used by each available baseline. H0-G MUST preserve this cardinality and MUST NOT redefine N-day return as a comparison across only N total closes.

Non-trading calendar days MUST NOT count as missing trading observations. Intraday snapshots MUST NOT be used as historical baseline observations.

## 4. Observation identity, validity, and ordering

Every valid historical observation MUST be bound to:

- the existing canonical target identity;
- resolved market and exact security code;
- official trading date;
- governed source family and source contract;
- source timing and retrieval evidence;
- citation and lineage evidence.

Observations MUST be deduplicated by governed target, market, and trading-date identity. Duplicate source rows MUST NOT increase `valid_observation_count`.

Observations MUST be ordered deterministically by official trading date. Missing sessions MUST NOT be invented, interpolated, forward-filled, or replaced with unofficial observations.

Binding failure, source-contract failure, and unavailable history MUST remain explicit. Company name MUST NOT be used as fallback binding authority.

## 5. Observation coverage model

H3 evidence MUST be capable of expressing at least these conceptual fields:

```text
requested_observations
valid_observation_count
first_observation_date
last_observation_date
coverage_status
missing_observation_count
available_baselines
unavailable_baselines
```

The frozen conceptual coverage states are:

- `complete`;
- `partial`;
- `insufficient`;
- `unavailable`;
- `source_failed`;
- `binding_failed`;
- `unsupported`;
- `not_applicable`.

Exact V3 field syntax is DEFERRED to H0-G.

The top-level coverage states have this deterministic precedence and are mutually exclusive:

1. `source_failed` or `binding_failed` applies when that governed failure prevents reliable evaluation; failure provenance MUST be retained even if other evidence exists.
2. `complete` requires all requested lookback observations, the governed end observation, and every requested baseline to be available.
3. `partial` requires at least one requested baseline to be available while the complete requested observation set or one or more other requested baselines are unavailable.
4. `insufficient` means governed observations exist but no requested baseline has the required endpoints/cardinality.
5. `unavailable` means no governed bounded-history evidence is available without asserting source failure.
6. `unsupported` and `not_applicable` retain their governed capability/applicability meanings.

Source and binding failures MUST NOT be collapsed into `partial`, `insufficient`, or `unavailable`.

## 6. Partial coverage and baseline availability

Partial coverage is a valid evidence result. For example, a request for 20 observations that returns 8 governed observations MAY report:

```text
requested_observations = 20
valid_observation_count = 8
coverage_status = partial
available_baselines = [5]
unavailable_baselines = [20]
```

The missing 12 observations MUST NOT be fabricated, obtained through an unauthorized source, or scheduled for later collection.

Baseline availability is independent of request success. Each requested baseline MUST state one of:

- `available`;
- `insufficient_coverage`;
- `unavailable`;
- `unsupported`.

A baseline N is `available` only when the governed evidence supplies the end close and the close exactly N valid trading rows earlier, with all identity, date, source-contract, and ordering requirements satisfied. The evidence record MUST expose the start and end observation dates and the N+1-close requirement, even when intermediate observations are delivered in a separate bounded set.

A successful partial request does not make every requested baseline available.

## 7. Recent close range

The canonical recent range is a **recent close range** based only on completed-session official closing prices.

Its conceptual basis is:

```text
range_basis = completed_session_closing_price
```

The range MUST NOT use the highest intraday high or lowest intraday low across the period. A future multi-session intraday envelope would require a separately named and authorized metric.

## 8. Raw return semantics

`recent_return_pct` is a factual raw, unadjusted close-to-close calculation. When locally calculated, its conceptual formula is:

```text
(close_end - close_start) / abs(close_start) * 100
```

A governed source-supplied equivalent MAY be retained with its source definition. The start and end closes MUST come from the declared available baseline. The existing M8R-03C ratio formula is equivalent before unit conversion; `recent_return_pct` multiplies that ratio by 100.

H3 MUST NOT call this adjusted return, total return, economic return, or shareholder return. It MUST NOT assume missing dividend or corporate-action evidence is zero.

The raw metric MAY be available even when ordinary return interpretation is blocked. H3 factual metric availability is separate from H4 interpretation permission.

## 9. Volume semantics and temporal alignment

Historical average volume MUST use completed official session volume. It MUST NOT use intraday snapshots as completed-session history.

H3 MUST preserve these conceptual dimensions:

```text
current_volume_basis:
  intraday_cumulative | completed_session

historical_average_basis:
  completed_official_sessions

comparison_alignment:
  aligned | partial_session_vs_completed_sessions | unavailable
```

When current volume is intraday cumulative and the historical average uses completed sessions, `comparison_alignment` MUST be `partial_session_vs_completed_sessions`.

The canonical deterministic result MUST NOT simplify that misaligned comparison into high volume, low volume, strong volume, weak volume, a signal, or a ranking.

## 10. H3 and H4 responsibility boundary

H3 MAY calculate source-factual raw close-derived metrics. It MUST NOT decide whether beginning and ending prices are ordinarily comparable across the requested window.

H4 owns deterministic discontinuity safety. Therefore:

```text
H3 factual metric availability != H4 interpretation permission
```

H3 MUST preserve the comparison window, source coverage, observation identities, and metric inputs required by H4.

## 11. Source and provider states

H3 MUST distinguish at least:

- `default_source_available`;
- `optional_provider_available`;
- `provider_unavailable`;
- `source_gap`;
- `manual_verification_only`;
- `source_failed`.

Current frozen source consequences are:

| Market | Latest completed-session official OpenAPI | Default fresh-install bounded 5D/20D route | Browser history | Optional licensed provider |
|---|---|---|---|---|
| TWSE | available for one published snapshot | **NOT PROVEN** | manual verification only | provider contract pending |
| TPEx | available for one published snapshot | **NOT PROVEN** | manual verification only | provider contract pending |

The latest-session OpenAPI snapshots do not satisfy a fresh-install 5D or 20D request by themselves. A browser-downloadable CSV is not an unattended production API.

An optional paid provider MUST NOT be required for a valid portable installation. Lack of subscription MUST yield provider unavailable, route inactive, partial/unsupported baseline, or source gap as appropriate.

## 12. Execution and persistence boundary

Any future H3 execution MUST remain explicit, target-scoped, lookback-bounded, authorized, execute-once, and auditable.

A 20-day request MUST NOT be translated into a full-history download, retained market-wide table, daily collection job, or future accumulation process.

Only target-bounded governed evidence, source provenance, hashes, citations, receipts, and audit artifacts needed for the authorized request MAY persist.

## 13. Remaining source issues

The following source issues remain open activation/provider gates and are not semantic-contract blockers:

- `H0-SRC-09`: authorized TWSE one-shot bounded 5D/20D machine source;
- `H0-SRC-10`: authorized TPEx one-shot bounded 5D/20D machine source;
- `H0-SRC-11`: selected TWSE licensed recent-history product and contract;
- `H0-SRC-12`: selected TPEx licensed recent-history product and contract.

This freeze reclassifies their consequence for H3 but does not claim they are closed.

## 14. Freeze decision

```text
H3 semantic contract = FROZEN
Capability reused = recent_performance
Lookback = 1..20 completed trading-session lookback observations plus one governed end observation
Default fresh-install 5D/20D route = NOT PROVEN
TWSE optional provider = PROVIDER-CONTRACT-PENDING
TPEx optional provider = PROVIDER-CONTRACT-PENDING
Runtime activation = NOT AUTHORIZED
Contract-freeze blockers = 0
```

This document freezes semantics only. It does not create V3 schema bytes, source adapters, runtime registration, source activation, Workbench changes, MCP changes, or a new data store.

## 15. Provenance

Normative upstream authority:

- `docs/governance/phase_h/Phase_H_Product_Boundary_and_Anti_Scope_Creep_FROZEN.md`;
- `docs/governance/phase_h/Phase_H_Official_Source_and_Automation_Authority_Matrix_FROZEN.md`;
- `docs/governance/phase_h/Phase_H_Official_Source_and_Automation_Authority_Matrix_FROZEN.json`;
- `docs/governance/phase_h/Phase_H_H2_Price_Basis_Corporate_Action_Contract_FROZEN.md`;
- `docs/governance/phase_h/PHASE_H_H0_A_D_FREEZE_MANIFEST.json`.

Research input:

- `docs/research/phase_h_h0_01a/Phase_H_H0_01A_Official_Source_Transport_Automation_Authority_Matrix.md`;
- `docs/research/phase_h_h0_01a/Phase_H_H0_01A_Source_Authority_Matrix.json`.

Existing Phase G capability authority:

- `docs/data_capabilities/unified_market_evidence_capability_catalog.v2.json`;
- `docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v2.json`;
- `scripts/m8r_05c/derived_metrics.py`;
- `skills/tw-market-evidence-agent/references/evidence_semantics.md`;
- `skills/tw-market-evidence-agent/references/current_limitations.md`.

This file's SHA-256 and byte size are recorded in `PHASE_H_H0_E_F_FREEZE_MANIFEST.json`.
