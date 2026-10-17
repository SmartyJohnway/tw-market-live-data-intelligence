# Phase L4-A5 — Dependency & Supply-Chain Hardening

## 1. Authority and base

Authority: `USER_CHAT_2026-10-17_PHASE_L_L4_A5_DEPENDENCY_SUPPLY_CHAIN_HARDENING_AUTHORIZATION`.

This offline-only tranche starts from the A4 Owner-accepted merge on
`origin/main` (`a2dfd7ff7c062257a7c7c8f193fced4f9c707a29`). It addresses only
the A0 findings DEP-001 and DEP-002. No provider, package-index, or external
network request was made; no package was installed or downloaded.

## 2. Dependency authorities

The repository contract is:

- `requirements.txt` is the human-maintained direct compatibility policy.
- `requirements-lock.txt` is the supported deterministic CORE installation
  graph for this release line.
- `requirements-browser-e2e.txt` is the browser acceptance extra layered on
  the core lock.

`requirements-browser-e2e.txt` now includes `requirements-lock.txt`, while the
Playwright pin remains `1.55.0`. Direct requirements remain ranges except the
already exact `mcp==1.29.0`; no package version changed. The lock remains the
existing exact graph generated in disposable CPython 3.11.15 on Windows 11
x86_64 with pip 26.2.1. Its package lines were not regenerated or edited.

The new `scripts/verify_dependency_supply_chain.py` parses requirements using
PEP 508/packaging semantics and checks direct-policy coverage, exact lock pins,
specifier compatibility, duplicates, markers, MCP/Playwright pins, browser
inheritance, and forbidden URL/VCS/editable/index directives. It is offline and
read-only.

## 3. Current install guidance

Current supported core installation guidance uses:

```text
python -m pip install -r requirements-lock.txt
```

Browser acceptance uses `requirements-browser-e2e.txt`. The Operator Workbench
remediation now points to the lock and reports the current Unified MCP
entrypoint. It does not install packages automatically. Its Python support
check uses the existing environment-verifier set: CPython 3.11 and 3.13.

The install-guidance evidence classifies current quick-start/troubleshooting and
onboarding docs separately from retained M5/M6 runbooks, release records, and
the explicitly superseded Operator Guide. Historical commands are left intact.

## 4. Active executable and subprocess boundary

The active inventory covers Mode B2, lifecycle, Operator Workbench, Unified
MCP, Unified Workbench, and the environment verifier. Internal child processes
use `sys.executable` with fixed repository-owned scripts/modules, fixed
argument arrays, and bounded timeouts/deadlines. Mode B2 continues to reject
caller-provided executable/script/module/shell/command fields. Lifecycle
host/port data can only enter the governed argument positions.

The Operator Workbench's external `git` calls are OS/operator-provisioned
executables. The helper now permits only `git branch --show-current` and
`git rev-parse --short HEAD`, with no shell and a finite timeout. The product
does not authenticate the Git or Python binary itself. No `shell=True`,
caller-selectable executable, generic user-selected plugin loader, runtime
package installation, or package download was found in the active inventory.

## 5. Validation and local environment

The offline supply-chain validator passed: 11 direct requirements, 49 lock
entries, and one browser extra. The environment verifier passed on CPython
3.13.7 / Windows 10 build 19045. Local installed versions differ from parts of
the lock; this was recorded and the environment was not changed. `pip check`
reported no broken installed requirements. These local checks do not replace
the repository manifest contract.

Focused A5 and affected lifecycle, Mode B2, execute-once, MCP, Workbench API,
and A4 boundary regressions passed under an external-network socket sentinel.
One existing Workbench API test skipped because its governed local candidate is
Git-ignored; it is not represented as passing. External socket attempts were
zero.

## 6. Explicit supply-chain residuals

- `PACKAGE_ARTIFACT_CRYPTOGRAPHIC_PROVENANCE = NOT_CLAIMED_IN_L4_A5`: the
  repository pins versions but does not bind downloaded wheel/sdist hashes or
  signatures. Destination: L7 release/reproducibility decision.
- `ONLINE_VULNERABILITY_CURRENTNESS = NOT_EVALUATED_IN_L4_A5`: no online
  vulnerability database or service was queried. Package safety is not
  inferred from tests.
- `HOST_EXECUTABLE_BINARY_AUTHENTICITY = OUTSIDE_REPOSITORY_LEVEL_A5_GUARANTEE`:
  fixed executable selection is covered; OS-provided Python/Git binary
  signatures are not.
- No Docker/base-image authority currently exists; container supply-chain
  policy remains for L6/L7 if such packaging is introduced.

## 7. Bounded dependency update policy

Changes to direct compatibility policy require explicit review. The lock is
regenerated only in a clean disposable environment; direct-policy and lock
changes are reviewed together, and transitive changes occur only through
explicit lock regeneration. The exact MCP pin remains until separately
validated. Playwright changes require browser acceptance evidence. Runtime
automatic dependency updates are prohibited. No schedule or updater is created
by this tranche.

## 8. Public boundary and disposition

The six MCP tools, request/result/audit schemas, Catalog, Route, capability
set, Security Master authority, provider routes, unsupported
`financial_statements` status, and no-trading boundary remain unchanged.

Final finding adjudication: `DEP-001 = COVERED` for repository manifest and
install-authority determinism; `DEP-002 = COVERED` for the inventoried active
executable boundary. These findings do not cover package artifact authenticity,
online vulnerability freshness, or host binary attestation.

Disposition: `L4_A5_DEPENDENCY_SUPPLY_CHAIN_HARDENING_PASS`.
L4-A5 Owner acceptance is pending. L4-A6+ and L5-L7 remain unauthorized.
