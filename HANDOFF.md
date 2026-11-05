# HANDOFF.md — Current Operational Handoff

This file is the **current stopping point** for a human or AI resuming repository work.
It is intentionally short. Historical root snapshots are preserved under
[`docs/archive/frontdoor/2026-10-28-pre-f3/`](docs/archive/frontdoor/2026-10-28-pre-f3/).

## Current status

Date: **2026-11-05**

```text
Stable product                  v1.5.1
Stable release source commit    1f3666eefdca7e2e9a1c88099f802696bf7970d6
Stable release source tree      d67e9bc1db34ff268b5b8d0f2a301d1a211df3b6
GitHub latest stable            PUBLISHED 2026-11-04
GitHub release assets           6 / 6 SHA-256 remote readback PASS
Publication manifest SHA256     791b42375f4f9d747d4389fcd0113dab16367aa04d6bd6b8bc8b95598be7af2b
Release Readiness               PASS (15 blocking gates)
Diagnostics                     default_ci FAIL; full_non_network FAIL (non-blocking)
Phase L / L7                    CLOSED / 29 of 29 PASS
RMA-0 through RMA-11            PASS / CLOSED
RMA open blockers / majors      0 / 0
Documentation Gate 2            COMPLETE_WITH_FINDINGS (13)
Documentation Gate 3            documentation-only reconciliation
MCP Registry                    v1.0.0 active/latest (separate publication)
Phase M                         NOT_AUTHORIZED
```

The authoritative [GitHub v1.5.1 Release](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.1)
and its six published assets are frozen under release governance. Later
documentation-only `main` commits do **not** redefine that release.
Historical v1.5.0 remains frozen, and Registry/Docker publication is separate.
See [post-publication record](docs/release/V1_5_1_RELEASE_PUBLICATION.md).

**Historical pre-promotion local checkpoint (not live Git HEAD):**
`b84f9fc8` ahead of `3f2e5b3a` with 56 selected RMA working-tree entries;
that state was superseded by exact final source `1f3666ee` and the official release.
Do not act on those checkpoint values; always re-read current Git refs.

## Current workstream

**Post-v1.5.1 documentation reconciliation**: Gate 2 audit completed 2026-11-05.
The separately authorized Gate 3 modifies CURRENT documentation on `main` only;
the published `v1.5.1` Tag/source/assets remain untouched. Gate 3 corrections
include bilingual product entry points, Launcher-first operator instructions,
the current six-tool Unified MCP and Registry separation.

Next productization P2–P5, any further live-provider acquisition, MCP Registry
publication, Docker registry publication, and Phase M require separate authorization.

## Historical prepublication RMA workstream / evidence index

The following RMA evidence links and per-group narratives are retained as
**historical pre-v1.5.1-publication acceptance**, not a current pending
source-promotion instruction. RMA-0..11 are PASS/CLOSED with zero open blockers
and majors; RMA-D022/D025 are deferred non-blocking. The former Windows P1
launcher work has already been incorporated into the published product.

Current RMA authorities:

- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_TEST_CONTRACT_2026-10-31.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_DEFECT_REGISTER_2026-10-31.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_RELEASE_PREFLIGHT_AND_CONTINUITY_2026-10-31.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_0_RELEASE_PROVENANCE_BASELINE_2026-10-31.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_1_FRESH_FIRST_RUN_INSTALLATION_2026-10-31.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_2_LAUNCHER_DAILY_OPERATION_2026-10-31.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_3_SECURITY_MASTER_LIFECYCLE_2026-11-01.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_4_LOCAL_SERVICE_MCP_REAL_INTEGRATION_2026-11-01.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_5_IDENTITY_RESOLUTION_MATRIX_2026-11-01.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_6_CAPABILITY_EXECUTION_MATRIX_2026-11-01.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_7_OFFICIAL_SOURCE_TLS_MATRIX_2026-11-01.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_8_RESULT_AUDIT_EVIDENCE_INTEGRITY_2026-11-02.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_9_FAILURE_RECOVERY_MATRIX_2026-11-02.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_10_NATIVE_PACKAGE_PORTABILITY_2026-11-02.md`
- `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_11_OPERATOR_EXPERIENCE_ACCEPTANCE_2026-11-03.md`

RMA-1 is **PASS/CLOSED** and closes `RMA-D002`/`RMA-D003`. RMA-2 is now
**PASS/CLOSED**: normal daily operation, adverse-state projection, and the
cross-RMA3 successful-update/explicit-Restart gate are all accepted; `RMA-D004`
is `CLOSED_PASS`.

RMA-3 is also **PASS/CLOSED**. Real Security Master install/update evidence proved
strict verified TLS plus evidence-gated compatibility retry, `QUALIFIED -> ACTIVE`,
and `restart_required`. The activation/Restart integration defect `RMA-D006` was
localized to the Security Master status timeout; a bounded 60-second candidate
passed targeted regression (2/2), directly affected regression (56/56), and fresh
Sandbox Restart/PID replacement/`RUNNING_READY` retest. `RMA-D007` Doctor failure
projection and harness-only `RMA-D005` are likewise `CLOSED_PASS`. Final isolated
RMA-3 lifecycle evidence also passed failed-update retention, stopped-runtime
next-start, history, bounded rollback, invalid rollback fail-closed behavior, and
final active/history integrity.

RMA-4 is also **PASS/CLOSED**. The validated current candidate passed `/api/health`,
Local Service contract v2, MCP startup-check, stdio initialize, exact six-tool
`tools/list`, all six public tool paths, Request V1/V2/V3 validation/preview, and
Capability Catalog access. The existing Stable `tw-market-local` deployment also
proved the real Native -> Local Service -> MCP -> Secure MCP Tunnel -> ChatGPT path
without repointing the Stable installation. Harness-only `RMA-D008` is `CLOSED_PASS`.

RMA-5 is now **PASS/CLOSED**. Public MCP identity validation proved code,
`MARKET:CODE`, ISIN and Chinese-name convergence, a TPEx common share, an allowed
ETF/non-common-share family, nonexistent fail-closed behavior, and a known warrant
that resolves to its canonical identity but is rejected as
`unsupported_security_type`. An exhaustive 54,842-record / 219,368-token exact
input scan found no natural ambiguity collision. Harness-only `RMA-D009` and
`RMA-D010` are `CLOSED_PASS`.

RMA-6 is now **PASS/CLOSED**. Offline inventory, Validate/Preview, authorization,
real Execute Once, Result/Audit materialization, and governed rejection behavior
were exercised against the current candidate. Live source failures remain truthful
capability outcomes rather than control-chain failures. `RMA-D013` exposed a real
Result V3 false-success defect for failed typed evidence; the bounded repair passed
118/118 affected regressions, 26/26 cross-version regressions, and a fresh targeted
network-enabled Sandbox retest reproducing all three TPEx source failures while
correctly projecting `missing_needs` and canonical Result `failed`.

RMA-7 — Official-source / TLS matrix is now **PASS/CLOSED**. `RMA-D001` was
reproduced, root-caused to nondeterministic cold Python/OpenSSL trust material,
qualified against the bundled certifi CA set, and closed after authorized bounded
repair. Fresh packaged cold-Sandbox retest produced 23/23 production routes usable,
23/23 product parser/schema PASS, verified TLS retained, zero retry and correct
strict/compatibility semantics. `RMA-D001` is `CLOSED_PASS`.

RMA-8 — Result / Audit / evidence integrity is **PASS/CLOSED**. Fresh isolated
success cases independently verified Control Package/authorization binding,
receipt, bundle, durable evidence bytes/hashes, citation mapping, Result V3, Audit
Package, replay lineage and persisted/API/Handoff consistency. Harness-only
`RMA-D016` and `RMA-D017` are `CLOSED_PASS`.

RMA-9 — Failure and recovery matrix is **PASS/CLOSED**. Fresh network-disabled
Sandboxes proved truthful fail-closed handling and bounded recovery across Native
lifecycle, MCP availability, port/ownership state, Security Master state, invalid
request/unsupported capability, Control Package tamper and official-source outage.
Harness-only `RMA-D018` and `RMA-D019` are `CLOSED_PASS`.

RMA-10 — Native package / portability is **PASS/CLOSED**. The same exact Native
candidate passed from two independently extracted locations inside a fresh
network-disabled Sandbox with identical package-manifest identity and 49/49
locked-wheel closure. Launcher, CLI, Security Master CLI, Local Service, MCP
startup and packaged Mode B2 entry all passed without developer-checkout or Stable
paths present in the guest. Tamper enforcement and exact-byte recovery also
passed. RMA-D018 was reused only for cleanup-state sampling; no RMA-10 product
defect was found.

RMA-11 — Operator experience acceptance is **PASS/CLOSED**. Owner-driven E2E
validated the normal built-Native path through setup, Security Master, Start,
Workbench request composition, blocked-state recovery, authorization, explicit
network confirmation, Execute Once, Result/Audit export and AI-ready handoff.
`RMA-D020`, `RMA-D021`, `RMA-D023`, `RMA-D024`, `RMA-D026` and `RMA-D027` are
`CLOSED_PASS`. `RMA-D022` and transient `RMA-D025` remain
`DEFERRED_NON_BLOCKING`; final defect counts are 0 open blockers, 0 open majors,
2 deferred non-blocking and 25 closed-pass items.

`RMA-0` through `RMA-11` are now **PASS/CLOSED**. The RMA program is complete.

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

Post-v1.5.1 **documentation-only maintenance** is the present authorization:
repair CURRENT navigation, operator/MCPB instructions, release metadata and
historical/current boundaries using the Gate 2 issue register. Use a distinct
`main` commit; do not retag the published release or replace its assets.

RMA closure and prior local build permissions are historical events, not standing
authorizations for any further runtime changes, provider calls, Registry/Docker
publication or Phase M. P2–P5 remain separately governed.

## Explicit stop boundaries

Do **not**:

- reopen or rerun Phase L acceptance solely for documentation maintenance;
- modify the governance-frozen `v1.5.0` **or `v1.5.1`** tag, source,
  historical evidence, or six published release assets;
- update `server.json` / MCP Registry metadata without separate publication authorization;
- publish a Docker image or imply a container-registry release exists;
- start Phase M;
- add a seventh MCP tool or create a competing request/result core;
- repeat consumed historical bounded-live authorities merely to refresh evidence;
- rewrite historical ledgers so their old `NOT_AUTHORIZED` / `unpublished` text
  looks current.

## Resume order

1. `PROJECT.md` — current product authority and release identity.
2. `HANDOFF.md` — current stopping point.
3. `ROADMAP.md` — durable phase scope, Phase M NOT_AUTHORIZED.
4. `AGENTS.md` — repository and AI tool/acceptance rules.
5. `docs/INDEX.md` — current documentation navigation.
6. `docs/release/V1_5_1_RELEASE_PUBLICATION.md` — published artifact hashes,
   retained test diagnostics and Registry boundary.
7. `docs/governance/post_v1_5/` — historical RMA contracts, per-group
   acceptance, defect register and release preflight.
8. Current Capability Catalog / Routing / executor authority for live
   executability questions; do not infer permission from documentation.

Before any subsequent work re-read Git status and the remote `main` and
annotated Tag refs. Historical acceptance material is not current authority.

## Recovery / history pointers

- High-level chronology: `docs/PROJECT_HISTORY.md`
- Governance navigation: `docs/governance/INDEX.md`
- Phase L evidence: `docs/governance/phase_l/`
- Pre-F3 root snapshots: `docs/archive/frontdoor/2026-10-28-pre-f3/`
- Latest public release: `https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.1`
- Previous historical release: `https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.0`

Current-state contradictions belong in current frontdoor documents. Historical
gate truth remains historical and must not be laundered into later wording.
