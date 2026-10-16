# Phase L L3-A5 — Source Lifecycle, Throttling & Publication Drift Contract

**Date:** 2026-10-15
**Status:** implementation candidate; independent review pending
**Base SHA:** `ea4697ecddb906b088765e0d32388830aa7baf1b`
**Branch:** `phase-l/l3-a5-source-lifecycle-publication-drift-contract`
**Worktree:** `D:\Codex-Workspace\projects\tw-market-live-data-intelligence-phase-l-l3-a5`

## Authority and scope

Owner explicitly authorized L3-A5 implementation only at the base above.
Authority recovered from the current Phase L recovery index, `PROJECT.md`,
`HANDOFF.md`, frozen L0, current Phase L Roadmap section, A0 inventory, and the
merged A1-A4 records. A0 identifies G05 as `PROBE_COVERAGE_GAP`, not a known
production correctness defect. This candidate defines deterministic
observation/adjudication for supplied facts. It performs no live source
recertification and does not claim current provider health.

G01-G04 and G06 are not reopened. There are no public schema or source runtime
changes. The pure internal contract is in
`server/services/phase_l_source_drift_contract.py`; it does not create a second
transport, source registry, public failure taxonomy, or evidence system.

## Observation versus inference

`observe_source_attempt()` accepts explicit, already-observed bounded facts:
contract identity, observation timestamp, status, optional `Retry-After`,
source-specific contract/semantic outcomes, empty-response policy, counts,
target-binding result, and source/requested period labels. It does not accept or
inspect a response body, call a source adapter, or use the current clock.
The observation is deterministic for identical inputs. Existing source
adjudication remains authoritative for empty responses, publication state,
target selection, and contract validity.

HTTP status observations are:

| Fact | Observation | Not inferred |
|---|---|---|
| 429 | `rate_limit_observed` | permanent provider throttle |
| 404 | `endpoint_not_found_observed` | source removed |
| 410 | `endpoint_gone_observed` | authority retired |
| 503 / other non-2xx | HTTP failure reported | source lifecycle conclusion |
| no HTTP status + supplied transport failure | transport failure reported | source removal |

The supplied source semantic outcome remains intact (`available`, `partial`,
`missing`, `unavailable`, `no_evidence_in_covered_scope`,
`not_yet_available`, `currentness_unknown`, `stale`, `source_failed`, or
`binding_failed`). `not_yet_available` may add the observation
`publication_delay_observed`; it does not become `source_failed`. A prior
reported period is retained as a label and is not automatically current or
stale. No age threshold or source-agnostic publication calendar is introduced.

## Retry-After

The pure parser distinguishes absent, non-negative decimal delta, normalized
HTTP-date, malformed/negative, and out-of-representation-range values. The
signed 32-bit maximum (`2,147,483,647`) is a representation bound only, not a
retry duration. HTTP dates are stored in canonical GMT form. The parsed fact
never sleeps, retries, schedules, changes a dispatch budget, or authorizes a
later request.

## 404, 410, deprecation, and source lifecycle

A single 404/410 only records endpoint response facts. Current A0 source
profiles expose no accepted explicit endpoint-deprecation signal protocol.
Bootstrap B03-B05 provide lifecycle *data* about securities, not an
authoritative signal that their endpoint/source authority is retired. The
observation helper has no response-body input, so arbitrary HTML/JSON text
containing “deprecated” cannot establish deprecation. No automatic source
retirement or replacement is performed.

## Publication, empty responses, and currentness

The helper requires source-specific outcomes and takes no publication schedule.
It preserves existing `not_yet_available`, `no_evidence_in_covered_scope`,
`partial`, `missing`, `unavailable`, and currentness states. An empty body or
empty collection is an observed form; only a caller-supplied exact source
policy of `invalid` yields `SOURCE_CONTRACT_REJECTS_EMPTY_RESPONSE`. `allowed`
and `unknown` preserve existing semantics and cannot turn an empty payload into
complete evidence. A2/A3 regressions continue to cover their source-specific
empty and publication behavior.

## Universe and target scope

The helper records `observed_row_delta` without classifying it as corruption.
Matched targets remain source-specifically adjudicated even when row counts
increase/decrease (including unrelated extras); absent targets remain separate
from ambiguous/duplicate target binding. An ambiguous target asks the
source-specific contract to adjudicate. A contractual selector/category
failure remains a contract failure, not a generic row-count conclusion. No
historical universe baseline or fixed row-count expectation is added.

## Source-profile traceability

The scope is the A0 current active contracts: P01-P18 plus B01-B05. Shared
status/Retry-After observation uses the single pure helper; this is not a claim
that every endpoint received a separately mutated transport fixture. The
source-specific regressions listed below were included in the guarded suite.

| Profile | Current source members | Existing source-specific regression used |
|---|---|---|
| MIS | P01 | `test_l3_a1_twse_mis_response_contract.py` |
| EOD | P02/P03 | `test_l3_a2_eod_diagnostic_propagation.py`, TWSE/TPEx EOD adapter tests |
| Research | P04-P07 | A3 test, material disclosure and monthly revenue tests |
| H1 composite | P08-P10 | A4 matrix test |
| H2 | P11 | `test_phase_j_b04_a3_h2_executor.py` |
| H3 | P12 | H3 stock-day adapter and walker tests |
| I1 | P13-P15 | I1 market-state and production-candidate tests |
| I2 | P16 | I2 offline, production transport, and injected transport tests |
| I3 | P17/P18 | I3 offline and R1 transport-accounting tests |
| Bootstrap | B01-B05 | dispatch-budget tests (including injected B01/B02 route behavior), TPEx delisted, and TWSE ETN lifecycle parser tests |

This matrix is profile-level traceability, not a Cartesian mutation matrix.
The shared helper tests exercise status, Retry-After, timeout, empty-response,
publication/currentness, target-binding, and row-delta cases offline.

## Deterministic fixture matrix

| Case | Expected bounded result |
|---|---|
| 200 healthy response | source-specific semantics preserved |
| 429 without header | throttle observed; no retry authority |
| 429 with delta / HTTP-date | parsed bounded fact only |
| malformed, negative, too-large Retry-After | unparseable/out-of-range observation only |
| 404 / 410 | endpoint-not-found/gone facts only |
| 503 / timeout | HTTP failure distinct from transport failure |
| source contract invalid | `CONTRACT_FAILURE_REPORTED` |
| valid source-specific empty collection | existing no-evidence/partial semantics preserved |
| invalid empty body | rejected only when exact source policy says invalid |
| not-yet-available / currentness unknown | original semantic state preserved |
| prior period supplied | date/period labels retained; no current/stale inference |
| row count increase/decrease | signed delta observed; no universe-invalid conclusion |
| target absent / ambiguous | target-scope observation; source-specific outcome retained |
| contractual selector/category absent | explicit source contract outcome `invalid`; contract failure reported |
| arbitrary “deprecated” body wording | cannot be interpreted; body is not accepted by helper |
| explicit accepted deprecation signal | none exists in current A0 source authority |

## Runtime and public compatibility

No production runtime adapter was changed. The current source seams have
different transport/envelope contracts and G05 has not authorized a shared
live-probe framework. The bounded pure helper is a private check-only
projection over supplied facts; existing active adapters keep their established
semantics. There is no production integration that emits persistent or public
drift evidence. This is deliberate: live source recertification is reserved for
separately authorized A6.

No Unified Request/Result/Audit schema, HTTP API, MCP tool, Catalog, Route,
executor activation, authorization model, evidence family, or capability set
changed. MCP remains exactly six tools.

## Verification

Focused deterministic test:

```text
python -X utf8 -m pytest -q tests/unit/test_phase_l_a5_source_drift_contract.py
53 passed
```

Integrated guarded offline regression:

```text
python -X utf8 -m pytest -q -p l3a5_no_external_network \
  -k "not test_lifecycle_drift_failure_report_preserves_code_without_retry_authority and not test_partial_batch_retains_observation_and_diagnostics_without_clean_success" \
  tests/unit/test_phase_l_a5_source_drift_contract.py tests/unit/test_l3_a1_twse_mis_response_contract.py tests/unit/test_l3_a2_eod_diagnostic_propagation.py tests/unit/test_l3_a3_research_source_contract_guard.py tests/unit/test_l3_a4_h1_composite_negative_fixture_matrix.py tests/unit/test_m8r_06_03_production_adapter.py tests/unit/test_m8a_twse_official_eod_adapter.py tests/unit/test_m8a_tpex_official_eod_adapter.py tests/unit/test_phase_g_material_disclosures.py tests/unit/test_phase_g_monthly_revenue.py tests/unit/test_phase_h_h3_i2a_twse_stock_day_adapter.py tests/unit/test_phase_h_h3_i2a1_twse_stock_day_walker.py tests/unit/test_phase_j_b04_a3_h2_executor.py tests/unit/test_phase_i_i1_market_state.py tests/unit/test_phase_i_i1_production_candidate.py tests/unit/test_phase_i_i2_a2_offline.py tests/unit/test_phase_i_i2_production_transport.py tests/unit/test_phase_i_i2_a3_live_transport.py tests/unit/test_phase_i_i3_a2_offline.py tests/unit/test_phase_i_i3_a3_r1_transport_accounting.py tests/unit/test_m8r_06_01b_bootstrap_dispatch_budget.py tests/unit/test_parse_tpex_delisted_json.py tests/unit/test_parse_twse_etn_expired_json.py tests/unit/test_validate_source_registry.py tests/unit/test_validate_v1_public_contracts.py tests/unit/test_phase_h_v3_contract_freeze.py
  583 passed, 2 deselected, 0 warnings
L3_A5_EXTERNAL_NETWORK_ATTEMPTS=0
```

The temporary guard rejects external `socket.connect`, `connect_ex`,
`create_connection`, and `urllib.request.urlopen`; loopback is permitted. The
first integrated run exposed one existing A2 test that calls the production
adapter because no offline TPEX result was injected. That exact test was
excluded from the final gate; its source attempt was blocked by the guard and
did not reach the network. The other deselected test,
`test_lifecycle_drift_failure_report_preserves_code_without_retry_authority`,
fails on the unmodified current bootstrap report writer because its recursive
JSON search may select a nested manifest before the report; A0 already records
this test-selection debt. Its initial run failed with `KeyError` for the
top-level field. Neither test is hidden or represented as passing.

An additional optional Security Master snapshot test module was explored but is
not in this gate: it produced 9 failures on the current fixtures due to
`current_skill_contract_hash_mismatch` (plus a subprocess locale decode warning
in the CLI test). Its hash function consumes Skill files that are unchanged in
this candidate; this unrelated fixture/current-Skill drift is not repaired in
A5. The module is not required to adjudicate G05.

Validators and compile checks all passed:

- `scripts/validate_source_registry.py`
- `scripts/validate_portable_catalog_sync.py`
- `scripts/validate_runtime_skill_guide_sync.py` (`tool_count=6`)
- `scripts/validate_v1_public_contracts.py` (`tool_count=6`)
- `scripts/validate_phase_h_v3_contracts.py`
- `python -X utf8 -B -m py_compile server/services/phase_l_source_drift_contract.py tests/unit/test_phase_l_a5_source_drift_contract.py`
- `git diff --check`

No Security Master, Watchlist, Result/Audit, production evidence, Catalog,
Route, activation, or other persistent user state was mutated. No fresh source
acquisition was performed. No retry/backoff, scheduler, polling, or monitoring
was added.

## G05 disposition and next boundary

Candidate disposition: `G05_DETERMINISTIC_CONTRACT_COMPLETE__LIVE_RECERTIFICATION_REQUIRED`.
This does not close all G05 or L3. Current endpoint health, provider lifecycle,
and freshness remain unknown from this offline tranche.

## Independent-review repair R1 — fact-contract coherence

Independent review found that the initial candidate validated individual
fields but accepted contradictory combinations. Reproduced witnesses included
`HTTP 200 + transport_outcome=transport_failure`,
`transport_outcome=http_response + http_status=None`,
`HTTP 429 + semantic_outcome=not_yet_available`,
`contract_outcome=invalid + semantic_outcome=not_yet_available`,
`empty_collection + semantic_outcome=available`, and
`observed_at="not-a-time"`. These inputs could create an internally
inconsistent private observation.

R1 adds only deterministic cross-field checks in
`server/services/phase_l_source_drift_contract.py`:

- `observed_at` must parse as ISO-8601 and include an explicit timezone/offset;
- `transport_failure` requires no HTTP status, and `http_response` requires a
  status;
- `not_yet_available` and `currentness_unknown` require a successful 2xx
  response and `contract_outcome=valid`, so failed transport, non-2xx, or
  invalid contract cannot emit these semantic-derived observations;
- `empty_body` / `empty_collection` cannot be paired with `available`;
- the other source-specific absence/currentness values and valid empty
  collection outcomes remain unchanged.

R1 does not change source transports, production adapters, public schemas,
retry behavior, or source-specific semantic policy. No clock is read.

Updated verification:

```text
focused A5 tests: 55 passed
integrated guarded offline gate: 585 passed, 2 deselected, 0 warnings
external network attempts: 0
source registry: PASS
Portable Catalog sync: PASS
runtime/Skill sync: PASS (exactly 6 tools)
V1 public contracts: PASS (exactly 6 tools)
Phase H V3 contracts: PASS
py_compile: PASS
git diff --check: PASS
```

The same two existing deselections described above remain; they were not
hidden. No technical PASS or Owner acceptance is recorded by this repair. The
candidate is ready for independent re-review only.

## Independent-review repair R2 — successful-response predicate

Review found that R1's `response_is_adjudicable` predicate still allowed
`transport_outcome="unknown"` with no HTTP status to support
`not_yet_available` or `currentness_unknown`, because it only excluded
`transport_failure` and treated a missing status as acceptable. R2 requires an
actually observed successful response:

```text
transport_outcome == http_response
AND http_status is present and 2xx
AND contract_outcome == valid
```

The exact unknown-transport/no-status witnesses for both semantic outcomes now
fail with `semantic_outcome_requires_valid_response`. Existing accepted 200 +
valid-contract cases remain accepted; 429, 503, explicit transport failure,
and invalid-contract combinations remain rejected. The `unknown` transport
value remains available for other coarse/legacy observations. This is a
bounded coherence correction with no architecture, public-surface, or
production-runtime scope change. Owner acceptance is not recorded; independent
technical PASS remains for external review.

Proposed future tranche is `L3-A6 — Bounded Live Source Drift Recertification`,
which requires separate Owner authorization and explicit source set, endpoints,
targets, dispatch/timeout bounds, zero retries/sleep/scheduler/polling, no state
or activation mutation, bounded retained evidence, one bounded run, and a
mandatory stop. This candidate does not select any provider as healthy. A6 is
not authorized; A7 and L4-L7 remain unauthorized.

## Independent technical acceptance and Owner authorization

Independent exact-head review of `b51e0415e456092e6aaa986f4755ec38015004bc` completed on 2026-10-16 with disposition:

`L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_ACCEPTANCE_REVIEW_PASS`

The review independently re-ran the final A5 focused gate (`55 passed`) and the guarded integrated offline gate (`585 passed, 2 deselected`) with `0` external network attempts, and verified the R2 successful-response coherence witnesses. No additional technical blocker remained.

Owner explicitly accepted L3-A5 and authorized merge in chat on 2026-10-16. Owner disposition:

`L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_OWNER_ACCEPTED_FOR_MERGE`

Authority: `USER_CHAT_2026-10-16_L3_A5_OWNER_ACCEPTANCE_AND_MERGE_AUTHORIZATION`.

This acceptance closes only the deterministic A5 tranche. G05 live recertification remains required. A6/A7 and L4-L7 remain NOT AUTHORIZED; no live probe or source acquisition is authorized by this acceptance.

## Stop boundary

Only this bounded G05 deterministic observation/adjudication candidate is
complete. Do not perform live probes, start A6/A7, or begin L4-L7 from this
candidate.

## Exact candidate file set

```text
PROJECT.md
HANDOFF.md
ROADMAP.md
docs/governance/phase_l/PHASE_L_CURRENT_STATUS_AND_RECOVERY_INDEX_2026-10-14.md
docs/governance/phase_l/PHASE_L_L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_2026-10-15.md
server/services/phase_l_source_drift_contract.py
tests/unit/test_phase_l_a5_source_drift_contract.py
```
