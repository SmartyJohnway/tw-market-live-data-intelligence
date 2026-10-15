# Phase L L3-A2 — Official EOD Diagnostic Propagation & Batch Contract Guard

**Base:** `7568d2fd0a4b0b8b217449a6771e552a66b6cf0f`
**Branch:** `phase-l/l3-a2-eod-diagnostic-propagation`
**Authority:** frozen L0; Owner-accepted/merged L3-A0 (PR #355, closure PR #356); Owner-accepted/merged L3-A1 (PR #357, closure PR #358); explicit Owner authorization in the L3-A2 instruction.
**Scope:** A0 Gap G03 only. No source polling or fresh market acquisition.
**Technical disposition:** `L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** `L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_OWNER_ACCEPTED_FOR_MERGE`
**Owner acceptance authority:** explicitly granted in conversation on 2026-10-15 after independent exact-head review of `0b88a1ba0df300d598c2587c3e7a581b7eca5d7e`; merge authorized, L3-A3+ and L4-L7 remain unauthorized.

## Predecessor and G03 root cause

Current `origin/main` at entry was `7568d2fd0a4b0b8b217449a6771e552a66b6cf0f`, containing the A1 implementation and merge closure. The new A2 worktree started clean at that SHA.

L3-A0 records G03: `_live_eod()` extracted adapter observations and returned only target rows. It discarded the adapter's batch status, counts, reported trade dates, rejected rows, field validation, and caveats. `_execute_source_groups()` treated every non-raising callable as `success`; target normalization then allowed a surviving row to make the execution appear clean. The wrapper therefore lost source/batch truth between the official EOD adapter and the Unified Result.

## Propagation contract

`_live_eod()` now returns normalized target rows together with a private bounded diagnostic projection. `_execute_source_groups()` retains that projection in the existing `source_execution_summary.group_results` and routes target-bindable rejection/field-validation facts to the existing `target_results` and `issues` envelopes. No second Result/Audit system was introduced.

The bounded projection contains:

```text
source_id
endpoint_contract_id
source_status
batch_status
row_count_received / examined / retained / rejected
reported_trade_dates / reported_trade_date_count
rejection_reason_codes
rejected_rows: symbol, reason_code, invalid field names only
partial_observations: symbol, observation_status, invalid field/reason codes
caveat_count / bounded caveat codes
http_status
```

Rows, values, raw payloads, HTTP bodies, headers, URLs, cookies, and tokens are not copied into Unified diagnostics. Target attribution is made only when the adapter supplies a returned symbol that exactly matches one requested symbol in that source group. Unattributable rejected rows remain group-level diagnostics. Lists and strings have fixed bounds and deterministic ordering.

## Batch adjudication

| Adapter state | Unified group outcome | Unified result behavior |
|---|---|---|
| `source_status=success`, `successful_eod_batch` | `success` | Existing normalized success remains possible. |
| `partial_source_success` | `status=success`, `reason_code=partial_source_success` | Retained observations remain usable; result cannot be clean success. Rejection reasons survive. The pre-existing group status vocabulary remains `success|failed`. |
| `date_mismatch` | `status=failed`, `reason_code=date_mismatch` | Adapter rows are retained only in bounded diagnostics and are not normalized into target evidence; reported dates and issue survive. No date is selected or rewritten. |
| `source_error` / `schema_drift`, or non-success source status | `status=failed`, bounded reason code | Adapter rows are not normalized into target evidence. No observation can hide a source or contract failure. With no other retained evidence, execution is `source_execution_failed`. |
| `empty_non_trading_day` with successful source status | `status=success`, `reason_code=empty_non_trading_day` | No row is fabricated; it is not reclassified as transport/source failure. Target remains unavailable/no-evidence with the legitimate empty-day reason rather than `missing_fixture_or_source_result`. |
| Clean batch with invalid optional values in retained row | `status=success`, `reason_code=partial_source_success` | Only invalid field names and bounded reason codes propagate; no values are defaulted to zero. Final Unified result is not clean success. |
| Rejected requested row | source/batch outcome retained | Exact-symbol rejection reason is attached to that target; unknown-symbol rejection remains group-level. |

### TWSE / TPEx adapter invariant

Deterministic preflight confirmed TPEx could return zero observations, rejected rows, `source_status=success`, and `batch_status=successful_eod_batch` when all rows were rejected. A minimal one-line repair now sets TPEx `batch_status=source_error` when rejected rows exist and no observations remain, matching the existing TWSE batch classification while preserving `source_status=success` as transport/parser completion. No parser, field, or source contract redesign was made.

TWSE and TPEx parity is covered for clean success, partial result, empty batch, duplicate/rejected rows, date mismatch, source/contract failure, and all-rejected outcome. A mixed-market execution retains the valid target and reports the rejected TPEx target as partial coverage.

## Field validation, fallback, and currentness

The Unified EOD normalizers intentionally do not copy the complete adapter `field_validation` object. A bounded projection now preserves invalid field names, stable reason codes, symbol, and adapter observation status through `target_results`; corresponding partial diagnostics prevent clean execution status. Source numeric values are never projected or replaced with defaults.

Existing MIS-to-EOD fallback behavior is unchanged. If an EOD fallback observation is usable but its batch is partial or invalid, the target still records `fallback_used`, and the group/result retains the EOD diagnostics and partial/failure disposition. No retry, alternate endpoint, TWSE/TPEX switch, MIS refetch, or other fallback was added.

Currentness is not modified. `reported_trade_dates` from a mismatched batch are diagnostics, not an instruction to choose a preferred date. `empty_non_trading_day` and a clean batch with a missing requested symbol keep the existing no-evidence/currentness path.

## A1 and public-surface containment

The A1 MIS returned-identity validation, strict UTF-8 decoding, envelope validation, duplicate handling, and fallback rules are unchanged; its regression module passes. No Request/Result/Audit schema version, MCP/HTTP surface, Catalog, Route, Executor activation, authorization semantics, or evidence family changed. MCP remains exactly six tools. No raw adapter result was copied wholesale.

## Verification

The focused offline gate ran the new A2 tests plus TWSE/TPEx adapter and observation tests, controlled EOD execution/context tests, current Watchlist controlled executor tests, Phase C source activation/policy/preview and calendar integration tests, M8R production adapter tests, A1 MIS regressions, and exact-six MCP contracts:

```text
101 passed, 0 failed, 0 warnings
L3_A2_EXTERNAL_SOCKET_ATTEMPTS=0
```

The guarded pytest argument list was:

```text
tests/unit/test_l3_a2_eod_diagnostic_propagation.py
tests/unit/test_m8a_twse_official_eod_adapter.py
tests/unit/test_m8a_tpex_official_eod_adapter.py
tests/unit/test_m8a_controlled_official_eod_execution.py
tests/unit/test_m8a_official_eod_context_integration.py
tests/unit/test_m8a_official_eod_observation.py
tests/unit/test_m8a_official_eod_failure_contract.py
tests/unit/test_m8r_03d_watchlist_controlled_execution.py
tests/unit/test_m8r_03d_production_calendar_integration.py
tests/unit/test_m8r_phase_c_source_activation.py
tests/unit/test_m8r_03e_phase_c_activation_policy.py
tests/unit/test_m8r_phase_c_execution_preview.py
tests/unit/test_m8r_06_03_production_adapter.py
tests/unit/test_l3_a1_twse_mis_response_contract.py
tests/unit/test_m8r_08b_mcp_tool_contracts.py
```

The two Phase C calendar integration tests had stale injection under the unused `fetch_source_call_groups` key. They were updated to inject deterministic rows through the current `SOURCE_ADAPTERS` seam; the calendar behavior remains tested, while EOD/MIS source calls are entirely in-memory.

Validators:

```text
python -X utf8 -B scripts/validate_source_registry.py             PASS
python -X utf8 -B scripts/validate_portable_catalog_sync.py       PASS
python -X utf8 -B scripts/validate_runtime_skill_guide_sync.py    PASS; tool_count=6
python -X utf8 -B scripts/validate_v1_public_contracts.py         PASS; tool_count=6
git diff --check                                                  PASS
```

All source adapter inputs in the focused gate are fixture or injected results. The socket sentinel recorded zero external attempts and no fresh market/source GET/POST occurred. Execution artifacts and authorization claims used isolated pytest temporary roots; no Security Master, persistent Watchlist, production Result/Audit, or repo-local live state was created or changed.

## Independent reviewer verification

Independent exact-head review re-ran the complete 101-case guarded gate and independently enforced a socket sentinel. Result: **101 passed, 0 failed, 0 warnings**, with `L3_A2_REVIEW_EXTERNAL_SOCKET_ATTEMPTS=0`. Source registry, Portable Catalog, runtime/Skill exact-six, public-contract validation, and `git diff --check` also passed.

Two bounded semantic defects were found and repaired on the same candidate branch without broadening A2 scope. First, the candidate had expanded `source_execution_summary.group_results.status` from the historical `success|failed` vocabulary to `partial_source_success` and `empty_non_trading_day`. The reviewer repair preserves the existing status vocabulary and carries partial/legitimate-empty detail through the already-existing `reason_code` plus bounded `adapter_diagnostics.batch_status`; final overall adjudication still treats `partial_source_success` as non-clean. Second, a legitimate `empty_non_trading_day` target could still be labeled `reason_code=missing_fixture_or_source_result` even though the source had returned a valid empty batch. The repaired target remains unavailable/no-evidence but now carries `reason_code=empty_non_trading_day` and the EOD source family/diagnostics.

These repairs do not change Request/Result/Audit schema versions, MCP/HTTP surfaces, source acquisition behavior, fallback policy, adapter field parsing, capability scope, or evidence-family boundaries. Independent technical disposition remains `L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_ACCEPTANCE_REVIEW_PASS`; Owner acceptance is recorded under `L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_OWNER_ACCEPTED_FOR_MERGE`.

## Remaining boundary and stop

This candidate closes G03 only. G04 research CSV structure, G05 bounded probes for rate limiting/removal/publication/universe changes, and G06 H1 negative fixtures remain deferred. No live probe, retry redesign, global resource ceiling, general observability framework, public surface, or capability expansion is included. L3-A3+ and L4-L7 remain unauthorized.

Candidate disposition: `L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_ACCEPTANCE_REVIEW_PASS`. Owner acceptance is recorded under `L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_OWNER_ACCEPTED_FOR_MERGE`; merge is authorized. L3-A3+ and L4-L7 remain unauthorized; do not begin A3.
