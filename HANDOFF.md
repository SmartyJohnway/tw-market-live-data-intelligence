# HANDOFF.md — Current Operational Handoff

This file is the **current stopping point** for a human or AI resuming repository work.
It is intentionally short. Historical root snapshots are preserved under
[`docs/archive/frontdoor/2026-10-28-pre-f3/`](docs/archive/frontdoor/2026-10-28-pre-f3/).

## Current status

Date: **2026-11-04**

```text
Stable product                  v1.5.0
Stable release source commit    acaf726a5b59baee4c5a30521ea5a5d5ec0cec76
Stable release source tree      d44f66dc154c21326ac8b105d2f15fd793f6071b
Phase L                         CLOSED
L7 exit contract                29 / 29 PASS
GitHub stable publication       PASS
RMA-0 through RMA-11            PASS / CLOSED
RMA open blockers / majors      0 / 0
Next boundary                   v1.5.1 final-candidate / release-gate decision
Phase M                         NOT_AUTHORIZED
```

Pre-promotion local baseline checkpoint (historical; verify live Git HEAD):

```text
branch                          main
HEAD                            b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c
origin/main                     3f2e5b3a3588d3778d5a4b380c9d8e0a2f41ca05
ahead / behind                  3 / 0
VERSION at baseline             1.5.0 (selected v1.5.1 in current local candidate)
working tree at baseline        intentionally dirty: 56-file RMA selection before version promotion
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

Current stopping point:

> **Post-v1.5 Productization & Stabilization — RMA-0 through RMA-11 CLOSED; local v1.5.1 clean-source / Native final-build gate authorized**

P0 and the original P1 Windows Launcher tranche are complete. Subsequent bounded
work produced three local commits on `main`, intentionally ahead of `origin/main`:

```text
b38fde12  feat(launcher): finalize v2 UX and native entry guard
8b482be4  fix(launcher): add explicit verified TLS compatibility retry
b84f9fc8  fix(packaging): include Mode B2 execute-once wrapper
```

RMA additionally produced bounded, accepted repair/test changes across
lifecycle/Launcher, deterministic verified TLS, Result V3 truthfulness, Workbench
operator UX/authorization readiness, explicit execution confirmation, and Mode C
handoff projection. These RMA-accepted changes are selected for a local v1.5.1 source promotion; they are not published release bytes. The normal operator entry for a built Native distribution remains the
bundle-root `Launch-TW-Market.cmd`.

Owner authorized the formal RMA-0 through RMA-11 program on 2026-10-31. It is now
complete: all twelve RMA groups are **PASS/CLOSED**. The final defect disposition
has zero open blockers and zero open majors; `RMA-D022` and `RMA-D025` are retained
as `DEFERRED_NON_BLOCKING` observations. `VERSION=1.5.1` was separately selected for a local unpublished candidate on
2026-11-04; frozen v1.5.0 authority remains unchanged. RMA closure did not
authorize commit/push/tag,
release publication, Registry publication, Phase M or P2–P5.

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

The RMA program is complete; there is no remaining RMA execution group. This
closure authorizes only the governance reconciliation recorded here. It does not
automatically authorize further product mutation or release actions.

Owner separately authorized v1.5.1 local clean-source promotion and an exact Native
final-build gate on 2026-11-04, without publication authority. The gate will:
select the intended accumulated RMA repair bytes, review unrelated working-tree
mutations, build an exact candidate, run the required current test/release
governance gates against those exact bytes, and record final hashes/results.

The Owner has selected `VERSION=1.5.1` and authorized bounded local commit/build
for this gate. Push, tag and publication still require separate Owner decisions. RMA closure itself does not
authorize version mutation, commit, push, tag, GitHub release, Registry
publication, Phase M or P2–P5. The frozen v1.5.0 tag/assets remain immutable.

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
3. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_RELEASE_PREFLIGHT_AND_CONTINUITY_2026-10-31.md`;
4. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_0_RELEASE_PROVENANCE_BASELINE_2026-10-31.md`;
5. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_1_FRESH_FIRST_RUN_INSTALLATION_2026-10-31.md`;
6. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_2_LAUNCHER_DAILY_OPERATION_2026-10-31.md`;
7. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_3_SECURITY_MASTER_LIFECYCLE_2026-11-01.md`;
8. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_4_LOCAL_SERVICE_MCP_REAL_INTEGRATION_2026-11-01.md`;
9. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_5_IDENTITY_RESOLUTION_MATRIX_2026-11-01.md`;
10. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_6_CAPABILITY_EXECUTION_MATRIX_2026-11-01.md`;
11. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_7_OFFICIAL_SOURCE_TLS_MATRIX_2026-11-01.md`;
12. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_8_RESULT_AUDIT_EVIDENCE_INTEGRITY_2026-11-02.md`;
13. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_9_FAILURE_RECOVERY_MATRIX_2026-11-02.md`;
14. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_10_NATIVE_PACKAGE_PORTABILITY_2026-11-02.md`;
15. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_11_OPERATOR_EXPERIENCE_ACCEPTANCE_2026-11-03.md`;
16. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_TEST_CONTRACT_2026-10-31.md`;
17. `docs/governance/post_v1_5/POST_V1_5_V1_5_1_RMA_DEFECT_REGISTER_2026-10-31.md`;
18. `ROADMAP.md` — durable phase scope and Phase M boundary;
19. `AGENTS.md` — repository/AI working rules;
20. current Catalog / Routing / executor authority when final-candidate review depends on capability truth.

Before continuing, re-read Git status and do not assume the checkpoint SHA in
this handoff is still current. Do not reconstruct current state by reading
historical milestone documents in chronological order.

## Recovery / history pointers

- High-level chronology: `docs/PROJECT_HISTORY.md`
- Governance navigation: `docs/governance/INDEX.md`
- Phase L evidence: `docs/governance/phase_l/`
- Pre-F3 root snapshots: `docs/archive/frontdoor/2026-10-28-pre-f3/`
- Public release: `https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.0`

Current-state contradictions belong in current frontdoor documents. Historical
gate truth remains historical and must not be laundered into later wording.
