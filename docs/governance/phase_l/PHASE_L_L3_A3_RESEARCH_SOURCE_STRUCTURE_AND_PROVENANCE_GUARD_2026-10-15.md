# Phase L L3-A3 — Phase G Research CSV Structure and Provenance Guard

**Date:** 2026-10-15
**Base:** `origin/main@0bb540f6e1719e07d5a68699fe0f155d89e80e30`
**Branch:** `phase-l/l3-a3-research-source-contract-guard`
**Scope:** L3-A0 Gap G04 only
**Disposition:** `L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** NOT RECORDED

## Authority and predecessor state

This candidate uses the frozen L0 source-drift obligation and the merged L3-A0
inventory as authority. L3-A1 (PR #357) and L3-A2 (PR #359) are Owner-accepted
and merged at the base ancestry. Current product scope remains limited to the
already active Phase G research routes:

| Route | Contract | Capability | Market |
|---|---|---|---|
| P04 | `t187ap04_L` | `material_disclosures` | TWSE |
| P05 | `t187ap04_O` | `material_disclosures` | TPEX |
| P06 | `t187ap05_L` | `monthly_revenue` | TWSE |
| P07 | `t187ap05_O` | `monthly_revenue` | TPEX |

## G04 root cause and repair

The accepted A0 G04 finding was reproduced with `a,b\n1,2,3\n`: the former
`csv.DictReader` path produced `{"a": "1", "b": "2"}` and silently discarded
the surplus cell held under the `None` key. The shared Phase G parser now uses
`csv.reader(..., strict=True)`, validates a non-empty normalized header with
unique non-empty field names, and requires every data row to have exactly the
header width before constructing row dictionaries. Structural failures raise
bounded `SourceFailure` codes; no evidence row is emitted from malformed CSV.

The parser continues to allow new named columns when the header and every row
are structurally consistent. Existing source-specific required aliases remain
the responsibility of `normalize_source_rows`; unaccepted field renames still
fail as `source_contract_required_field_missing`. Empty-but-present cells stay
empty strings and are distinct from absent cells. In particular, monthly
revenue nullable percentages and notes remain valid when their columns exist.
Material-disclosure subject and description remain allowed to be empty.

CSV decoding is strict UTF-8 / UTF-8-SIG. Invalid bytes yield
`csv_decode_failed`. Valid quoted commas and multiline fields retain standard
Python CSV semantics. No Big5/CP950 guessing or replacement decoding was added.

## Failure provenance and fallback

`fetch_once()` retains the existing single-fallback order:

```text
official_csv → on failure, official_json_openapi → stop
```

The primary attempt now records `SourceFailure.code` (for example,
`csv_row_width_mismatch`) instead of collapsing the failure to
`SourceFailure`. Non-`SourceFailure` errors are represented by their stable
exception class name only. Exception messages, traceback, URL/query, headers,
and response bytes are not included. The existing `attempt_failures` shape and
both Phase G evidence schemas are unchanged.

If CSV structure fails and governed JSON is valid, JSON evidence succeeds with
`transport=official_json_openapi`, `fallback_used=true`,
`fallback_attempted=true`, and the CSV structural code preserved. If both
transports fail, the result remains `source_failed`, `fallback_used=false`,
`fallback_attempted=true`, with deterministic CSV then JSON failure entries.
Healthy CSV remains primary and does not invoke JSON fallback.

## Transport envelope boundary

No transport stack or response-envelope type was introduced. Production still
uses the existing `urllib.request` seam and body-byte fetcher. Its existing HTTP
exception behavior prevents a non-success HTTP response from being parsed;
this tranche adds no retry or HTTP policy. Current authority does not define a
content-type allowlist or redirect/effective-URL acceptance rule, so those facts
are neither newly captured nor enforced. No MIME, redirect, or route policy was
guessed. This is a documented future contract gap, not a runtime failure in the
bounded CSV repair.

## Coverage and preserved semantics

Deterministic fixtures cover all four P04-P07 capability/market combinations:

- healthy CSV with an additive named column;
- surplus and short rows, with successful governed JSON fallback;
- fallback failure with bounded ordered reasons;
- existing TWSE/TPEX mappings and target binding.

Additional cases cover blank/duplicate normalized headers, strict quoting,
quoted comma/multiline fields, UTF-8-SIG and invalid UTF-8, empty cells,
nullable revenue values, empty disclosure text, and no raw error text leakage.
Current source-specific normalization remains responsible for reporting date,
period identity, required aliases, exact company-code binding, duplicate
conflict, publication time, monetary and percentage semantics. Existing
missing/no-evidence, not-yet-available, source-failed, binding-failed, and
snapshot date/period distinctions remain unchanged. Transport fields do not
enter normalized semantic record hashes.

Production adapter tests pass injected CSV/JSON bytes through
`phase_g_official_research_executor` and `m8r_06_03_production_adapter`, verify
fallback provenance in persisted operation evidence, and validate against the
existing schemas. Test writes use isolated `tmp_path` roots.

## Verification

Guarded offline regression command selected:

```text
tests/unit/test_l3_a3_research_source_contract_guard.py
tests/unit/test_phase_g_material_disclosures.py
tests/unit/test_phase_g_monthly_revenue.py
tests/unit/test_phase_g_runtime_activation.py
tests/unit/test_phase_g_routing_and_planner.py
tests/unit/test_phase_g_result_v2_projection.py
tests/unit/test_m8r_06_03_production_adapter.py
tests/unit/test_l3_a1_twse_mis_response_contract.py
tests/unit/test_l3_a2_eod_diagnostic_propagation.py
tests/unit/test_m8r_08b_mcp_tool_contracts.py
```

The gate patched `socket.connect`, `socket.create_connection`, and the
production adapter's `urlopen`; loopback required for asyncio was permitted.
The two A2 mixed-market tests that omit one market's adapter fixture were run
with explicit empty offline responses for the unprovided route. Result:
**176 passed, 0 failed, 0 warnings; external network attempts = 0**.

Validators required by the tranche:

- `python -X utf8 -B scripts/validate_source_registry.py` — PASS (`errors=[]`).
- `python -X utf8 -B scripts/validate_portable_catalog_sync.py` — PASS (deep equality).
- `python -X utf8 -B scripts/validate_runtime_skill_guide_sync.py` — PASS (`tool_count=6`).
- `python -X utf8 -B scripts/validate_v1_public_contracts.py` — PASS (`tool_count=6`).
- `python -X utf8 -B -m py_compile scripts/phase_g/research_executor.py` — PASS.

No fresh source GET/POST was performed. No production Security Master,
Watchlist, authorization, Result/Audit, live evidence root, or primary-worktree
`data/` state was read or mutated. `git diff --check` — PASS after final candidate edits.

## Public and frozen-surface containment

No schema, request/result, Audit, Catalog, Route, Executor registration,
authorization, MCP, or HTTP contract changed. MCP remains exactly six tools.
No evidence family, source, route, capability, encoding fallback, retry, or
transport stack was added. The production code change is limited to the Phase G
research CSV parsing and attempt-failure projection.

## Deferred boundaries

G05 rate limiting, Retry-After, source removal/deprecation, publication-delay
probes and universe-collapse probes remain deferred. G06 H1 negative-fixture
coverage remains separate. Content-type and redirect/effective-endpoint policy
remain unenforced absent current accepted authority. No live MOPS probe was
performed. A4+ and L4-L7 remain unauthorized.

## Stop boundary

This candidate closes only the L3-A0 G04 structural CSV and bounded failure
provenance gap. It does not authorize A4, G05/G06, live probes, or later Phase L
work. Owner acceptance remains NOT RECORDED.
