# Phase L4-A2 — Filesystem / Path Containment Hardening

**Date:** 2026-10-17
**Authority:** `USER_CHAT_2026-10-17_PHASE_L_L4_A2_PATH_CONTAINMENT_HARDENING_AUTHORIZATION`
**Branch:** `phase-l/l4-a2-path-containment-hardening`
**Entry:** `2ef46379d6ca81ecff134192116cedfb5215dc8f` / tree `00d8571a5876ce77db19a48fc31a3b626e63858e`

## 1. Scope and base

L4-A1 was Owner-accepted and merged through PR #370 as merge commit
`2ef46379d6ca81ecff134192116cedfb5215dc8f`. A2 was performed from that exact
new main. This tranche addressed only A0 findings PATH-001, PATH-003, and
PATH-005. No provider acquisition, user-data migration, dependency operation,
load test, size/resource ceiling, authentication, or secret work was performed.

## 2. Root authority model

The product retains separate subsystem-owned roots for Watchlist authority,
Security Master authority, control/Result/Audit packages, runtime temporary
files, operational diagnostics, and backup/restore. No universal repository
root was introduced. An explicitly configured ordinary external Watchlist
root remains supported; selecting a root is an authority choice, while
containment validates the selected root and descendants.

## 3. Shared path-safety behavior

`scripts/m8r_filesystem_safety.py` now detects symbolic links and Windows
reparse points using non-following metadata, checks lexical component chains
before resolution, validates roots before and after directory creation, and
checks destination leaves and parents. Atomic write and exclusive-create paths
capture root/parent identities and revalidate around publication. Exclusive
creation retains `O_EXCL` no-replay behavior and cleans only the file identity
created by that invocation.

Persistent Watchlist initialization validates its selected root and SQLite
leaf before open and revalidates after connection. Mode B2/Mode C retain the
selected control root lexically until validation. Mode C control, F3, Result,
and Audit reads/writes use validated package-relative paths. 05C staged output
publication checks root/parent identity and destination safety. Lifecycle owner
files use the shared exclusive/atomic writers; operational event logging
rejects unsafe parents/leaves while retaining non-fatal logging behavior.

## 4. Findings

| Finding | A0 state | A2 technical result | Evidence |
| --- | --- | --- | --- |
| PATH-001 | PARTIAL / HARDENING_REQUIRED | COVERED | External-root, root-link/reparse, DB-leaf, and regular SQLite tests |
| PATH-003 | PARTIAL / HARDENING_REQUIRED | COVERED | Control/Mode C, output component, reparse, identity continuity, legacy containment tests |
| PATH-005 | PARTIAL / TEST_COVERAGE_GAP | COVERED | Operational event, lifecycle runtime/owner, and lexical CONTROL_ROOT tests |

The race checks reduce detectable path substitution windows. They do not prove
immunity to a same-privilege hostile process replacing filesystem objects in
the final OS-level race window; stronger handle-based primitives would be
needed for that guarantee.

## 5. Offline evidence

Acceptance run: `l4-a2-20261017T085705Z`. Its manifest binds the five evidence
records and the preflight result. The focused offline suite reported 281 passed,
4 platform-inapplicable POSIX-only cases skipped, and the two exact A0-governed
historical Mode-C tests deselected. The two tests remain disclosed historical
failures (`92 passed, 1 skipped, 2 failed` in the A0 attempt); they are not
represented as passing and were not repaired in this tranche. External socket
attempts: 0. Provider requests and destructive load tests: 0.

Validators passed: source registry, Portable Catalog sync, runtime/Skill
exact-six, V1 public contracts exact-six, Phase H V3, compileall, changed-file
py_compile, and `git diff --check`.

## 6. Compatibility and stop boundary

No public MCP tool, Request/Result/Audit schema, Catalog, Route, capability,
source registry, provider route, Security Master authority, financial
statements support, or trading/order boundary changed. A2 did not add size
limits, quotas, authentication, ACL redesign, secrets, dependencies, or load
controls.

L4-A2 technical disposition is `L4_A2_PATH_CONTAINMENT_HARDENING_PASS`.
Owner acceptance is pending. L4-A3+ and L5-L7 remain unauthorized; no A3 work
was started.
