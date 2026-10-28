# HANDOFF.md — Current Operational Handoff

This file is the **current stopping point** for a human or AI resuming repository work.
It is intentionally short. Historical root snapshots are preserved under
[`docs/archive/frontdoor/2026-10-28-pre-f3/`](docs/archive/frontdoor/2026-10-28-pre-f3/).

## Current status

Date: **2026-10-28**

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

Authorized workstream:

> **Post-Phase-L Frontdoor / Documentation Maintenance**

Current tranche status:

- F0 — Frontdoor inventory / information architecture: **CANDIDATE_COMPLETE**.
- F1 — Public product frontdoor: **CANDIDATE_COMPLETE**.
- F2 — Install / Quick Start / Distribution: **CANDIDATE_COMPLETE**.
- F3 — Engineering Frontdoor Consolidation: **CANDIDATE_COMPLETE**.
- F4 — AI / discoverability / visual polish: **CANDIDATE_COMPLETE**.
- F5 — documentation-only validation: **CANDIDATE_COMPLETE**.
- F5-R1 — independent-review targeted documentation corrections: **CANDIDATE_COMPLETE**.

The initial cumulative independent review found three documentation-only blockers;
F5-R1 has corrected all three and passed the same focused validation gate. Final
acceptance still requires an independent re-review of the corrected cumulative diff.

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

The corrected F0–F5 + F5-R1 documentation candidate is complete. The next
bounded step is an independent re-review of the cumulative Post-Phase-L diff and
its correction evidence. A documentation-only commit / push / PR requires a
separate acceptance/authorization decision; it is not performed by F5-R1 itself.

Documentation work may advance `main` beyond the frozen v1.5.0 commit. It must
not mutate the v1.5.0 tag, release assets, or claim those later docs are part of
the frozen release source. Phase M remains separately unauthorized.

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
