# Post-v1.5 — v1.5.1 Real-Machine Acceptance Test Contract

Date: 2026-10-31 (Asia/Taipei)
Status: **OWNER_AUTHORIZED_TEST_PLANNING / EXECUTION_PENDING**

## 1. Purpose

This contract defines the bounded real-machine acceptance program used to decide
whether current post-v1.5 fixes are suitable for a `v1.5.1` patch release.

The program is named:

`RMA — v1.5.1 Real-Machine Acceptance & Patch Release Preflight`

RMA is post-v1.5 stabilization work. It does **not** start Phase M, P2–P5, or a
new capability-development phase. It validates the existing product through the
actual Windows / Native bundle / Local Service / MCP / official-source chain.

## 2. Release semantics

`VERSION` remains `1.5.0` during RMA. Passing RMA may justify selecting
`1.5.1`; it does not itself authorize a version bump, tag, push, GitHub release,
or mutation of the frozen `v1.5.0` release.

## 3. Baseline to preserve

At contract creation:

```text
branch       main
HEAD         b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c
origin/main  3f2e5b3a3588d3778d5a4b380c9d8e0a2f41ca05
ahead/behind 3 / 0
VERSION      1.5.0
working tree clean
```

Current local candidate commits are:

1. `b38fde12` — Launcher v2 UX and native-entry guard;
2. `8b482be4` — explicit verified TLS compatibility retry in Launcher;
3. `b84f9fc8` — Native packaging inclusion of Mode B2 execute-once wrapper.

These commits are candidate patch content, not release authorization.

Frozen `v1.5.0` remains commit `acaf726a...` / tree `d44f66dc...`.

## 4. Evidence and preservation rules

RMA evidence root should be `C:\twmarket_temp\v1.5.1-rma-20261031\` or a later
explicitly recorded successor root. Evidence is retained. No cleanup or deletion
is implied by test completion.

RMA must not delete historical evidence, caches, acceptance roots, local state,
old bundles, or recovery material. Any deletion requires a separate itemized
Owner authorization.

Each RMA group must record:

- exact source commit / candidate bytes;
- exact command or operator action;
- machine/runtime identity relevant to the result;
- stdout/stderr or UI evidence where applicable;
- Result/Audit/artifact identifiers where applicable;
- PASS / FAIL / BLOCKED / GOVERNED_REJECTION classification;
- linked defect ID for every unexpected failure.

## 5. Result classifications

`PASS` means the tested contract behaved as required.

`GOVERNED_REJECTION` means fail-closed behavior was expected and correct; it is
not a defect. Examples include unsupported capability, plan-only capability,
missing required source-date binding, invalid authorization, or unsupported
instrument scope.

`BLOCKED` means the test could not validly execute because a prerequisite or
external condition was unavailable; it is not automatically a product defect.

`FAIL` means observed behavior contradicts the current product contract or the
RMA acceptance criterion and requires defect adjudication.

## 6. RMA execution groups

### RMA-0 — Release / provenance baseline

Goal: freeze the exact candidate under test before any acceptance execution.

Required evidence:

- branch, HEAD, `origin/main`, ahead/behind, `VERSION`, Git status;
- Native package manifest, ZIP SHA-256 and packaged product metadata when built;
- runtime / installation / Security Master identifiers used by the test;
- rollback references and evidence-root path;
- proof that no unrelated source bytes changed during the RMA tranche.

Acceptance: provenance is complete, internally consistent, and reproducible enough
to identify the exact bytes under every later RMA result.

### RMA-1 — Fresh first-run installation

Goal: validate a real user starting from the built Native distribution rather than
the source tree.

Required scenarios: first-run GUI, `Set Up TW-Market`, offline bootstrap, exact
locked dependency closure, installation initialization, transition to Daily View,
repeated setup/idempotence, path-with-spaces and non-ASCII path handling, and a
clear fail-fast result when a source-template launcher is misused.

Acceptance: setup succeeds without hidden provider acquisition, Security Master is
not silently installed, and the normal user can reach a valid Daily View without
manual Python commands.

### RMA-2 — Launcher daily operation

Goal: validate truthful daily control behavior from the real Native launcher.

Required scenarios: Start, Stop, Refresh, Diagnose, Open Workbench, explicit
Restart after Security Master update, and state projection for `STOPPED`,
`STARTING`, `RUNNING_READY`, `RUNNING_UNHEALTHY`, `PORT_CONFLICT`,
`STALE_OWNERSHIP`, incomplete installation and status-error cases.

Acceptance: UI state/action availability matches canonical lifecycle truth and
never invents runtime, Workbench, Security Master or MCP authority.

### RMA-3 — Security Master lifecycle

Goal: validate first install, update, retry, activation, restart and recovery.

Required scenarios include `NOT_INITIALIZED -> Install`, strict verified TLS,
evidence-gated compatibility retry, successful `QUALIFIED -> ACTIVE`,
`restart_required`, stopped-runtime next-start behavior, update failure with
current release retained, history and bounded rollback in isolated state.

Acceptance: no silent TLS fallback, no certificate/hostname verification disable,
no `unsafe-explicit` Launcher path, and activation/restart semantics remain atomic
and fail-closed.

### RMA-4 — Local Service + MCP real integration

Goal: validate the actual product service and six-tool MCP surface, including the
real ChatGPT-connected deployment path on this machine.

Required scenarios: `/health`, MCP startup-check, stdio initialize, `tools/list`,
all six public tools, Request V1/V2/V3 compatibility, Capability Catalog access,
and a real Native bundle -> Local Service -> MCP client -> ChatGPT closed loop.

Host-specific Secure MCP Tunnel behavior is deployment evidence only; it must not
become a TW-Market product dependency or Launcher requirement.

### RMA-5 — Identity resolution matrix

Goal: prove identity behavior beyond one successful symbol.

Required cases must cover code, `MARKET:CODE`, ISIN, Chinese name, at least one
TPEx common share, at least one non-common-share instrument family, nonexistent
identity, and ambiguity where available.

Acceptance: canonical target, market, ISIN, instrument family/type and execution
eligibility are consistent with current Security Master and fail closed where
identity or eligibility is unsupported.

### RMA-6 — Capability execution matrix

Goal: validate executable and intentionally non-executable capability behavior.

For eligible targets, execute the current Catalog/Routing-supported families that
matter to daily research, including current observation, recent performance,
monthly revenue, material disclosures and accepted trading/status context. Test
conditional capabilities such as institutional-flow context only when their
required source-date/input binding is valid.

Each case follows: Validate -> Preview -> explicit authorization -> Execute Once
-> Evidence -> Result -> Audit. Correct plan-only or unsupported rejection is
recorded as `GOVERNED_REJECTION`, not FAIL.

### RMA-7 — Official-source / TLS matrix

Goal: determine whether each production source family works under the supported
Windows / Python runtime without weakening transport security.

At minimum classify TWSE MIS, TWSE OpenAPI/source families, TWSE historical data,
MOPS CSV/JSON/OpenAPI paths and TPEx official paths used by executable routes.
Record strict-TLS outcome, any governed compatibility-TLS outcome, certificate
validation, hostname verification, HTTP/source result, parser/schema result and
the capability affected.

Acceptance: executable public capability paths must have a governed usable route
or an explicitly adjudicated external-source condition; silent insecure fallback
is forbidden.

### RMA-8 — Result / Audit / evidence integrity

Goal: prove every successful execution is traceable from user-visible result back
to governed evidence.

Required checks: Control Package / authorization binding, execution receipt,
evidence artifact existence and hash, citation binding, Result V3 reference,
Audit Package reference, and lineage consistency. No chat response alone counts
as proof of a successful capability execution.

### RMA-9 — Failure and recovery matrix

Goal: deliberately exercise bounded failure modes without corrupting durable state.

Required scenarios should include stopped service, unavailable MCP, port conflict,
stale ownership, Security Master unavailable/corrupt state, invalid Request V3,
unsupported capability, tampered package, missing runtime component and official
source unavailability where safely reproducible.

Acceptance: failures are truthful, fail closed, use governed reason codes where
available, preserve state, and have a bounded recovery path. Diagnostics must not
misclassify governance rejection as product corruption.

### RMA-10 — Native package / portability

Goal: validate the distribution rather than the developer checkout.

Test at least two independently extracted Native bundles/locations, bootstrap and
run from each, and verify relocation, manifest/tamper enforcement, exact locked
wheel closure, Launcher, CLI, MCP, Security Master CLI and Mode B2 child wrapper.

Acceptance: package behavior is location-independent within supported Windows
constraints and no host/developer path becomes a hidden runtime dependency.

### RMA-11 — Operator experience acceptance

Goal: validate the product from a non-developer daily-user perspective.

The normal entry must be the built bundle root `Launch-TW-Market.cmd`. A normal
user should be able to complete setup, start/stop runtime, open Workbench, install
or update Security Master and diagnose problems without entering Python, venv,
PowerShell implementation paths, MCP adapter internals or source-tree commands.

Acceptance: the primary experience is understandable, truthful and recoverable;
technical details remain available without becoming the main workflow.

## 7. Release-blocking policy

A defect is a `v1.5.1` release blocker when it is reproducible on the supported
Windows/CPython runtime and materially breaks one of:

- installation / Native entry;
- runtime lifecycle or durable-state safety;
- Security Master installation/update integrity;
- six-tool MCP compatibility;
- a currently advertised executable public capability;
- Result/Audit/evidence traceability;
- package integrity / portability;
- transport security or fail-closed governance.

A correct governed rejection, documented unsupported scope, or external outage is
not automatically a release blocker. Classification must be evidence-based.

## 8. v1.5.1 release gate

A `v1.5.1` release candidate may be proposed only after:

1. RMA-0 through RMA-11 have a recorded disposition;
2. all release blockers are closed or explicitly rejected as not defects;
3. fresh Native install and daily Launcher acceptance pass;
4. Security Master lifecycle acceptance passes;
5. Local Service and six-tool MCP acceptance pass;
6. advertised executable capability paths pass their required matrix;
7. Result/Audit/evidence integrity passes;
8. Native portability/package integrity passes;
9. required current test/release governance gates pass for the final bytes;
10. final candidate has no unreviewed unrelated mutation.

Only after that gate may a separate Owner authorization select `VERSION=1.5.1`,
build the final candidate, tag/publish, or push release changes.

## 9. Authorization boundary

Creating this contract authorizes documentation and subsequent bounded RMA
planning only. Individual live-network executions, code fixes, commit/push/tag,
release publication, Phase M and P2–P5 remain separately governed.

`DELETE = NOT_AUTHORIZED` remains absolute for RMA evidence and repository files.
