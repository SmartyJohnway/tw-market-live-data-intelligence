---
title: "tw-market-live-data-intelligence — Roadmap V3.2"
version: "3.2"
updated: "2026-09-14"
canonicalized_in_repo: "2026-09-23"
status_reconciled_through: "2026-10-27: L7-A0-A5 Owner-accepted and merged through PR #418; A5 technical/live, independent and merge acceptance PASS; GAP-15 CLOSED; EXIT-19 PASS; post-merge governance reconciliation in progress; A6/A7 NOT AUTHORIZED; ProductVersion 1.5.0 selected/unpublished; stable publication and Phase M NOT AUTHORIZED; Phase L NOT CLOSED"
project: "tw-market-live-data-intelligence"
product_positioning: "Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents"
stable_product_release: "v1.0.0"
stable_release_commit: "e02bcb125999f542308a75f349c212f0ff3fee83"
roadmap_role: "Durable architecture and product roadmap; progress is tracked by checkboxes, not rolling status prose."
tags:
  - tw-market-live-data-intelligence
  - roadmap
  - market-evidence
  - research-evidence
  - mcp
  - ai-agent
  - local-first
  - governance
---

# tw-market-live-data-intelligence

## Current L7-A6-P0 merged state (2026-10-27)

L7-A6-P0 release infrastructure readiness is **PASS**; independent review is **PASS**; Owner merge is **COMPLETE** and `merged: true`.

- merge commit: `32fc28fc33cb19337bf8d8a2d2e857f978b31b4c`
- merge tree: `5d30bd899978fa068d0b89de682a8ce5dcf9a8a2`
- accepted head: `94be7102b046dab6e2a62d3735505402b3a838f6`
- parents: `ddae25ee4c0539edc7f43073708113795a56e58b` and `94be7102b046dab6e2a62d3735505402b3a838f6`
- PR #420 merged normally at `2026-10-27T04:09:39Z`.

Canonical release-blocking CI remains `1895 passed / 0 failed / 4 contracted skips / 20 deselected / 386 guard events / 0 denials / 0 unexpected skips`; Portable validator remains `205 passed / 0 failed`. M6E legacy-route drift and M6G legacy-route drift are both `CLOSED_BY_R1`.

L7-A6 overall acceptance is **NOT_YET**; stable source and artifacts are not frozen. `L7-GAP-16`, `L7-GAP-17`, and `L7-GAP-18` remain **OPEN**. `L7-EXIT-16`, `L7-EXIT-20`, `L7-EXIT-21`, `L7-EXIT-22`, `L7-EXIT-23`, and `L7-EXIT-24` remain **NOT_YET_PASS**. ProductVersion is `1.5.0 selected / unpublished`; published stable is `v1.0.0`.

**A6-R1 is READY_FOR_SEPARATE_OWNER_AUTHORIZATION and NOT_STARTED by this reconciliation.** Its future scope is limited to the additive typed publication manifest, canonical v1.5.0 artifact-set decision, first-party SBOM final-RC binding, release notes/retained-limitations source, and stable-source self-reference avoidance contract. A7 is **NOT_AUTHORIZED**; stable publication is **NOT_AUTHORIZED**; Phase L is **NOT_CLOSED**; Phase M is **NOT_AUTHORIZED**.

## Current L7-A5 merged state (2026-10-27)

L7-A5 is **OWNER-AUTHORIZED AND MERGED**. PR #418 normal-merged accepted head
`70cafb61144afea0f0014563873004c8864822ac`, tree `16677e83c87efd1b7b3440711e527bf877899186`,
at merge commit `a812e212cb710a869289a18b3e7a29c886a43512` on `2026-10-26T16:52:54Z`.
The merge parents are prior canonical main `617ccea728befa2fd3ea7b847665072c0e728f00` and the exact accepted A5 head;
GitHub merge verification is valid and all eight accepted A5 commits remain in ancestry.

A5 technical acceptance, independent acceptance and normal-merge acceptance are **PASS**.
`L7-GAP-15 = CLOSED`; `L7-EXIT-19 = PASS`; the GH2 temporal finding is closed by R5/R5.1/R5.2 + GH5.
ProductVersion remains **1.5.0 selected/unpublished**; published stable remains **v1.0.0**.
Post-merge reconciliation: `docs/governance/phase_l/PHASE_L_L7_A5_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-27.md`.

**A6 and A7 are NOT AUTHORIZED. Stable publication and Phase M remain NOT AUTHORIZED. Phase L remains NOT CLOSED.**
A6 requires a separate Owner authorization after this post-merge reconciliation is independently accepted and merged.

All subsequent dated milestone records are historical; their authorization/status statements describe those milestones only.

## Current L7-A5 technical/live acceptance (2026-10-26)

L7-A0–A4 remain Owner-accepted and merged. L7-A5 technical/live acceptance is
**PASS** and independent acceptance is **PASS**. R5/R5.1/R5.2 consolidated review
is `L7_A5_R5_R5_1_R5_2_CONSOLIDATED_INDEPENDENT_REVIEW_PASS`; fresh GH5 review is
`L7_A5_GH_TEMPORAL_PROVENANCE_LIVE_RECERTIFICATION_5_ACCEPTANCE_REVIEW_PASS`.
The consolidated result is `L7_A5_R5_R5_1_R5_2_AND_GH5_CONSOLIDATED_ACCEPTANCE_PASS`.

Exact accepted implementation input: HEAD `1d87d2b9301e7caf5976fcf4cd0b8ebc98866942`,
tree `843d11de216924ea16fce39e38bdd5248295211c`.
**L7-GAP-15 = CLOSED; L7-EXIT-19 = PASS.**
`L7_A5_GH2_TEMPORAL_PROVENANCE_INVERSION = CLOSED_BY_R5_R5_1_R5_2_AND_GH5`;
historical GH2 temporal failure/final-acceptance block remains unchanged.

A5 Owner merge acceptance is **PENDING**; A5 is **NOT MERGED**.
ProductVersion remains **1.5.0 selected/unpublished**; published stable remains **v1.0.0**.
**A6 and A7 are NOT AUTHORIZED. Stable publication and Phase M remain NOT AUTHORIZED.
Phase L remains NOT CLOSED.** No A6/A7 exit criterion gains PASS here.

Current A5 report: [PHASE_L_L7_A5_FINAL_GOVERNANCE_RECONCILIATION_2026-10-26.md](docs/governance/phase_l/PHASE_L_L7_A5_FINAL_GOVERNANCE_RECONCILIATION_2026-10-26.md).

Repository GH5 historical evidence: [l7-a5-gh5-live-20261026T153216Z](docs/governance/phase_l/acceptance_runs/l7-a5-gh5-live-20261026T153216Z/manifest.json).

Next boundary: Review the exact A5 final governance-sealing candidate. If independently accepted, obtain explicit Owner authorization for push / PR / normal merge. Only after A5 is merged may L7-A6 be separately authorized.

All subsequent dated milestone records are historical; their authorization/status statements describe those milestones only.

## Current L7-A4 merged state (2026-10-25)

L7-A4 is **OWNER-ACCEPTED AND MERGED** under
`L7_A4_PUBLIC_COMPATIBILITY_MCP_SDK_STABLE_VERSION_DECISION_PASS`.
Independent disposition is `L7_A4_INDEPENDENT_TECHNICAL_REVIEW_PASS`, review `5642080353`;
Owner disposition is `L7_A4_OWNER_ACCEPTED_FOR_MERGE`, review `5642097513`.
PR #416 normal-merged accepted head `902febc323b2fd568a2d00c00a18eac24f5ae655`, tree
`d264f509efda2affbf13c3253363e1844651cc17`, at merge commit
`28a22ffc206db425ffefa8e578bf5ef7dcdb1a19`; GitHub merge verification is valid.

ProductVersion **1.5.0 is selected but unpublished**; published stable remains v1.0.0.
Published Local Service v1 compatibility is retained, current v2/exact-six remain supported,
and MCP SDK support is frozen at exact `mcp==1.29.0`. GAP-13 and GAP-14 are closed under
the accepted A4 policy; only EXIT-08/09/10/14/15 gain A4 PASS.
**L7-A5+, stable publication, Phase M and Phase L closure remain NOT AUTHORIZED.**

Report: `docs/governance/phase_l/PHASE_L_L7_A4_PUBLIC_COMPATIBILITY_MCP_SDK_STABLE_VERSION_DECISION_2026-10-25.md`.
Reconciliation: `docs/governance/phase_l/PHASE_L_L7_A4_POST_MERGE_GOVERNANCE_RECONCILIATION_2026-10-25.md`.

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

## Historical L6-A3 merge snapshot (2026-10-23)

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
phase is started by the A3 merge or by this reconciliation.
Earlier dated L6-A2/A3-candidate prose below is retained as historical entry context
and is superseded by this current block; frozen evidence remains unchanged.

## Historical L5/L6 entry snapshot (2026-10-21; superseded above)

L5 is **CLOSED** under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`, following technical exit `PHASE_L_L5_EXIT_REVIEW_PASS`. L5-A7 is OWNER-ACCEPTED AND MERGED via PR #395 at `fea5259f8214aa405ed4017c7e9727bbf6d63ea9`. Owner authority: `USER_CHAT_2026-10-21_ACCEPT_AND_MERGE_L5_A7`. A0-A6 remain Owner-accepted and merged; retained A7 limitations remain visible and unchanged. L6 is STARTED; L6-A0 is OWNER-ACCEPTED AND MERGED via PR #397 at `7ec798d682ac91db776608a5e9a6a98e179dd1ec`; L6-A1 is OWNER-ACCEPTED AND MERGED via PR #398 at `430f280f9c1b4f8d0f387503bb22044214126b39`; L6-A2 is AUTHORIZED and its technical candidate is COMPLETE / Owner acceptance PENDING; L6-A3+, L7 and Phase M remain NOT AUTHORIZED. See `docs/governance/phase_l/PHASE_L_L5_OWNER_FINAL_CLOSURE_2026-10-21.md`.


Historical L6-A2 entry authority (superseded above): `docs/governance/phase_l/PHASE_L_L6_A2_NATIVE_INSTALLATION_LIFECYCLE_INTEGRATION_2026-10-21.md`; evidence `l6-a2-20261021T142354Z`. Native packaging, Docker and installer implementation remain NOT AUTHORIZED.

> **Historical Phase L entry boundary (2026-10-21; superseded above):** L5 is Owner-closed. L6 is STARTED; L6-A0 is OWNER-ACCEPTED AND MERGED via PR #397. L6-A1 is OWNER-ACCEPTED AND MERGED via PR #398. L6-A2 is AUTHORIZED; technical candidate COMPLETE / Owner acceptance PENDING. L6-A3+, Native packaging, Docker/installer implementation, L7 and Phase M remain NOT AUTHORIZED. Native Tier-1 from L6 onward is Windows 11 x64 only under the prospective Owner policy; historical L0-D03 remains unchanged. See the L6-A0 governance record and Windows 11 policy supersession record.

A1 contract: `docs/governance/phase_l/PHASE_L_L6_A1_INSTALLATION_IDENTITY_STATE_CONFIGURATION_CONTRACT_2026-10-21.md`. A1 is the accepted frozen contract; the separately authorized A2 implements its Native installation/lifecycle subset. A3+ remains NOT AUTHORIZED.

# Roadmap V3.2 — Post-V1.0 Stable Release & Pre-Phase-G Reconciliation

> **版本日期：2026-09-14**  
> **產品穩定版：`v1.0.0`**  
> **Roadmap 版本與產品版本彼此獨立。**  
> **本文件不是 Git / release / deployment 狀態日誌。**  
> **未來一般進度更新只需由 Owner 將 `[ ]` 改為 `[x]`；不需要因 milestone 完成而重寫 Roadmap。**

> **Current repository reconciliation — 2026-10-13:** This file remains the
> canonical Roadmap V3.2 authority; durable phase scope is unchanged. Broader
> Phase G and Phase H scope remains incomplete. Phase I's accepted I1, I2, and
> I3 capabilities satisfy its minimum optional cross-market and spot/derivatives
> descriptive-context intent under the I0 Evidence Value Gate; deferred
> candidates are not phase-exit prerequisites. Phase I is checked complete by
> the final exit review. Phase J is checked complete by the 2026-10-12
> closure authority reconciliation. Post-Phase-J portability/runtime hygiene
> (PR #327), K0 Charter PR #328, K1 Scenario Set PR #329, K2-A PR #330, and the
> K1-05 finalized stale-package supplement PR #331 are merged. K2-A is complete
> with all eight deterministic assets and no preparation gaps. K2-B has completed
> its initial three-host pilot: Hermes Agent and ChatGPT are `NATIVE_PASS`;
> Antigravity CLI is `PARTIAL_HOST_LIMITATION` / `HOST_LIMITATION`; host evaluation
> count is three, product compatibility defects found remain zero, and no fresh
> market/source acquisition was introduced. Phase K is complete under
> `PHASE_K_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. Phase L is now STARTED. L0 —
> Production Boundary & Architecture Contract is frozen under
> `PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN`; the next authorized boundary is
> L1 — Runtime Operability.

---

# 0. V3.2 的角色與使用規則

## 0.1 為什麼從 V3.1 升為 V3.2

Roadmap V3.1 建立了目前仍有效的核心產品哲學：

```text
AI
→ 理解使用者
→ 產生 Unified Market Evidence Request

TW-Market
→ Validate
→ Resolve Identity
→ Plan / Preview
→ Explicit Authorization
→ Execute Once
→ Result / Audit / AI Handoff

AI
→ 閱讀完整 evidence
→ 分析、比較、解釋、持續對話
```

V3.1 之後，工程實際完成了：

```text
Unified Workbench vertical closure
Local Service
Minimal six-tool MCP
Real Agent Closed-Loop Acceptance
Pre-Phase-F portability / identity realignment
Persistent Watchlist
Workbench integration
V1 feature closure
v1.0.0 stable release
MCP distribution / registry publication
```

其中最重要的架構演進不是「多了一個 release」，而是：

```text
Security Master
從 project-private runtime dependency
正式升格為 installation-local Taiwan Market Identity Service

durable cash-security identity
正式固定為 ISIN

fresh install
正式支援 NOT_INITIALIZED

Candidate B
不再是新 installation 的 production requirement
```

因此 V3.2 不是推翻 V3.1，而是：

> **把 V3.1 已落地的產品 contract、M8R-08G 的 portability / identity contract、Phase F closure 與 V1 stable release 整合成新的長期 Roadmap authority。**

## 0.2 Roadmap 不再追蹤會快速過期的狀態

V3.2 不再維護：

```text
CURRENT NEXT
CURRENT AUTHORIZED
NOT AUTHORIZED
current main SHA
current PR
current external directory review
current deployment queue
```

這些狀態由 Git、GitHub、release metadata、acceptance records、HANDOFF / PROJECT operational records 負責。

Roadmap 只回答：

```text
我們已經定案了什麼？
接下來想把產品做到什麼程度？
每個 Phase 必須做到哪些內容？
哪些邊界不可破壞？
什麼條件成立才算完成？
```

## 0.3 Checkbox 規則

Phase 與主要 milestone 使用：

```text
[x] completed
[ ] not yet completed
```

Owner 完成 milestone 後直接打勾即可。單純 `[ ] → [x]` 不需要升 Roadmap 版本。

只有下列情況才需要考慮 `V3.2 → V3.3`：

- 核心產品 contract 改變
- Phase scope 實質重排
- Identity authority 改變
- AI / runtime responsibility boundary 改變
- 新增會改變整體產品方向的大型 capability family
- Automation / execution safety contract 實質改寫

## 0.4 歷史文件處理原則

以下文件保留，不刪、不改寫：

```text
tw-market-live-data-intelligence_Roadmap_V3.1_2026-08-11.md

Base on Roadmapv3.1
Pre-Phase-F Portability,
Taiwan Market Identity Service
& Skill Realignment Plan.md
```

定位：

```text
historical architecture / planning evidence
```

第二份 Pre-Phase-F 文件中的已接受核心裁決已濃縮吸收進 V3.2。V3.2 成為後續規劃的 current Roadmap authority。

---

# 1. Frozen V1 Product Contract

以下內容視為 V1 已接受產品 contract。後續 Phase 原則上只做：

```text
extend
enrich
harden
evaluate
orchestrate
```

不得重新發明第二套核心 contract。

## 1.1 AI 與 TW-Market 的責任分界

### AI 負責

```text
理解自然語言與對話上下文
判斷是否需要呼叫 TW-Market
選擇 targets
選擇 data_needs
決定時間範圍
必要時向使用者追問
產生 Unified Market Evidence Request
閱讀完整 Unified Result
區分 observations / derived / missing / stale
整合不同 evidence family
分析、比較、解釋
生成使用者需要的研究報告
```

### TW-Market 負責

```text
request schema validation
canonical identity resolution
capability validation
resource bounds
deterministic planning
preview
explicit authorization boundary
source / route selection
bounded execute-once
deterministic calculations
currentness / timing semantics
coverage
fallback / missing evidence
citations
lineage
auditability
fail-closed behavior
```

### TW-Market 不負責

```text
建立第二套自然語言 intent classifier
取代 AI 理解使用者
替 AI 主觀挑選「最值得看」的證據
在 canonical result 中產生買賣建議
預測價格
執行交易
管理 broker credentials
```

核心原則：

> **我們不需要教程式理解使用者；我們需要讓 AI 能安全、明確、可稽核地使用程式。**

## 1.2 Canonical AI-facing contract

保留單一 Unified contract family：

```text
Unified Market Evidence Request
Canonical Preview
Unified Result
Capability Catalog
```

後續 Research Evidence 原則上應：

```text
extend data_needs / result sections
```

而不是建立第二套 competing AI-facing request language。

如果未來研究資料需要新的 subordinate schema，可以新增 evidence-family contract；但 AI-facing request authority 仍以 Unified Request 為核心。

## 1.3 Product workflow

```text
Mode A
Inspect / Validate

Mode B
Preview / Authorize / Execute Once

Mode C
Result / Audit / AI Handoff
```

完整使用者流程：

```text
Natural Language
→ AI
→ Unified Request
→ Validate
→ Preview
→ explicit confirmation / authorization
→ Execute Once
→ Result
→ Audit reference
→ AI Handoff
→ AI analysis / report
```

## 1.4 Six-tool MCP contract

V1 正式 MCP tool surface 固定為六個：

```text
1. market_describe_capabilities
2. market_validate_request
3. market_preview_request
4. market_read_result
5. market_export_ai_handoff
6. market_fetch_evidence
```

原則：

```text
no seventh persistent-watchlist mutation tool in V1
no MCP-only planner
no MCP-only request schema
no MCP-only result vocabulary
```

未來若真的需要新增 MCP tool：

> 必須先證明現有六工具無法在不扭曲語意的情況下完成新 capability，並以新的 Roadmap / contract decision 明確處理。

## 1.5 Execution safety contract

不可退讓：

```text
no trading
no order routing
no broker credential handling

no silent persistent mutation
no startup market fetch
no hidden full-market scan
no default polling
no default scheduler
no background refresh by default

preview != authorization
authorization != execution
execution must be bounded
execution must be explicit
fixture never silently becomes production authority
missing authority fails closed
```

## 1.6 Complete bounded evidence principle

正式原則：

> **Exhaustive within the authorized request scope.**

Authorized scope 由：

```text
targets
data_needs
time scope
supported market
resource bounds
authorization
```

共同決定。

範圍內應盡可能完整輸出：

```text
canonical observations
deterministic derived metrics
source
observed / published / effective timing
currentness
coverage
missing evidence
fallback
caveats
citations
lineage
audit references
```

Raw transport payload 不等於 AI context。Raw artifacts 可保留為 audit evidence、hash-bound reference、replay / verification material。

---

# 2. Frozen Identity, Portability & Persistence Contract

## 2.1 Taiwan Market Identity Service

Security Master 正式定位：

```text
Taiwan Market Identity Service
```

`tw-market-live-data-intelligence` 是主要 consumer，但不應成為唯一 consumer。

可服務未來：

```text
Market Evidence
Research Evidence
Persistent Watchlist
Portfolio consumers
ETF tools
Backtesting
Screening
Corporate Actions
Alert / monitoring consumers
other Taiwan market projects
AI / Agent Skills
```

## 2.2 Identity 三層模型

### Instrument Primary Identity

對受支援的台灣 cash-market securities：

```text
Instrument Primary Identity = ISIN
```

不得另外發明 custom permanent UUID 或 parallel durable security ID。

### Listing / Routing Identity

```text
market + security_code
```

例如：

```text
TWSE:2330
TPEX:6488
```

這是 current listing identity / routing identity，不是永久 instrument identity。

### Human-facing identity

```text
current name
historical name
aliases
English name
common shorthand
```

皆屬 metadata，不得作 durable primary key。

## 2.3 Knowledge universe 與 execution universe 分離

```text
identity known
≠
execution supported
```

Security Master 可以知道某 instrument 存在；Market Evidence runtime 可以仍然 `execution_eligibility = unsupported`。

不得因 identity knowledge 擴大，就自動擴張 execution scope。

## 2.4 Successor identity migration

若 corporate-action evidence 證明：

```text
Old ISIN
→ New ISIN
```

Persistent consumer 不得 silent rewrite。

必須：

```text
IDENTITY_MIGRATION_REVIEW_REQUIRED
```

使用者決定追蹤 successor 或保留原 instrument reference。

## 2.5 Installation-local Security Master release

Fresh installation：

```text
Security Master = NOT_INITIALIZED
```

這是合法 product state，不是 corruption。

依賴 identity authority 的操作應：

```text
FAIL CLOSED
→ SECURITY_MASTER_NOT_INITIALIZED
```

不得 fixture fallback、hidden network acquisition，亦不得把 FileNotFoundError leakage 當 product semantics。

## 2.6 Local release lifecycle

```text
BUILDING
→ CANDIDATE
→ QUALIFIED
→ ACTIVE
→ RETIRED
```

失敗：

```text
CANDIDATE
→ REJECTED
```

Production activation 必須 qualified、hash-bound、atomic、fail-closed。

## 2.7 Runtime consistency

保留：

```text
PROCESS_LIFETIME_IMMUTABLE_SELECTION
```

典型更新：

```text
build
→ qualify
→ seal
→ atomic active pointer swap
→ controlled restart
→ new process loads new ACTIVE release
```

不要求複雜 hot reload。

## 2.8 Candidate B 的永久定位

Historical Candidate B：

```text
historical development / acceptance evidence
regression provenance
audit reference
```

新 installation：

```text
不得要求 Candidate B
不得 copy Candidate B 作 production bootstrap
不得 fresh reprobe 後聲稱等價於 Candidate B
```

每個 installation 建立自己的 local Security Master Release。

## 2.9 Persistent Watchlist contract

Persistent Watchlist 的 durable reference：

```text
ISIN
```

Display / audit snapshot 可保留：

```text
name
market
security_code
resolved_under_release_id
```

Runtime execution：

```text
current ACTIVE Security Master Release
→ current routing projection
```

治理要求：

```text
installation-local persistence
immutable revisions
current projection
expected_version optimistic concurrency
preview → commit
no conversation-local target silently persists
no silent successor migration
```

V1 bounds：

```text
max 32 lists
max 500 entries per list
```

---

# 3. Frozen Local-First Product Boundary

## 3.1 Local-first

產品核心維持：

```text
local service
local persistence
local Security Master
explicit bounded network acquisition
MCP / UI reuse same service/runtime semantics
```

Local-first 不代表 offline-only，而是：

> **execution authority、state、identity、authorization 與 audit 預設由 installation 自己掌握。**

## 3.2 Workbench authority

Canonical Workbench：

```text
/workbench/
```

Compatibility surface：

```text
/workbench/mode-a/
→ compatibility redirect only
```

Simple Request Builder 為主要 UX；Advanced JSON 保留為完整 contract surface。

## 3.3 Distribution 不應成為 feature blocker

V1 public distribution 可包含 GitHub Release、MCP package、Official MCP Registry、third-party directories、container introspection、host compatibility。

但 external directory approval、registry ranking、social promotion、download count 不應阻塞後續產品 Phase。

---

# 4. Completed Product Foundation

# [x] Phase A — Governed Evidence Core

### 已定案內容

```text
official market evidence sources
TWSE / TPEx / TAIFEX source families
currentness semantics
source lineage
normalized evidence
partial / missing disclosure
fail-closed source behavior
```

### 預期成果 — 已達成

> 建立「資料從哪裡來、什麼時間、能不能用、缺什麼」的 governed evidence foundation。

# [x] Phase B — AI Guide & Portable Skill Baseline

### 已定案內容

```text
AI usage guide
Skill when-to-call semantics
facts / derived / assumptions / missing separation
source / currentness reading rules
portable Skill source packages
```

### 預期成果 — 已達成

> AI 不只會「叫工具」，而是知道何時該叫、如何建立 Request、如何閱讀 evidence。

# [x] Phase C — Unified Contract & Runtime

### 已定案內容

```text
Unified Request
Capability Catalog
Canonical Preview
Unified Result
deterministic planning
authorization binding
execute-once orchestrator
Result + separate Audit
```

### 預期成果 — 已達成

> Backend contract 成為單一、可驗證、可重用的 evidence execution chain。

# [x] Phase D — Unified Workbench

### 已定案內容

```text
Mode A Validate
Mode B Preview
Mode B Authorize
Execute Once
Mode C Result / AI Handoff
localhost-only operator workflow
```

### 預期成果 — 已達成

> Human operator 不依賴 MCP 也能完成完整 evidence journey。

# [x] Phase E — Local Service, MCP & Real-Agent Closed Loop

### 已定案內容

```text
local-first service layer
six-tool MCP
same canonical contracts
same execution boundary
real-agent acceptance
TWSE
TPEx
partial success
identity ambiguity
source failure
TAIFEX boundary
stale/currentness
```

### 預期成果 — 已達成

> AI Agent 可透過 MCP 完成與 Workbench 相同語意的 evidence closed loop。

# [x] Phase E-P — Portability, Identity Service & Skill Realignment

### 已定案內容

```text
fresh clone portability
NOT_INITIALIZED
installation-local Security Master Release
qualification
atomic activation
rollback semantics
ISIN durable identity
listing history
alias history
successor migration review
portable Skill realignment
dependency reproducibility
Candidate B runtime dependency removal
```

### 預期成果 — 已達成

> Repository 不依賴開發者原電腦的 private runtime payload；新 installation 可以自己建立 identity authority。

# [x] Phase F — Persistent Watchlist & Productization

### 已定案內容

```text
persistent Watchlist
durable ISIN references
immutable revisions
optimistic concurrency
preview → commit
Workbench integration
explicit persistence
```

### 預期成果 — 已達成

> TW-Market 從 conversation-local evidence engine 進化成具 installation-local durable user state 的產品。

# [x] V1 Release Gate — Stable Productization

### 已定案內容

```text
V1 feature complete
stable release freeze
release validation
v1.0.0
MCP distribution
registry publication
public product front door
```

Stable release anchor：

```text
v1.0.0
commit:
e02bcb125999f542308a75f349c212f0ff3fee83
```

### 預期成果 — 已達成

> V1 不只是 repository 中的一組功能，而是可以被第三方取得、安裝、辨識與驗證的正式產品版本。

---

# 5. Future Product Strategy

V1 之後的主軸不再是「做更多 quote API」。

目標是逐步進化成：

> **Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents**

核心能力應回答：

```text
Who is this instrument?
What officially happened?
What market evidence exists?
How current is it?
What is missing?
What changed?
How does this compare to recent history?
What disclosures / fundamentals are relevant?
What official evidence supports the answer?
Can another AI consume this safely?
```

而不是直接回答：

```text
Should I buy?
Will the price rise?
Which stock will outperform?
Can you trade it for me?
```

# [ ] Phase G — Research Evidence Expansion

## G.0 Phase Goal

將 V1 的 `Market Evidence` 擴張為 `Market + Official Research Evidence`。

讓 AI 不只知道「現在市場發生什麼」，還能取得：

```text
公司正式揭露了什麼
近期營運與財務狀況是什麼
哪些官方文件支持這些事實
```

## G.1 Official Disclosure Evidence

需要做到：

```text
TWSE listed company material information
TPEx listed company material information
publication timestamp
company / instrument binding
announcement category
title
official source URL / source identity
raw evidence reference
normalized evidence record
amendment / correction semantics
```

第一優先資料族：重大訊息、重要公告、公司正式揭露事件。

要求：

```text
official source first
published_at preserved
observed_at preserved separately
company code must resolve through Identity Service
historical / current retrieval semantics must be explicit
duplicate / corrected disclosure handling must be deterministic
```

不得只抓新聞標題冒充重大訊息、用搜尋引擎摘要取代 official disclosure、把 AI 自動摘要寫回 canonical fact。

## G.2 Fundamentals & Periodic Operating Evidence

第一階段候選：

```text
monthly revenue
income statement
balance sheet
selected official financial statement fields
EPS / operating result where source semantics are clear
dividend distribution where relevant
```

每一筆資料必須保留至少：

```text
reporting period
period type
publication / filing time if available
currency
unit
consolidated / standalone semantics
industry-specific statement family
revision / restatement status
source
lineage
```

不得把 monthly、quarterly、annual、TTM、single-quarter、YTD 混為同一數值語意。

## G.3 Research Evidence Contract

Phase G 必須先建立 research evidence family contract。

原則：

```text
new research capability
→ extend Unified data_needs
→ project into Unified Result
```

而不是建立第二套 AI request language。

Research Evidence 至少需要：

```text
evidence_family
instrument identity
source authority
effective period
published time
observed time
currentness class
normalized facts
raw evidence reference
citation
missing / partial semantics
```

## G.4 Research Evidence Bundle

建立一個適合 AI 研究使用的完整 evidence projection：

```text
Research Evidence Bundle

├─ identity
├─ current market evidence
├─ official disclosures
├─ periodic operating evidence
├─ fundamentals
├─ currentness matrix
├─ missing evidence
├─ caveats
├─ citations
└─ audit references
```

這個 Bundle 是 AI report input，不是 AI-written investment report。

## G.5 Governed Research Orchestration

AI 可以要求：

```text
current market evidence
+ latest material disclosures
+ latest monthly revenue
+ selected financial statements
```

TW-Market deterministic 地 validate、plan、preview、authorize、fetch、normalize、package。

不能變成 unbounded web search、random crawler、general-purpose news agent。

## G.6 Phase G Acceptance

至少驗證：

```text
TWSE company research
TPEx company research
multi-target research
material disclosure available
no recent disclosure
corrected / duplicate disclosure
monthly revenue
quarterly statement
industry-specific financial schema
partial source failure
stale source
publication-time ambiguity
identity mismatch
unsupported evidence family
```

### Phase G 預期成果

完成後，AI 應可以安全處理類似：
> 「幫我研究 2330 最近發生什麼，包含目前行情、最近重大訊息、最新月營收與最近一期主要財務資訊，並把資料日期與缺漏講清楚。」

輸出必須 official-evidence-grounded、time-aware、citation-ready、missing-aware，而不是投資建議。

# [ ] Phase H — Interpretation & Historical Reference

## H.0 Phase Goal

解決：

> **資料本身正確，但 AI 因缺少市場制度、corporate action 或歷史基準而解讀錯誤。**

Phase H 是 interpretation safety，不只是附加資料。

## H.1 Regulatory / Trading Status Context

需要納入：

```text
注意股票
處置股票
變更交易
暫停 / 恢復交易
交易限制
其他會影響 quote interpretation 的 official status
```

每個狀態必須保留：

```text
status type
effective from
effective to if known
official reason / condition
source
published_at
observed_at
```

AI 必須能區分 ordinary market movement 與 market-supervision / restriction context。

## H.2 Corporate Action Interpretation

第一階段至少：

```text
cash dividend
stock dividend
ex-right
ex-dividend
capital reduction
split / consolidation where official evidence exists
capital increase effects
reference-price events
```

核心：

```text
raw close-to-close price change
≠
economic interpretation
```

若存在 corporate action，reference-price context 必須揭露。

不得在 corporate action unresolved 時直接產生一般「暴跌 / 暴漲」描述。

## H.3 Recent Historical Reference Baseline

最小 baseline：

```text
5D price range
20D price range
5D average volume
20D average volume
current position in range
current volume vs average
valid observation count
official date range
missing trading-day semantics
```

原則：descriptive context only，不是 technical indicator engine、strategy engine、backtester。

## H.4 Adjustment / Discontinuity Safety

若歷史期間跨越 ex-right、ex-dividend、capital reduction、split 或其他 material price-basis discontinuity，系統必須 detect、explain、adjust if governed method exists，否則 fail closed / caveat。

不得用 unresolved raw discontinuity 產生普通 return interpretation。

## H.5 Unified Quote Interpretation Context

Phase H 最終應能輸出：

```text
quote
+ regulatory status
+ corporate action context
+ reference-price context
+ recent baseline
+ caveats
```

作為 Unified Result 的 optional interpretation section。

### Phase H 預期成果

AI 能回答：

> 「今天這個跌幅到底代表市場下跌，還是除息／減資等價格基準改變？今天成交量相對最近 20 天到底大不大？」

並且不需要靠模型猜。

# [x] Phase I — Cross-Market & Optional Context

## I.0 Phase Goal

提供：

> **只有在研究問題真的需要時才載入的市場背景。**

不把 Unified Result 變成資料百科全書。

## I.1 Evidence Value Gate

任何新 evidence family 在正式加入前必須回答：

```text
1. 是否有官方或足夠可信來源？
2. 是否直接改善 AI interpretation？
3. timing semantics 能否誠實定義？
4. normalization 是否不需主觀猜測？
5. missing 時是否會造成重大誤解？
6. 應該 default load 還是 optional load？
7. 是否容易誘發過度投資推論？
8. storage / network / latency cost 是否合理？
```

未通過：`DO NOT ADD`。

## I.2 Spot–Derivatives Descriptive Context

候選：

```text
spot market state
index futures
options
settlement references
open interest
put/call ratio
institutional futures/options positions
contract adjustment
```

必須揭露：

```text
spot observed time
derivatives observed time
settlement date
statistics frequency
contract identity
timing alignment status
```

禁止 leading-signal claim、prediction、manipulation claim、automatic bull / bear label。

## I.3 Derivatives Identity Boundary

Cash security 使用 ISIN-primary identity；不得強行套到 futures series、options series、expiring contracts。

Phase I 必須建立或重用清楚的 derivatives contract identity semantics，而不是污染 cash-market identity contract。

## I.4 Optional Equity-Market Context Candidates

候選 evidence family：

```text
market breadth
advance / decline counts
turnover concentration
industry classification / industry context
institutional investor flows
margin financing
short selling
securities lending
day-trading statistics
ETF composition / relationship
index constituent relationships
fund size / beneficiary context
```

每一項都必須先過 Evidence Value Gate。

## I.5 Default Result Minimalism

Phase I 不能導致每次查單一標的就自動抓所有 TAIFEX、融資融券、ETF、三大法人與市場寬度。

應維持 explicit / AI-selected data_needs 與 bounded optional loading。

### Phase I 預期成果

AI 在需要時可以得到：

> 「這個現貨變動在期貨、選擇權、市場寬度、籌碼或 ETF 關係背景下是什麼樣子？」

但 canonical evidence 不會直接宣告 bullish、bearish、leading 或 manipulated。

# [x] Phase J — Integrated Research Acceptance

## J.0 Phase Goal

Phase J adds no new product capability。

它是：

> **Market + Research + Interpretation 的完整 acceptance gate。**

## J.1 Golden Research Scenarios

建立 governed scenario suite，至少涵蓋：

```text
normal TWSE
normal TPEx
multi-target
current market evidence
official EOD
material disclosure
no material disclosure
corrected disclosure
monthly revenue
financial statements
attention / disposition
suspend / resume
ex-dividend
ex-right
capital reduction
reference-price discontinuity
5D / 20D baseline
TAIFEX context
timing mismatch
partial success
stale
missing
source failure
identity ambiguity
unsupported identity
authorization refusal
resource bound
```

## J.2 Acceptance Layers

至少：

```text
contract fixture
deterministic unit
integration
service API
Workbench
MCP
fresh-install
real bounded network
real AI / agent
```

不是每個 scenario 都要每層完整重跑；但必須建立可追蹤的 coverage matrix。

## J.3 Golden Expected Semantics

Acceptance 不以文字完全一致判斷。

應檢查：

```text
correct identity
correct source
correct period
correct currentness
correct missing
correct partial
correct corporate-action handling
correct authorization
correct bounded execution
correct citations
correct no-trading boundary
```

## J.4 Regression Authority

Golden scenarios 應成為 new source、new evidence family、new MCP version、new agent host、new release 的 regression baseline。

### Phase J 預期成果

可以合理宣稱：

> **TW-Market 不只會抓資料；它能在主要台灣市場研究情境下維持一致、可驗證的 evidence semantics。**

# [x] Phase K — Multi-Agent Compatibility & Evaluation

### Current entry — Phase K COMPLETE (2026-10-13)

K0, K1, K2-A, and the K1-05 finalized stale-package supplement are merged. K2-A
provides deterministic assets for all eight K1 scenarios with no preparation gaps.
K2-B completed the initial three-host pilot under
`docs/governance/phase_k/PHASE_K_K2B_SMALL_MULTI_HOST_PILOT_2026-10-13.md` and
`docs/governance/phase_k/PHASE_K_K2B_INITIAL_HOST_OBSERVATIONS_2026-10-13.md`.
Hermes Agent and ChatGPT are `NATIVE_PASS`. Antigravity CLI remains
`PARTIAL_HOST_LIMITATION` / `HOST_LIMITATION`; this is a non-blocking host limitation,
not a core product defect. Host evaluation count is three, product compatibility
defects found remain zero, and no fresh market/source acquisition occurred.
Final adjudication passed and Owner accepted closure under
`PHASE_K_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`, recorded in
`docs/governance/phase_k/PHASE_K_FINAL_OWNER_ACCEPTANCE_AND_CLOSURE_2026-10-13.md`.
**Validate interoperability, not behavioral conformity.** Phase K is complete.

## K.0 Phase Goal

驗證：

> **不同 AI / Agent 是否能正確使用相同 TW-Market contract。**

不是比較哪個模型投資建議比較準，而是比較 tool-use correctness、protocol adherence、evidence interpretation、safety behavior。

## K.1 Agent Evaluation Dimensions

至少：

```text
是否知道何時需要 TW-Market
是否產生合法 Unified Request
是否選擇合理 data_needs
是否正確處理 identity
是否先 Preview
是否尊重 authorization
是否理解 execute-once
是否理解 partial
是否理解 stale/currentness
是否揭露 missing
是否正確讀 citations
是否會把 full_success 說成 realtime guarantee
是否會產生 unsupported trading claim
```

## K.2 Tool / Protocol Compatibility

測試：

```text
MCP tool discovery
tool schema interpretation
tool-call sequencing
structured result handling
large result handling
timeout behavior
host confirmation behavior
transport differences
```

Agent / Host 名單可以隨時演進。Roadmap 不把任何單一 vendor 永久寫成 mandatory。

候選：ChatGPT、Claude、Gemini、GitHub Copilot、Hermes、OpenCode、other MCP-capable agents。

## K.3 Compatibility Matrix

產出 Agent Compatibility Matrix。

每個 host 至少標記：

```text
transport support
six-tool discovery
Validate
Preview
Execute Once
Result
AI Handoff
large-output behavior
confirmation semantics
known limitations
```

## K.4 No Host-Specific Core Fork

若某個 Agent 有限制，先做 adapter / packaging / documentation。

不得輕易修改 canonical result、增加 competing tool contract、破壞 local-first semantics，只為迎合單一 host。

### Phase K 預期成果

TW-Market 可以被描述為：

> **agent-portable evidence service，而不是只對單一模型調教成功的專案。**

# [ ] Phase L — Production Hardening & Extension Architecture

### Current entry - L4 security/resource boundary inventory (2026-10-17)

L3 is CLOSED under `PHASE_L_L3_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`, following
`PHASE_L_L3_EXIT_REVIEW_PASS`. A0-A6 are Owner-accepted and merged. A6's accepted
live disposition remains PARTIAL (17 transport-degraded sources, six HTTP-200
sources, zero deterministic contract drift proven); its one-shot authority is
consumed and a second run is prohibited. L4-A0 inventory is Owner-accepted and merged under
`L4_A0_SECURITY_RESOURCE_BOUNDARY_INVENTORY_OWNER_ACCEPTED_FOR_MERGE`. L4-A1 is Owner-accepted and merged under
`L4_A1_NETWORK_EXPOSURE_REQUEST_SURFACE_HARDENING_OWNER_ACCEPTED_FOR_MERGE`.
L4-A2 is Owner-accepted and merged under `L4_A2_PATH_CONTAINMENT_HARDENING_OWNER_ACCEPTED_FOR_MERGE`; L4-A3 is Owner-accepted and merged; L4-A4 is Owner-accepted and merged through PR #373 at `a2dfd7ff7c062257a7c7c8f193fced4f9c707a29`; L4-A5 is Owner-accepted and merged at c8c23e2; L4-A6 is OWNER-ACCEPTED AND MERGED under `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE`, with technical disposition `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS` (PR #375; merge commit `9a3a274df1f2602dced30633ea5fa119bc39d0e6`); L4-A7 technical exit review passed under `PHASE_L_L4_EXIT_REVIEW_PASS`; L4 is CLOSED under `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` after A7 merge through PR #378 at `e184e2b5abfabc4656943d9734e4dc68230a8bbd`; L5 is CLOSED under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`; L5-A1 Owner-accepted and merged under `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_OWNER_ACCEPTED_FOR_MERGE` via PR #382 at `8ff92ca79af821a8641967184a26ee37db69d326`; L5-A2: OWNER-ACCEPTED AND MERGED under `L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_HARDENING_OWNER_ACCEPTED_FOR_MERGE`; L5-A3 is OWNER-ACCEPTED AND MERGED under `L5_A3_SEMANTIC_PROJECTION_LINEAGE_CONFORMANCE_HARDENING_OWNER_ACCEPTED_FOR_MERGE` via PR #386 at `cebc4d16ffa2db8903c72297ba2fdc00e60fb453`; L5-A4 is OWNER-ACCEPTED AND MERGED under `L5_A4_TEST_CATALOG_SKILL_GUIDE_PUBLICATION_INTEGRATION_OWNER_ACCEPTED_FOR_MERGE` via PR #388 at `11691c2eb9a33d2adbcce38fb59a50f822e15284`; L5-A5 is OWNER-ACCEPTED AND MERGED under `L5_A5_REPRESENTATIVE_EXISTING_FAMILY_CONFORMANCE_OWNER_ACCEPTED_FOR_MERGE` via PR #390 at `303e2ba444721f939ce74a5f2c15b0a5bb562a7a`; L5-A6 is OWNER-ACCEPTED AND MERGED under `L5_A6_INTEGRATED_DETERMINISTIC_EXTENSION_CONTRACT_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE` via PR #392 at `7748f18e33a64a912f920c6303f73da67b0ab788`; Owner acceptance record merged via PR #393 at `b7c37d2e6a78c2dce3f446bb118ff6f27f5a6059`; L5-A7 is OWNER-ACCEPTED AND MERGED via PR #395 at `fea5259f8214aa405ed4017c7e9727bbf6d63ea9`; L5 is CLOSED under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; L6-A0 is OWNER-ACCEPTED AND MERGED via PR #397 at `7ec798d682ac91db776608a5e9a6a98e179dd1ec`; L6-A1 is OWNER-ACCEPTED AND MERGED via PR #398 at `430f280f9c1b4f8d0f387503bb22044214126b39`; L6-A2 is AUTHORIZED and its technical candidate is COMPLETE / Owner acceptance PENDING; L6-A3+, L7 and Phase M remain NOT AUTHORIZED. See
`docs/governance/phase_l/PHASE_L_L4_A0_SECURITY_RESOURCE_BOUNDARY_INVENTORY_2026-10-17.md`,
`docs/governance/phase_l/PHASE_L_L4_A1_NETWORK_EXPOSURE_REQUEST_SURFACE_HARDENING_2026-10-17.md`,
and `docs/governance/phase_l/PHASE_L_L4_A2_PATH_CONTAINMENT_HARDENING_2026-10-17.md`.

### Historical entry - L3 source drift hardening after A7 technical exit review (2026-10-17)

Phase L is **STARTED**. L0 - Production Boundary & Architecture Contract remains frozen
under `PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN`. L1 Runtime Operability is CLOSED under
`PHASE_L_L1_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`.

L2 - Replay / Retention / Migration is **CLOSED** under
`PHASE_L_L2_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. A0 is complete, A1/A1-R1 are frozen, A2-A6 are
merged/closed, and the integrated A7 exit review passed under `PHASE_L_L2_EXIT_REVIEW_PASS`.
PR #353 merged the final L2 closure at `b84ba8a4ac4819d115de33e55cf9adf2a5801e00`.
The accepted L2 boundary preserves conservative retention, explicit backup/restore compatibility,
A5 `MIGRATION_REQUIRED` zero-restore-write semantics, verified A4 checkpoint/rollback lineage,
and no fabricated production Watchlist v0-to-v1 transformer. See
`docs/governance/phase_l/PHASE_L_L2_EXIT_REVIEW_2026-10-15.md` and the Phase L recovery index.

L3 — Source Drift Hardening is STARTED under explicit Owner entry authority.
L3-A0 inventory is COMPLETE under `L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_COMPLETE`, passed
independent review under `L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_ACCEPTANCE_REVIEW_PASS`, and is
Owner-accepted under `L3_A0_SOURCE_DRIFT_SURFACE_INVENTORY_OWNER_ACCEPTED_FOR_MERGE`; PR #355
merged at `1983c1d5363fe3253a3c5e556508ba5138163337`. L3-A1 TWSE MIS
returned-identity/response-contract guard passed independent review under
`L3_A1_TWSE_MIS_RESPONSE_CONTRACT_GUARD_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L3_A1_TWSE_MIS_RESPONSE_CONTRACT_GUARD_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #357
at `b2e1908fb5d2e584b38bc354f88df6e121b7b13b`. L3-A2 EOD diagnostic propagation passed independent review under
`L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L3_A2_EOD_DIAGNOSTIC_PROPAGATION_GUARD_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #359 at
`e521a2fcc73ecd40e819a0d51342abcd4a55354c`. L3-A3 Phase G research CSV structure and bounded
attempt provenance passed independent technical review under
`L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under
`L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_OWNER_ACCEPTED_FOR_MERGE`, and merged through
PR #361 at `ddd023f11a23420c096a5b20022848cfcf900db9`. L3-A4 H1 composite
negative-fixture candidate passed independent technical review under
`L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_ACCEPTANCE_REVIEW_PASS`; reviewer
verification reconciled direct missing-required-field coverage across P08/P09/P10
without production runtime changes. A4 is Owner-accepted under
`L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_OWNER_ACCEPTED_FOR_MERGE` and merged through PR #363 at
`ff330f94049adce93c72a9179b4d7b44d297fb2b`. L3-A5 passed independent technical review under `L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_ACCEPTANCE_REVIEW_PASS`, is Owner-accepted under `L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_OWNER_ACCEPTED_FOR_MERGE`, and merged through PR #365 at `d2b3be8bafa3ad0eebeec5ffbece1fc6a759b3bd`. A0-A6 are Owner-accepted and merged. A6 is Owner-accepted and merged under `L3_A6_BOUNDED_LIVE_SOURCE_DRIFT_RECERTIFICATION_OWNER_ACCEPTED_FOR_MERGE`; its technical live disposition is PARTIAL (17 transport-degraded sources, six HTTP-200 sources, zero deterministic contract drift proven), with its one-shot authority consumed and no second run permitted. A7 technical exit review passed under `PHASE_L_L3_EXIT_REVIEW_PASS`; L3 Owner-closed under `PHASE_L_L3_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`. L4-A0 through A4 are Owner-accepted and merged; A4 merged through PR #373 at `a2dfd7ff7c062257a7c7c8f193fced4f9c707a29`; L4-A5 is Owner-accepted and merged at c8c23e2; L4-A6 is OWNER-ACCEPTED AND MERGED under `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE`, with technical disposition `L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS` (PR #375; merge commit `9a3a274df1f2602dced30633ea5fa119bc39d0e6`); L4-A7 technical exit review passed under `PHASE_L_L4_EXIT_REVIEW_PASS`; L4 is CLOSED under `PHASE_L_L4_OWNER_ACCEPTED_FINAL_CLOSURE_PASS` after A7 merge through PR #378 at `e184e2b5abfabc4656943d9734e4dc68230a8bbd`; L5 is CLOSED under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; L5-A0 is Owner-accepted and merged via PR #380 at `241a5249987c008a28d959677704eee483a1c216`; L5-A1 Owner-accepted and merged under `L5_A1_MINIMUM_EVIDENCE_FAMILY_EXTENSION_CONTRACT_OWNER_ACCEPTED_FOR_MERGE` via PR #382 at `8ff92ca79af821a8641967184a26ee37db69d326`; L5-A2 is OWNER-ACCEPTED AND MERGED under `L5_A2_EXPLICIT_REGISTRATION_CONFORMANCE_HARDENING_OWNER_ACCEPTED_FOR_MERGE`; L5-A3 is OWNER-ACCEPTED AND MERGED under `L5_A3_SEMANTIC_PROJECTION_LINEAGE_CONFORMANCE_HARDENING_OWNER_ACCEPTED_FOR_MERGE` via PR #386 at `cebc4d16ffa2db8903c72297ba2fdc00e60fb453`; L5-A4 is OWNER-ACCEPTED AND MERGED under `L5_A4_TEST_CATALOG_SKILL_GUIDE_PUBLICATION_INTEGRATION_OWNER_ACCEPTED_FOR_MERGE` via PR #388 at `11691c2eb9a33d2adbcce38fb59a50f822e15284`; L5-A5 is OWNER-ACCEPTED AND MERGED under `L5_A5_REPRESENTATIVE_EXISTING_FAMILY_CONFORMANCE_OWNER_ACCEPTED_FOR_MERGE` via PR #390 at `303e2ba444721f939ce74a5f2c15b0a5bb562a7a`; L5-A6 is OWNER-ACCEPTED AND MERGED under `L5_A6_INTEGRATED_DETERMINISTIC_EXTENSION_CONTRACT_ACCEPTANCE_OWNER_ACCEPTED_FOR_MERGE` via PR #392 at `7748f18e33a64a912f920c6303f73da67b0ab788`; Owner acceptance record merged via PR #393 at `b7c37d2e6a78c2dce3f446bb118ff6f27f5a6059`; L5-A7 is OWNER-ACCEPTED AND MERGED via PR #395 at `fea5259f8214aa405ed4017c7e9727bbf6d63ea9`; L5 is CLOSED under `PHASE_L_L5_OWNER_ACCEPTED_FINAL_CLOSURE_PASS`; L6-A0 is OWNER-ACCEPTED AND MERGED via PR #397 at `7ec798d682ac91db776608a5e9a6a98e179dd1ec`; L6-A1 is OWNER-ACCEPTED AND MERGED via PR #398 at `430f280f9c1b4f8d0f387503bb22044214126b39`; L6-A2 is AUTHORIZED and its technical candidate is COMPLETE / Owner acceptance PENDING; L6-A3+, L7 and Phase M remain NOT AUTHORIZED. See
`docs/governance/phase_l/PHASE_L_L3_A0_SOURCE_DRIFT_SCOPE_AND_INVENTORY_2026-10-15.md` and
`docs/governance/phase_l/PHASE_L_L3_A3_RESEARCH_SOURCE_STRUCTURE_AND_PROVENANCE_GUARD_2026-10-15.md`;
the A4 record is
`docs/governance/phase_l/PHASE_L_L3_A4_H1_COMPOSITE_NEGATIVE_FIXTURE_MATRIX_2026-10-15.md`.
`docs/governance/phase_l/PHASE_L_L3_A5_SOURCE_LIFECYCLE_THROTTLING_AND_PUBLICATION_DRIFT_CONTRACT_2026-10-15.md` records the accepted deterministic contract, technical review, Owner authorization, and merge provenance.

Frozen L0 implementation sequencing maps Source Drift Hardening to current L3;
the older durable subsection label `L.4 Source Drift Management` remains
historical roadmap organization and is not rewritten. No architecture conflict
exists; durable subject matter remains valid while L0 controls tranche sequencing.

## L.0 Phase Goal

把已經能用的產品，整理成：

> **可以長期維護、可以持續增加 evidence family，而不讓治理與可靠性隨規模崩解的平台。**

## L.1 Observability

至少：

```text
structured logs
trace / request IDs
execution IDs
source timing
adapter timing
failure reason codes
resource usage
network attempt accounting
```

不得把敏感內容或大 raw payload 無限制寫 log。

## L.2 Replay & Audit

建立：

```text
request replay semantics
result replay semantics
artifact reference retention
audit retention policy
hash verification
reproduction limits
```

要能區分 replay old evidence 與 re-fetch current evidence。

## L.3 Schema & Migration Policy

至少：

```text
schema compatibility policy
database migration policy
Watchlist migration
Security Master release compatibility
result compatibility
Skill compatibility
MCP tool-schema compatibility
```

禁止 silent incompatible migration。

## L.4 Source Drift Management

每個 source adapter 必須能面對：

```text
schema drift
field rename
encoding change
empty-but-200 response
delayed publication
unexpected universe delta
HTTP failure
rate limiting
source removal
```

重要 source 需建立 contract probes、drift fixtures、failure reason code。

## L.5 Security Hardening

至少：

```text
localhost exposure review
path containment
input bounds
output bounds
dependency review
supply-chain review
MCP prompt/tool injection boundary
authorization review
secret handling if future source requires it
```

維持 no broker credential handling。

## L.6 Resource & Load Boundaries

驗證：

```text
large Watchlist
multi-target
large disclosure result
large supported evidence result
long AI handoff
bounded concurrent local calls
timeout
memory
disk retention
```

確定 max targets、max evidence rows、max payload、max artifacts 都有可預期行為。

## L.7 Evidence Family Extension Contract

未來新增 new evidence family 應有固定流程：

```text
source inventory
→ source contract
→ capability
→ schema
→ adapter
→ normalization
→ timing/currentness
→ Result projection
→ tests
→ Skill / guide update
→ acceptance
```

不能每次新增資料都重新修改整個 architecture。

## L.8 CI / Release Governance

包含：

```text
required CI profile
Windows compatibility
fresh clone
non-network deterministic profile
network acceptance profile
release manifest
dependency lock
branch / merge protection where appropriate
release reproducibility
```

### Phase L 預期成果

> TW-Market 從「完成很多功能的 repository」進化成「可以長期擴張與維護的 evidence platform」。

# [ ] Phase M — Agent-Scheduled Research & Bounded Monitoring

## M.0 Phase Goal

Phase M 的 Automation 定義正式為：

> **讓外部 Agent / scheduler 安全地定時或短時間重複呼叫 TW-Market；不是讓 TW-Market 默默變成永久 background polling daemon。**

核心：

```text
Scheduling belongs to the invoking Agent by default.

TW-Market remains:
bounded
auditable
explicit
evidence-oriented
```

## M.1 Scheduled One-Shot Research

典型：

```text
每天 10:00
→ Agent invokes TW-Market once
→ Research Evidence Bundle
→ AI writes report

每天 12:00
→ invoke once
→ noon research update

after close
→ EOD research
```

TW-Market 不需要理解 cron / calendar / daily schedule。

它只需在每次 invocation：Validate → Preview / policy authorization → Execute Once → Result。

## M.2 Research Report Handoff

建立適合 scheduled Agent 使用的：

```text
Research Evidence Bundle
→ AI report-generation contract
```

TW-Market 提供 facts、periods、currentness、changes、missing、citations。

AI 負責 narrative、comparison、executive summary、user-facing report。

TW-Market 不直接成為 investment commentary generator。

## M.3 Bounded Repeated Research Session

支援例如：

```text
10:00 → 11:00
every 5 minutes
max 12 invocations
targets = [...]
data_needs = [...]
```

必要 contract：

```text
session_id
start
end
interval
max_invocations
max_network_requests
targets
data_needs
per-invocation receipt
result sequence
```

不得 monitor_forever = true、unbounded polling、silent extension。

## M.4 External Scheduler First

預設由 ChatGPT / Agent scheduler、Hermes scheduler、OS scheduler、CI scheduler 或 other agent runner 負責 clock / recurrence。

TW-Market does not need internal scheduler。

只有在未來證明 external orchestration cannot satisfy a governed requirement 才考慮 internal scheduling component。

## M.5 Deterministic Condition Contract

進一步的盤中監控可支援：

```text
if deterministic evidence condition becomes true
→ return condition_met event
```

例如概念：

```text
price_change_pct <= -3
AND
relative_volume_20d >= 2
```

AI 可以把自然語言需求轉成 condition contract；但 runtime 應 deterministically evaluate explicit condition。

不得讓 LLM subjective judgement 成為每五分鐘是否觸發警報的唯一 authority。

## M.6 Alert Delivery Boundary

預設：

```text
condition event
→ returned to Agent / scheduler
→ Agent decides notification channel
```

TW-Market 不必第一版內建 email、LINE、Telegram、SMS、push。

## M.7 Monitoring Authorization Envelope

Repeated monitoring 的 authorization 不等於 unlimited authorization。

應綁：

```text
exact session
targets
data_needs
time window
interval
maximum calls
maximum network requests
condition contract
expiry
```

Session 過期 fail closed。

## M.8 Security Master Refresh Boundary

Security Master 仍不是高頻資料。

如未來允許 Agent 定期觸發 update：

```text
must be explicit opt-in policy
must retain qualification
must retain atomic activation
must retain old ACTIVE on failure
```

不得把 market monitoring schedule 自動等同於 refresh identity authority。

## M.9 Scheduled / Monitoring Acceptance

至少：

```text
daily one-shot research
scheduled noon report
bounded 1-hour monitoring
max invocation enforcement
session expiry
network bound
source failure mid-session
stale data mid-session
corporate action during session
condition not met
condition met exactly once
duplicate alert suppression policy
Agent restart
machine sleep / missed invocation semantics
timezone / market-session boundary
```

### Phase M 預期成果

使用者可以要求外部 Agent：

> 「每天中午幫我做一次這份 Watchlist 的盤中研究報告。」

或者：

> 「今天 10:00 到 11:00，每 5 分鐘檢查一次 2330；如果明確條件成立就提醒我。」

而 TW-Market 核心仍保持 local-first、bounded、auditable、non-trading、explicit。

---

# 6. Cross-Phase Global Rules

所有 G–M 都必須遵守。

## 6.1 Official-source-first

優先 TWSE、TPEx、MOPS、TAIFEX 與其他 authoritative Taiwan market institutions。

第三方資料只能在 official source unavailable、value is clear、provenance is explicit、legal / usage terms acceptable 後再評估。

## 6.2 Timing is part of the data

每一個 evidence family 都要能回答：

```text
What period does this represent?
When was it published?
When did we observe it?
When does it become effective?
How stale can it be?
```

不得用單一 timestamp 掩蓋不同時間語意。

## 6.3 Missing is not zero

```text
missing
unknown
not published
not supported
source failed
stale
not applicable
```

必須可區分。

## 6.4 Evidence is not conclusion

Canonical evidence 可以包含 facts、deterministic calculations、descriptive comparisons。

不得偷偷加入 buy / sell、price target、bullish / bearish verdict、causal claim without evidence。

## 6.5 No second product core

後續功能不得建立 parallel identity authority、parallel request contract、parallel result contract、parallel planner、parallel execution model。

## 6.6 Scope grows only when semantics are governed

能抓到資料不代表應加入產品。

每次擴張都必須先回答 source authority、identity、time semantics、normalization、currentness、missing、failure、value to AI。

---

# 7. Long-Term Product Boundary

TW-Market 的長期目標：

> **Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents**

它應該成為可靠的：

```text
identity layer
market evidence layer
official research evidence layer
interpretation context layer
audit / lineage layer
agent integration layer
```

它不是：

```text
broker
autonomous trader
portfolio accounting system
full backtesting platform
technical-analysis signal engine
general-purpose web crawler
general-purpose RAG
AI investment advisor
```

上述系統都可以成為 consumer，但不應全部被 TW-Market 吞入核心。

---

# 8. Target Architecture After V3.2 Future Phases

```text
                       Human
                         │
                         ▼
                    AI / Agent
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       ChatGPT          Claude         Gemini
          │              │              │
          └──────────────┴──────────────┘
                         │
                         ▼
              Unified Evidence Request
                         │
                         ▼
        ┌──────────────────────────────────┐
        │            TW-Market             │
        │                                  │
        │ Taiwan Market Identity Service   │
        │ Market Evidence                  │
        │ Official Disclosures             │
        │ Fundamentals                     │
        │ Corporate Actions                │
        │ Regulatory Context               │
        │ Historical Reference             │
        │ Optional Cross-Market Context    │
        │ Currentness / Missing / Audit    │
        └──────────────────────────────────┘
                         │
                         ▼
               Research Evidence Bundle
                         │
                         ▼
                    AI / Agent
                         │
              analysis / report / alert
```

Scheduled use：

```text
External Agent Scheduler
          │
          ├─ 10:00 invoke once
          ├─ 12:00 invoke once
          └─ every 5m for bounded 1h session
                         │
                         ▼
              same TW-Market contract
```

---

# 9. V3.2 Phase Checklist

```text
[x] Phase A — Governed Evidence Core
[x] Phase B — AI Guide & Portable Skill Baseline
[x] Phase C — Unified Contract & Runtime
[x] Phase D — Unified Workbench
[x] Phase E — Local Service, MCP & Real-Agent Closed Loop
[x] Phase E-P — Portability, Identity Service & Skill Realignment
[x] Phase F — Persistent Watchlist & Productization
[x] V1 Release Gate — v1.0.0 Stable Productization

[ ] Phase G — Research Evidence Expansion
[ ] Phase H — Interpretation & Historical Reference
[x] Phase I — Cross-Market & Optional Context
[x] Phase J — Integrated Research Acceptance
[x] Phase K — Multi-Agent Compatibility & Evaluation
[ ] Phase L — Production Hardening & Extension Architecture
[ ] Phase M — Agent-Scheduled Research & Bounded Monitoring
```

---

# 10. V3.2 Principal Product Decision

```text
PRESERVE:
V1 frozen evidence contract
local-first architecture
six-tool MCP
ISIN durable identity
installation-local Security Master
explicit execute-once
complete bounded evidence
auditability
non-trading boundary

EXPAND NEXT:
official research evidence
interpretation safety
historical context
optional cross-market context

VALIDATE:
integrated research scenarios
multi-agent behavior

HARDEN:
platform extensibility
observability
migration
security
source drift

AUTOMATE LAST:
external-agent scheduled research
bounded repeated monitoring
deterministic alert conditions
```

最終原則：

> **先把證據做深、把解讀做安全、把跨 Agent 使用做穩，再讓排程與監控把這些成熟能力放大。**
