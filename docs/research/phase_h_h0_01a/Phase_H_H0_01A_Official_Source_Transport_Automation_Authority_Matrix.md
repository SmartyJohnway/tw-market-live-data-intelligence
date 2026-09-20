# Phase H H0-01A Official Source / Transport / Automation Authority Matrix

Status: **freeze preparation only**  
Research date: 2026-09-20 through 2026-09-21  
Repository baseline: `main` at `aa315918e0b5b431f4e63334c3ff91eac4e4e8f5`  
Machine-readable companion: `Phase_H_H0_01A_Source_Authority_Matrix.json`

## 0. Executive Decision

The source landscape is mature enough to freeze a truthful Unified Contract V3 and H1-H4 contracts. It is not mature enough to activate every H2 or H3 route.

| Area | Decision | Basis |
|---|---|---|
| H1 trading status | **YELLOW** | Both exchanges expose the required machine-readable families, so the contract is freeze-ready; exact license/cadence mappings for several routes remain activation gates. |
| H2 price-basis events | **YELLOW** | Ex-right/dividend coverage is strong. TPEx exposes a free final calculation; TWSE final TWT49U is licensed. Capital-reduction reference pages exist but no documented OpenAPI automation contract was found. Par-value/split/consolidation event feeds remain gaps. |
| H3 recent reference | **YELLOW** | Free OpenAPI supports the latest completed-session snapshot, but no default free multi-day machine route was proven for a fresh installation. Official licensed lanes are plausible but need product-specific contracts. |
| H4 discontinuity safety | **READY** | A deterministic fail-closed state model can be frozen without an adjustment engine, provided event coverage is explicit. |
| Unified V3 direction | **READY_TO_FREEZE** | V3 can represent partial/unsupported provider routes without pretending they are executable. |

Overall: **READY_FOR_H0_CONTRACT_FREEZE**.

This is not a production-readiness decision. H2 capital-reduction/par-value routes and H3 multi-day acquisition remain inactive until their source-specific activation gates close.

Decision scale: `GREEN` means both contract and default source authority are sufficiently closed; `YELLOW` means the contract can be frozen but one or more route activation, license, cadence, lifecycle or provider gates remain; `BLOCKED` means even a truthful contract boundary cannot yet be frozen. H4 `READY` means its deterministic fail-closed state machine is freeze-ready, not that all H2 providers are active.

## 1. Scope / Product Boundary

The investigation covers TWSE and TPEx `company_share/common_share` evidence needed for a current conversation:

- H1 instrument-specific official trading status;
- H2 events that change the price comparison basis;
- H3 bounded `recent_performance` for 1-20 completed trading sessions;
- H4 deterministic discontinuity safety derived from H2 plus H3.

It does not authorize a historical database, scheduled downloader, polling, backfill, corporate-action warehouse, adjusted-price series, technical-analysis engine, or new MCP tool.

## 2. Repository Baseline

Preflight found:

- branch: `main`;
- `HEAD`: `aa315918e0b5b431f4e63334c3ff91eac4e4e8f5`;
- `origin/main`: the same SHA;
- worktree: clean before these two research artifacts were created.

Current Phase G authority was verified:

- accepted requests: `unified_market_evidence_request.v1` and `.v2`;
- preferred request: `.v2`;
- emitted Result/Audit: `.v2`;
- `recent_performance` exists with `lookback_trading_days` 1-20 and remains `contract_supported`, not runtime executable;
- the MCP surface is exactly six tools;
- Phase G closure records no scheduler, polling, background refresh, research warehouse, or full-market payload persistence.

Frozen V2 schema SHA-256 values recorded before research:

| File | SHA-256 |
|---|---|
| `unified_market_evidence_request.v2.schema.json` | `757d864c3a00d296f8ebf2eccdbb47a1d39ca8a222e9d939f34ef854f4245e3b` |
| `unified_market_evidence_result.v2.schema.json` | `ed9928530be37fc4b2a4d1e386eb2ea8ff5dbe33e4c6598d0a8010c338dea444` |
| `unified_market_evidence_audit_package.v2.schema.json` | `a798e435168a185c00250f56bb88aa09fc57788fcd47048fdd42ae29c977b14e` |

No frozen schema was modified.

## 3. Research Method

The investigation used:

1. read-only repository inspection of catalog, routing, schemas, projector logic, skill semantics and Phase G closure evidence;
2. official TWSE and TPEx Swagger descriptions;
3. bounded official endpoint probes to confirm field names, row shape and current-vs-history behavior;
4. official government open-data records for license and cadence;
5. official exchange web/product pages for human-query and licensed lanes.

No crawler, recursive discovery, historical bulk backfill, or full-market durable payload was created. Probe payloads were transient. One exploratory PowerShell rendering expanded a large current response in command output; no response body was written to the repository or runtime.

Evidence labels used here:

- **VERIFIED FACT**: direct official metadata, payload, product page or rule;
- **SUPPORTED INFERENCE**: conclusion strongly implied by current official descriptions;
- **DESIGN RECOMMENDATION**: proposed contract behavior;
- **UNRESOLVED**: source contract or authority not proven.

## 4. Source Licensing / Automation Policy

The [Government Open Data License 1.0](https://data.gov.tw/license) is the strongest default automation lane where the exact exchange dataset is mapped to data.gov.tw. The OpenAPI source must still retain attribution, source contract identity, retrieval time and payload validation.

[TWSE website terms](https://accessibility.twse.com.tw/zh/terms/use.html) distinguish content released under government open data from other website content. A browser page or CSV button is therefore not automatically a production crawler contract.

Official paid products are separate authorities. The [TWSE Data E-Shop](https://eshop.twse.com.tw/zh/) and [TPEx data products](https://www.tpex.org.tw/zh-tw/service/data/product/post.html) require product-specific account, payment, use-scope and redistribution review. “Official” does not mean “free”, and “machine-readable” does not mean “default production source”.

## 5. H1 TWSE Investigation

The current [TWSE OpenAPI](https://openapi.twse.com.tw/) exposes four useful families:

| Subtype | Route | Proved semantics | Disposition |
|---|---|---|---|
| attention | `/announcement/notice` | Dated current attention rows; code, name, attention text/count and price/PE fields | Default candidate |
| disposition | `/announcement/punish` | Publication date, disposition period, reasons, measures, detail and link | Default candidate |
| suspension/resumption | `/exchangeReport/TWTAWU` | Halt and resumption date/time fields in one official row | Default candidate |
| changed trading | `/exchangeReport/TWT85U` | Current changed/periodic-call status snapshot | Default candidate |

These sources prove exchange determinations. TW-Market must not compute a severity/risk/abnormality score or attempt to reproduce the exchange surveillance algorithm.

Important limit: current snapshots do not by themselves prove a complete historical lifecycle. Absence from an incomplete or failed snapshot cannot be rendered as “normal”. Where official metadata did not state a refresh cadence, the matrix records cadence as unresolved rather than inferring it from the dataset name.

## 6. H1 TPEx Investigation

The current TPEx OpenAPI exposes:

| Subtype | Route | Proved semantics | Disposition |
|---|---|---|---|
| attention | `/tpex_trading_warning_information` | Dated warning/attention text bound by `SecuritiesCompanyCode` | Default candidate |
| disposition | `/tpex_disposal_information` | Period, reasons and disposal condition | Default candidate |
| current suspend/resume | `/tpex_spendi_today` | Current-day suspension and resumption values | Default candidate |
| suspend/resume history | `/tpex_spendi_history` | Historical rows with separate date/time fields | Governed fallback candidate |
| changed/periodic/managed | `/tpex_cmode` | Current official status flags and matching frequency | Default candidate |

The attention and disposition datasets are explicitly listed under ODGL 1.0 as [dataset 11395](https://data.gov.tw/dataset/11395) and [dataset 11396](https://data.gov.tw/dataset/11396).

Source-native field names differ materially from TWSE. A route-specific normalizer is required; blind alias sharing would weaken source-contract validation.

## 7. H1 Contract Recommendation

Freeze one `trading_status_context` evidence family with source-native subtypes and explicit coverage:

- `attention`;
- `disposition`;
- `changed_trading_method`;
- `suspension`;
- `resumption`.

Each item should carry official source family/contract, market and exact security code, publication/report date when supplied, effective start/end when supplied, official reason/conditions/measures, observed-at, and lifecycle status `reported | effective | ended | unresolved` only when directly supported.

Required status distinction: `available`, `no_evidence_in_covered_scope`, `source_failed`, `binding_failed`, `not_applicable`, `unsupported`, `partial`. “No evidence” is legal only when the complete governed snapshot for the declared scope was successfully validated.

## 8. H2 TWSE Investigation

### TWT48U_ALL preannouncement

`/exchangeReport/TWT48U_ALL` is the official ex-right/ex-dividend **preannouncement** table. It exposes the event date and ratios/amounts including cash dividend, stock dividend, subscription ratio and subscription price. [Data.gov dataset 89748](https://data.gov.tw/dataset/89748) identifies it as ODGL 1.0, free, irregularly updated.

Observed source values include empty string, numeric zero, and `尚未公告`. They are different states and must remain different.

### TWT49U final calculation

The official [TWT49U Data E-Shop product](https://eshop.twse.com.tw/zh/product/detail/000000006f6a5e3401702cea7ba20041) is the final calculation file, not another name for TWT48U. The product description lists previous close, ex-right/dividend reference, rights/dividend values, limits, opening reference and opening-auction basis. It is produced daily at 13:50, with data from 2020-03-02, and is licensed/paid. It is therefore an `OPTIONAL_LICENSED_PROVIDER`, not a free default route.

### Capital reduction and other basis changes

The official [TWSE capital-reduction reference page](https://wwwc.twse.com.tw/zh/announcement/reduction/twtauu.html) provides formulas, date-range queries, a machine-readable CSV export and data since 2011-01-01. It proves official values exist. The current OpenAPI Swagger did not expose a corresponding unattended automation route. Until a documented machine contract/license is bound, this remains `MANUAL_VERIFICATION_ONLY`.

Official TWSE educational/rule material proves par-value changes and ETF split/reverse-split can create a proportional basis reset. It does not provide a bounded common-share event API. That route remains `PLAN_ONLY_SOURCE_GAP`.

## 9. H2 TPEx Investigation

`/tpex_exright_prepost` is the preannouncement source. `/tpex_exright_daily` is the next-business-day final calculation and exposes previous close, official reference, stock/cash dividend, opening reference, limits, subscription price and allocation ratios. [Data.gov dataset 11633](https://data.gov.tw/dataset/11633) identifies the final calculation as a daily ODGL 1.0 dataset. It is a strong free default route.

The official [TPEx capital-reduction reference page](https://www.tpex.org.tw/en-us/announce/market/reduction/reference.html) exposes date-range search, HTML and machine-readable CSV export, and data since 2013-01. No matching unattended OpenAPI route appeared in the current Swagger, so default production automation remains unproven.

The [TPEx par-value reference calculator](https://www.tpex.org.tw/zh-tw/announce/market/change/quotes.html) explicitly says the calculation is for reference and actual data follow official announcements. It is not an event feed and cannot close the source contract.

## 10. Corporate Action Lifecycle Findings

The official evidence supports these states with different strengths:

| Lifecycle state | Support |
|---|---|
| announced/scheduled | Strong through preannouncement tables |
| effective | Strong where event date is present and source snapshot is current |
| official_reference_calculated | Strong for TPEx final OpenAPI and TWSE licensed TWT49U |
| corrected/amended | A new official snapshot may differ, but stable correction linkage was not proven |
| cancelled | No uniform machine-readable cancellation contract was proven |

Contract rule: preserve every source snapshot’s report/effective dates and hash. Do not infer `supersedes`, `corrects`, or “same event” from target/date/text similarity alone. Use `revision_relation.status = unresolved` unless the source supplies linkage.

## 11. Price-Basis Event Taxonomy

Freeze a narrow taxonomy:

- `ex_dividend`;
- `ex_right`;
- `ex_right_dividend`;
- `capital_reduction_resume`;
- `par_value_change_resume`;
- `split`;
- `reverse_split` / `share_consolidation`;
- `cash_capital_increase_effect` only when included in an official reference calculation;
- `other_official_reference_price_event` only with explicit source proof.

Provider coverage must be attached per subtype. A schema vocabulary entry does not imply an executable route.

## 12. H3 TWSE Historical Reference Investigation

`/exchangeReport/STOCK_DAY_ALL` is a free ODGL latest/current daily snapshot with date, OHLC, volume, value and transaction count ([dataset 11549](https://data.gov.tw/dataset/11549)). Its Swagger route has no previous-date or multi-day parameter. `STOCK_DAY_AVG_ALL` likewise provides a current snapshot/monthly average, not a governed arbitrary-history API.

The official [TWSE individual daily trading page](https://wwwc.twse.com.tw/zh/trading/historical/stock-day.html) offers date/code query and machine-readable CSV, with data from 2010-01-04, but no unattended automation authority was proven. The government platform also records a user request noting the public dataset exposes only the latest data and asking for history support ([suggestion 136936](https://data.gov.tw/suggests/136936)).

Fresh installation answer:

- free/default lane: **NO DEFAULT ROUTE PROVEN** for a one-shot 5D or 20D baseline;
- optional licensed official provider: **PARTIAL / product contract required**.

## 13. H3 TPEx Historical Reference Investigation

`/tpex_mainboard_daily_close_quotes` provides the current completed-session quote table; [dataset 11371](https://data.gov.tw/dataset/11371) is ODGL 1.0 and daily. The current OpenAPI exposes no arbitrary date/multi-day parameter.

The official [TPEx individual history page](https://www.tpex.org.tw/zh-tw/mainboard/trading/info/stock-pricing.html) provides monthly/code query and machine-readable CSV, with data from ROC year 83. Browser-mediated export is not a documented unattended API contract.

Fresh installation answer:

- free/default lane: **NO DEFAULT ROUTE PROVEN** for a one-shot 5D or 20D baseline;
- optional licensed official provider: **PARTIAL / product contract required**.

## 14. Historical Source / Provider Comparison

| Market | Latest free machine source | Free bounded history | Official human history | Licensed history |
|---|---|---|---|---|
| TWSE | `STOCK_DAY_ALL` | No default route proven | Available | Data E-Shop family; exact product contract unresolved |
| TPEx | `tpex_mainboard_daily_close_quotes` | No default route proven | Available | TPEx information products; exact delivery contract unresolved |

Honest H3 partial semantics:

```text
requested_observations: 20
valid_observation_count: 8
coverage_status: partial
available_baselines: [5]
unavailable_baselines: [20]
```

Do not fill missing observations from unofficial websites, search results, silent cache accumulation, or future background collection.

Metric basis to freeze:

- close range means completed-session close range, not multi-day intraday high/low;
- average volume uses completed official sessions;
- current-vs-average volume must expose `current_volume_basis`, `historical_average_basis`, and `comparison_alignment`;
- partial intraday cumulative volume versus full sessions cannot be labeled simply “high” or “low”.

## 15. Source Authority Matrix

The companion JSON contains the required source-by-source columns, including transport, license, account/payment, target identity, coverage, historical support, time fields, revision semantics, missing-value rules, asymmetry, confidence, open issues and disposition.

Disposition count:

| Disposition | Count | Meaning |
|---|---:|---|
| `DEFAULT_PRODUCTION_CANDIDATE` | 13 | Source contract sufficiently supported for later adapter design; activation still requires H0+ implementation acceptance |
| `GOVERNED_FALLBACK_CANDIDATE` | 1 | Useful official bounded history route with additional coverage policy |
| `OPTIONAL_LICENSED_PROVIDER` | 3 | Official machine lane exists/plausible but account/payment/product contract applies |
| `MANUAL_VERIFICATION_ONLY` | 4 | Official human query exists; unattended automation not proven |
| `PLAN_ONLY_SOURCE_GAP` | 2 | Contract vocabulary may be frozen but no production source route is authorized |

## 16. GREEN / YELLOW / BLOCKED Capability Matrix

| Capability / subtype | TWSE | TPEx | Decision |
|---|---|---|---|
| H1 attention | YELLOW | GREEN | TWSE exact license mapping remains an activation gate |
| H1 disposition | YELLOW | GREEN | TWSE exact license mapping remains an activation gate |
| H1 suspend/resume | YELLOW | YELLOW | Freeze; pin license/cadence before activation |
| H1 changed trading | YELLOW | YELLOW | Freeze; pin license/cadence/lifecycle before activation |
| H2 ex-right/dividend preannouncement | GREEN | YELLOW | TPEx license is closed by dataset 11634; correction/cancellation lifecycle remains unresolved |
| H2 final ex-right/dividend reference | YELLOW: licensed TWT49U | GREEN: free OpenAPI | Freeze provider-specific availability |
| H2 capital reduction reference | YELLOW: human official page | YELLOW: human official page | Freeze vocabulary; route inactive |
| H2 par-value/split/consolidation | BLOCKED route | BLOCKED route | Freeze gap semantics only |
| H3 latest completed session | GREEN | GREEN | Latest input usable |
| H3 5D/20D fresh-install default | YELLOW | YELLOW | No default free route proven; partial/unsupported must be explicit |

## 17. H4 Safety Implications

H4 should be a deterministic composition state, not a network capability:

```text
no_material_discontinuity_detected
discontinuity_detected_reference_available
discontinuity_detected_reference_unavailable
coverage_incomplete
```

Legal transition rules:

1. `no_material_discontinuity_detected` requires complete event coverage for the comparison window. “No row found” under partial/failed coverage is insufficient.
2. If an event and official reference are available, preserve both the raw close comparison and official reference context.
3. If an event is known but reference evidence is unavailable, preserve factual raw prices but set ordinary-return interpretation to `NOT_COMPARABLE_AS_ORDINARY_RETURN`.
4. If H2 coverage is incomplete, suppress an ordinary-return conclusion and emit `coverage_incomplete`.

Existing `recent_return_pct = (close_end - close_start) / abs(close_start) * 100` may remain a factual raw metric. Its interpretation must be gated by H4. No adjustment factor, total-return history or rebasing engine is required.

## 18. V3 Contract Impact

V2 exact schemas are frozen. The safest evolution is:

- Request V3: add `trading_status_context` and `corporate_action_context`; retain `recent_performance`; accept bounded provider-aware parameters only if frozen;
- Result V3: add typed H1/H2 evidence and H4 discontinuity interpretation state;
- Audit V3: bind source attempts, provider availability, coverage and deterministic H4 derivation;
- Catalog V3: publish per-market/subtype execution state, optional licensed providers and source gaps;
- Routing Matrix V3: map only activated subtypes; `PLAN_ONLY_SOURCE_GAP` entries must never produce operations.

Likely repository impact:

| Area | Expected H0/H implementation impact |
|---|---|
| `schemas/` | New V3 request/result/audit and typed H1/H2 schemas; V1/V2 bytes untouched |
| `docs/data_capabilities/` | Catalog V3 and Routing Matrix V3 with per-provider/subtype truth |
| `scripts/m8r_05a_f3/` | Retain canonical identity and common-share applicability; no new identity authority |
| `scripts/m8r_05b_01/` | Per-target route applicability, optional-provider and plan-only behavior |
| `scripts/m8r_05c/` | Typed projection, H4 deterministic gate, citations and V1/V2/V3 read compatibility |
| production adapter registry | Explicit H1/H2/H3 adapters only after route acceptance; no scheduler |
| `server/services/` | Version dispatch and current-authority activation only in a later governed PR |
| `server/unified_mcp/` | Existing six tools, updated Unified schema only |
| skill | Regenerated portable Catalog V3 and truthful limitations after activation |
| tests | Exact source fixtures, schema tests, per-market asymmetry, missing semantics, H4 fail-closed and historical compatibility |

Plan/Authorization/Claim/Execution Request/Operation Result/Receipt/Bundle may remain v1 if they can truthfully carry these operations. Versioning them for cosmetic consistency is not justified.

## 19. Remaining Source Gaps

| ID | Status | Question | Current/closure evidence | Blocks |
|---|---|---|---|---|
| H0-SRC-01 | SUPERSEDED | Broad H1 license mapping issue | Decomposed into H0-SRC-01A through H0-SRC-01G; lineage retained | Neither |
| H0-SRC-01A | OPEN | TWSE attention exact license authority | Official OpenAPI verified; exact ODGL/data.gov mapping remains required | TWSE attention activation |
| H0-SRC-01B | OPEN | TWSE disposition exact license authority | Official OpenAPI verified; exact ODGL/data.gov mapping remains required | TWSE disposition activation |
| H0-SRC-01C | OPEN | TWSE suspension/resumption exact license authority | Official OpenAPI verified; exact ODGL/data.gov mapping remains required | TWSE suspend/resume activation |
| H0-SRC-01D | CLOSED | TWSE changed-trading exact license authority | ODGL 1.0, free, data.gov dataset 11760, TWSE OAS | Neither |
| H0-SRC-01E | OPEN | TPEx current suspension/resumption exact license authority | Official OpenAPI verified; exact ODGL/data.gov mapping remains required | TPEx current suspend/resume activation |
| H0-SRC-01F | CLOSED | TPEx historical suspension/resumption exact license authority | ODGL 1.0, free, data.gov dataset 48665, TPEx OAS | Neither |
| H0-SRC-01G | CLOSED | TPEx changed/periodic/managed exact license authority | ODGL 1.0, free, data.gov dataset 11736, TPEx OAS | Neither |
| H0-SRC-02 | OPEN | Complete lifecycle depth for changed-trading and halt/resume snapshots | Current/history asymmetry observed; official retention/revision semantics required | Coverage claim |
| H0-SRC-03 | OPEN | Preannouncement correction/cancellation representation | Snapshots exist; stable revision linkage not proven | Lifecycle activation |
| H0-SRC-04 | OPEN | TWT49U replacement/correction and licensed redistribution terms | Product, fields, price and cadence verified; subscriber contract review required | TWSE final-reference activation |
| H0-SRC-05 | OPEN | TWSE capital-reduction CSV unattended machine authority | Official human query/CSV exists; no OpenAPI route | TWSE capital-reduction activation |
| H0-SRC-06 | OPEN | TPEx capital-reduction CSV unattended machine authority | Official human query/CSV exists; no OpenAPI route | TPEx capital-reduction activation |
| H0-SRC-07 | OPEN | TWSE common-share par-value/split/consolidation event feed | Formula/concept proven; feed not proven | Subtype activation and complete H4 coverage claim |
| H0-SRC-08 | OPEN | TPEx common-share par-value/split/consolidation event feed | Calculator says official announcement controls; feed not proven | Subtype activation and complete H4 coverage claim |
| H0-SRC-09 | OPEN | Authorized TWSE one-shot bounded 5D/20D machine product | Latest OpenAPI only; human history page exists | TWSE H3 activation |
| H0-SRC-10 | OPEN | Authorized TPEx one-shot bounded 5D/20D machine product | Latest OpenAPI only; human history page exists | TPEx H3 activation |
| H0-SRC-11 | OPEN | TWSE E-Shop product for target-bounded recent OHLCV | Product selection, sample schema and license review required | Optional provider activation |
| H0-SRC-12 | OPEN | TPEx licensed product/delivery for target-bounded recent OHLCV | Product specification, sample and use contract required | Optional provider activation |
| H0-SRC-13 | CLOSED | TPEx `tpex_exright_prepost` exact license authority | ODGL 1.0, free, daily, data.gov dataset 11634, TPEx OAS | Neither |

Open issues do not block contract freeze. They block only the stated source activation, optional-provider activation, lifecycle claim, or coverage claim.

## 20. Explicit Anti-Scope-Creep Confirmation

This research did not implement or recommend as a workaround:

- a market/history/corporate-action database;
- daily downloader, scheduler, polling, background refresh or automatic backfill;
- full-market snapshot persistence;
- total-return or adjusted-price engine;
- technical indicators, screening, ranking or backtesting;
- sentiment/news/search ingestion;
- a seventh MCP tool;
- parallel Security Master, request contract, planner or unauthorized scraper.

## 21. Recommended H0 Freeze Decisions

1. Freeze Unified V3 rather than mutate V2 bytes.
2. Freeze `trading_status_context` for the verified H1 subtypes.
3. Freeze `corporate_action_context` with provider/subtype availability and explicit lifecycle uncertainty.
4. Keep `recent_performance`; do not add a competing history capability.
5. Freeze H3 partial coverage fields: requested count, valid count, actual dates, coverage status and unavailable baseline list.
6. Freeze H4 as deterministic derived evidence with fail-closed coverage semantics.
7. Freeze official-source attempt and license metadata in Audit V3.
8. Keep capital-reduction/par-value/split/consolidation routes plan-only until their machine authorities close.
9. Keep 5D/20D runtime plan-only unless a default or licensed official bounded-history contract is approved.
10. Preserve exactly six MCP tools.

## 22. Recommended Next Step

Proceed to H0 contract freeze work only. Draft the exact V3 schemas, Catalog V3, Routing Matrix V3, acceptance matrix and provider activation gates from this matrix. Do not start source adapters or current-authority activation during freeze.

The freeze must treat missing official coverage as evidence. It must never convert a source gap into silent scraping, accumulation, or a false “no event” conclusion.

## Owner Review Amendments

Owner review status: `ACCEPTED_WITH_MINOR_AMENDMENT` on 2026-09-21.

- H0-SRC-13 is CLOSED by [Government Open Data dataset 11634](https://data.gov.tw/dataset/11634): ODGL 1.0, free, daily, with TPEx OAS authority.
- H0-SRC-01 is preserved as `SUPERSEDED` and decomposed into route-specific H0-SRC-01A through H0-SRC-01G.
- H0-SRC-01D is CLOSED by [dataset 11760](https://data.gov.tw/dataset/11760).
- H0-SRC-01F is CLOSED by [dataset 48665](https://data.gov.tw/dataset/48665).
- H0-SRC-01G is CLOSED by [dataset 11736](https://data.gov.tw/dataset/11736).
- H0-SRC-01A, 01B, 01C and 01E remain activation gates. They are not contract-freeze blockers.

Pre-amendment hashes:

- Markdown: `566a91f5c7fa1da18dfb85753a19ba6f446973a5dc8040a3ac7996dde0fe31d3`
- JSON: `6a05968b4e2c6bd444bd90942eaffd9f24a55c99b17bd29365211ea3c5cd53f7`

Post-amendment hashes are recorded in the H0-A-D freeze manifest to avoid self-referential content.
