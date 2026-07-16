# M8R-03B AI Conversation Input/Output Design Review

Status: `m8r_03b_design_review_completed`

Decision: `GO_WITH_PHASED_IMPLEMENTATION_REQUIRED`

Starting baseline: `8401e818051f8ecf378eafd29950a6acb66b86b1`.

## Product north star

A future AI-assisted Taiwan market intelligence system should accept normal user market questions, resolve scope and time meaning, acquire official or governed evidence, package facts, derived metrics, assumptions, and missing evidence, and then let the AI explain the grounded context conversationally. The user should not have to pre-supply internal route, source-family, EOD/MIS, security identity, derivative expiry, weekly/monthly type, strike, call/put, benchmark, lookback, or package-schema fields.

This review is design and contract work only. It does not implement a frontend, MCP server, scheduler, public API, background polling, permanent user watchlist storage, portfolio management, broker integration, trading execution, or autonomous recommendation engine.

## Repository-grounded constraints

The design inherits M8R-03 package separation between source facts, missing context, caveats, approvals, and AI-safe projection. M8R-02B-F2 already supports bounded conversational TAIFEX derivatives resolution for current futures/options prompts, including exact identity disclosure and freshness guards. M8/M8C registry policy permits TWSE_MIS and TAIFEX_MIS as caveated live-ish context sources, and TWSE_OPENAPI, TPEX_OPENAPI, and TAIFEX_OPENAPI as official EOD/statistical/reference sources. Existing governance still forbids raw payload exposure, trading signals, trading advice, recommendations, and treating retrieved_at as an exchange timestamp.

## Layer separation

The data system owns identity correctness, route/source selection, provenance, currentness, time scope, official-source classification, fact-versus-derived labeling, assumptions, missing evidence, and bounded retention. The AI response layer owns summarization, comparison, explanation, hypotheses, risk discussion, follow-up questions, research suggestions, and style. Product policy such as trading-language boundaries remains a separate layer and may evolve without changing source capability semantics.

## Conversation scope contract

Contract: `m8r_ai_market_conversation_intent.v1`. The machine-readable contract is validator-ready: it defines each object field name, type, required/optional status, nullability, enums, defaults, nested structures, and invariants for the next implementation task.

Primary scope modes:

- `watchlist`: a persistent or operator-supplied watchlist. It is not a whole-market scan.
- `market_overview`: the scope is determined by market dimensions such as indices, turnover, breadth, positioning, and derivatives, not by the user's watchlist.
- `dynamic_research`: the AI proposes a temporary bounded evidence request for a topic, sector, theme, benchmark, derivative set, and time range.

Composite scope is allowed. For example, `最近AI科技股如何？我的觀察清單裡面哪些最強？` may resolve to `dynamic_research`, `watchlist_subset`, and `market_overview` in one evidence request. `persistent_watchlist` and `dynamic_evidence_request` are separate concepts; dynamic requests must never mutate permanent watchlists silently.

## Time-intent model

Supported modes are `current`, `recent`, `current_plus_recent`, `historical`, and `explicit_range`.

- `current`: MIS primary where integrated, latest completed EOD as reference.
- `recent`: EOD time series primary, MIS optional as latest endpoint.
- `current_plus_recent`: default for ambiguous prompts such as `幫我看一下觀察清單` or `大盤如何`; no clarification is required merely because current versus recent is omitted.
- `historical`: completed historical periods only.
- `explicit_range`: preserves user constraints such as `近5個交易日`, `過去20個交易日`, `今年以來`, or `從7月1日到現在`.

## Evidence-depth model

- `quick`: minimum evidence for an immediate conversational answer.
- `standard`: default product behavior.
- `deep`: expanded comparison and research evidence.
- `diagnostic`: source, identity, missing-data, and currentness troubleshooting detail.

The user need not say these internal terms; orchestration selects them and discloses material assumptions.

## Clarification policy

Do not ask clarification for ordinary prompts such as `我的觀察清單現在怎麼樣？`, `我的觀察清單最近表現如何？`, `幫我看一下觀察清單`, `今天大盤怎麼樣？`, or `最近AI科技股如何？`; use bounded defaults. Clarification may be required when the market/entity cannot be identified, multiple materially different entities share a name, a period is contradictory, a request implies unbounded whole-market extraction, or an AI-generated entity set cannot be bounded or justified.

## Common AI evidence request

Contract: `m8r_ai_evidence_request.v1`. The machine-readable evidence contract is validator-ready and defines typed evidence requirements, dynamic entity requests, watchlist references, market-context requests, identity resolver output, follow-up context, bundle envelopes, derived metric records, missing evidence records, and target coverage records. The envelope distinguishes original user text, conversation intent, explicit user constraints, inferred defaults, persistent watchlist reference, dynamic entity requests, market context requests, required/useful/optional evidence, execution policy, clarification decision, and resolver output. Default execution policy for this design review remains manual/operator-confirmed, no network by default, no polling, and no scheduler.

## Standard evidence bundles

### Watchlist snapshot

Contracts: `m8r_watchlist_snapshot_request.v1` and `m8r_watchlist_snapshot_bundle.v1`. Answers current watchlist questions. Every enabled target must have identity, current MIS evidence when available, latest completed EOD reference, and coverage status `usable`, `partial`, or `unavailable` with reason. Current fields include latest price, change, change percent, open, high, low, volume, source timestamp, retrieved_at, currentness status, and source family. EOD reference fields include previous effective trade date, previous close, and latest completed EOD status.

### Watchlist performance

Contracts: `m8r_watchlist_performance_request.v1` and `m8r_watchlist_performance_bundle.v1`. Answers recent watchlist ranking and trend questions. EOD series are primary. Derived metrics may include 1/5/10/20-day returns, range high/low/position, drawdown, average volume, volume ratio, realized volatility, and market-relative return. Derived metrics are system calculations and must not be described as official-source fields.

### Market pulse

Contracts: `m8r_market_pulse_request.v1` and `m8r_market_pulse_bundle.v1`. The target product has six dimensions: index direction, turnover/liquidity, breadth, weight/style, cash-market positioning, and derivatives/risk appetite. This complete market pulse is not currently executable; the capability matrix marks currently available, partial, not integrated, future expansion, and external official-source-probe-required groups.

### Dynamic research

Contracts: `m8r_dynamic_evidence_request.v1` and `m8r_dynamic_research_bundle.v1`. The AI may propose bounded temporary entities and benchmarks with selection reason, entity role, priority, time range, timing class, and fallback. Proposed entities pass through security master, market classifier, listing/lifecycle state, route resolution, and source capability checks before execution. The request records `persistent_watchlist_mutation: false`.

Recommended dynamic bounds are intentionally policy recommendations, not hard runtime constants: quick = small representative set; standard = bounded representative set plus benchmarks; deep = larger bounded set with explicit justification and review against existing target/retention limits.

## AI input package layers

AI-facing context has four distinct layers:

1. `facts`: source-normalized price, volume, turnover, index level, open interest, institutional position, source timestamp, and trade date.
2. `derived_metrics`: formula/derivation identifier, input period, source dependencies, and calculation status.
3. `resolution_assumptions`: bounded defaults and identity resolutions, such as recent = 20 trading days or current TXO = nearest active MIS expiry.
4. `missing_evidence`: unavailable, stale, unintegrated, or failed evidence requirements.

The AI must be able to tell what is known, derived, inferred, and missing.

## AI output design

The answer contract is flexible, not one rigid template. Required disclosure elements are `answer_summary`, `key_findings`, `supporting_evidence`, `assumptions`, `missing_or_stale_evidence`, and `follow_up_context`. The AI should answer first, surface decision-relevant findings, disclose material limits and automatic resolutions, preserve timing distinctions, and support follow-up. It must avoid row dumps before conclusions, treating EOD as intraday, treating `retrieved_at` as exchange time, or treating derived metrics as source facts.

## Follow-up conversation model

Future evidence packages may carry `conversation_context_id`, `parent_evidence_request_id`, `reusable_resolutions`, and `freshness_recheck_required`. Follow-ups may reuse topic, time range, benchmarks, resolved market context, and prior package IDs. Current/live MIS evidence requires a freshness check before reuse. Recent EOD evidence may be reused when the completed trade-date coverage still satisfies the requested period. This PR defines the contract only and does not implement persistent conversation storage.

## Current capability mapping summary

TWSE_OPENAPI and TPEX_OPENAPI are available official EOD/reference families for bounded retained symbols. TAIFEX_OPENAPI is available for official derivatives EOD/statistical reference. TWSE_MIS is available with caveats for listed, supported OTC route, and TAIEX live-ish observation. TAIFEX_MIS is available with caveats for exact/current futures/options regular-session safe-field context through conversational current-contract resolution. Current derivative contract resolution is GO from M8R-02B-F2.

Missing or partial market-pulse groups include TWSE/TPEx breadth, turnover rolling baselines, sector/style indices, cash-market institutional flows, margin/short balances, securities lending, day-trading ratios, TAIFEX institutional positions, large-trader positions, put/call historical series, futures OI structure, cash-futures basis, volatility index, option OI distribution, implied volatility, and skew. Repository evidence is insufficient to mark these implemented; many require separate official-source probes or adapters.

## Source-expansion priorities

Priority 1, minimum useful market pulse: TWSE/TPEx breadth, TWSE/TPEx turnover and rolling baselines, TAIFEX front-future volume/open interest, cash-futures basis, and TAIFEX put/call ratios. Priority 2, positioning and participation: three-institution flows, TAIFEX institutional positions, margin/short balances, and lending/borrowed-share selling. Priority 3, structure and volatility: sector indices, large/small participation, option OI distribution, volatility index, implied volatility/skew, and large-trader positions.

## Scenario walkthroughs

A current watchlist request maps to `watchlist` + `current`, with MIS primary, latest EOD reference, and every enabled target represented. A recent watchlist request maps to EOD-series performance metrics. An ambiguous watchlist request defaults to `current_plus_recent`. A current market pulse maps to market overview dimensions and discloses missing groups. A derivatives-focused question reuses TAIFEX MIS current future/option resolution plus OpenAPI EOD reference when available. A dynamic AI/technology question creates a temporary research request with validated entities. A composite follow-up reuses topic/time/benchmarks and applies watchlist subset with freshness checks. A missing-evidence question states which side is available and records precise missing requirements rather than fabricating.

## Relationship to M8R-04

M8R-04 should be split or scope-revised. The immediate next bounded engineering task is `M8R-03C-CONVERSATION-CONTRACT-VALIDATORS-AND-WATCHLIST-BUNDLE-SKELETONS`: implement validators for `m8r_ai_market_conversation_intent.v1`, `m8r_ai_evidence_request.v1`, and bundle envelopes, then build watchlist snapshot/performance skeletons before any broad AI handoff automation. New source-expansion tasks are needed before claiming complete market pulse automation. `m8r04_completed` remains false.

## Final M8R-03B decision

`GO_WITH_PHASED_IMPLEMENTATION_REQUIRED`: the north-star and contracts are coherent, but significant implementation and source gaps remain. This review does not claim the final product is implemented.
