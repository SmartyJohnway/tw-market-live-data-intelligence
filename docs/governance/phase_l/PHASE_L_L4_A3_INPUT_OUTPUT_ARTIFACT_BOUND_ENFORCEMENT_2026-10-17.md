# Phase L4-A3 — Input, Output, and Artifact Bound Enforcement

Date: 2026-10-17
Authority: `USER_CHAT_2026-10-17_PHASE_L_L4_A3_INPUT_OUTPUT_ARTIFACT_BOUND_ENFORCEMENT_AUTHORIZATION`
Base: `6f896c124918c9b340358f7010f4c3403e862335` (`c9131977fbcbea32873617bd7d8db9572cc101bb`)

## 1. Scope and authority

L4-A2 was Owner-accepted and merged through PR #371 at the base above. A3 uses
only the nine A0 findings assigned to A3: IN-001, IN-003, IN-004, IN-005,
OUT-001, OUT-002, OUT-003, LOAD-002, and LOAD-003. It does not reopen A1/A2
findings or start A4-A7.

## 2. Input and transport bounds

The existing 1 MiB Unified request authority is now centralized and applied
before full HTTP body materialization. A trustworthy oversized Content-Length
is rejected before reading; requests without that header are consumed
incrementally and rejected at the first over-bound chunk. All six governed
Unified POST routes use the shared reader.

MCP continues to use `mcp==1.29.0`, `Server`, and the SDK `stdio_server`.
`BoundedStdin` reads binary input in bounded chunks and rejects an oversized
raw line before yielding it to SDK JSON parsing. The first frame is checked
before the Local Service startup contract request. No SDK fork or stdout line
backstop was added; producer-side output bounds are primary.

The Local Service client continues to enforce its existing 1 MiB request and
8 MiB response values. Server JSON responses are serialized once and emitted
from the bounded bytes; an oversized response returns the stable
`response_too_large` error with HTTP 500.

## 3. Public projection and handoff

Mode-C Result JSON, Audit JSON, and AI-ready Markdown are measured together
against the existing 8 MiB public envelope before any output is materialized.
Persisted Mode-C outputs are bounded before parsing/public return. Rejection
does not publish a partial output set. The existing 50 MiB M8R-05C per-file
staging sanity check remains an internal staging guard and is not treated as a
public transport ceiling.

The final serialized Mode-C AI handoff is bounded, including the structured
result and Markdown. MCP `CallToolResult` accounts for UTF-8 text plus
serialized `structuredContent`; an oversized result is replaced with the
bounded `mcp_result_too_large` error.

## 4. Existing parameter and mutation bounds

A3 introduces no new numeric business or resource ceiling. Existing authorities
remain in force: Catalog default/hard targets 10/50 and hard operations 100;
recent-performance lookback 1..20 trading days; execution maximum records
1..500 and timeout 1..60 seconds; existing source/schema row bounds; and
Persistent Watchlist bounds (32 watchlists, 500 entries per list, 20 tags,
64-character tags, 4096-character notes, 120-character names, 1 MiB import,
JSON depth 20).

IN-003 is split by dimension. Watchlist input/mutation/import bounds are
`COVERED`. Cumulative SQLite and revision-history growth is a resource/retention
residual deferred to L4-A6. A3 does not truncate revision history or change
preview cleanup. No user data was migrated or production Watchlist state
initialized.

## 5. A0 finding reconciliation

| Finding | A3 disposition | Remaining boundary |
| --- | --- | --- |
| IN-001 | COVERED | None within bounded HTTP ingress |
| IN-003 input/mutation | COVERED | Cumulative storage deferred to L4-A6 |
| IN-004 | COVERED | Raw MCP frames bounded before SDK parsing |
| IN-005 | COVERED | Existing Catalog/schema/source bounds consolidated |
| OUT-001 | COVERED | No SDK stdout backstop claimed |
| OUT-002 | COVERED | Peak memory and load behavior deferred to L4-A6 |
| OUT-003 | COVERED | Peak memory/performance deferred to L4-A6 |
| LOAD-002 serialized dimension | COVERED | Memory, disk pressure, and performance deferred to L4-A6 |
| LOAD-003 serialized dimension | COVERED | Long-handoff capacity/performance deferred to L4-A6 |

These results establish serialized-payload bounds only. They do not establish
peak-memory behavior, performance under large workloads, disk-exhaustion
behavior, or concurrent-call stability; those remain explicit L4-A6 work.

## 6. Test and validator evidence

Run `l4-a3-20261017T102100Z` records 218 passed, 1 skipped, 2 governed A0
historical Mode-C semantic-tamper tests deselected, and 0 failures. The skip is
the existing integration case requiring a Git-ignored local candidate. The two
deselected tests are not represented as passing. The previously disclosed A1
MCP safe-surface exploratory `mcp_adapter_internal_error` remains outside this
bounded gate and is not represented as passing or repaired.

The MCP integration tests ran under the repository's external-network socket
guard; no external socket attempt or provider request occurred. Validators
passed: source registry, Portable Catalog sync, runtime/Skill exact-six, V1
public contracts exact-six, Phase H V3, compileall, changed-file py_compile,
and `git diff --check`. Evidence and hashes are in
`docs/governance/phase_l/acceptance_runs/l4-a3-20261017T102100Z/manifest.json`.

## 7. Compatibility and stop boundary

No Request/Result/Audit schema, Catalog, Route, capability, source registry,
provider route, Security Master authority, six-tool MCP topology,
`financial_statements` support, or trading/order boundary changed. No
authentication, secret handling, dependency work, disk quota, memory governor,
concurrency architecture, or provider acquisition was introduced.

Disposition: `L4_A3_INPUT_OUTPUT_ARTIFACT_BOUND_ENFORCEMENT_PASS`. This is a
technical result only; Owner acceptance is pending. L4-A4+ and L5-L7 remain
unauthorized.
