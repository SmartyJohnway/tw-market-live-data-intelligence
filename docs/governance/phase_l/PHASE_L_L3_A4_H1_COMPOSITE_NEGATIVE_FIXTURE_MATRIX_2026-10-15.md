# Phase L L3-A4 — H1 Composite Deterministic Negative-Fixture Matrix

**Date:** 2026-10-15
**Base:** `origin/main@cbde2fb1bf5010d3aec417251cbd3077fecbfc2a`
**Branch:** `phase-l/l3-a4-h1-composite-negative-fixtures`
**Scope:** L3-A0 G06 fixture coverage only
**Disposition:** `L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `NOT RECORDED`

## Authority and entry

The current-main entry gate confirmed PR #361 (L3-A3 implementation/Owner
acceptance) and PR #362 (merge-closure reconciliation). L0 is frozen, L1/L2
are closed, and A0-A3 are Owner-accepted and merged. The A4 worktree began
clean at the base above. The primary worktree's existing untracked `data/`
directory was not read, staged, modified, or cleaned.

The governing classification is A0 G06 `FIXTURE_COVERAGE_GAP`, not a known
production defect. A4 exercised the current production core
`server/services/phase_h_h1_tpex_composite.py`, especially
`execute_composite_operation`, `_decode_payload`, and `_validate_source_rows`,
plus the fixed production adapter route
`phase_h_h1_tpex_composite_executor`. Historical J-B03 Stage B R1 is used only
for its exception boundary: expected transport and enumerated source errors
stay component-local; unexpected programming, invariant, and assembled
composite failures propagate to operation/dispatch handling.

No production runtime file changed.

## Fixed H1 source set

| Source | Contract | Current behavior exercised |
|---|---|---|
| P08 `H1-TPEX-ATTENTION-OPENAPI` | `tpex_trading_warning_information` | Exact-target attention row; exact duplicate ambiguity; wrong-target no-match |
| P09 `H1-TPEX-DISPOSITION-OPENAPI` | `tpex_disposal_information` | One or multiple retained target rows; wrong-target no-match |
| P10 `H1-TPEX-CHANGED-TRADING-OPENAPI` | `tpex_cmode` | Native unresolved observation; duplicate ambiguity; wrong-target no-match |

Capability remains `trading_status_context`, market TPEX, on the existing
composite executor. The accepted P10 field spelling `" FinancialAnnouncements"`
(including its leading space) is preserved. No source, route, family,
capability, or H1 coverage was added.

## Healthy baseline

Retained P08/P09 rows from
`tests/fixtures/phase_h_h1_adapters/source_rows.json` and the accepted
source-shaped P10 row were returned through the current direct composite
injection seam using fixed `retrieved_at`, status 200, JSON MIME, exact endpoint,
and zero redirects. The production adapter integration used a monkeypatched
`official_get`; no HTTP client was invoked.

The operation returned `succeeded` with one `trading_status_context_composite.v1`
primary artifact, three component evidence artifacts, and three
`phase_h_source_attempt_governance.v1` sidecars, in the existing fixed source
order.

## Source-local negative matrix

All expected source-local cases retain an unavailable/failed component with a
bounded failure code, component source identity and citation. Other healthy
components remain materialized. Sidecar `outcome`, `coverage_result`, and
`failure_code` agree with the component and the optional response log. No
exception message or raw response body is recorded.

| Failure class | P08 | P09 | P10 | Expected layer / code |
|---|---:|---:|---:|---|
| Healthy | yes | yes | yes | successful composite operation, partial H1 coverage |
| Timeout | yes | yes | yes | source-local `source_failed:transport_failure` |
| `URLError` / `ConnectionError` | representative | representative | — | source-local `source_failed:transport_failure` |
| Generic HTTP 503 | representative | — | — | `source_failed:http_or_content_type` |
| Wrong MIME | representative | — | — | `source_failed:http_or_content_type` |
| Invalid UTF-8 / malformed JSON | representative | — | — | `source_failed:strict_json_decode` |
| Invalid JSON root / non-object row | representative | — | — | `source_failed:invalid_top_level_rows` |
| Missing required field | yes | yes | yes | bounded `source_failed:missing_required_field:<field>` |
| Required-field type drift | yes | yes | yes | bounded `source_failed:invalid_required_field_type:<field>` |
| Date contract drift | yes | yes | yes | bounded `source_failed:date_contract_drift:...` |
| Exact-target ambiguity | duplicate rejected | multiple target rows retained | duplicate rejected | source-local typed binding failure; no first/last selection |
| Redirect/effective endpoint mismatch | representative | — | — | `source_failed:redirect_or_effective_url_mismatch` |
| Patched response ceiling exceeded | representative | — | — | `source_failed:response_ceiling_exceeded` |

The exact-target duplicate code remains `binding_failed:ambiguous_exact_target_rows`;
the composite's established failure artifact is `source_failed` with that typed
code preserved. P09 multiplicity is valid: two exact-code disposition records
survive as two items. Wrong-target rows preserve source-specific no-match
semantics and do not bind another target. Empty `[]` was directly checked
against current normalizers: it remains a non-failure partial component with
retrieval and contract validation true and no fabricated item. It is not
promoted to complete coverage.

One expected source-local timeout yields a composite with failed component,
healthy peer components, and `aggregate_coverage.declared_scope_complete=false`.
When all three expected transport attempts fail, every component and the
aggregate composite status are `source_failed`; the enclosing operation returns
`succeeded` because it successfully materializes a truthful source-failure
composite artifact. It does not claim available or complete evidence. This
matches the current composite contract and R1's component-local failure model.

## Programming and invariant failure boundary

| Injected condition | Result |
|---|---|
| `raw_bytes` is not bytes | `TypeError(phase_h_composite_response_bytes_invariant_invalid)` propagates |
| Provider `AssertionError` | propagates; not converted to source component failure |
| Provider / normalizer `TypeError` | propagates |
| Unenumerated `H1NormalizationError` code | `_expected_normalization_failure_code` re-raises |
| Composite validation invariant exception | propagates after component validation; no successful composite result returned |

The production adapter entry was also exercised with the current selected
executor and an in-memory replacement for `official_get`. A provider
`AssertionError` propagated through that adapter boundary. The R1 behavior is
unchanged; no broad exception catch was introduced.

## Artifacts, response log, and leakage

Tests inspect persisted component, primary, and sidecar artifacts under isolated
`tmp_path` roots. Source-local failures retain their source contract, target,
citation, bounded caveat, and sidecar failure code. Response log entries retain
source ID, outcome, failure code, deterministic request ordinal, bounded
response size/hash, and the existing attempt metadata; they do not contain
`raw_bytes` or a payload object. Persisted artifacts do not contain the exact
raw response-body bytes, raw payload/sample fields, provider exception details,
or stack traces. Existing source-native normalized provenance remains governed
by its current H1 evidence contract.

## Verification

Direct A4 matrix:

```text
python -X utf8 -B -m pytest -q tests/unit/test_l3_a4_h1_composite_negative_fixture_matrix.py
42 passed, 0 failed, 0 warnings
```

Guarded integrated regression command covered A4, current H1 composition and
normalizers, Phase J A2.5/A2.6 accepted fixtures, production adapter, H1
activation, and bounded A1/A2/A3 regressions:

```text
199 passed, 0 failed, 1 deselected, 0 warnings
L3_A4_EXTERNAL_NETWORK_ATTEMPTS=0
```

The deselected existing A2 test is
`test_partial_batch_retains_observation_and_diagnostics_without_clean_success`.
It omits an offline TPEX adapter result and would fall through to the production
source adapter. During an initial guarded discovery run, the urllib sentinel
intercepted its attempted TPEx `urlopen` before any socket connection. To keep
the acceptance gate at zero source acquisition, only that test was excluded;
no A2 test/runtime source was edited. All other tests in the selected A2 module
ran, as did the explicit A2 sentinel in the final gate.

Validators:

```text
python -X utf8 -B scripts/validate_phase_h_v3_contracts.py          PASS
python -X utf8 -B scripts/validate_source_registry.py                PASS
python -X utf8 -B scripts/validate_portable_catalog_sync.py           PASS
python -X utf8 -B scripts/validate_runtime_skill_guide_sync.py       PASS; tool_count=6
python -X utf8 -B scripts/validate_v1_public_contracts.py            PASS; tool_count=6
python -X utf8 -B -m py_compile server/services/phase_h_h1_tpex_composite.py tests/unit/test_l3_a4_h1_composite_negative_fixture_matrix.py PASS
git diff --check                                                    PASS
```

The final guarded gate patched `socket.connect`, `socket.connect_ex`,
`socket.create_connection`, and `urllib.request.urlopen`; attempts were zero.
No fresh source GET/POST, live TPEX endpoint access, or production-state
mutation occurred. All fixture execution artifacts were written under isolated
pytest temporary roots; no production-state root was used.

## Independent exact-head review

Independent review began from PR #363 candidate head
`849807d171825bab09aa8ce186ef9f4c1424568d`. No production-runtime correctness
defect was found. The reviewer independently re-ran the focused matrix at
**42 passed** and the selected integrated gate at **199 passed, 1 deselected**.
A reviewer-level global socket/`urlopen` sentinel measured
`L3_A4_REVIEW_EXTERNAL_NETWORK_ATTEMPTS=0`. Phase H contracts, source registry,
Portable Catalog sync, runtime/Skill exact-six, V1 public contracts, Python
compile, and `git diff --check` all passed.

Review found one bounded fixture/governance mismatch: the governance matrix
claimed direct `missing required field` coverage for P08/P09/P10, while the
candidate A4 file directly exercised that failure class only for P08; the P09
and P10 entries in the mixed test exercised type and date drift instead. The
reviewer repaired the test-only matrix by parameterizing a contract-critical
missing-field mutation for each of P08 (`SecuritiesCompanyCode`), P09
(`DispositionPeriod`), and P10 (`AlteredTrading`). Existing separate three-source
type-drift and date-drift tests remain unchanged, so coverage was reconciled
without adding production code or changing test count. Focused and integrated
gates remained 42 and 199/1-deselected respectively after the repair.

The independent disposition remains
`L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_ACCEPTANCE_REVIEW_PASS`. Owner
acceptance is still `NOT RECORDED`; G05, A5+, and L4-L7 remain unauthorized.

## Boundaries and disposition

G05 remains deferred: throttling/429, Retry-After, 404/410, source removal or
deprecation, publication delay, universe change, and bounded live probes. No
provider freshness is inferred from these offline fixtures. L3-A5+, G05, and
L4-L7 remain unauthorized. No public schema, MCP/HTTP surface, Catalog, Route,
Executor activation, authorization semantics, or evidence family changed; MCP
remains exactly six tools.

Candidate technical disposition: `L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_ACCEPTANCE_REVIEW_PASS`.
Owner acceptance is `NOT RECORDED`. Stop after the A4 PR is opened; do not
merge, probe live sources, start A5/G05, or begin L4.
