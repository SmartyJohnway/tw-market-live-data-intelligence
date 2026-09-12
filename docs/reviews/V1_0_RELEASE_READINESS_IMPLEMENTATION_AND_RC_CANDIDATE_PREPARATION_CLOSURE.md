# V1.0 Release Readiness Implementation and RC Candidate Preparation — Closure

## Decision

The exact validated code subject is `1d815e2407f6a9d24974b215f8df4e60574e346e` (tree `c31c2bceaf3260a10e2c82199fb90b42bad2faa1`). It was pushed before validation and validated from a true external `git clone --no-local`.

`ce8fa7cc06509dbea3935a5c4f3e1fb5ccbc933f` / `2f460d70b78749be12c8c16891887128a805d4bc` is superseded by this PR #222 correction. `29812e824ddbd24009a46a210d5207fe9fc9ad4a` is also superseded because its first corrected gate exposed two active README-assertion failures.

The principal decision is `V1_0_RELEASE_READINESS_COMPLETE_READY_FOR_RC1_POST_MERGE_VALIDATION`. This finalization is evidence-only: no runtime, test, profile, or product-contract code changes follow the validated code commit.

## Candidate and release state

- Repository candidate version: `1.0.0-rc.1`.
- Latest published GitHub Release: `v0.1.0`.
- RC tag and GitHub prerelease: not created. Final v1 tag/release: not created.
- Phase F is closed; Phase G is not started.

## Corrected current-product and historical boundaries

- Persistent Watchlists are supported installation-local state and mutate only by explicit preview/commit. There is no automatic polling, scheduler, startup fetch, Watchlist-driven automatic execution, trading, or realtime guarantee.
- The M8-through-M8C description is explicitly historical pre-Phase-F architecture, not competing current V1 authority.
- `test_m8r_05c_lineage.py` no longer receives a module-wide historical mark. Only the exact preflight historical node is classified by `tests/conftest.py`; its six previously-green tamper regressions remain active.
- The historical M4 readiness ledger was restored exactly to the baseline, not resealed. `run_m4_readiness_check.py --check-only` is an explicit historical exclusion; current-safe `run_m4_local_validation.py --check-only` remains active.

## Exact-code clean-clone validation

The external report `D:\Codex-Workspace\runtime\tw-market-live-data-intelligence\v1-rc-correction-final-gate-1d815e2-r2\v1_release_readiness.json` has SHA-256 `f9a1fa081658c1bd1fae98c0deaaf56e2c8e21deef2d5070af1606e98a02afa0`. The working tree was clean before and after the gate. The fresh clone installed `requirements-lock.txt`, passed `pip check`, and used CPython 3.13.7 on Windows 10.

- Default CI: `949 passed, 0 failed, 4 skipped`.
- Full non-network profile: `2409 passed, 0 failed, 16 skipped`.
- Environment, dependency check, version consistency, public contracts, release hygiene, portable catalog, runtime/Skill/Guide drift, both Skill validators, compileall, operator preflight, actual Playwright browser E2E, release manifest, JavaScript syntax, and source archive all passed.
- The source archive had no `.git`; its environment, version, Local Service import, and MCP startup smoke all passed.

## Historical reconciliation

All original 69 preflight failure nodes are machine-readably reconciled in the companion JSON: 10 stale current expectation/error-code nodes were updated to current authority; 3 loopback harness nodes were repaired/isolated and remain active; 55 D/E/G nodes remain exact historical/legacy/duplicate dispositions. The historical scope audit found 55 expected and 55 actual nodes, with no additional or missing historical node.

The original default-CI baseline (`929 passed, 10 failed, 2 skipped`) is separately reconciled with all ten exact node IDs. Nine are preserved Mode-C lineage provenance debt and the one loopback harness node is active and passes. Current default CI has zero failures.

## Installation and browser acceptance

The isolated installation journey passed fresh installation, schema-1 existing-install reopen without history loss, and v0.1 legacy import through preview/commit. Identity-dependent operations fail closed with `SECURITY_MASTER_NOT_INITIALIZED` before local initialization and do not use a Candidate B fallback.

Actual Playwright acceptance ran `/workbench/` with an external runtime root. It verified the initial not-initialized boundary, CSP cleanliness, XSS-safe rendering, persistent watchlist flow, temporary-target nonpersistence, validation/preview/authorization, exactly one Execute Once action, and Result/Audit/Handoff reads. It used one deterministic source invocation and no external market network.

## Boundaries retained

No production persistent state or Security Master authority was mutated. No market network was used. This closure does not tag, publish, or release the candidate, and does not begin Phase G. Windows 10 / CPython 3.13.7 is the validated platform; Linux and macOS remain outside this evidence set.
