# HANDOFF.md — Current Operational Handoff

## Current L7-A4 merged state (2026-10-25)

L7-A4 is **OWNER-ACCEPTED AND MERGED** under
`L7_A4_PUBLIC_COMPATIBILITY_MCP_SDK_STABLE_VERSION_DECISION_PASS`.
Independent disposition is `L7_A4_INDEPENDENT_TECHNICAL_REVIEW_PASS`, review
`5642080353`; Owner disposition is `L7_A4_OWNER_ACCEPTED_FOR_MERGE`, review
`5642097513`. PR #416 normal-merged exact accepted head
`902febc323b2fd568a2d00c00a18eac24f5ae655`, tree
`d264f509efda2affbf13c3253363e1844651cc17`, at merge commit
`28a22ffc206db425ffefa8e578bf5ef7dcdb1a19`. Merge parents are prior canonical main
`9bc3be99bd37d035cb7d1f02172569f7120781ea` and the exact accepted A4 head; GitHub merge verification is valid.

ProductVersion is **1.5.0 selected/unpublished**; published stable remains v1.0.0.
Published Local Service v1 clients remain supported through the accepted compatibility bridge,
current v2 and exact-six remain supported, and MCP SDK policy is exact `mcp==1.29.0`.
Canonical A1 remains 1895 passed / 0 failed / four contracted skips / zero guard denials;
A4 focused compatibility/version/state acceptance remains 240 passed. GAP-13 is
`CLOSED_BY_EXPLICIT_EXACT_PIN_POLICY`; GAP-14 is
`CLOSED_BY_V1_5_0_PUBLIC_STATE_COMPATIBILITY_DECISION`; only EXIT-08/09/10/14/15 gain A4 PASS.

Report: `docs/governance/phase_l/PHASE_L_L7_A4_PUBLIC_COMPATIBILITY_MCP_SDK_STABLE_VERSION_DECISION_2026-10-25.md`.
Policy: `docs/contracts/L7_PUBLIC_COMPATIBILITY_MCP_SDK_VERSION_POLICY.md`.
Reconciliation: `docs/governance/phase_l/PHASE_L_L7_A4_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-25.md`.
**L7-A5+ remains NOT AUTHORIZED. ProductVersion 1.5.0 is not published. Stable publication,
Phase M and Phase L closure remain NOT AUTHORIZED.**

## Historical L7-A3 merged state (2026-10-25)

L6 remains **CLOSED**. L7-A0, L7-A1, L7-A2 and L7-A3 are **OWNER-ACCEPTED AND MERGED**.
L7-A3 technical disposition remains `L7_A3_DEPENDENCY_REPRODUCIBILITY_SUPPLY_CHAIN_CONTRACT_PASS`;
independent disposition is `L7_A3_INDEPENDENT_TECHNICAL_REVIEW_PASS`; Owner disposition is
`L7_A3_OWNER_ACCEPTED_FOR_MERGE`. Independent review is `5640713251`; provenance-review correction is
`5640717276`; Owner acceptance review is `5640717621`.

PR #414 normal-merged exact accepted head `3805b5542b03fc3e707aa9550ff7d0892d743cb6`, tree
`ac178739d478f06b2ac6287633d30110a80b9970`, at merge commit `c06108e40930881f340e44ed61b45a42d8ceb046`.
Merge parents are prior canonical main `5c62d6d8cc6c49b2803126aa2190a1778fa1d4ac` and the exact accepted A3 head;
GitHub merge verification is valid. The independent-review checkout-v4 SHA transcription defect is corrected by
review `5640717276`; repository/evidence bytes were already correct.

Canonical release/build/CI Python is 3.13; independently proven 3.11 source/developer compatibility remains
noncanonical and separately locked; Python 3.12 remains unsupported. Core dependency versions, MCP 1.29.0 and
VERSION remain unchanged. Native reproducibility is byte-identical; Docker retains the accepted equal-content /
explicit OCI metadata boundary. The canonical A1 gate remains 1895 passed / 0 failed / four contracted skips /
zero guard denials, and the A2 release path was repeated successfully under the frozen A3 authority.

L7-GAP-08/09 are CLOSED; GAP-10 is `ACCEPTED_WITH_EXPLICIT_REPRODUCIBILITY_BOUNDARY`; GAP-11 is
`CLOSED_BY_EXPLICIT_POLICY`; GAP-12 is `HARDENED_WITH_HOSTED_RUNNER_PROVENANCE_BOUNDARY`. Only
L7-EXIT-11/12/13/17/18 gain A3 PASS. Public/exact-six final compatibility acceptance remains deferred to A4.

**L7-A4+ NOT AUTHORIZED. Stable release/publication NOT AUTHORIZED. Phase M NOT AUTHORIZED.
Phase L NOT CLOSED.** This reconciliation is governance-only and does not start A4.

Report: `docs/governance/phase_l/PHASE_L_L7_A3_DEPENDENCY_REPRODUCIBILITY_SUPPLY_CHAIN_CONTRACT_2026-10-25.md`.
Evidence: `docs/governance/phase_l/acceptance_runs/l7-a3-20261024T182923Z/`.
Reconciliation: `docs/governance/phase_l/PHASE_L_L7_A3_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-25.md`.

## Historical L7-A2 merged state (2026-10-25)

L6 remains **CLOSED**. L7-A0 and L7-A1 remain **OWNER-ACCEPTED AND MERGED**;
A1 post-merge governance is reconciled at canonical entry `0e903ba042df7fed63f2c0ccd1c82dd5a28b62b5`.
L7-A2 is **OWNER-ACCEPTED AND MERGED** under
`L7_A2_FRESH_CLONE_WINDOWS_NATIVE_DOCKER_RELEASE_VALIDATION_INTEGRATION_PASS`.
Independent review disposition is `L7_A2_INDEPENDENT_TECHNICAL_REVIEW_PASS`; Owner disposition is
`L7_A2_OWNER_ACCEPTED_FOR_MERGE`.

PR #412 normal-merged accepted head `56e418e9a22469f1c7ed8fbeda01cf7474e029de`,
tree `dc91f58ec8a4b45733c3852036afd29d35986be3`, at merge commit
`2219552d9817e11219c08b53e606d2969a368d02`. Merge parents are prior canonical main
`0e903ba042df7fed63f2c0ccd1c82dd5a28b62b5` and the exact accepted A2 head; GitHub merge verification is valid.
The bounded validator reproducibility correction is included in the accepted head; its prior review blocker is closed.

Fresh clone, genuine Windows11 x64 guest, Native and Docker validation artifacts remain accepted;
canonical A1 gate is 1895 passed / 0 failed / four contracted historical witness skips,
with no unexpected skips/xfails or guard denials. GAP05/06/07 are CLOSED; GAP20 remains a retained
nonblocking historical limitation with current A2 replacement/state-survival proof.
Only EXIT04/05/06/07 gain A2 PASS; exact-six/public contracts remain preservation checks,
with final L7 acceptance deferred. Existing A1 acceptance and immutable failed/TEMP evidence remain.

**L7-A3+ NOT AUTHORIZED. Stable release/publication NOT AUTHORIZED.
Phase M NOT AUTHORIZED. Phase L NOT CLOSED.** No dependency/support policy or VERSION changes.

Report: `docs/governance/phase_l/PHASE_L_L7_A2_FRESH_CLONE_WINDOWS_NATIVE_DOCKER_RELEASE_VALIDATION_INTEGRATION_FINAL_2026-10-24.md`.
Evidence: `docs/governance/phase_l/acceptance_runs/l7-a2-20261024T133622Z-final/`.
Reconciliation: `docs/governance/phase_l/PHASE_L_L7_A2_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-25.md`.

## Historical L7-A1 merged state (2026-10-24)

L6 remains **CLOSED**; L7-A0 is **OWNER-ACCEPTED AND MERGED**, reconciled by
PR #409 normal merge `405bf16f5f82f4d37062d036ca6815eba27f7c4d`.
L7-A1 is **OWNER-ACCEPTED AND MERGED** under
`L7_A1_DETERMINISTIC_REQUIRED_CI_AND_HISTORICAL_FAILURE_CLASSIFICATION_PASS`.
Independent review disposition is `L7_A1_INDEPENDENT_TECHNICAL_REVIEW_PASS`; Owner disposition is
`L7_A1_OWNER_ACCEPTED_FOR_MERGE`.

PR #410 normal-merged accepted head `c2cdb66fb8d5e1a697f56a8c65de9f7313dafc14`,
tree `f1105c640e749247c99ed23dd2e45c9432bb1b4a`, at merge commit
`fe07765e67422dbad065cb5be8aad4ddb3d14914`. Merge parents are prior canonical main
`405bf16f5f82f4d37062d036ca6815eba27f7c4d` and the exact accepted A1 head; GitHub merge verification is valid.

Canonical `release-blocking-ci` v1 remains accepted at 1895 passed / 0 failed / four named optional
historical artifact witnesses skipped; zero unexpected skips and guard denials. All 47 baseline
failures remain finally adjudicated with DECISION_REQUIRED=0. DEFAULT_CI remains diagnostic FAIL;
FULL_NON_NETWORK remains diagnostic FAIL at the preserved Windows `fcntl` collection boundary.

Only L7-GAP-01/02/03/04 are CLOSED; only L7-EXIT-01/02/03/27 are PASS. The other 17 A0 gaps and
25 final release criteria remain unaccepted. **L7-A2+ NOT AUTHORIZED. Stable release/publication
NOT AUTHORIZED. Phase M NOT AUTHORIZED. Phase L NOT CLOSED.**

Report: `docs/governance/phase_l/PHASE_L_L7_A1_DETERMINISTIC_REQUIRED_CI_AND_HISTORICAL_FAILURE_CLASSIFICATION_2026-10-24.md`.
Reconciliation: `docs/governance/phase_l/PHASE_L_L7_A1_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-24.md`.
Evidence: `docs/governance/phase_l/acceptance_runs/l7-a1-20261024T003128Z/`.

## Historical L7-A0 merged state (2026-10-24)

L6 remains **CLOSED** under `PHASE_L_L6_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`.
L7 is **STARTED**. L7-A0 is **OWNER-ACCEPTED AND MERGED** under
`L7_A0_CI_RELEASE_CURRENT_STATE_INVENTORY_AND_GOVERNANCE_CONTRACT_FROZEN`.
Independent re-review disposition is `L7_A0_INDEPENDENT_REVIEW_PASS`; Owner disposition is
`L7_A0_OWNER_ACCEPTED_FOR_MERGE`.

PR #408 normal-merged accepted head `15d601a8ca98c4fd49577d7b1c7f8d038ad2b01f`,
tree `34da9233c4f3acee39afe92c1e8c288d8544ca89`, at merge commit
`37b6a836fd80addfd6a8cf03c3c6f19848b3e143`. Merge parents are prior canonical main
`125188604126bcdbfcfea0f6421eae6a160e9085` and the exact accepted A0 head; GitHub merge verification is valid.

The accepted A0 contract retains 15 L7 obligations, 21 owned gaps / 0 unowned gaps, and the
canonical 29-item L7 exit contract. Default CI remains overall FAIL at 1245 passed / 45 failed /
4 skipped / 5 deselected; expanded evidence remains overall FAIL at 525 passed / 2 historical
assertions. Windows 11 x64 remains the release-blocking Native Tier-1 for L6/L7 under the accepted
prospective supersession; historical L0-D03 remains unchanged.

**L7-A1+ remains NOT AUTHORIZED. Stable release/publication remains NOT AUTHORIZED.
Phase M remains NOT AUTHORIZED. Phase L remains NOT CLOSED.**

Report: `docs/governance/phase_l/PHASE_L_L7_A0_CI_RELEASE_CURRENT_STATE_INVENTORY_AND_GOVERNANCE_CONTRACT_2026-10-23.md`.
Reconciliation: `docs/governance/phase_l/PHASE_L_L7_A0_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-24.md`.
Evidence: `docs/governance/phase_l/acceptance_runs/l7-a0-20261023T164344Z/`.

## Historical L6 closure state ? CLOSED (2026-10-23)

L6 is **CLOSED** under `PHASE_L_L6_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`, following
technical exit `PHASE_L_L6_EXIT_REVIEW_PASS`. L6-A6 is OWNER-ACCEPTED AND MERGED
via PR #406 at normal merge `5a071013a5d0d333f32e1928a4d081904078197a`, tree
`e29ff3fd71805fdeedcd647004e44434ae26f171`; the accepted A6 candidate is
`4bf95ca87211e16e9c53a1a935cf731bdca5ebd3`. Independent review disposition is
`L6_A6_INDEPENDENT_TECHNICAL_REVIEW_PASS`; Owner disposition is
`L6_A6_OWNER_ACCEPTED_FOR_MERGE`.

The accepted exit retains 23/23 L6 criteria PASS, unresolved A0 findings=0,
unresolved A1 gaps=0, P1?P6 PASS, post-A5 product drift=0, exact-six MCP, and L2
as the sole backup/verify/isolated-restore/migration authority. Default CI remains
overall FAIL at 1245 passed / 45 failed / 4 skipped / 5 deselected on both base
and candidate with candidate-only failures=0; expanded validation remains overall
FAIL at 525 passed / 2 unchanged historical L5 scope assertions. Retained A6
limitations remain visible and unchanged.

No L6-A7 is created or authorized. **L7 remains NOT AUTHORIZED. Phase M remains
NOT AUTHORIZED.** Release/signing/publication, image publication, installer work,
and any new product capability remain outside this closure. Phase L itself is not
closed because L7 has not been authorized or completed.

Closure: `docs/governance/phase_l/PHASE_L_L6_OWNER_FINAL_CLOSURE_2026-10-23.md`.
Technical review: `docs/governance/phase_l/PHASE_L_L6_A6_PACKAGING_PORTABILITY_TECHNICAL_EXIT_REVIEW_2026-10-23.md`.
Evidence: `docs/governance/phase_l/acceptance_runs/l6-a6-20261023T141800Z/`.

## Historical L6-A5 merged state (2026-10-23)

L6-A5 is **OWNER-ACCEPTED AND MERGED**. Technical disposition is
`L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_PASS`; independent review is
`L6_A5_INDEPENDENT_TECHNICAL_REVIEW_PASS`; Owner disposition is
`L6_A5_OWNER_ACCEPTED_FOR_MERGE`. P1=PASS, P2=PASS, P3=PASS, P4=PASS,
P5=PASS and P6=PASS.

The accepted runtime/package source is `3707c553497240f6ff0f7e5358301395fd60205a`, tree
`946e765b26b2520f623672dc49a51c913139f44f`. The exact accepted A5 candidate is `32bc480cccdd7eb394062ccfe34a44958fc56bf1`,
tree `041f7c660a3fba40b84d5fbab869c2ee353919ac`. PR #404 normal-merged that exact candidate at
`08bec63ec3d924d2c3b206ecc4fcc017b259ea75`, tree `041f7c660a3fba40b84d5fbab869c2ee353919ac`. Merge parents are prior canonical main
`d5dac702c25e9728db86e9ef32f4fe8185086b89` and the accepted A5 candidate; GitHub merge verification is valid.

Accepted artifact identities remain Native ZIP SHA-256 `6772e8c3550525ff0d952929c7e36cef4833e265936b0009b6d517152ab74e04`, Docker source
image `sha256:2b25c1e54879b0761d3c0a3591236cb2a1f820c1530fee25f643ec93cf962675`, and Docker replacement image
`sha256:98bafa33505e0d5f4c088e58949e388768b21b0a0741f4da5649eff539f91323`. Default CI remains FAIL at 1245 passed / 45 failed /
4 skipped / 5 deselected on both exact base and final candidate, with identical failed-node
sets and candidate-only regressions = 0. The expanded applicability suite remains
525 passed / 2 unchanged historical L5 scope-assertion failures. No acceptance result is
rerun or rewritten by this reconciliation.

Phase L/L6 is **not closed**. L6-A6 technical exit review, L7, Phase M,
installer/release work and image publication remain **NOT AUTHORIZED**. The next bounded
action requires separate Owner authorization for L6-A6.

See `docs/governance/phase_l/PHASE_L_L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_2026-10-23.md`,
`docs/governance/phase_l/acceptance_runs/l6-a5-20261023T132500Z/`, and
`docs/governance/phase_l/PHASE_L_L6_A5_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-23.md`.


## Historical L6-A4 merged state (2026-10-23)

L6-A0 through L6-A4 are OWNER-ACCEPTED AND MERGED. L6-A4 Docker Local Service
Packaging completed under `L6_A4_DOCKER_LOCAL_SERVICE_PACKAGING_COMPLETE`, passed
independent review under `L6_A4_INDEPENDENT_TECHNICAL_REVIEW_PASS`, and was Owner-accepted
under `L6_A4_OWNER_ACCEPTED_FOR_MERGE`. PR #402 normal-merged exact accepted head
`99f756f8f5b0a6582ec47c1c5de390ec6d1f8f9b` at merge commit `85a4351f9be46efeb28794079ed7adfeeae0fc8a`, tree
`1d11660978b1952ef5fe8301fa9a3f6fd0e63e33`. The merge parents are the prior canonical main
`ee316f784831fe684e21fa8d146512d96a888050` and the accepted A4 candidate. GitHub merge verification is valid.

The Docker application payload remains bound to implementation source commit `5a747fad735527f349dfc2760366359ff5da67fd`,
tree `729708fb292565d1414ef432c5723f199eadd6de`. Accepted evidence remains `docs/governance/phase_l/acceptance_runs/l6-a4-20261023T061105Z/`.
Post-merge governance reconciliation is recorded in `docs/governance/phase_l/PHASE_L_L6_A4_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-23.md`.

P6 remains `IMPLEMENTED_A4 / FINAL_ACCEPTANCE_PENDING_A5`; this is not final integrated
P1-P6 portability acceptance. L6-A5, L7, Phase M, installer work and image publication
remain NOT AUTHORIZED. No later phase is implicitly authorized or started by the A4 merge
or by this reconciliation.

## Historical L6-A3 merged state (2026-10-23)

L6-A0, L6-A1, L6-A2 and L6-A3 are OWNER-ACCEPTED AND MERGED. L6-A3 is the
post-incident clean reimplementation of Native Application / Resource Distribution
Packaging using Package C (versioned application bundle plus per-bundle isolated
Python venv). PR #400 accepted exact candidate
`b3792975941957d37f2e4f4470c742e1ce6594e2` and was normal-merged at
`a40141f43f3a1bdeccbab61e67a4a5e161eb8f37`, tree
`84152aeb9b0ded744a6a55a96c0ffc888dd745b7`. The merge commit parents are the
accepted A2 base `911a841b866795e8d0cd83d80b30b34701aa5980` and the accepted A3 candidate.

Technical disposition: `L6_A3_NATIVE_APPLICATION_RESOURCE_DISTRIBUTION_PACKAGING_COMPLETE`.
Independent review: `L6_A3_INDEPENDENT_OWNER_REVIEW_PASS`. Owner disposition:
`L6_A3_OWNER_ACCEPTED_FOR_MERGE`. Current A3 authority remains
`docs/governance/phase_l/PHASE_L_L6_A3_NATIVE_APPLICATION_RESOURCE_DISTRIBUTION_PACKAGING_2026-10-22.md`;
final acceptance evidence is `l6-a3-clean-final-20261023T010756Z`; post-merge
reconciliation is recorded in
`docs/governance/phase_l/PHASE_L_L6_A3_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-23.md`.

Accepted ZIP identity remains `TW-Market-1.0.0-windows-x64.zip`, SHA-256
`14dfd36c61ccf173999836932031304e151d93e9b342482bf3cd3d467b48ff7d`,
333 archive members and 49 locked wheels. Exact upstream embedded-path exceptions
remain limited to eight approved unchanged wheel identities. Default CI remains
FAIL at 1246 passed / 44 failed / 4 skipped / 5 deselected for both same-environment
A2 and A3 candidate, with candidate-only failures = 0.

A1-G07 is CLOSED; A1-G16 is CLOSED_A3. P1/P3 are materially improved but are not
final integrated acceptance; P2/P4/P5 remain PARTIAL. The P6/A4 disposition in
this historical snapshot is superseded by the current status above. No later
phase is started by the A3 merge or by its reconciliation.
Earlier dated L6-A2/A3-candidate prose below is retained as historical entry context
and is superseded by this current block; frozen evidence remains unchanged.

Historical L6-A2 entry authority (superseded above): `docs/governance/phase_l/PHASE_L_L6_A2_NATIVE_INSTALLATION_LIFECYCLE_INTEGRATION_2026-10-21.md`; evidence `l6-a2-20261021T142354Z`. Native packaging, Docker and installer implementation remain NOT AUTHORIZED.

## Current L5 state ? CLOSED (2026-10-21)

L5 is **CLOSED** under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`, following technical exit `PHASE_L_L5_EXIT_REVIEW_PASS`. L5-A7 is OWNER-ACCEPTED AND MERGED via PR #395 at `fea5259f8214aa405ed4017c7e9727bbf6d63ea9`. Owner authority: `USER_CHAT_2026-10-21_ACCEPT_AND_MERGE_L5_A7`. A0-A6 remain Owner-accepted and merged; retained A7 limitations remain visible and unchanged. L6-A0 is OWNER-ACCEPTED AND MERGED via PR #397 at `7ec798d682ac91db776608a5e9a6a98e179dd1ec`; L6-A1 is OWNER-ACCEPTED AND MERGED via PR #398 at `430f280f9c1b4f8d0f387503bb22044214126b39`; L6-A2 is AUTHORIZED and its technical candidate is COMPLETE / Owner acceptance PENDING; L6-A3+, L7 and Phase M remain NOT AUTHORIZED. See `docs/governance/phase_l/PHASE_L_L5_OWNER_FINAL_CLOSURE_2026-10-21.md`.

## Historical L6 entry state (2026-10-21; superseded above)

Phase L5 is CLOSED. Phase L6 is STARTED; L6-A0 is OWNER-ACCEPTED AND MERGED via PR #397. L6-A1 is OWNER-ACCEPTED AND MERGED via PR #398. L6-A2 is AUTHORIZED; technical candidate COMPLETE / Owner acceptance PENDING. L6-A3+ remains NOT AUTHORIZED. Docker and installer implementation remain NOT AUTHORIZED. L7 and Phase M remain NOT AUTHORIZED. Native Tier-1 from L6 onward is Windows 11 x64 only; Windows 10 is not a release-blocking Tier-1 target under Owner authority `USER_CHAT_2026-10-21_WINDOWS11_NATIVE_TIER1_BASELINE_SUPERSESSION`. Historical L0-D03 remains unchanged. See `PHASE_L_L6_WINDOWS11_TIER1_PROSPECTIVE_POLICY_SUPERSESSION_2026-10-21.md` and the L6-A0 inventory record.

A1 contract: `docs/governance/phase_l/PHASE_L_L6_A1_INSTALLATION_IDENTITY_STATE_CONFIGURATION_CONTRACT_2026-10-21.md`. A1 is the accepted frozen contract; the separately authorized A2 implements its Native installation/lifecycle subset. A3+ remains NOT AUTHORIZED.

## Current Phase L handoff (2026-10-20)

L3 is CLOSED under `PHASE_L_L3_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`, following technical exit `PHASE_L_L3_EXIT_REVIEW_PASS`. A0-A6 are Owner-accepted and merged. A6 remains PARTIAL (17 transport-degraded, six HTTP-200, zero deterministic contract drift proven); its one-shot authority is consumed and a second run is prohibited. L4-A0 through A4 are Owner-accepted and merged; A4 merged through PR #373 at `a2dfd7ff7c062257a7c7c8f193fced4f9c707a29`. L4-A5 is Owner-accepted and merged at c8c23e2; L4-A6 is OWNER-ACCEPTED AND MERGED under `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE`, with technical disposition `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS` (PR #375; merge commit `9a3a274df1f2602dced30633ea5fa119bc39d0e6`); L4-A7 technical exit review passed under `PHASE_L_L4_EXIT_REVIEW_PASS`; L4 is CLOSED under `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` after A7 merge through PR #378 at `e184e2b5abfabc4656943d9734e4dc68230a8bbd`; L5 is CLOSED under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`; L5-A1 Owner-accepted and merged under `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_OWNER_ACCEPTED_FOR_MERGE` via PR #382 at `8ff92ca79af821a8641967184a26ee37db69d326`; L5-A2: OWNER-ACCEPTED AND MERGED under `L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_HARDENING_OWNER_ACCEPTED_FOR_MERGE`; L5-A3 is OWNER-ACCEPTED AND MERGED under `L5_A3_SEMANTIC_PROJECTION_LINEAGE_CONFORMANCE_HARDENING_OWNER_ACCEPTED_FOR_MERGE` via PR #386 at `cebc4d16ffa2db8903c72297ba2fdc00e60fb453`; L5-A4 is OWNER-ACCEPTED AND MERGED under `L5_A4_TEST_CATALOG_SKILL_GUIDE_PUBLICATION_INTEGRATION_OWNER_ACCEPTED_FOR_MERGE` via PR #388 at `11691c2eb9a33d2adbcce38fb59a50f822e15284`; L5-A5 is OWNER-ACCEPTED AND MERGED under `L5_A5_REPRESENTATIVE_EXISTING_FAMILY_CONFORMANCE_OWNER_ACCEPTED_FOR_MERGE` via PR #390 at `303e2ba444721f939ce74a5f2c15b0a5bb562a7a`; L5-A6 is OWNER-ACCEPTED AND MERGED under `L5_A6_INTEGRATED_DETERMINISTIC_EXTENSION_CONTRACT_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE` via PR #392 at `7748f18e33a64a912f920c6303f73da67b0ab788`; Owner acceptance record merged via PR #393 at `b7c37d2e6a78c2dce3f446bb118ff6f27f5a6059`; L5-A7 is OWNER-ACCEPTED AND MERGED via PR #395 at `fea5259f8214aa405ed4017c7e9727bbf6d63ea9`; L5 is CLOSED under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; L6 is STARTED; L6-A0 is OWNER-ACCEPTED AND MERGED via PR #397 at `7ec798d682ac91db776608a5e9a6a98e179dd1ec`; L6-A1 is OWNER-ACCEPTED AND MERGED via PR #398 at `430f280f9c1b4f8d0f387503bb22044214126b39`; L6-A2 is AUTHORIZED and its technical candidate is COMPLETE / Owner acceptance PENDING; L6-A3+, L7 and Phase M remain NOT AUTHORIZED.

Phase J and Phase K are **COMPLETE**; do not reopen their acceptance work. Phase K
closed under `PHASE_K_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` with no product
compatibility defect.

Phase L is now **STARTED**. L0 — Production Boundary & Architecture Contract is
**FROZEN** under `PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN`:

`docs/governance/phase_l/PHASE_L_L0_PRODUCTION_BOUNDARY_AND_ARCHITECTURE_CONTRACT_2026-10-13.md`

L0 freezes the D01-D12 product boundary, including the historical Windows 10/11 targets in L0-D03; the current prospective L6+ Tier-1 baseline is Windows 11 x64 only,
Native Windows plus Docker Local Service deployment, machine/user/path/state
portability, application/state separation, configuration precedence, lifecycle UX,
no-silent-migration, backup/restore, and optional Agent integrations. `v1.5.0` is the
provisional stable target; `v2.0.0` is reserved for an explicitly approved breaking
change.

L1-A0 inventory is complete. L1-A1 minimum lifecycle/status/doctor passed
`L1_A1_ACCEPTANCE_REVIEW_PASS`, was Owner-accepted under `L1_A1_OWNER_ACCEPTED_FOR_MERGE`,
and is merged through PR #335. The product entry point remains `python -m scripts.tw_market`
with `start`, `status`, `stop`, and read-only `doctor`; Security Master initialization remains
explicit.

The **Operational Correlation Foundation** passed technical review, was Owner-accepted, and is
merged through PR #336 at `e16303935fef75a38159c5cebfd7b74c37fd33f3`. The merged runtime
provides dedicated `trace_id` propagation across MCP → Local Service → execute-once private
boundaries and a bounded ephemeral diagnostic sink while preserving Audit/Result/authorization
semantics and the exact six-tool MCP surface.

The **Adapter Execution Timing** tranche passed technical review, was Owner-accepted, and is
merged through PR #337 at `ea0f4683e662b8d3f89c032ea94dd1ab139cebe2`. It instruments the
common controlled single/batch adapter callable boundary with monotonic elapsed timing and
bounded diagnostic events only; source transports, canonical artifacts, routing, retry/timeout
policy, and authorization semantics remain unchanged.

The **Bounded Resource Snapshots** tranche passed technical review, was Owner-accepted, and is
merged through PR #338 at `42ca42d8bbe12b591a266e1ea6637a70477a6e22`. It adds
instantaneous best-effort managed-service process memory, application/runtime disk-free
snapshots, and Local Service process-memory event metrics only; no background sampler,
threshold policy, resource-limit enforcement, or governed artifact change was introduced.

The next bounded selection chose **Source Acquisition Timing Coverage** without assigning an A2
name. Implementation and technical review are complete under
`L1_SOURCE_ACQUISITION_TIMING_ACCEPTANCE_REVIEW_PASS`; Owner acceptance is recorded under
`L1_SOURCE_ACQUISITION_TIMING_OWNER_ACCEPTED_FOR_MERGE`; PR #339 is merged at
`b3d6722d174f91da3e9c7cba4cf11e2f1306102b`. Current production source acquisition callables
emit bounded monotonic operational timing while preserving source transport/error semantics.
The frozen I1 live-tested candidate remains unchanged and is wrapped only at the current
production registry boundary. See
`docs/governance/phase_l/PHASE_L_L1_SOURCE_ACQUISITION_TIMING_2026-10-14.md`.

The formal L1 Exit Review passes technically under `PHASE_L_L1_EXIT_REVIEW_PASS` and is
Owner-closed under `PHASE_L_L1_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. **L1 is CLOSED.**

L2 - Replay / Retention / Migration is **CLOSED** under
`PHASE_L_L2_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. L2-A0 current persistence/replay inventory
is complete under `L2_A0_CURRENT_PERSISTENCE_REPLAY_INVENTORY_COMPLETE`; L2-A1 replay semantics
are frozen under `L2_A1_REPLAY_SEMANTICS_CONTRACT_FROZEN`, with R1 clarification
`L2_A1_R1_STATE_CLASSIFICATION_SCOPE_CLARIFICATION_FROZEN`.

L2-A2 - Read-Only Finalized Package Inspector / Replayability Classifier has passed technical
review under `L2_A2_READ_ONLY_REPLAYABILITY_INSPECTOR_ACCEPTANCE_REVIEW_PASS`. Owner acceptance
is recorded under `L2_A2_READ_ONLY_REPLAYABILITY_INSPECTOR_OWNER_ACCEPTED_FOR_MERGE` and merged through PR #343 at `bdd9588bc34ab25af8e22ba7cd7900160a56abf5`.
The tranche is internal only and changes no public HTTP/MCP surface, Mode C behavior,
backup/restore, retention, or migration apply semantics.

L2-A3 - Retention Classification & Policy passed technical review under
`L2_A3_RETENTION_CLASSIFICATION_AND_POLICY_ACCEPTANCE_REVIEW_PASS` and is Owner-accepted under
`L2_A3_RETENTION_CLASSIFICATION_AND_POLICY_OWNER_ACCEPTED_FOR_MERGE` and merged through PR #345
at `378acb454a4e1e4e82e2be14b5957dc7d912f751`.

L2-A4 - Backup Manifest & Verification passed technical review under
`L2_A4_BACKUP_MANIFEST_AND_VERIFICATION_ACCEPTANCE_REVIEW_PASS` and is Owner-accepted under
`L2_A4_BACKUP_MANIFEST_AND_VERIFICATION_OWNER_ACCEPTED_FOR_MERGE` and is merged through PR #347
at `fb2fef0c50c3ee50581bc62af534b36116b332e7`.

L2-A5 - Restore Compatibility & Bounded Restore passed technical review under
`L2_A5_RESTORE_COMPATIBILITY_AND_BOUNDED_RESTORE_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L2_A5_RESTORE_COMPATIBILITY_AND_BOUNDED_RESTORE_OWNER_ACCEPTED_FOR_MERGE`, and is merged through
PR #349 at `97386f756f2dcc6dbf4d3ee7934a41066fa1b0c2`. The tranche remains internal, restores only to
isolated targets, and does not activate state or apply migration.

L2-A6 - Migration & Rollback Lifecycle passed technical review under
`L2_A6_MIGRATION_AND_ROLLBACK_LIFECYCLE_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L2_A6_MIGRATION_AND_ROLLBACK_LIFECYCLE_OWNER_ACCEPTED_FOR_MERGE`, and is merged through PR #351
at `e090ae353cb00d3b1d076cdb40c5a76cf2229d5d`. The tranche uses the verified A4 package as
`SOURCE_A4_BACKUP`, preserves A5 migration classification semantics, and keeps the only current
production migration ID `watchlist-schema-v0-to-v1` as `KNOWN_NOT_IMPLEMENTED`.

L2 is **CLOSED** under
`PHASE_L_L2_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` after technical exit
`PHASE_L_L2_EXIT_REVIEW_PASS`; PR #353 merged at
`b84ba8a4ac4819d115de33e55cf9adf2a5801e00` and PR #354 reconciled final closure.

**Current stop boundary:** Owner-authorized L3 — Source Drift Hardening is
STARTED. L3-A0 inventory is COMPLETE under
`L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_COMPLETE`, passed independent review under
`L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_ACCEPTANCE_REVIEW_PASS`, and is Owner-accepted under
`L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_OWNER_ACCEPTED_FOR_MERGE`; PR #355 merged at
`1983c1d5363fe3253a3c5e556508ba5138163337`. The confirmed TWSE MIS returned-identity gap
was addressed by L3-A1, which passed independent review under
`L3_A1_TWSE_MIS_RESPONSE_CONTRACT_GUARD_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L3_A1_TWSE_MIS_RESPONSE_CONTRACT_GUARD_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #357
at `b2e1908fb5d2e584b38bc354f88df6e121b7b13b`. L3-A2 EOD diagnostic propagation passed independent
technical review under `L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #359 at
`e521a2fcc73ecd40e819a0d51342abcd4a55354c`. L3-A3 Phase G research CSV structural and bounded
attempt-provenance guard passed independent technical review under
`L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_OWNER_ACCEPTED_FOR_MERGE`, and merged through
PR #361 at `ddd023f11a23420c096a5b20022848cfcf900db9`. The reviewer re-ran the 176-case offline gate
with zero external network attempts. L3-A4 H1 composite negative-fixture tranche
passed independent technical review under
`L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #363 at
`ff330f94049adce93c72a9179b4d7b44d297fb2b`. Reviewer verification preserved the test/governance-only scope, reconciled the direct
missing-required-field matrix across P08/P09/P10, and independently re-ran the 199-case guarded
gate with zero external network attempts. No live probe or source acquisition was performed.
L3-A5 passed independent technical review under `L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under `L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #365 at `d2b3be8bafa3ad0eebeec5ffbece1fc6a759b3bd`.
G05 deterministic observation/adjudication is complete; live source recertification remains required.
See `docs/governance/phase_l/PHASE_L_L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_2026-10-15.md`.
See `docs/governance/phase_l/PHASE_L_L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_2026-10-15.md`.
See `docs/governance/phase_l/PHASE_L_L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_2026-10-15.md`.
Recover Phase L from
`docs/governance/phase_l/PHASE_L_CURRENT_STATUS_AND_RECOVERY_INDEX_2026-10-14.md`
and read `docs/governance/phase_l/PHASE_L_L3_A0_SOURCE_DRIFT_SCOPE_AND_INVENTORY_2026-10-15.md`.

The older Phase J readiness section below is historical pre-entry context and is
superseded for current operational status by this closure handoff.

## Phase J readiness preflight (2026-10-05)

Phase I is complete under the final exit closure. Phase J is not started or
authorized. Draft PR #303 is undergoing Owner-authorized Product Intent
Realignment. The original 27-scenario G/H/I inventory remains; its initial
four-blocker interpretation is superseded by
`PHASE_J_READINESS_PREFLIGHT_HOLD_FOR_BOUNDED_CONVERSATIONAL_CORRECTNESS_GAPS`.
Current J-entry predecessors are limited to bounded H1 disposition/suspend-resume
and H2 corporate-action/price-discontinuity correctness. Financial statements
are optional evidence; unproven correction linkage must remain explicitly
unresolved. This governance tranche performs no market GET or activation.
See `docs/governance/phase_j/PHASE_J_GHI_INTEGRATED_READINESS_PREFLIGHT_2026-10-05.md`
and its companion JSON for the exact scenario and acceptance-layer inventories.

## Current I3-A4 stopping point (2026-10-05)

I3-A0 is `GO_PASS`, I3-A1 is `FROZEN_PASS`, and I3-A2-R1 is `PASS`.
I3-A3 is `OWNER_ACCEPTED_INDEPENDENTLY_ACCEPTED_BOUNDED_LIVE_PASS` under
`docs/governance/phase_i/PHASE_I_I3_A3_OWNER_FINAL_ACCEPTANCE_CLOSURE_2026-10-04.json`.
Attempts 1–3 remain historical HOLD outcomes; Attempt 4 is the accepted PASS.
Its single-use live authority is consumed. No further A3 acquisition or
Attempt 5 is authorized or required.

I3-A4 is `OWNER_ACCEPTED_INDEPENDENTLY_ACCEPTED_PRODUCTION_ACTIVATION_PASS` and
closed under final Owner acceptance. Current topology is two active
official sources, one logical same-market route, and two default-runtime
market executor registrations. Governed TWSE date binding is pre-authorization;
Public V3 and evidence V2 are active. This tranche performed no market GETs.
Additional live acceptance was not required. PR #301 merged as
`39e162fa9f0b321b23300b20bfac8ce096646b63`. Phase I final exit review passed;
Phase J is not started or authorized. MCP remains exactly six tools.

Activation ledger:
`docs/governance/phase_i/PHASE_I_I3_A4_BOUNDED_PRODUCTION_ACTIVATION_2026-10-05.json`.

Final Owner acceptance closure:
`docs/governance/phase_i/PHASE_I_I3_A4_FINAL_OWNER_ACCEPTANCE_AND_CLOSURE_2026-10-05.json`.

Phase I exit review and closure:
`docs/governance/phase_i/PHASE_I_FINAL_EXIT_REVIEW_2026-10-05.json`;
`docs/governance/phase_i/PHASE_I_FINAL_CLOSURE_2026-10-05.json`.

## Current I2 production activation boundary (2026-10-01)

I2-A4 production activation is Owner-accepted and merge-authorized.

- Catalog: `index_futures_context` is runtime executable with
  `phase_i_activation_state=selected_route_active`.
- Routing: resolved, approval required, `same_source`, selected
  `phase_i_i2_index_futures_context_executor`; one normal TWSE production route.
- Source authority: one active TAIFEX source; eligible cash targets remain TWSE
  company/common shares. Loading is explicit/optional only, never startup refresh.
- `I2-ROLL-001`: PASS; deterministic rollback target remains
  `7ffbdf7fb102668457b2a15877c10ad7673da9bf`.
- No additional market request was authorized or performed for activation.
- I1 remains active with two routes and three sources; MCP remains exactly six.
- I3-A3 and I3-A4 are Owner-accepted and merged; Phase I exit review passed.
  Phase J is not started or authorized.

Activation evidence:

`docs/governance/phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_CANDIDATE_2026-10-01.json`

`docs/governance/phase_i/PHASE_I_I2_A4_PRODUCTION_ROUTE_ACTIVATION_ACCEPTANCE_LEDGER_2026-10-01.json`

## Status

Date: **2026-10-05**

Baseline main before this documentation-governance consolidation:

`f70c5d8dcd580bbd6c9c66d15dbf76d56ca84c96`

Current workstream:

> **H-ACT-H3 is Owner-accepted. Phase I I1 production activation is
> Owner-accepted and merged. I2-A0/A1/A2/A3 are accepted, and I2-A4 final
> production activation is Owner-accepted with rollback proof. `index_futures_context`
> is production executable on one approval-gated TWSE route backed by one active
> TAIFEX source. I3-A3 bounded-live adapter acceptance is Owner-accepted.
> I3-A4 production activation is Owner-accepted and closed; live acquisition
> was not performed for A4 closure.**

The purpose of this handoff is to let a new human or agent resume without
reconstructing the repository from hundreds of historical milestone documents.

## Most recent accepted runtime milestones

### H-ACT-H1

- PR #244
- selected route: `H1-TPEX-ATTENTION-OPENAPI`
- market: TPEx
- capability: `trading_status_context`
- route-level bounded-live: PASS
- route rollback: PASS
- complete H1 coverage: **not claimed**

### H-ACC-7L

- PR #245
- selected-product full governed E2E: PASS
- workflow run: `35797640831`
- Request -> identity -> preview -> authorization -> execute-once -> live TPEx
  -> Result V3 -> Audit V3 -> AI handoff
- broad crawl/polling/retry storm: none

### H-ACT-V3 preflight

- PR #246
- promotion preflight and exact authority inventory: PASS

### H-ACT-V3 promotion

- PR #247
- merge commit: `f70c5d8dcd580bbd6c9c66d15dbf76d56ca84c96`
- workflow run: `35807933991`
- focused promotion acceptance: 5 passed
- default non-network CI: 1241 passed, 4 skipped, 9 deselected
- actual V3 -> V2 preferred-version rollback rehearsal: PASS
- frozen/source activation containment: PASS

## Current runtime truth

```text
Accepted Requests     V1 / V2 / V3
Preferred Request     V3
Preferred new Result  V3
Preferred new Audit   V3
MCP tools             exactly 6
Phase H active source count  2
Active Phase H routes        H1-TPEX-ATTENTION-OPENAPI
                             H3-TWSE-DEFAULT-BOUNDED
H1 complete coverage         NO
H2 activation                NOT STARTED / INACTIVE
H3 TWSE recent_performance   ACTIVE; H0H-LIVE-003 PASS; H0H-ROLL-004 PASS
H3 TPEX                      BLOCKED / NON-EXECUTABLE
Provider automation         NOT_ESTABLISHED_TERMS_CONFLICTED
Phase I I1 implementation    ACCEPTED
I1 bounded live acceptance   ACCEPTED / PASS
I1-ROLL-001                  PASS
I1 production activation     OWNER_ACTIVATION_ACCEPTED / MERGED
Catalog/Routing              runtime_executable / resolved
selected executor            phase_i_i1_market_state_executor
normal production I1 routes  2 (TWSE + TPEX)
Phase I active sources       3
I2-A0                        PASS_GO (one previously Owner-executed bounded probe)
I2-A1                        SOURCE / EVIDENCE CONTRACT FROZEN_PASS
I2-A2                       OWNER_ACCEPTED / DORMANT OFFLINE IMPLEMENTATION
I2-A3                       OWNER_ACCEPTED / BOUNDED LIVE PASS / MERGE AUTHORIZED
I2 production activation    OWNER_ACTIVATION_ACCEPTED
I2 runtime                  PRODUCTION EXECUTABLE / APPROVAL-GATED
I2 active sources / routes   1 / 1
I2 selected executor        phase_i_i2_index_futures_context_executor
I3-A3                        OWNER_ACCEPTED / BOUNDED LIVE PASS
I3 active sources            2 (TWSE + TPEX)
I3 logical production route  1 (same_market)
I3 runtime market routes    2 (TWSE + TPEX)
I3 A4                        OWNER_ACCEPTED / CLOSED / MERGED
I3 final-closure market GETs 0; additional A4 live acceptance not required
Phase I                      EXIT REVIEW PASS / COMPLETE
```

V1/V2 remain compatibility contracts. Existing persisted artifacts retain their
stored schema version.

## Phase G truth

The accepted PR-D closure proves the initial G1/G2 production slice:

- material disclosures;
- monthly revenue;
- TWSE/TPEX eligible company common-share scope;
- official bounded source acquisition;
- Result/Audit/citation integration.

Primary evidence:

- `docs/acceptance_runs/phase_g_pr_d_closure.json`
- `docs/acceptance_runs/phase_g_pr_d_p0_ledger.json`
- `docs/acceptance_runs/phase_g_pr_d_controlled_live.json`

Do not convert this into a claim that every Roadmap V3.2 Phase G research item
is complete.

## Phase H truth

Primary current evidence:

- `docs/governance/phase_h/PHASE_H_H_ACT_H1_TPEX_ATTENTION_ACCEPTANCE_LEDGER.json`
- `docs/governance/phase_h/PHASE_H_H_ACC_7L_SELECTED_PRODUCT_LIVE_E2E_LEDGER.json`
- `docs/governance/phase_h/PHASE_H_H_ACT_V3_PROMOTION_ACCEPTANCE_LEDGER.json`
- `docs/governance/phase_h/PHASE_H_H_ACT_H3_TWSE_RECENT_PERFORMANCE_ACCEPTANCE_LEDGER.json`
- `docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json`
- `docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json`

Important distinction:

> H-ACT-V3 is closed; the full Roadmap Phase H capability scope is not.

The active H1 product slice is TPEx attention only. H3 is limited to the
Owner-accepted bounded TWSE `recent_performance` route; TPEx H3 remains blocked,
H2 remains inactive, and provider automation permission is not established.
Attempt #2E is valid bounded-live evidence after offline corrected acceptance
verification; its original runner nonzero exit remains recorded as a harness
false negative. No new live execution is required for this closure.

## Current closure and next boundary

The H-ACT-H3 final activation is Owner-accepted for the selected bounded TWSE
`recent_performance` route. The route-specific acceptance ledger records the
technical candidate and its live/rollback evidence. Separately, Owner accepted
the frozen Phase I I1 source contract and authorized a bounded,
production-capable executor candidate for `market_state_context`. The separate
`PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE` gate is accepted PASS under Owner authority;
its ledger is
`docs/governance/phase_i/PHASE_I_I1_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-09-30.json`.
The acceptance used exactly three official GETs (TWSE FMTQIK 1, TWSE breadth 1,
TPEx 1), zero retries; TWSE is governed partial due to preserved date mismatch
and TPEx is complete. The final Owner decision accepts production activation
of the selected I1 market-state route. Current runtime authority has two normal
production routes (TWSE and TPEx) and exactly three active I1 sources.
`I1-ROLL-001` passed. No new market requests were made during final activation
closure. I2-A0/A1 are complete. I2-A2 dormant offline implementation is
Owner-accepted; A3 bounded live acceptance is PASS under the fresh single-GET
Owner authority. I2 runtime is now active under its separately accepted A4
route. I3-A3 is Owner-accepted. At the time of this 2026-10-04 I1 activation
snapshot, I3 production remained inactive; the later I3-A4 activation is
documented in the current handoff section above. The broader Roadmap Phase I
remains incomplete.

I1 timing semantics: acceptance execution/acquisition reference timestamp is
`2026-09-30T01:56:37Z`; each source transport retrieval timestamp is recorded
individually in bounded-live telemetry. Normalized evidence `retrieved_at` uses
the governed execution/acquisition reference timestamp for the I1 v1 contract;
transport telemetry `retrieved_at` is the individual HTTP retrieval observation
time.

## Historical documentation problem already closed

Before this consolidation, repository documentation had multiple competing
eras:

- root/product docs partly current;
- `docs/roadmap/M8_POST_M8C_REVISED_ROADMAP.md` still acted like a current
  roadmap while containing obsolete phase definitions and pre-v1 release prose;
- several operator/reference/architecture pages still described the M5/M6
  product model;
- historical acceptance and reviews correctly preserved old facts but were easy
  to mistake for current state;
- root `AGENTS.md` still described a high-freedom source-discovery project
  rather than the governed product now in the repository.

This consolidation establishes the four-file governance front door:

```text
PROJECT.md   current project/product state
ROADMAP.md   durable Roadmap V3.2 direction and phase scope
HANDOFF.md   current operational stopping point and evidence pointers
AGENTS.md    repository/agent working rules
```

## Resume order

A new agent should read, in order:

1. `PROJECT.md`
2. `ROADMAP.md`
3. `HANDOFF.md`
4. `AGENTS.md`
5. current Catalog/Route authority
6. only then the specific frozen contract/ledger relevant to the task

Do not start by reading hundreds of `docs/reviews/` or `docs/protocol/`
files unless the task requires historical evidence.

## Current allowed next work

I1 production activation has been Owner-accepted and merged after bounded live
acceptance and deterministic rollback proof. Do not repeat live acquisition or
rollback. I2-A0 is PASS_GO and I2-A1 source/evidence contract is FROZEN_PASS.
I2-A2 dormant offline implementation and I2-A3 bounded-live acceptance are
accepted historical stages. I2-A4 production activation is now Owner-accepted
and merge-authorized for PR #299. Its
live ledger is `docs/governance/phase_i/PHASE_I_I2_A3_BOUNDED_LIVE_ACCEPTANCE_LEDGER_2026-10-01.json`; the Owner acceptance / merge closure ledger is
`docs/governance/phase_i/PHASE_I_I2_A3_OWNER_ACCEPTANCE_AND_MERGE_CLOSURE_2026-10-01.json`.
Exactly one TAIFEX GET was used, retry zero, TWSE/TPEx GETs zero. Two target
operations share the acquisition; both are complete, with alignment
not_comparable and currentness unknown. No further live request is authorized.
I3-A3 and I3-A4 are Owner-accepted. I3 production is active; additional live
acquisition was not required. PR #301 is merged; Phase I exit review passed.

## Explicit stop boundary

**Do not repeat I1 live acceptance or rollback, the consumed I2-A3 single GET,
or I3-A3 live acceptance. Preserve accepted evidence. I3-A4 is closed,
Owner-accepted, and merged. Phase I exit review is PASS. Phase J is complete
under the 2026-10-12 closure authority reconciliation; do not run Attempt #7.
Phase K is complete under `PHASE_K_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. Do not repeat the Phase K host matrix for closure. Phase L is started and L0 is frozen under `PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN`. L1 - Runtime Operability is CLOSED under `PHASE_L_L1_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; L2 - Replay / Retention / Migration is CLOSED under `PHASE_L_L2_EXIT_REVIEW_PASS`, with PR #353 merged at `b84ba8a4ac4819d115de33e55cf9adf2a5801e00`. L3 - Source Drift Hardening is CLOSED under `PHASE_L_L3_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; A0-A6 are Owner-accepted and merged and A6 remains PARTIAL with its one-shot authority consumed. L4-A0 through A4 are Owner-accepted and merged; A4 merged through PR #373 at `a2dfd7ff7c062257a7c7c8f193fced4f9c707a29`; L4-A5 is Owner-accepted and merged at c8c23e2; L4-A6 is OWNER-ACCEPTED AND MERGED under `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE`, with technical disposition `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS` (PR #375; merge commit `9a3a274df1f2602dced30633ea5fa119bc39d0e6`); L4-A7 technical exit review passed under `PHASE_L_L4_EXIT_REVIEW_PASS`; L4 is CLOSED under `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` after A7 merge through PR #378 at `e184e2b5abfabc4656943d9734e4dc68230a8bbd`; L5 is CLOSED under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`; L5-A1 Owner-accepted and merged under `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_OWNER_ACCEPTED_FOR_MERGE` via PR #382 at `8ff92ca79af821a8641967184a26ee37db69d326`; L5-A2: OWNER-ACCEPTED AND MERGED under `L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_HARDENING_OWNER_ACCEPTED_FOR_MERGE`; L5-A3 is OWNER-ACCEPTED AND MERGED under `L5_A3_SEMANTIC_PROJECTION_LINEAGE_CONFORMANCE_HARDENING_OWNER_ACCEPTED_FOR_MERGE` via PR #386 at `cebc4d16ffa2db8903c72297ba2fdc00e60fb453`; L5-A4 is OWNER-ACCEPTED AND MERGED under `L5_A4_TEST_CATALOG_SKILL_GUIDE_PUBLICATION_INTEGRATION_OWNER_ACCEPTED_FOR_MERGE` via PR #388 at `11691c2eb9a33d2adbcce38fb59a50f822e15284`; L5-A5 is OWNER-ACCEPTED AND MERGED under `L5_A5_REPRESENTATIVE_EXISTING_FAMILY_CONFORMANCE_OWNER_ACCEPTED_FOR_MERGE` via PR #390 at `303e2ba444721f939ce74a5f2c15b0a5bb562a7a`; L5-A6 is OWNER-ACCEPTED AND MERGED under `L5_A6_INTEGRATED_DETERMINISTIC_EXTENSION_CONTRACT_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE` via PR #392 at `7748f18e33a64a912f920c6303f73da67b0ab788`; Owner acceptance record merged via PR #393 at `b7c37d2e6a78c2dce3f446bb118ff6f27f5a6059`; L5-A7 is OWNER-ACCEPTED AND MERGED via PR #395 at `fea5259f8214aa405ed4017c7e9727bbf6d63ea9`; L5 is CLOSED under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; L6 is STARTED; L6-A0 is OWNER-ACCEPTED AND MERGED via PR #397 at `7ec798d682ac91db776608a5e9a6a98e179dd1ec`; L6-A1 is OWNER-ACCEPTED AND MERGED via PR #398 at `430f280f9c1b4f8d0f387503bb22044214126b39`; L6-A2 is AUTHORIZED and its technical candidate is COMPLETE / Owner acceptance PENDING; L6-A3+, L7 and Phase M remain NOT AUTHORIZED. Recover current Phase L state from `docs/governance/phase_l/PHASE_L_CURRENT_STATUS_AND_RECOVERY_INDEX_2026-10-14.md` before starting a new boundary.**

Roadmap Phase I is Cross-Market & Optional Context. I0, I1 source contract,
and I2-A1 source/evidence contract are frozen; I1 is accepted and active. The
one I2-A0 probe is historical preflight evidence only. I2-A2 dormant offline
implementation is Owner-accepted; A3 bounded live acceptance is PASS. Runtime
is production executable under the accepted I2-A4 route. I3-A3 is separately
Owner-accepted. This paragraph is a historical checkpoint preceding the
2026-10-05 activation; current I3 authority is summarized at the top of this
handoff. The old unused A3 authority is superseded_without_use and the fresh
single-GET authority is consumed. At that historical checkpoint, broader Phase I
was incomplete; the current exit disposition is recorded in the Phase I final
exit review linked above.

## Before any future Phase I work

At minimum:

1. read `ROADMAP.md` Phase I;
2. preserve the completed I3-A0 preflight and A1 frozen contract; do not
   repeat source acquisition under consumed A3 authority;
3. apply the Evidence Value Gate to each candidate evidence family;
4. keep derivatives identity separate from cash-security ISIN identity;
5. preserve explicit/optional bounded loading;
6. preserve accepted I1/I2/I3 evidence; Phase I is closed. That historical
   Phase I closure did not itself authorize Phase J; Phase J was later closed
   separately by the 2026-10-12 authority reconciliation. Future production
   authority changes still require separate authorization.

## Historical-document rule

Do not "fix" accepted historical ledgers to match the current V3 state. A
statement such as "V2 remained preferred" inside an H-ACT-H1 ledger is correct
for that gate's time and must remain intact.

Current-state contradictions belong in current entry-point docs, not by
rewriting history.
