# HANDOFF.md — Current Operational Handoff

This file is the **current stopping point** for a human or AI resuming repository work.
It is intentionally short. Historical root snapshots are preserved under
[`docs/archive/frontdoor/2026-10-28-pre-f3/`](docs/archive/frontdoor/2026-10-28-pre-f3/).

## Current status

Date: **2026-10-29**

```text
Stable product                  v1.5.0
Stable release source commit    acaf726a5b59baee4c5a30521ea5a5d5ec0cec76
Stable release source tree      d44f66dc154c21326ac8b105d2f15fd793f6071b
Phase L                         CLOSED
L7 exit contract                29 / 29 PASS
GitHub stable publication       PASS
Phase M                         NOT_AUTHORIZED
```

The v1.5.0 tag and six frozen, SHA-256-verified GitHub Release assets remain the
release authority. Post-release documentation commits on `main` do not redefine
v1.5.0. GitHub Immutable Releases enforcement is not enabled for this release.

## Current workstream

The Post-Phase-L Frontdoor / Documentation Maintenance tranche is complete and
was merged through PR #423 on 2026-10-28.

```text
main after merge                 b86ae52a2f43f53fd854e9d84cfde1c80050dcc9
frontdoor documentation commit   e5f61e1289be46d1bab6f2c6de931a3973badc90
PR #423                          MERGED
```

Current authorized workstream:

> **Post-v1.5 Productization & Stabilization — P1 Windows Launcher / First-run UX**

P0 Current-state Reconciliation is complete. Its accepted six-file correction
candidate was independently re-reviewed as `ACCEPT_WITH_NOTES`, committed as
`430d320784d5249508c37bbd6e8272732bf63ee8`, and pushed to `origin/main`.

P1-A0 Existing Windows Native Launcher / Runtime Architecture Audit is complete.
P1-A1 First-run / Setup UX Contract is **OWNER_FROZEN** on 2026-10-29. The frozen
contract selects the P1-Minimal model: a thin Windows Launcher orchestrates the
existing bootstrap and lifecycle authority; external CPython 3.13 x64 remains a
prerequisite, but the operator is not required to type Python commands. Setup has
zero automatic external network activity and does not acquire market data, update
Security Master, start Local Runtime, open Workbench, start MCP, or auto-repair /
delete existing runtime or business state.

P1-A2 — Daily Main Launcher / Runtime Control UX Contract is **OWNER_FROZEN** on
2026-10-29 after Owner review accepted it with zero blockers. It freezes the
normalized daily runtime states, explicit Start/Stop/Refresh/Diagnose controls,
validated loopback-only Workbench opening, status-only Security Master/MCP
projections, and no timer-based background polling.

P1-A3 — Minimal Windows Launcher Implementation first reached an uncommitted
closure candidate and received an independent `CHANGES_REQUIRED` review. The
bounded **P1-A3-R1** correction then received an independent re-review that was
also `CHANGES_REQUIRED`. The bounded **P1-A3-R2** correction closed the two
remaining defects without scope expansion. Deterministic P1-A3/lifecycle/package
revalidation is `97 passed`. Exact-current Windows Sandbox **R5** headless
lifecycle + fresh interactive GUI acceptance passed against launcher SHA-256
`96f9cbaeaf61d7292aa5ff0e783e32e8d17689056ce8dfdbfa60eedf1e299aa5`.
A separate interactive R5 failure-path probe also verified Setup failure preserves
`SETUP_BLOCKED / EXISTING_STATE_REQUIRES_EXPLICIT_TRANSFER` in Technical Details.
A fresh Codex independent re-review of R2/R5 returned `PASS_WITH_NOTES` with zero
blocking findings. Owner then explicitly authorized the controlled commit/push.
P1-A3-R2 implementation, tests, R1–R5 evidence and post-v1.5 governance were
committed and pushed to `main` as `3059531b7cb02bede681938228a0f258b8b5b9d9`.
v1.5.0 release authority remains unchanged.

P0 also identified one protected machine-authority summary debt: the Catalog V3
top-level `known_limitations` summary still contains stale H1/H2 wording even
though the capability entries and V3 Routing contain the later selected-route
truth. The debt remains deferred; do **not** bypass the L5/A4 semantic-authority
gate merely to make summary wording look current.

## Current product/runtime truth to preserve

- Request V3 is preferred; V1/V2 remain compatibility authorities.
- New governed Result/Audit materialization uses V3.
- Unified MCP remains exactly six tools.
- Security Master is installation-local Taiwan Market Identity Service.
- Cash durable identity is ISIN; listing/routing identity is `MARKET:CODE`.
- Persistent Watchlists are installation-local durable state with explicit
  preview/commit mutation.
- Network execution remains explicit, bounded, authorized, and auditable.
- Current executability comes from Catalog / Routing / executor authority.

Do not infer full Phase G/H roadmap completion from accepted implementation
tranches. Do not infer MCP Registry v1.5.0 publication from the GitHub v1.5.0
release; Registry publication remains separate.

## Allowed next work

P1-A1 and P1-A2 are Owner-frozen. P1-A3-R1 independent re-review returned
`CHANGES_REQUIRED`; bounded P1-A3-R2 corrections, `97 passed` deterministic
revalidation, exact-current R5 headless + fresh GUI acceptance, targeted GUI
failure-details acceptance, and the fresh P1-A3-R2 independent re-review are now
complete. The independent disposition is `PASS_WITH_NOTES` with zero blocking
findings. Owner authorized controlled commit/push, and the P1-A3-R2 implementation
commit `3059531b7cb02bede681938228a0f258b8b5b9d9` is now present on `origin/main`.

P1-A3-R2 does not authorize release mutation, Security Master live update UX,
ChatGPT/tunnel integration, a persistent MCP daemon, P2–P5, or Phase M. The
protected Catalog V3 summary debt also remains separately governed and deferred.

Later post-release work may advance `main` beyond the frozen v1.5.0 commit. It
must not mutate the v1.5.0 tag, release assets, or claim those later changes are
part of the frozen release source. Phase M remains separately unauthorized.

## Explicit stop boundaries

Do **not**:

- reopen or rerun Phase L acceptance solely for documentation maintenance;
- modify the governance-frozen `v1.5.0` tag or six published release assets;
- update `server.json` / MCP Registry metadata without separate publication authorization;
- publish a Docker image or imply a container-registry release exists;
- start Phase M;
- add a seventh MCP tool or create a competing request/result core;
- repeat consumed historical bounded-live authorities merely to refresh evidence;
- rewrite historical ledgers so their old `NOT_AUTHORIZED` / `unpublished` text
  looks current.

## Resume order

A new human or agent should read:

1. `PROJECT.md` — current product/project authority;
2. `HANDOFF.md` — current stop point and allowed work;
3. `ROADMAP.md` — durable phase scope and Phase M boundary;
4. `AGENTS.md` — repository/AI working rules;
5. `docs/INDEX.md` — persona-oriented documentation map;
6. current Catalog / Routing / executor authority for capability questions;
7. only then the exact frozen governance record required by the task.

Do not reconstruct current state by reading historical milestone documents in
chronological order.

## Recovery / history pointers

- High-level chronology: `docs/PROJECT_HISTORY.md`
- Governance navigation: `docs/governance/INDEX.md`
- Phase L evidence: `docs/governance/phase_l/`
- Pre-F3 root snapshots: `docs/archive/frontdoor/2026-10-28-pre-f3/`
- Public release: `https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.0`

Current-state contradictions belong in current frontdoor documents. Historical
gate truth remains historical and must not be laundered into later wording.
