# Post-v1.5 — v1.5.1 RMA Release Preflight & Continuity Record

Date: 2026-10-31 (Asia/Taipei)
Last reconciled: 2026-11-03 (Asia/Taipei)
Status: **RMA CLOSURE SNAPSHOT — SUCCESSOR v1.5.1 LOCAL PROMOTION GATE ACTIVE**

As of 2026-11-04 the Owner separately selected local unpublished `VERSION=1.5.1`
and authorized bounded clean-source promotion / Native final-build verification.
The dated RMA-closure checkpoint below remains historical; the live Git HEAD and
version must be freshly read. No push/tag/publication is authorized.

## 1. Why this record exists

This record is the handoff anchor for a new ChatGPT/Codex conversation. It avoids
reconstructing the current workstream from historical Phase L / P1 records.

A resumed agent should read `PROJECT.md`, `HANDOFF.md`, this record, the RMA Test
Contract, and the RMA Defect Register before changing code or running live tests.

## 2. Exact current repository checkpoint

```text
repository    D:\Codex-Workspace\projects\tw-market-live-data-intelligence
branch        main
HEAD          b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c
origin/main   3f2e5b3a3588d3778d5a4b380c9d8e0a2f41ca05
ahead/behind  3 / 0
VERSION       1.5.0
working tree  intentionally dirty: RMA governance evidence + accumulated bounded RMA repair/test files through RMA-11
```

Frozen release authority remains `v1.5.0` at commit `acaf726a...`, tree
`d44f66dc...`. Phase L is CLOSED. Phase M and P2–P5 remain NOT_AUTHORIZED.

## 3. Current local patch candidate

Three local commits are intentionally ahead of `origin/main`:

1. `b38fde12 feat(launcher): finalize v2 UX and native entry guard`
2. `8b482be4 fix(launcher): add explicit verified TLS compatibility retry`
3. `b84f9fc8 fix(packaging): include Mode B2 execute-once wrapper`

RMA subsequently produced bounded **uncommitted** repairs across lifecycle/Launcher,
verified production TLS, Result V3 truthfulness, Workbench request/preview/authorization
UX, Mode B2 authorization-readiness projection, explicit network-confirmation UX,
and Mode C recent-performance / AI-handoff projection. Their direct and adjacent
regressions plus named RMA retests are recorded in the Defect Register and RMA closure
records. They remain working-tree candidate content rather than final release bytes.

These changes collectively address the daily Windows entry, Security Master lifecycle,
Native Mode B2 package completeness, deterministic verified TLS, Result/Audit truth,
operator recovery/confirmation, and Mode C handoff consistency. They are candidate
`v1.5.1` content, but `v1.5.1` has not been selected, assembled as an exact final
release candidate, committed, tagged, pushed or released.

The normal end-user entry for a built Native distribution is the bundle-root:

`Launch-TW-Market.cmd`

The source-tree file under `packaging_native/launchers/` is an implementation
source and assumes the built distribution layout; it is not the final user-ready
entry when run in-place from the source tree.

## 4. RMA program purpose and closure

RMA exercised the real usage chain where integration defects matter more than isolated unit correctness:

`Native Launcher -> Installation/Runtime -> Security Master -> Local Service -> MCP -> AI client -> Request/Preview/Authorization -> Mode B2 -> official evidence -> Result/Audit`.

Owner-driven and isolated Windows acceptance converted prior ad-hoc success/failure discovery into a formal release-decision evidence set. RMA-0 through RMA-11 are now PASS/CLOSED; the next boundary is final-candidate assembly and a separate v1.5.1 release-gate decision.

## 5. Known issue entering RMA

The pre-seeded defect `RMA-D001 — Production Evidence TLS Policy Integration` was
reproduced, root-caused and closed under RMA-7. Fresh cold Windows/Python evidence
proved lazy platform trust-store population, while the governed bundled certifi CA
set provided deterministic verified TLS. The authorized bounded repair then passed
a packaged cold-Sandbox 23-source production-policy matrix with 23/23 usable routes
and 23/23 product parser/schema PASS.

Security constraints remain non-negotiable: no silent fallback, no certificate
verification disable, no hostname-verification disable.

## 6. RMA authorities and current progress

- Test contract:
  `POST_V1_5_V1_5_1_RMA_TEST_CONTRACT_2026-10-31.md`
- Defect register:
  `POST_V1_5_V1_5_1_RMA_DEFECT_REGISTER_2026-10-31.md`
- RMA-0 baseline:
  `POST_V1_5_V1_5_1_RMA_0_RELEASE_PROVENANCE_BASELINE_2026-10-31.md`
- RMA-1 acceptance:
  `POST_V1_5_V1_5_1_RMA_1_FRESH_FIRST_RUN_INSTALLATION_2026-10-31.md`
- RMA-2 launcher daily-operation closure:
  `POST_V1_5_V1_5_1_RMA_2_LAUNCHER_DAILY_OPERATION_2026-10-31.md`
- RMA-3 Security Master lifecycle closure:
  `POST_V1_5_V1_5_1_RMA_3_SECURITY_MASTER_LIFECYCLE_2026-11-01.md`
- RMA-4 Local Service + MCP real-integration closure:
  `POST_V1_5_V1_5_1_RMA_4_LOCAL_SERVICE_MCP_REAL_INTEGRATION_2026-11-01.md`
- RMA-5 identity-resolution matrix closure:
  `POST_V1_5_V1_5_1_RMA_5_IDENTITY_RESOLUTION_MATRIX_2026-11-01.md`
- RMA-6 capability-execution matrix closure:
  `POST_V1_5_V1_5_1_RMA_6_CAPABILITY_EXECUTION_MATRIX_2026-11-01.md`
- RMA-7 official-source / TLS matrix closure:
  `POST_V1_5_V1_5_1_RMA_7_OFFICIAL_SOURCE_TLS_MATRIX_2026-11-01.md`
- RMA-8 closure: `POST_V1_5_V1_5_1_RMA_8_RESULT_AUDIT_EVIDENCE_INTEGRITY_2026-11-02.md`
- RMA-9 failure/recovery closure:
  `POST_V1_5_V1_5_1_RMA_9_FAILURE_RECOVERY_MATRIX_2026-11-02.md`
- RMA-10 Native package / portability closure:
  `POST_V1_5_V1_5_1_RMA_10_NATIVE_PACKAGE_PORTABILITY_2026-11-02.md`
- RMA-11 Operator experience acceptance closure:
  `POST_V1_5_V1_5_1_RMA_11_OPERATOR_EXPERIENCE_ACCEPTANCE_2026-11-03.md`
- This file is the continuity / release-preflight handoff.

Current progress:

```text
RMA-0  Release / Provenance Baseline   PASS / CLOSED
RMA-1  Fresh first-run installation    PASS / CLOSED
RMA-2  Launcher daily operation        PASS / CLOSED
RMA-3  Security Master lifecycle       PASS / CLOSED
RMA-4  Local Service + MCP integration PASS / CLOSED
RMA-5  Identity resolution matrix      PASS / CLOSED
RMA-6  Capability execution matrix     PASS / CLOSED
RMA-7  Official-source / TLS matrix    PASS / CLOSED
RMA-8  Result / Audit / evidence       PASS / CLOSED
RMA-9  Failure and recovery matrix     PASS / CLOSED
RMA-10 Native package / portability    PASS / CLOSED
RMA-11 Operator experience acceptance PASS / CLOSED
```

RMA groups use distinct `PASS`, `FAIL`, `BLOCKED`, and `GOVERNED_REJECTION`
classifications. Correct fail-closed governance rejection is not a product defect.

## 7. Resume / next-action order

A new conversation should continue in this order:

1. Re-read exact Git status and confirm HEAD, VERSION, committed candidate changes,
   and all uncommitted RMA repair/test files still match this record; do not assume
   the checkpoint stayed unchanged.
2. Read the RMA Test Contract, RMA-0 through RMA-11 closure records and the finalized
   RMA Defect Register disposition.
3. Treat the RMA program as complete: `RMA-0` through `RMA-11` are **PASS/CLOSED**,
   with `RMA-D022` and `RMA-D025` preserved as `DEFERRED_NON_BLOCKING` observations
   and zero open blockers/majors.
4. The next work, if separately authorized, is v1.5.1 **final-candidate assembly and
   release-gate verification**; do not treat any diagnostic ZIP as release-eligible.
5. Preserve the RMA-D001 bundled-certifi verified TLS semantics and the exact I1
   post-v1.5 supersession authority; do not rewrite historical Phase-I ledgers.
6. Preserve RMA-8 Result/Audit/evidence lineage semantics and RMA-11 operator/Mode-C
   truthfulness; chat text is not execution proof.
7. Preserve RMA-10 exact Native package identity, locked-wheel closure and tamper
   enforcement as the portability baseline; final bytes require fresh final-candidate gates.
8. Before proposing a release candidate, assemble the exact intended patch bytes,
   review unrelated mutations, run required current test/release governance gates,
   and record their exact hashes/results.
9. Local `VERSION=1.5.1` selection and bounded commit/build were separately
   authorized on 2026-11-04. Push/tag/publish, Phase M and P2–P5 remain unauthorized.

## 8. Version decision

The current hypothesis is that the accumulated Launcher/native-packaging fixes plus
any RMA-proven compatibility repairs are suitable for a patch release named
`v1.5.1`, because the intended work preserves the v1 public contract rather than
introducing a new product contract.

That hypothesis was not a release decision. On 2026-11-04 the Owner separately
selected an unpublished local `VERSION=1.5.1` candidate and authorized a clean-source
Native final-build gate; no release/tag/push/publication is implied.

## 9. Hard stop boundaries

Do not delete files/evidence; do not mutate the frozen v1.5.0 tag/assets; do not
start Phase M or P2–P5; do not add public MCP tools or competing request/result
contracts; do not commit, push, tag or publish without explicit Owner authority.
