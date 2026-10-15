# Phase L L3-A0 — Source Drift Scope, Inventory, and Hardening Plan

**Date:** 2026-10-15

**Base:** `origin/main@3b8f1532fac1a2d2366d0d38254ebd4a7a7c6b55`

**Disposition:** `L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_COMPLETE`

**Independent technical review:** `L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_ACCEPTANCE_REVIEW_PASS`

**Owner entry authority:** explicit 2026-10-15 L3-A0 instruction.

**Owner candidate acceptance:** not recorded. L3 STARTED; A1 NOT YET AUTHORIZED;
L4-L7 NOT AUTHORIZED. This inventory identifies an unresolved production
correctness gap; it does not certify all sources as hardened.

## 1. Entry, authority, and numbering

`git fetch origin` found the expected current main. PR #353 merged at
`b84ba8a4ac4819d115de33e55cf9adf2a5801e00`; PR #354 is this review base.
L0 is FROZEN, L1 CLOSED, and L2 CLOSED under
`PHASE_L_L2_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. A new clean worktree was created
on `phase-l/l3-a0-source-drift-inventory`; initial HEAD and origin/main were the
base above. Existing L2 and primary worktrees were not reused.

Recovery order: current recovery index, PROJECT, HANDOFF, frozen L0, Roadmap
Phase L section, L2 exit closure only, then current Catalog/Route/Executor and
source-specific runtime/contracts/tests. L1's accepted source-timing record
was used to cross-check the current acquisition seam set. Selective I2
activation-ledger reading resolved its older candidate metadata wording.

No architecture conflict exists. Roadmap durable subject matter remains valid,
while frozen L0 controls current Phase L tranche sequencing. Older Roadmap
subsections `L.2 Replay & Audit`, `L.3 Schema & Migration Policy`, and `L.4
Source Drift Management` organize subjects; the L0 implementation sequence is
L1 Runtime Operability, L2 Replay/Retention/Migration, L3 Source Drift Hardening,
L4 Security/Resources, L5 Extension Architecture, L6 Packaging/Portability,
L7 CI/Release. No historical subsection is renumbered and L2 is not reopened.

## 2. Runtime derivation and inventory boundaries

Primary current authorities:

- `docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json`
- `docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json`
- `config/m8r_06_03_executor_registry_metadata.json`
- `scripts/m8r_06_03_production_adapter.py::build_production_runtime_adapter_registry`
- `docs/data_capabilities/phase_i_i1_source_authority.v1.json`,
  `phase_i_i2_source_authority.v1.json`, and `phase_i_i3_source_authority.v1.json`
- Phase H source descriptors, interpreted with current selected routes and
  production implementations rather than their historical `dormant` filenames.

Current metadata/runtime tests establish **17 executor/capability/market
registrations**. Expanding their callable source sets and de-duplicating H1
attention shared by dedicated and composite adapters yields **18 logical
source contracts** below. Four research contracts each have CSV and JSON
alternatives: **22 primary endpoint alternatives**, not 22 independent
authorities. These counts describe the Unified execution set, not every
historical source listed anywhere in the repository.

Five additional explicit Security Master bootstrap acquisition members are
inventoried separately. Legacy bounded derivative clients and NCDR are also
listed so they cannot silently disappear from the production-capable inventory.
No total provider/source count is inferred from the broad M8 family registry.

`docs/source_registry/source_authority_registry.json` is a general risk/coverage
registry; `m8_source_capability_registry.json` also carries older aggregate
family declarations. Neither independently promotes every entry to a Unified
route. In particular, Catalog's available NCDR family does not supply the
missing selected `session_status` executor. I1's old dormant module docstring,
I2 source-authority `final_owner_activation_acceptance=PENDING`, and the dormant
H2 descriptor are historical/candidate wording: current registrations and
I2 `PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-10-01.json`
(`OWNER_ACTIVATION_ACCEPTED`) establish accepted runtime truth. No competing
current activation authority was found; A0 leaves frozen/candidate bytes intact.

### 2.1 Current Unified acquisition contracts

All P01-P18 have status `ACTIVE_PRODUCTION`. IDs preserve runtime spelling.
For G1/G2, the stable source family plus route contract identifies the member.
Profiles T/C/S and test/probe references are expanded in sections 3-5.

| Key / source ID or family:contract | Provider / market | Capability | Executor / transport and parser |
|---|---|---|---|
| P01 `TWSE_MIS` | TWSE browser endpoint / TWSE,TPEX | current_observation | `m8r_03d_watchlist_controlled_executor_adapter`; `m5k_common.execute_live_observation` / `observation_contract.normalize_twse_mis_row` |
| P02 `TWSE_OPENAPI` | TWSE / TWSE | official_eod_reference | same executor; `m8a_twse_official_eod_adapter` |
| P03 `TPEX_OPENAPI` | TPEx / TPEX | official_eod_reference | same executor; `m8a_tpex_official_eod_adapter` |
| P04 `MOPS_MATERIAL_DISCLOSURE_OPEN_DATA:t187ap04_L` | MOPS/TWSE / TWSE | material_disclosures | `phase_g_official_research_executor`; shared `_fetch_official_payload`, `phase_g/research_executor`, `mops_material_disclosures` |
| P05 `MOPS_MATERIAL_DISCLOSURE_OPEN_DATA:t187ap04_O` | MOPS/TPEx / TPEX | material_disclosures | same G1 path, route-specific mappings |
| P06 `MOPS_MONTHLY_REVENUE_OPEN_DATA:t187ap05_L` | MOPS/TWSE / TWSE | monthly_revenue | same research executor/transport; `mops_monthly_revenue` |
| P07 `MOPS_MONTHLY_REVENUE_OPEN_DATA:t187ap05_O` | MOPS/TPEx / TPEX | monthly_revenue | same G2 path, route-specific mappings |
| P08 `H1-TPEX-ATTENTION-OPENAPI` | TPEx / TPEX | trading_status_context | selected `phase_h_h1_tpex_composite_executor`; `phase_h_h1_tpex_composite.official_get` / `phase_h_trading_status_adapters`; dedicated attention executor also registered |
| P09 `H1-TPEX-DISPOSITION-OPENAPI` | TPEx / TPEX | trading_status_context | composite executor/transport; disposition normalizer |
| P10 `H1-TPEX-CHANGED-TRADING-OPENAPI` | TPEx / TPEX | trading_status_context | composite executor/transport; representative H1 component normalizer |
| P11 `H2-TWSE-EXRIGHT-PRE-OPENAPI` | TWSE / TWSE | corporate_action_context | `phase_h_h2_twse_exright_pre_executor`; `phase_h_h2_twse_exright_executor.official_get_once` / `phase_h_corporate_action_adapters`; depends on verified H3 |
| P12 `H3-TWSE-DEFAULT-BOUNDED` | TWSE / TWSE | recent_performance | `phase_h_h3_twse_recent_performance_executor`; `phase_h_h3_twse_stock_day_adapter` / walker / recent-performance semantic validator |
| P13 `I1-TWSE-FMTQIK-OPENAPI` | TWSE / TWSE | market_state_context | `phase_i_i1_market_state_executor`; current timed wrapper -> `phase_i_i1_production_candidate` / `phase_i_market_state_adapters` |
| P14 `I1-TWSE-BREADTH-TWTAZU-OPENAPI` | TWSE / TWSE | market_state_context | same I1 path, exact stock breadth selector |
| P15 `I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI` | TPEx / TPEX | market_state_context | same I1 path, TPEx row/unit contract |
| P16 `I2-TAIFEX-DAILYMARKETREPORTFUT-OPENAPI` | TAIFEX / source TAIFEX; target TWSE | index_futures_context | `phase_i_i2_index_futures_context_executor`; `phase_i_i2_production_transport` / `phase_i_i2_index_futures_adapters` |
| P17 `I3-TWSE-T86-INSTITUTIONAL-TRADING` | TWSE / TWSE | cash_institutional_flow_context | `phase_i_i3_cash_institutional_flow_context_executor`; `phase_i_i3_production_transport` / `phase_i_i3_cash_institutional_flow_adapters` / V2 evidence |
| P18 `I3-TPEX-3INSTI-DAILY-TRADING` | TPEx / TPEX | cash_institutional_flow_context | same I3 path, market-specific retained contract |

Endpoint authority remains in those source files: P01 `getStockInfo.jsp` with
approved `tse_`/`otc_` channels; P02 `STOCK_DAY_ALL`; P03
`tpex_mainboard_daily_close_quotes`; P04-P07 explicit `ROUTES` CSV URLs on
`mopsfin.twse.com.tw` plus fixed TWSE/TPEx JSON fallbacks; P08
`tpex_trading_warning_information`; P09 `tpex_disposal_information`; P10
`tpex_cmode`; P11 `TWT48U_ALL`; P12 `exchangeReport/STOCK_DAY` HTML by exact
stock/month; P13 `FMTQIK`; P14 `twtazu_od`; P15 `tpex_mainborad_highlight`;
P16 `DailyMarketReportFut`; P17 `/rwd/zh/fund/T86` with pre-authorized date;
P18 `tpex_3insti_daily_trading` with source-reported date, no date parameter.

### 2.2 Explicit installation and auxiliary surfaces

Bootstrap status is `ACTIVE_PRODUCTION` for the supported explicit
`manage_security_master update --live` lifecycle path; no initialized local
release is assumed. It is not an execution-time identity refresh.

| Key / source | Provider / market / role | Current seam / format | Status |
|---|---|---|---|
| B01 `twse_isin_mode2_zh` | TWSE / listed identity | materializer -> classifier `probe_sources.probe` -> `isin_parser.parse_html`; `C_public.jsp?strMode=2` | ACTIVE_PRODUCTION |
| B02 `twse_isin_mode4_zh` | TWSE / TPEx identity | same, mode 4 | ACTIVE_PRODUCTION |
| B03 `twse_delisted` | TWSE / lifecycle | `company/suspendListingCsvAndHtml?lang=zh&type=html`; lifecycle table parser | ACTIVE_PRODUCTION |
| B04 `tpex_delisted` | TPEx / lifecycle | fixed POST `/www/zh-tw/company/deListed`; manifest request contract / `parse_tpex_delisted` JSON | ACTIVE_PRODUCTION |
| B05 `twse_etn_expired` | TWSE / lifecycle | direct GET `/rwd/zh/ETN/expireEnd?response=json`; `parse_twse_expired_json` | ACTIVE_PRODUCTION |
| `TAIFEX_MIS` REST/SockJS | TAIFEX / exact future/option snapshot | `m8r_production_source_adapters` -> M8C REST `getCmdyDDLItemByKind`, `getCmdyMonthDDLItemByKind`, `getQuoteList`, `getQuoteListOption`, `getQuoteDetail`; `/futures/rt/info`, bounded `xhr`/`xhr_send` initial state | PRODUCTION_CAPABLE_BUT_NOT_ACTIVE in Unified; explicit legacy CLI registry |
| `TAIFEX_OPENAPI` | TAIFEX / derivative contexts | M8B allowlist `DailyMarketReportFut`, `DailyMarketReportOpt`, `FinalSettlementPrice`, `OpenInterestOfLargeTradersFutures`, `OpenInterestOfLargeTradersOptions`, `PutCallRatio`, `BlockTrade`; exact future/option selection through legacy one-shot registry | PRODUCTION_CAPABLE_BUT_NOT_ACTIVE in Unified; P16 has its own active contract |
| M5K TAIFEX TX quote | TAIFEX / front-month TX snapshot | `m5k_common.fetch_taifex_tx_observation`, POST `getQuoteList`; explicit legacy HTTP confirmation | PRODUCTION_CAPABLE_BUT_NOT_ACTIVE in Unified |
| `NCDR_DGPA_CLOSURE_CAP` | NCDR/DGPA / session closure | `m8a_ncdr_dgpa_closure_cap`; `RssAtomFeed.ashx?AlertType=33`, XML Atom/CAP | PRODUCTION_CAPABLE_BUT_NOT_ACTIVE as a Unified acquisition route; `session_status` blocked/no selected executor |
| nonselected H1 TWSE attention/disposition/suspend-resume/changed-trading; TPEx suspend-today/history | exchange status | descriptor/pure normalizer authority only | DORMANT_CURRENT |
| H2 final ex-right, TPEx ex-right, capital-reduction and par/split gaps; TPEx H3 EDIS | exchange actions/performance | unselected descriptors, parser/transport candidates; no current selected Unified route | DORMANT_CURRENT |
| Yahoo/Fugle/FinMind/general legacy probes and old acceptance runners | comparison/acceptance | no selected current Unified route | HISTORICAL_ONLY for this inventory; not silently promoted |
| injected/fake runtime registrations, synthetic rows and fixtures | testing | no source authority | TEST_ONLY |

## 3. Transport -> contract -> semantic profiles

| Profile / members | Transport validation (T) | Contract validation (C) | Semantic validation (S) |
|---|---|---|---|
| MIS / P01 | urllib timeout/HTTP exceptions; no MIME envelope check; UTF-8 `replace`; JSON parse; batch fallback disabled by Unified caller | `msgArray` list/rtcode check, channel-key map; no coherent returned c/ex/ch binding; duplicate key last-wins | source z vs y reference semantics, quality flags, source timestamps and family currentness; caller identity can mask conflicting returned identity (G01) |
| EOD / P02,P03 | HTTP 2xx, MIME contains json, strict UTF-8-sig JSON list; generic exception caveat; read unbounded in this seam | per-row required fields, row-object checks, exact requested code, duplicates | dates/numerics in field_validation, mixed-date batch flags, partial rows, instrument classification; Unified wrapper primarily checks observation presence, not all batch diagnostics (G03) |
| Research / P04-P07 | shared urllib bytes-only fetch hides HTTP envelope on success; strict UTF-8(-sig), CSV/JSON; one governed alternate transport, no unlimited retry | route/transport field aliases; required identity/date/period columns, snapshot consistency; CSV DictReader drops surplus cells (G04) | exact company code/name-mismatch diagnostic, duplicate conflicts, G1 publication time, G2 period/value parsing; legitimate no target remains no_evidence/not_yet_available; no invented current-period schedule |
| H1 composite / P08-P10 | fixed HTTPS, verified compatibility TLS, no redirects, 4 MiB, timeout; HTTP/MIME check, strict UTF-8 JSON rows | all declared fields string-typed, source-specific dates, exact target/duplicate checks; P08 dedicated route has older generic fetch path | per-source coverage/partial failure, missing target distinct from global clearance; unresolved source snapshot dates remain caveated; no fixed universe row count |
| H2 / P11 | fixed HTTPS no redirect, response cap, MIME/status, strict UTF-8 JSON list | source row/date/identity contract, duplicate/exact target; output evidence schema | verified H3 window dependency; scheduled vs not announced vs blank/zero distinct; no match is scope-limited no evidence |
| H3 / P12 | timeout/cap, verified TLS, status, effective URL, HTML MIME+declared charset; strict declared-codec decode | exact same-table heading+header, code/month binding, row width, dates, duplicates | finite positive closes/volume, unavailable-close provenance, valid empty table vs invalid/missing table, bounded lookback coverage |
| I1 / P13-P15 | fixed no-redirect endpoints, 64 KiB, status/MIME, strict UTF-8-sig JSON list of mappings | latest FMTQIK date uniquely selected; exact 股票 breadth selector; TPEx single-row; required fields/numeric units | cross-component dates preserved; missing breadth/benchmark partial/unavailable, malformed selected fields fail; currentness unknown rather than newly-current by retrieval |
| I2 / P16 | one fixed no-redirect GET, 2 MiB, status/MIME, strict UTF-8-sig list, row cap | max valid date then unique nearest TX YYYYMM regular-session row; selected required fields/types | finite values, nonnegative volume/OI, missing markers partial/unavailable; newer application state is unrelated to source drift; currentness remains unknown |
| I3 / P17,P18 | one acquisition per market, no retry/redirect, exact MIME, 4 MiB, Content-Length/partial body checks, strict UTF-8-sig | duplicate JSON keys, root/field uniqueness, row width, required fields/date/code, every row arithmetic | target binding/duplicate ambiguity; buy-sell=net and institutional/dealer totals, TWSE authorized date exact; absent target vs source_failed; publication finality/currentness unknown |
| Bootstrap / B01-B05 | allowlisted HTTPS, explicit shared 10-dispatch budget across five probes, max one allowed redirect per probe, no hidden retry; status/type/body assessments | ISIN controlled strict encodings: declared charset, UTF-8-sig/UTF-8/CP950/Big5/Big5-HKSCS; lifecycle JSON strict UTF-8-sig, headers/shape/dates; classification/release qualification | identity/classification/lifecycle conflicts, source error/security-block signatures; B04/B05 failure hard-stops before export; no invented universe size floor |

Auxiliary M8B uses strict UTF-8-sig JSON arrays, per-endpoint required fields,
numeric/date/session/contract validation and currentness; transport HTTP errors
are typed but successful-response MIME is recorded rather than enforced.
M8C bounds HTTP bodies/time/frames, strict JSON/UTF-8, typed REST/SockJS errors,
exact returned derivative identity, partial/missing initial states; its finite
initial-state frame collection is not a new permanent polling authorization.
Legacy M5K TAIFEX and NCDR both use UTF-8 replacement decoding and coarse
exceptions. NCDR parses XML/CAP status, area, date, scope, and cancellation
semantics; it is not authority that work closure always means market closure.

## 4. Source-by-source coverage and fixture/probe inventory

Probe labels: `OFFLINE_CONTRACT_PROBE` means deterministic validation of supplied
bytes/rows or authority, not a fresh provider health claim.
`HISTORICAL_ACCEPTANCE_ONLY` means saved accepted live evidence/runners exist
but no separately established current on-demand L3 probe contract.
`BOUNDED_LIVE_PROBE` is existing explicit code with its own bounds, not fresh
permission to execute it. No source was probed live in A0.

| Source | T/C/S profile | Probe / test references | Fixtures / negative coverage observed | Typed failure / gap |
|---|---|---|---|---|
| P01 | MIS | OFFLINE_CONTRACT_PROBE: `test_twse_mis_normalization_v2`, production adapter tests; older explicit MIS/M5Q probes | `market_sources/twse_mis/{success,empty,normalization_v2_matrix}.json`; prices/placeholders/currentness | missing/source failure and quality flags; identity G01, decode G02; no unified drift probe |
| P02 | EOD | OFFLINE_CONTRACT_PROBE: `test_m8a_twse_official_eod_adapter`; old standalone OpenAPI probe | `m8a_official_eod/twse_*`: normal, schema, partial, mixed date, invalid date/numeric, duplicate, empty | row reason codes + batch status; propagation G03 |
| P03 | EOD | OFFLINE_CONTRACT_PROBE: `test_m8a_tpex_official_eod_adapter`; old standalone OpenAPI probe | corresponding `tpex_*` normal/schema/empty/invalid/duplicate fixtures | same G03; lexical field spelling is contractual |
| P04 | Research | OFFLINE_CONTRACT_PROBE: `test_phase_g_material_disclosures`; HISTORICAL_ACCEPTANCE_ONLY live | inline CSV, wrong code/name, missing/renamed identity, fallback, report-date conflicts, target cap | SourceFailure/caveats; shared G04/envelope gap |
| P05 | Research | same tests, TPEx JSON field mapping | distinct English Date/SecuritiesCompanyCode fallback; market mismatch | same; no fresh provider proof |
| P06 | Research | OFFLINE_CONTRACT_PROBE: `test_phase_g_monthly_revenue`; HISTORICAL_ACCEPTANCE_ONLY live | inline signed/null/revenue/period/duplicate/field mutations | not_yet_available/source_failed/binding_failed; G04 |
| P07 | Research | same tests, TPEx route | saved source-shaped JSON represented in tests; required field/period mutations | same |
| P08 | H1 | offline normalizer/activation + dedicated production adapter tests; HISTORICAL_ACCEPTANCE_ONLY live | `phase_h_h1_adapters/source_rows.json`, type/date/binding mutations | source_transport_failed/source_json_invalid/source_contract_failed on dedicated route; composite typed prefixes; G06 |
| P09 | H1 | offline pure adapter/composition/activation; HISTORICAL_ACCEPTANCE_ONLY live | same source_rows disposition cases | composite source_failed/binding_failed; direct composite transport fixture gap G06 |
| P10 | H1 | offline representative normalizer/composition/activation; HISTORICAL_ACCEPTANCE_ONLY live | changed-trading status/date/required string contract in current code | composite date_contract_drift and field prefixes; G06 |
| P11 | H2 | OFFLINE_CONTRACT_PROBE: `test_phase_j_b04_a3_h2_executor` exercises current runtime despite dated filename | injected timeout/status/MIME/bytes, zero/blank/not-announced, duplicate, H3 dependency cases | http_or_content_type/strict_json_decode/window/binding codes |
| P12 | H3 | OFFLINE_CONTRACT_PROBE: `test_phase_h_h3_i2a_twse_stock_day_adapter`, walker tests; historical live acceptance | generated HTML headings/headers, swapped tables, numeric grouping, unavailable close, HTTP/challenge/empty, target/month mutations | detailed source_failed/binding_failed/no_evidence; no current live probe |
| P13 | I1 | OFFLINE_CONTRACT_PROBE: I1 production/activation/market-state tests; HISTORICAL_ACCEPTANCE_ONLY live | `phase_i_i1/twse_fmtqik.json`, unordered/duplicate/bad date/empty mutations | fmtqik_* typed reasons |
| P14 | I1 | same | `twse_breadth.json`, missing/duplicate 股票, component date mismatch | partial/missing/source_failed; no fixed all-market count |
| P15 | I1 | same | `tpex_highlight.json`, row count/unit/numeric mutations | invalid_rows/required field/numeric codes |
| P16 | I2 | OFFLINE_CONTRACT_PROBE: I2 production transport/A2 offline and passive registry node; HISTORICAL_ACCEPTANCE_ONLY A3 live | inline deterministic source rows/byte payload; invalid UTF-8/root/selected numeric/date, duplicate series, no regular TX | transport codes + complete/partial/unavailable/binding_failed; stateful test debt section 8 |
| P17 | I3 | OFFLINE_CONTRACT_PROBE: I3 A2 offline/A4 candidate/activation; HISTORICAL_ACCEPTANCE_ONLY A3 Attempt 4 | `phase_i_i3_a0/twse_synthetic.json`, body read/size/MIME/date/fields/arithmetic mutations | AcquisitionError telemetry, prepared-source error + failed V2 evidence |
| P18 | I3 | same | accepted dealer-sell adjudication scenario fixture; source-native optional/malformed core rows | same; hypothesis-only TPEx fixture is not accepted current source authority |
| B01 | Bootstrap | BOUNDED_LIVE_PROBE code `probe_sources.probe`; OFFLINE bootstrap tests | injected redirect/HTTP/body/classifier fixtures | generic source qualification/rejection; historical identity minima not universal universe authority |
| B02 | Bootstrap | same | mode4 explicit inventory/budget tests | same |
| B03 | Bootstrap | same plus lifecycle parsers | source table/header/date schema tests | LifecycleSchemaDrift / BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT |
| B04 | Bootstrap | same + `test_parse_tpex_delisted_json` | method/body/redirect/status/schema tests | BOOTSTRAP_TPEX_LIFECYCLE_SOURCE_FAILURE / schema drift |
| B05 | Bootstrap | same | endpoint/JSON field-order/row-width/content-type/transport tests | BOOTSTRAP_TWSE_ETN_LIFECYCLE_SOURCE_FAILURE / PARSER_FAILURE / schema drift |

Auxiliary fixtures: `m8b_taifex_openapi` plus per-endpoint adapter tests;
`m8c_taifex_mis/sockjs_quote_frame.txt`, identity/protocol/preflight tests;
`m8a_emergency_closure/*.xml` and CAP tests. Their existing live probe scripts
are explicit legacy mechanisms, not an approved common L3 probe system.
H1 composite runtime `_decode_payload`/`_validate_source_rows` has no directly
named test caller found by the current test search; pure-normalizer and route
coverage must not be overstated as full composite transport mutation coverage.

Existing probe mechanisms are distinguished from source adapters and saved live
acceptance witnesses:

| Mechanism | Classification for L3 inventory | Fields/layers it actually checks / limit |
|---|---|---|
| Current adapter/contract unit tests and source/catalog validators | OFFLINE_CONTRACT_PROBE | supplied payload shape, required fields, identity/date/numeric semantics, registry coherence; no claim about today's provider |
| `probe_twse_mis.py`, `probe_twse_mis_rich_fields.py`, `probe_twse_openapi.py`, `probe_tpex_openapi.py` | HISTORICAL_ACCEPTANCE_ONLY as L3 probe authority | standalone source investigation/normalization envelopes exist; no accepted shared L3 T/C/S probe contract or current execution permission |
| `run_m5q_source_health_probe.py` | BOUNDED_LIVE_PROBE mechanism, no A0 live permission | explicit execute flag; check-only path validates route/governance; source availability/freshness health does not prove every source contract |
| G/H/I bounded acceptance runners and I3 attempt/probe mapping records | HISTORICAL_ACCEPTANCE_ONLY | source-specific retained shapes, transport/semantic evidence at their accepted observation time; cannot recertify current provider or reuse consumed acceptance authority |
| classifier `probe_sources.probe` via explicit Security Master update | BOUNDED_LIVE_PROBE | allowlist, transport/MIME, parse/schema presence, semantic error signatures and source-specific lifecycle parsing under bootstrap dispatch budget |
| Separate current common L3 drift probe envelope/scheduler | NO_PROBE | not implemented; no scheduler or polling is proposed |

Fresh L3 probes require a separately approved bounded contract. Saved historical
probe fields are implementation evidence, not current external observations.

## 5. Nine drift classes and current machine outcomes

| Drift class | Exposed sources | Existing detection / machine outcome | Fixture/probe / gap |
|---|---|---|---|
| Schema drift | all | strict shape/required-field checks in research,H1-H3,I1-I3/bootstrap; EOD rejected_rows/schema_drift; MIS envelope only | many offline mutations; MIS G01/G02, EOD G03, CSV G04 remain |
| Field rename | all field-based contracts | required key absence generally fails; legitimate optional source-native fields in I3 become caveated unavailable, not core failure | G1/G2 key mutations, H3 strict headers, I1/I2/I3 required-field tests; no blanket alias guessing; optional disclosure text/CSV column loss not exhaustively protected |
| Encoding change | all byte sources | UTF-8 strict failures generally map to JSON/decode/source_failed; H3 declared codec; ISIN controlled alternatives | I1/I2/I3/H3 malformed decode tests; MIS/legacy TAIFEX/NCDR replacement decoding G02; complete codec mutation matrix absent |
| Empty-but-200 | all | empty bytes fail parse in strict JSON; `[]` is EOD empty_non_trading_day, I1 unavailable/partial, I2 unavailable, I3 failed required/date/code; valid H3 empty table is no_evidence; research empty/header-only fails | MIS `msgArray=[]` yields target missing, not complete evidence; no uniform code required. Do not treat legitimate empty target scope as corruption |
| Delayed publication | dated/batch sources P02-P18,B01-B05; MIS source timestamp | G1/G2 retained report/period and no_evidence/not_yet_available; H1 snapshot date uncertainty; H3 bound month/window; I1 cross-date components; I2/I3 currentness unknown | no source-agnostic schedule authority or fresh latest validation. Previous period is not automatically labeled current; dedicated late-publication probes incomplete |
| Unexpected universe delta | multi-row feeds/all target feeds | exact requested targets, duplicate identities, I1 股票 category/one-row expectations, I2 TX regular-series selection, I3 every-row identity/arithmetic, bootstrap lifecycle contracts | no generally authoritative historical-universe baseline; row-count change alone is not drift. Whole-source collapse beyond declared semantic expectations remains PROBE_COVERAGE_GAP |
| HTTP failure | all transports | urllib/requests status/exception handling; H3/I1/I2 and I3 telemetry preserve status; older sources coarsen exception/caveat | injected HTTP/timeout/read tests strong in modern seams; research response envelope not retained, older MIME/redirect coverage incomplete |
| Rate limiting | all remote providers | HTTP 429 usually becomes existing HTTP/source failure; some bootstrap error-signature checks; status may remain in telemetry | no comprehensive provider throttle-body/Retry-After fixture matrix; no new retry or Retry-After scheduling authorized; G05 |
| Source removal | all remote providers | 404/410/non-data/invalid-schema fails through existing HTTP/contract paths | temporary outage vs endpoint deletion vs loss of authority cannot be inferred from one response; no accepted deprecation protocol/current probe; G05 |

Detailed existing vocabulary is retained rather than collapsed:

- Transport: `source_failed:http_status`, `transport_failure`,
  `invalid_json_or_utf8`, `invalid_utf8_or_json`, `html_decode_failed`,
  `source_failed:http_or_content_type`; I3 `http_error`, `unsupported_mime`,
  `content_length_mismatch`, `empty_body`, `body_read_failed` in telemetry.
- Contract: research `source_contract_required_field_missing`,
  `source_snapshot_report_date_invalid`, `source_snapshot_period_identity_invalid`;
  H1 `missing_required_field:*`, `invalid_required_field_type:*`,
  `date_contract_drift:*`; H3 `report_table_contract_missing`/heading failures;
  I3 duplicate keys/row width/required code/fields and arithmetic errors.
- Legitimate semantics: `no_evidence_in_covered_scope`, `not_yet_available`,
  `missing`, `unavailable`, `partial`, reference-only, stale/unresolved/unknown
  currentness remain distinct from `source_failed`/`binding_failed`.
- EOD per-field validation and rejected-row codes are machine-readable inside
  adapter results; generic Unified success must not be mistaken for proof that
  all batch diagnostics were enforced. Research fetch exceptions currently
  preserve exception class names across fallback; they do not preserve a full
  HTTP envelope or a bounded transport/contract/semantic taxonomy.
- Authorization and preflight errors (network not authorized, invalid approved
  target/route) are control-plane failures, not drift. A0 adds no failure code.

## 6. Gap register and priority

| Gap | Severity | Evidence / effect | Priority |
|---|---|---|---|
| G01 returned MIS identity conflicts can be relabeled as requested target | BLOCKING_CORRECTNESS_GAP | channel-key map in `m5k_common` followed by caller-identity normalization; isolated reproduction below | 1: A1 candidate |
| G02 MIS replacement decode, weak response envelope and duplicate-key/row ambiguity | HARDENING_GAP | P01 decode uses `errors=replace`; no MIME guard, duplicate channel map overwrites; auxiliary TAIFEX/NCDR share replacement risk but different contracts | 1 within bounded P01 response contract; auxiliary changes deferred |
| G03 EOD batch/field diagnostics not fully enforced by Unified wrapper | HARDENING_GAP | adapter marks invalid date/numerics/mixed date or partial status; wrapper selects observations by symbol without inspecting all diagnostics | 2: separate source-result propagation adjudication; no claim invalid numeric is fabricated as zero |
| G04 CSV structural strictness and research envelope/provenance | HARDENING_GAP | DictReader surplus values under None are discarded; row values stringified; `_fetch_official_payload` returns body only | 3: explicit structural guard before field mapping; determine source-specific text requirements |
| G05 429/throttle/404/410/deprecation and publication/universe probes | PROBE_COVERAGE_GAP | status generic or telemetry only; no authority to infer removed source or add retries/schedule | 4: bounded probe contract after correctness fixes |
| G06 composite H1 transport negatives and common drift fixtures | FIXTURE_COVERAGE_GAP | pure adapter/activation fixtures exist; direct current composite transport matrix not found | 3; lack of fixtures alone is not proof of defective production behavior |
| G07 I1 old dormant docstring, I2 pending candidate field, H2 dormant descriptor | OBSERVABILITY_ONLY | superseded by explicit current route and accepted activation authority | later minimal governance cleanup if separately justified |
| G08 partial/not-yet/unknown semantics already explicit | NO_GAP | current G/H/I evidence contracts intentionally preserve uncertainty | keep; do not invent generic drift errors |

### 6.1 Deterministic G01 witness

Before A0 edits, an in-memory Response replaced `urllib.request.urlopen` and
socket connect/create_connection were forbidden. Starting from retained
`tests/fixtures/market_sources/twse_mis/success.json` first row, set
`key=tse_2330.tw_20261015`, `ch=2330.tw`, `c=2317`, `ex=otc`; keep its valid
z/time values. Call the actual `execute_live_observation` with one caller
instrument TWSE:2330, `write_latest=False`, `allow_individual_fallback=False`.
No bytes were fetched or persisted. Actual output:

```json
{"validation":true,"observations":[{"symbol":"2330","market":"twse","status":"ok","price":1015.0}],"returned_c":"2317","returned_ex":"otc","network_calls":[]}
```

The normalizer fills symbol/market from the caller rather than proving coherence
with returned c/ex. Unified current-observation adapters then consume those
observations. This is a reproducible silent wrong-binding path under malformed
source input, not a claim that a live provider currently returns this payload.
A0 records the defect and does not modify the runtime.

## 7. Recommended bounded A1 contract candidate

**L3-A1 — TWSE MIS Returned Identity and Response Contract Guard**

Candidate contract status: `FROZEN_CANDIDATE_FOR_REVIEW`, not Owner accepted or
implementation-authorized. First priority is contradictory/missing returned
identity, followed by strict decoding and unambiguous source envelope at the
same acquisition seam. It affects the active TWSE and TPEX current-observation
routes without building a second HTTP client or registry.

Allowed candidate surface: `scripts/m5k_common.py` MIS response parsing seam,
minimal source-specific helper only if needed, focused source fixtures/tests,
and production adapter regressions. Avoid changing pure observation/currentness
semantics or unrelated TAIFEX/NCDR clients. Source drift checks may share
structural validation helpers, but field meaning, expected `tse`/`otc` identity,
valid no-data forms, and channel semantics remain MIS-specific.

Required candidate behavior:

1. Strictly decode the supported UTF-8 bytes; malformed bytes cannot become
   replacement-corrupted accepted source data. Validate JSON object/msgArray
   shape and existing provider status semantics before target fanout.
2. Require source-returned identity fields supported by current fixtures to
   coherently match the exact approved symbol/market/channel. A matching key
   cannot override contradictory c/ex/ch. Missing/renamed identifier, wrong
   market, duplicate/conflicting exact channel rows fail closed. Do not bind by
   name or synthesize missing identifiers from the caller.
3. Preserve valid z/current vs y/reference-only and missing/no-data distinctions,
   source timestamps, currentness, batching, explicit authorization, and existing
   no-individual-fallback Unified behavior. A matching request identity is not
   proof of returned source identity.
4. Return bounded internal reason metadata through existing failure channels;
   any proposed new internal reason names need A1 review. No public schema,
   evidence family, source activation, retry policy, scheduler, or MCP change.
5. Offline tests: valid TWSE and TPEx rows, missing/renamed c/ex/ch, contradictory
   identity with valid key, duplicate exact channels, malformed UTF-8, HTML/error
   response, bad root/array/row shape, empty valid msgArray, valid placeholders,
   reference-only and partial multi-target outcomes; zero sockets, no unintended
   writes or authorization side effects. Run existing MIS/production/currentness
   and exact-six regressions.

No fresh live authority is required to implement/test this bounded candidate.
A future provider recertification would require `LIVE_PROBE_AUTHORITY_REQUIRED`
with exact endpoints, targets, dispatch/timeout/retention bounds. A0 does not
authorize or execute that probe or start A1.

## 8. Verification, debt, and mutation containment

Validators executed successfully:

```text
python -B scripts/validate_source_registry.py
python -B scripts/validate_portable_catalog_sync.py
```

The first broad attempted test run, before any A0 code/document changes, had
**348 passed, 36 failed, 6 warnings**. Causal classification:

- Six MCP failures were introduced by A0's overly strict execution wrapper,
  which blocked Windows asyncio loopback socketpair creation at
  `127.0.0.1`. Associated six warnings were event-loop/coroutine cleanup effects.
  The wrapper was corrected to allow loopback while denying external sockets.
- 28 I2-A4 tests failed at `phase_i_i2_a4_proof.production_preview` ->
  `load_active_mode_a_security_master(ROOT/data/security_master)` ->
  `NOT_INITIALIZED`, before source transport. The passive registry/authority
  node is usable without that installed state. No machine state was initialized.
- Bootstrap's source-text test used locale-default `Path.read_text()` on UTF-8
  source and failed CP950 decoding. Running Python with `-X utf8` resolves it.
- `test_lifecycle_drift_failure_report_preserves_code_without_retry_authority`
  searches arbitrary rglob JSONs for the text `bootstrap_failure_code`; it can
  select `source_evidence_manifest.json` containing the nested probe code instead
  of the governed report, then raises KeyError for the top-level code. Runtime
  `_write_failure_report` constructs both files and explicitly sets the report
  field. This test selection debt is recorded, not repaired or hidden as a pass.

The accepted inventory gate uses the same 19 test surfaces, selects the passive
I2-A4 authority node only, runs UTF-8 mode, and explicitly deselects the one
bootstrap traversal-order test. Result: **354 passed, 1 deselected, 0 failed,
0 warnings**. An external-socket guard on connect/connect_ex permits only
literal loopback/localhost and counted **0 external socket attempts**.

Exact pytest argument vector used by the guarded Python bootstrap:

```text
-q -k "not test_lifecycle_drift_failure_report_preserves_code_without_retry_authority"
tests/unit/test_validate_source_registry.py
tests/unit/test_m8r_06_03_production_adapter.py
tests/unit/test_m8r_08b_mcp_tool_contracts.py
tests/unit/test_phase_g_material_disclosures.py
tests/unit/test_phase_g_monthly_revenue.py
tests/unit/test_m8a_twse_official_eod_adapter.py
tests/unit/test_m8a_tpex_official_eod_adapter.py
tests/unit/test_twse_mis_normalization_v2.py
tests/unit/test_phase_h_h3_i2a_twse_stock_day_adapter.py
tests/unit/test_phase_j_b04_a3_h2_executor.py
tests/unit/test_phase_i_i1_production_candidate.py
tests/unit/test_phase_i_i1_production_activation.py
tests/unit/test_phase_i_i2_a4_activation.py::test_current_catalog_source_and_unique_passive_registry
tests/unit/test_phase_i_i2_production_transport.py
tests/unit/test_phase_i_i2_a2_offline.py
tests/unit/test_phase_i_i3_a2_offline.py
tests/unit/test_phase_i_i3_a4_candidate.py
tests/unit/test_phase_i_i3_a4_activation.py
tests/unit/test_m8r_06_01b_bootstrap_dispatch_budget.py
```

Invocation was `python -X utf8 -B -c $gateCode`; the bootstrap patches socket
connect/connect_ex to reject non-loopback addresses, runs `pytest.main` with
the vector above, prints `L3_A0_EXTERNAL_SOCKET_ATTEMPTS`, and fails if nonzero.
Source responses are fixtures/injected delegates. Tests with historical names
are included only where they directly test current code. Saved bounded-live
acceptance/attempt scripts are `LIVE_ACCEPTANCE` or `HISTORICAL_ONLY`, not a
requirement to rerun live. No default/full CI or live gate was run.

Fresh worktree status was clean before and after tests; no untracked product
state, Security Master, Watchlist, backup, Result/Audit, or source payload was
created. Only A0 governance/front-door changes follow. HTTP, Unified Request,
Result/Audit schemas, authorization, active routes and source activation state
are unchanged. Exact-six MCP contract tests pass. `financial_statements` stays
outside capability scope. No source GET/POST or fresh market acquisition was
performed; Git/GitHub operations are the only external service operations.

Candidate containment: exactly this inventory plus PROJECT, HANDOFF, ROADMAP
current reconciliation, and the Phase L recovery index. No runtime/test/schema/
registry file is changed. `git diff --cached --check`: PASS.

### 8.1 Independent reviewer verification

Independent exact-head review reproduced the confirmed MIS wrong-binding path
with an injected retained fixture and no source network: a response row with a
matching requested channel key but contradictory `c=2317` / `ex=otc` still
produced a caller-bound `TWSE:2330` observation with `status=ok`. The simplified
review print did not project the price field, but the identity-coherence defect
itself was reproduced and remains a `BLOCKING_CORRECTNESS_GAP`.

The reviewer re-ran the guarded focused gate and confirmed **354 passed, 1
deselected, 0 failed**, with `L3_A0_REVIEW_EXTERNAL_SOCKET_ATTEMPTS=0`. Source
registry validation, Portable Catalog synchronization, runtime/Skill exact-six
validation, and `git diff --check` also passed. A direct runtime registry sanity
check confirmed 17 current registrations, consistent with the inventory basis.

One governance-only inconsistency was repaired: the later `HANDOFF.md` section
named `Explicit stop boundary` still said L3-L7 were unauthorized, while the
current handoff already recorded Owner-authorized L3-A0 entry. That section now
matches the current A0 candidate boundary. No runtime, test, schema, registry,
route, activation, authorization, or source behavior changed.

Independent technical disposition:

`L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_ACCEPTANCE_REVIEW_PASS`

Owner candidate acceptance remains not recorded. A1 and L4-L7 remain not
authorized.

## 9. Deferred boundaries and stop

L4 owns general payload/target/concurrency/resource/security ceilings. Existing
source-specific bounds are inventoried here, not globally redesigned. L5 owns
extension architecture; L6 installer/Docker/init/state mapping/portability;
L7 release workflows/manifests/SDK range/version decisions. No Phase M monitor,
automatic refresh, permanent poll, new source or new capability is introduced.

Inventory is complete under
`L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_COMPLETE`. G01 remains a blocking
production correctness gap selected for a separate A1 remediation decision.
The A0 candidate does not claim L3 completion or Owner acceptance. Stop after
commit/push/PR for independent review. A1 and L4-L7 remain NOT AUTHORIZED.
